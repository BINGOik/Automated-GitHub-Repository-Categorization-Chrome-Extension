from __future__ import annotations

from typing import Any, Dict, List, Optional

# Kimi/Moonshot API is OpenAI-SDK compatible
# Docs: https://api.moonshot.cn/v1 (OpenAI SDK compatible) :contentReference[oaicite:1]{index=1}
try:
    # OpenAI python SDK v1.x
    from openai import OpenAI
except Exception as e:
    OpenAI = None  # type: ignore


class DomainClassifier:
    """
    Kimi version of your gpt_predictor.DomainClassifier
    Usage:
        domain_classifier = DomainClassifier(api_key="YOUR_MOONSHOT_API_KEY")
        result = domain_classifier.classify(readme_text=..., prediction_dict=...)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "kimi-k2-turbo-preview",
        base_url: str = "https://api.moonshot.cn/v1",
        timeout: float = 30.0,
        use_proxy: bool = False,
        http_proxy: str = "http://localhost:7890",
        https_proxy: str = "http://localhost:7890",
    ):
        if not api_key:
            raise ValueError("api_key is required (Moonshot/Kimi API key).")

        if OpenAI is None:
            raise RuntimeError(
                "OpenAI SDK not found or too old. Please install/upgrade: pip install --upgrade 'openai>=1.0.0'"
            )

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

        # Optional proxy support (default off)
        if use_proxy:
            import os
            os.environ["http_proxy"] = http_proxy
            os.environ["https_proxy"] = https_proxy

        # Create OpenAI-compatible client pointing to Moonshot
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def openai_sdk_chat_http_api(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Returns the assistant content (string). None if request fails.
        """
        try:
            resp = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=0,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content
            return (content or "").strip()
        except Exception as e:
            print(f"Kimi API request error: {e}")
            return None

    def classify(self, readme_text: str, prediction_dict: Dict[str, Any]) -> str:
        """
        传入 readme 文本 + 预测结果字典，返回 Result: 后面的分类字符串
        （保持和你 gpt_predictor.py 的输出格式/行为一致）
        """
        predictions = []
        for i in range(1, 13):
            class_key = f"Top{i} Class"
            prob_key = f"Top{i} Probability"
            if class_key in prediction_dict and prob_key in prediction_dict:
                predictions.append(
                    f"Top{i}: {prediction_dict[class_key]} ({prediction_dict[prob_key]})"
                )
        predictions_str = ", ".join(predictions)

        system_prompt = (
            "You are a open source project's development domain classifier. "
            "Your task is to classify the domain of a software development project according "
            "to the following text of the project description and README files. Categories include: "
            "desktop applications; ai and machine learning applications; WeChat application development; "
            "enterprise applications; web applications; mobile applications; code development tools or plugins; "
            "Server application; Game development; application Plugins; Others; 未分类 . "
            "The current model predictions for this project are as follows - "
            + predictions_str
            + ". "
            "We believe there may be issues with the labeling. Please relabel this project according to its actual "
            "application scope. Please provide the Result: and Reasons: "
            + readme_text
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please output Result: and Reasons: based on the README above."},
        ]

        response = self.openai_sdk_chat_http_api(messages, model=self.model)
        return self.extract_result_line(response)

    @staticmethod
    def extract_result_line(response: Optional[str]) -> str:
        """
        提取首个出现的 "Result:" 后面的内容（去除前后空格）
        """
        if not response:
            return ""
        for line in response.splitlines():
            if line.strip().lower().startswith("result:"):
                return line.split(":", 1)[1].strip()
        return ""
