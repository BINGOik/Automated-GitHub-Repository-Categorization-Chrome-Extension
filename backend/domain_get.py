import os
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from svm_predictor import Predictor
from readme_words import extract_keywords_from_readme
from kimi_predictor import DomainClassifier

app = Flask(__name__)
CORS(app, supports_credentials=True)

predictor = Predictor(
    model_path='linear_svc_model.pkl',
    label_mapping_path='label_mapping.pkl',
    scaler_path='scaler.pkl',
    keyword_dict_path='keyword_dict.pkl'
)


GITHUB_TOKEN = "***"


PROB_GAP_THRESHOLD = 0.15


def fetch_readme(owner: str, repo: str) -> str:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN 未配置（请设置环境变量 GITHUB_TOKEN）")

    headers_raw = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "domain-classifier-backend",
    }

    # 1) 直接拿默认 README 原文
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    r = requests.get(url, headers=headers_raw, timeout=15)
    if r.ok:
        return r.text

    # 2) 兜底：contents/README.md（base64）
    headers_json = headers_raw.copy()
    headers_json["Accept"] = "application/vnd.github+json"
    url2 = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
    r2 = requests.get(url2, headers=headers_json, timeout=15)
    if r2.ok:
        data = r2.json()
        content = data.get("content")
        if content:
            return base64.b64decode(content).decode("utf-8", errors="ignore")

    raise RuntimeError(
        f"README 获取失败：/readme={r.status_code} {r.text[:120]} | /contents={r2.status_code} {r2.text[:120]}"
    )


@app.route("/domain", methods=["POST", "OPTIONS"])
def domain_post():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}

    owner = (data.get("owner") or "").strip()
    repo = (data.get("repo") or "").strip()
    repo_url = (data.get("repo_url") or "").strip()

    # ✅ 兼容：允许传 repo_url: https://github.com/owner/repo/...
    if (not owner or not repo) and repo_url:
        try:
            parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
        except Exception:
            pass

    if not owner or not repo:
        return jsonify({"error": "请提供 owner/repo 或 repo_url"}), 400

    # ✅ GPT 需要的 OpenAI Key（沿用你旧版逻辑：前端传 api_key）
    api_key = (data.get("api_key") or "").strip()

    # 1) 后端拉 README
    try:
        readme_text = fetch_readme(owner, repo)
    except Exception as e:
        app.logger.exception("GitHub README 获取失败")
        return jsonify({"error": str(e)}), 500

    # 2) 抽关键词
    keywords = extract_keywords_from_readme(readme_text)
    if not keywords:
        return jsonify({"tags": keywords, "result": "", "svm_result": []})

    # 3) SVM 预测
    try:
        svm_result = predictor.predict_from_keyword(keywords)
    except Exception as e:
        app.logger.exception("SVM预测失败")
        return jsonify({"error": "SVM预测失败: " + str(e)}), 500

    if not svm_result:
        return jsonify({"tags": keywords, "result": "", "svm_result": []})

    # 4) 概率差判断
    prob1 = svm_result[0].get("prob", 0.0) if len(svm_result) > 0 else 0.0
    prob2 = svm_result[1].get("prob", 0.0) if len(svm_result) > 1 else 0.0

    # ✅ 差值足够大：直接用 SVM Top1
    if (prob1 - prob2) >= PROB_GAP_THRESHOLD:
        print("svm use")
        return jsonify({
            "tags": keywords,
            "result": svm_result[0]["class"],
            "svm_result": svm_result
        })

    # ✅ 差值不够：用你写好的 DomainClassifier 做判定
    if not api_key:
        # 没有 key 无法调用 GPT：回退 Top1（也可改成直接报错）
        return jsonify({
            "tags": keywords,
            "result": svm_result[0]["class"],
            "svm_result": svm_result,
            "warning": "prob gap <= 0.15 but no api_key provided; fallback to svm top1"
        })

    try:
        domain_classifier = DomainClassifier(api_key=api_key)  # :contentReference[oaicite:1]{index=1}
        prediction_dict = {}
        for i in range(min(len(svm_result), 12)):
            prediction_dict[f"Top{i + 1} Class"] = svm_result[i]["class"]
            prediction_dict[f"Top{i + 1} Probability"] = svm_result[i]["prob"]

        # 直接用你的 classify(readme_text, prediction_dict) :contentReference[oaicite:2]{index=2}
        result = domain_classifier.classify(readme_text=readme_text, prediction_dict=prediction_dict)
        print("kimi use")
    except Exception as e:
        app.logger.exception("大模型判定失败")
        return jsonify({"error": "大模型判定失败: " + str(e)}), 500

    return jsonify({
        "tags": keywords,
        "result": result,
        "svm_result": svm_result
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
