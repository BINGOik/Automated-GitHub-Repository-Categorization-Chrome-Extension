# 测试文档

> 本文档说明项目测试体系、运行方式、覆盖目标、Mock 策略、CI 建议和常见问题。  
> 测试目标是保证后端 API、GitHub README 获取、关键词抽取、SVM 推理、LLM 二次判定、Chrome 插件页面解析和端到端链路的稳定性。

---

## 1. 测试目标

项目测试需要覆盖以下核心问题：

1. `/domain` 接口是否能接收合法请求并返回标准 JSON；
2. 请求参数缺失时是否返回合理错误；
3. GitHub README 获取失败时是否能正确处理；
4. README 关键词抽取是否稳定；
5. SVM 模型推理是否返回合法类别和概率；
6. 低置信样本是否能触发 LLM 二次判定逻辑；
7. 无 API Key 时是否能回退到 SVM Top1；
8. Chrome 插件是否能正确识别仓库页面和列表页；
9. 插件是否能正确渲染分类徽标；
10. 端到端链路是否能从仓库 URL 得到最终分类结果。

---

## 2. 测试目录建议

推荐测试目录结构如下：

```text
tests/
├── README.md
├── conftest.py
│
├── backend/
│   ├── test_api_classify.py
│   ├── test_github_fetcher.py
│   ├── test_feature_extractor.py
│   ├── test_model_predictor.py
│   └── test_llm_refiner.py
│
├── extension/
│   ├── test_extension_static.py
│   ├── test_badge_rendering.js
│   └── test_content_parser.js
│
├── fixtures/
│   ├── sample_readme_web.md
│   ├── sample_readme_plugin.md
│   └── sample_response.json
│
└── integration/
    └── test_end_to_end_classification.py
```

---

## 3. 测试模块划分

| 模块 | 建议测试数量 | 覆盖范围 |
|---|---:|---|
| 后端 API | 8 | 分类接口、请求校验、OPTIONS、异常响应 |
| GitHub 数据获取 | 6 | README 获取、base64 兜底、网络错误、超时 |
| 特征抽取 | 8 | Markdown 清洗、URL 去除、停用词过滤、TopK |
| 模型推理 | 6 | one-hot 编码、softmax、类别排序、topn |
| LLM 二次判定 | 5 | 低置信判断、API Key、Result 解析、异常回退 |
| Chrome 插件 | 8 | URL 解析、页面识别、徽标渲染、缓存、配置读取 |
| 集成测试 | 5 | 从请求到最终分类结果的完整链路 |
| 合计 | 46 | 覆盖主要业务路径与异常路径 |

---

## 4. 安装测试依赖

项目依赖中已经包含 `pytest` 和 `pytest-cov`。如果需要并行测试，可额外安装 `pytest-xdist`。

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-xdist
```

---

## 5. 运行测试

### 5.1 运行全部测试

```bash
pytest tests/ -v
```

### 5.2 运行带覆盖率的测试

```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing
```

生成 HTML 覆盖率报告后，可打开：

```bash
# macOS / Linux
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### 5.3 运行指定测试目录

```bash
pytest tests/backend/ -v
pytest tests/integration/ -v
pytest tests/extension/ -v
```

### 5.4 运行指定测试文件

```bash
pytest tests/backend/test_api_classify.py -v
pytest tests/backend/test_feature_extractor.py -v
pytest tests/integration/test_end_to_end_classification.py -v
```

### 5.5 运行指定测试函数

```bash
pytest tests/backend/test_api_classify.py::test_domain_accepts_owner_repo -v
```

### 5.6 并行运行测试

```bash
pytest tests/ -n auto
```

### 5.7 只看失败详情

```bash
pytest tests/ -vv --tb=short
```

---

## 6. Pytest 标记建议

建议在 `pytest.ini` 中配置标记：

```ini
[pytest]
testpaths = tests
addopts = -ra
markers =
    unit: unit tests that do not require real network or model files
    integration: integration tests for the classification pipeline
    extension: tests for Chrome extension static behavior
    slow: slow tests
```

使用方式：

```bash
pytest -m unit
pytest -m integration
pytest -m extension
pytest -m "not slow"
```

---

## 7. Mock 策略

项目测试应尽量避免依赖真实网络、真实模型文件和真实 LLM API。

### 7.1 为什么需要 Mock

如果测试依赖真实外部资源，会出现以下问题：

| 外部依赖 | 风险 |
|---|---|
| GitHub API | 网络不稳定、限流、Token 缺失 |
| `.pkl` 模型文件 | 文件路径、版本、体积、环境兼容性问题 |
| Kimi / OpenAI API | 需要真实 Key、调用成本、响应不稳定 |
| Chrome 真实页面 | GitHub DOM 经常变化，端到端测试难以稳定 |
| 浏览器插件环境 | CI 中难以直接运行完整 Chrome Extension |

因此，单元测试应以 Mock 为主，真实调用仅保留在手工验证或少量可选集成测试中。

---

## 8. 后端 API 测试

### 8.1 测试目标

后端 API 测试主要验证：

1. `POST /domain` 可接收 `owner/repo`；
2. `POST /domain` 可接收 `repo_url`；
3. 缺少参数时返回 400；
4. README 获取异常时返回 500；
5. SVM 高置信时返回 SVM Top1；
6. SVM 低置信且无 API Key 时返回 warning；
7. SVM 低置信且有 API Key 时调用 LLM；
8. 响应 JSON 包含 `tags / result / svm_result`。

### 8.2 建议 Mock 对象

| 对象 | Mock 方法 |
|---|---|
| `fetch_readme` | 返回固定 README 文本 |
| `extract_keywords_from_readme` | 返回固定关键词字符串 |
| `predictor.predict_from_keyword` | 返回固定 SVM 候选类别 |
| `DomainClassifier.classify` | 返回固定 LLM 分类 |
| `requests.get` | 模拟 GitHub API 成功或失败 |

### 8.3 典型测试用例

#### 参数合法

```python
def test_domain_accepts_owner_repo(client, monkeypatch):
    response = client.post("/domain", json={
        "owner": "facebook",
        "repo": "react"
    })
    assert response.status_code == 200
```

#### 参数缺失

```python
def test_domain_requires_repo_identity(client):
    response = client.post("/domain", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()
```

#### 高置信 SVM

```python
def test_domain_uses_svm_when_probability_gap_is_large(client, monkeypatch):
    # mock svm_result:
    # [
    #   {"class": "网页应用", "prob": 0.90},
    #   {"class": "服务器应用", "prob": 0.05}
    # ]
    response = client.post("/domain", json={
        "owner": "facebook",
        "repo": "react"
    })
    data = response.get_json()
    assert data["result"] == "网页应用"
```

#### 低置信无 API Key

```python
def test_domain_falls_back_to_svm_when_low_confidence_without_api_key(client):
    response = client.post("/domain", json={
        "owner": "demo",
        "repo": "ambiguous"
    })
    data = response.get_json()
    assert "warning" in data
```

---

## 9. GitHub README 获取测试

### 9.1 测试目标

| 测试点 | 说明 |
|---|---|
| `/readme` 成功 | 直接返回 README 原文 |
| `/readme` 失败但 `/contents/README.md` 成功 | base64 解码并返回文本 |
| 两个接口都失败 | 抛出 RuntimeError |
| 网络超时 | 正确处理异常 |
| Token 缺失 | 返回配置错误 |
| 非 UTF-8 内容 | 使用 ignore 策略避免崩溃 |

### 9.2 Mock 建议

使用 `monkeypatch` 替换 `requests.get`：

```python
class FakeResponse:
    def __init__(self, ok, text="", status_code=200, json_data=None):
        self.ok = ok
        self.text = text
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data
```

---

## 10. 特征抽取测试

### 10.1 测试目标

关键词抽取测试应覆盖：

1. 空文本返回空字符串；
2. Markdown 代码块被移除；
3. 行内代码被移除；
4. URL 被移除；
5. Markdown 链接保留文本；
6. 英文统一转小写；
7. 停用词被过滤；
8. TopK 限制生效。

### 10.2 输入示例

```markdown
# React Todo App

This is a web application built with React and Flask.

```bash
npm install
```

Visit https://example.com for docs.
```

期望关键词中包含：

```text
react todo web application built flask
```

不应包含：

```text
npm install https example.com
```

---

## 11. SVM 推理测试

### 11.1 测试目标

SVM 推理测试应覆盖：

| 测试点 | 说明 |
|---|---|
| 模型文件加载 | Predictor 初始化时调用 joblib.load |
| 关键词 one-hot 编码 | 已知关键词位置置 1 |
| 未知关键词忽略 | 字典外关键词不报错 |
| softmax 输出 | 概率和接近 1 |
| 类别排序 | 按概率从高到低返回 |
| topn 参数 | 只返回指定数量候选 |

### 11.2 Mock 模型

可以用假模型替代真实 `.pkl`：

```python
class FakeModel:
    def decision_function(self, X):
        return [[2.0, 1.0, 0.1]]
```

假 scaler：

```python
class FakeScaler:
    def transform(self, X):
        return X
```

这样无需依赖真实模型文件即可测试推理逻辑。

---

## 12. LLM 二次判定测试

### 12.1 测试目标

LLM 相关测试应覆盖：

1. `api_key` 缺失时抛出错误；
2. OpenAI SDK 缺失时提示安装；
3. 传入 prediction_dict 后能构造候选类别列表；
4. 响应中存在 `Result:` 时能正确提取；
5. 响应为空或格式错误时返回空字符串。

### 12.2 输出解析测试

```python
def test_extract_result_line():
    response = "Result: 应用插件\nReasons: Chrome Extension"
    assert DomainClassifier.extract_result_line(response) == "应用插件"
```

### 12.3 异常响应测试

```python
def test_extract_result_line_returns_empty_for_invalid_response():
    assert DomainClassifier.extract_result_line(None) == ""
    assert DomainClassifier.extract_result_line("No result here") == ""
```

---

## 13. Chrome 插件测试

### 13.1 当前测试方式

当前 `package.json` 中 JavaScript 测试 Runner 尚未正式配置，因此建议使用两种方式：

1. **Python 静态测试**  
   通过 pytest 检查 `manifest.json`、`content.js`、`popup.js` 中的关键配置和字符串。

2. **JS 参考测试文件**  
   在 `tests/extension/` 中保留 `test_badge_rendering.js` 和 `test_content_parser.js`，后续接入 Jest、Vitest 或 Playwright 后可直接迁移。

### 13.2 静态测试内容

| 文件 | 测试点 |
|---|---|
| `manifest.json` | `manifest_version = 3` |
| `manifest.json` | 包含 `https://github.com/*` host permission |
| `manifest.json` | 包含 `http://127.0.0.1:8000/*` host permission |
| `manifest.json` | content script 匹配 GitHub |
| `content.js` | 包含 API 地址 `/domain` |
| `content.js` | 包含 `chrome.storage.local` |
| `content.js` | 包含 `sessionStorage` 缓存 |
| `content.js` | 包含徽标相关 class/id |
| `popup.js` | 包含插件开关逻辑 |
| `popup.js` | 包含 API Key 或 Token 存储逻辑 |

### 13.3 后续 JS 测试 Runner 建议

推荐接入 Vitest 或 Jest。

示例依赖：

```bash
npm install -D vitest jsdom
```

示例 `package.json`：

```json
{
  "scripts": {
    "test": "vitest run",
    "test:python": "pytest tests/ -v"
  },
  "devDependencies": {
    "vitest": "^2.0.0",
    "jsdom": "^24.0.0"
  }
}
```

---

## 14. 集成测试

### 14.1 测试目标

集成测试验证从 API 请求到最终分类结果的完整链路，但仍应 Mock 外部资源：

```text
client.post("/domain")
      ↓
mock fetch_readme
      ↓
extract keywords
      ↓
mock predictor
      ↓
confidence gap
      ↓
optional mock LLM
      ↓
response JSON
```

### 14.2 典型用例

| 用例 | 期望 |
|---|---|
| Web README | 返回“网页应用” |
| Chrome Extension README | 返回“应用插件” |
| 低置信有 API Key | 调用 LLM 并返回 LLM 类别 |
| 低置信无 API Key | 返回 SVM Top1 和 warning |
| README 为空 | 返回空 result 或未分类逻辑 |

---

## 15. 覆盖率目标

建议覆盖率目标：

| 指标 | 目标 |
|---|---:|
| 后端语句覆盖率 | ≥ 80% |
| API 路由分支覆盖率 | ≥ 80% |
| 特征抽取函数覆盖率 | ≥ 90% |
| SVM 预测逻辑覆盖率 | ≥ 80% |
| LLM 输出解析覆盖率 | ≥ 90% |
| 插件静态检查覆盖 | 覆盖核心配置和关键字符串 |

运行覆盖率：

```bash
pytest tests/ --cov=backend --cov-report=term-missing
```

查看未覆盖行后，优先补充：

1. 异常路径；
2. 低置信分支；
3. 空输入分支；
4. 外部 API 失败分支。

---

## 16. CI 建议

建议使用 GitHub Actions 自动运行测试。

示例 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  python-tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-xdist

      - name: Run tests
        run: |
          pytest tests/ -v --cov=backend --cov-report=term-missing
```

如果后续接入 JS 测试，可新增 Node job：

```yaml
  js-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - run: npm install

      - run: npm test
```

---

## 17. 测试数据建议

### 17.1 Web 应用 README fixture

```markdown
# React Todo App

A web application built with React, TypeScript and Vite.
It provides a browser-based task management interface.
```

期望类别：

```text
网页应用
```

### 17.2 应用插件 README fixture

```markdown
# GitHub Badge Chrome Extension

A Chrome extension that injects category badges into GitHub repository pages.
It runs as a browser extension and modifies GitHub UI.
```

期望类别：

```text
应用插件
```

### 17.3 服务器应用 README fixture

```markdown
# Flask Auth API

A backend service that provides REST API endpoints for user authentication.
It uses Flask, PostgreSQL and JWT.
```

期望类别：

```text
服务器应用
```

---

## 18. 常见问题

### Q1：测试导入 `domain_get.py` 时直接加载模型失败

原因：

`domain_get.py` 顶层会初始化 `Predictor` 并加载 `.pkl` 文件。

解决方式：

- 在测试中用 `monkeypatch` 或 import 前 stub 掉相关模块；
- 使用 `conftest.py` 注入假的 `Predictor`；
- 或将后端代码重构为应用工厂模式，例如 `create_app()`。

### Q2：测试访问了真实 GitHub API

原因：

没有 Mock `requests.get` 或 `fetch_readme`。

解决方式：

- 单元测试中始终 Mock 网络；
- 将真实网络测试标记为 `@pytest.mark.slow`；
- CI 默认跳过真实网络测试。

### Q3：LLM 测试需要真实 API Key

不建议在自动化测试中调用真实 LLM。

解决方式：

- Mock `DomainClassifier.classify`；
- 单独测试 `extract_result_line`；
- 将真实 LLM 调用放入手工测试或本地可选测试。

### Q4：Chrome 插件 JS 测试无法运行

当前项目尚未配置 JavaScript 测试 Runner。可先使用 pytest 做静态检查，后续再接入 Vitest/Jest。

### Q5：覆盖率低

优先补以下测试：

1. 参数错误；
2. GitHub API 失败；
3. README 为空；
4. SVM 预测异常；
5. 低置信无 API Key；
6. LLM 调用异常；
7. 插件配置缺失。

---

## 19. 测试通过标准

一次完整提交建议满足：

- `pytest tests/ -v` 全部通过；
- 后端覆盖率不低于 80%；
- 不依赖真实 GitHub API；
- 不依赖真实 LLM API Key；
- 不提交真实密钥；
- 插件核心配置通过静态检查；
- 新增功能同步新增测试；
- 修改类别体系时更新 fixtures 和断言。

---

## 20. 小结

本项目测试的重点是隔离外部依赖，验证核心业务逻辑。测试不应依赖真实网络、真实大模型或真实浏览器页面，而应通过 Mock 构造稳定、可重复的输入输出。

一句话原则：

> 外部服务用 Mock，核心逻辑用断言，端到端链路用小规模集成测试兜底。
