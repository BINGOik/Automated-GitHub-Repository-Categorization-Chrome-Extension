# 后端 API 文档

> 本文档说明 Chrome Extension 与 Flask 后端之间的接口约定。  
> 当前核心接口为 `POST /domain`，用于根据 GitHub 仓库信息返回仓库领域分类结果。

---

## 1. 接口概览

| 项目 | 内容 |
|---|---|
| 服务类型 | Flask 本地后端服务 |
| 默认 Host | `127.0.0.1` |
| 默认端口 | `8000` |
| 默认 Base URL | `http://127.0.0.1:8000` |
| 核心接口 | `POST /domain` |
| 数据格式 | JSON |
| 调用方 | Chrome Extension、调试脚本、其他 API Client |
| 跨域支持 | 后端启用 CORS，支持浏览器插件调用 |
| 主要功能 | 获取仓库 README，抽取关键词，执行 SVM 分类，必要时调用 LLM 二次判定 |

---

## 2. 调用前准备

### 2.1 启动后端服务

在项目根目录执行：

```bash
cd backend
python domain_get.py
```

启动成功后，后端默认运行在：

```text
http://127.0.0.1:8000
```

分类接口地址为：

```text
http://127.0.0.1:8000/domain
```

### 2.2 后端依赖

项目根目录中的 `requirements.txt` 包含后端运行所需依赖，主要包括：

| 依赖 | 用途 |
|---|---|
| `flask` | 提供 HTTP API 服务 |
| `flask-cors` | 允许 Chrome 插件跨域访问本地后端 |
| `requests` | 请求 GitHub API 获取 README |
| `numpy` | 模型推理中的数值计算 |
| `scikit-learn` | SVM 模型与特征处理依赖 |
| `joblib` | 加载 `.pkl` 模型与映射文件 |
| `python-dotenv` | 读取环境变量配置 |
| `openai` | 调用 OpenAI SDK 兼容的大模型接口 |
| `pytest` / `pytest-cov` | 自动化测试与覆盖率统计 |

安装命令：

```bash
pip install -r requirements.txt
```

---

## 3. 分类接口：`POST /domain`

### 3.1 基本信息

| 项目 | 说明 |
|---|---|
| URL | `/domain` |
| 完整地址 | `http://127.0.0.1:8000/domain` |
| Method | `POST` |
| Content-Type | `application/json` |
| 是否需要认证 | 本地接口本身不需要认证；访问 GitHub API 和 LLM API 可能需要 Token / Key |
| 是否支持预检请求 | 支持 `OPTIONS`，用于浏览器跨域预检 |

### 3.2 功能描述

`/domain` 接收 GitHub 仓库标识，例如 `owner + repo`，后端会执行以下步骤：

1. 根据 `owner/repo` 请求 GitHub API 获取 README；
2. 对 README 文本进行清洗和关键词抽取；
3. 将关键词输入 SVM 模型，得到候选类别和概率；
4. 计算 `Top1 概率 - Top2 概率`；
5. 如果概率差大于等于阈值 `0.15`，直接返回 SVM Top1 类别；
6. 如果概率差小于阈值，并且请求中提供了 `api_key`，则调用 Kimi/GPT 类大模型进行二次判定；
7. 如果概率差小于阈值，但没有提供 `api_key`，则回退返回 SVM Top1，并附带 warning。

---

## 4. 请求参数

### 4.1 推荐请求体：`owner + repo`

```json
{
  "owner": "facebook",
  "repo": "react"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---:|:---:|---|
| `owner` | string | 是 | GitHub 仓库所属用户或组织名，例如 `facebook` |
| `repo` | string | 是 | GitHub 仓库名称，例如 `react` |
| `api_key` | string | 否 | 大模型 API Key；当 SVM 低置信时用于 LLM 二次判定 |
| `github_token` | string | 否 | 前端预留字段；当前后端实现主要使用后端配置中的 GitHub Token |
| `repo_url` | string | 否 | 仓库完整 URL；当未提供 `owner/repo` 时可作为替代输入 |

### 4.2 替代请求体：`repo_url`

当前后端兼容 `repo_url` 字段：

```json
{
  "repo_url": "https://github.com/facebook/react"
}
```

后端会从 URL 中解析：

```text
owner = facebook
repo  = react
```

### 4.3 带 LLM API Key 的请求体

当需要启用低置信样本的大模型二次判定时，可传入 `api_key`：

```json
{
  "owner": "facebook",
  "repo": "react",
  "api_key": "your_kimi_or_openai_compatible_api_key"
}
```

> 注意：请勿将真实 API Key 写入仓库、测试文件或公开日志。推荐通过本地配置、浏览器插件存储或环境变量管理密钥。

---

## 5. 响应结构

当前后端实际返回字段以 `tags / result / svm_result` 为主。

### 5.1 高置信 SVM 响应

当 `Top1 - Top2 >= 0.15` 时，后端直接采用 SVM 结果：

```json
{
  "tags": "react javascript ui library component web frontend",
  "result": "网页应用",
  "svm_result": [
    {
      "class": "网页应用",
      "prob": 0.8731
    },
    {
      "class": "代码开发工具或插件",
      "prob": 0.0612
    }
  ]
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---:|---|
| `tags` | string | 从 README 中抽取出的关键词，使用空格拼接 |
| `result` | string | 最终分类结果 |
| `svm_result` | array | SVM 输出的类别候选列表，按概率从高到低排列 |
| `svm_result[].class` | string | 候选类别名称 |
| `svm_result[].prob` | number | 候选类别概率，通常为 0 到 1 之间的小数 |

### 5.2 低置信但未提供 API Key 的回退响应

当 `Top1 - Top2 < 0.15` 且请求中没有 `api_key` 时，后端会回退使用 SVM Top1：

```json
{
  "tags": "plugin browser extension github badge api",
  "result": "应用插件",
  "svm_result": [
    {
      "class": "应用插件",
      "prob": 0.312
    },
    {
      "class": "代码开发工具或插件",
      "prob": 0.286
    }
  ],
  "warning": "prob gap <= 0.15 but no api_key provided; fallback to svm top1"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---:|---|
| `warning` | string | 说明当前结果是低置信样本的 SVM 回退结果 |

### 5.3 低置信并启用 LLM 的响应

当 `Top1 - Top2 < 0.15` 且提供了 `api_key` 时，后端会调用大模型进行二次判定：

```json
{
  "tags": "extension github repository classify badge backend flask svm",
  "result": "应用插件",
  "svm_result": [
    {
      "class": "代码开发工具或插件",
      "prob": 0.301
    },
    {
      "class": "应用插件",
      "prob": 0.292
    }
  ]
}
```

此时 `result` 可能来自 LLM 二次判定，而不一定等于 `svm_result[0].class`。

---

## 6. 异常响应

### 6.1 参数缺失

如果没有提供 `owner/repo`，也没有提供可解析的 `repo_url`，返回 400：

```json
{
  "error": "请提供 owner/repo 或 repo_url"
}
```

### 6.2 README 获取失败

如果 GitHub API 请求失败、仓库不存在、README 不存在或网络异常，返回 500：

```json
{
  "error": "README 获取失败：/readme=404 ... | /contents=404 ..."
}
```

### 6.3 SVM 预测失败

如果模型文件缺失、关键词字典无法加载、特征维度不匹配或推理异常，返回 500：

```json
{
  "error": "SVM预测失败: error detail"
}
```

### 6.4 大模型判定失败

如果低置信样本进入 LLM 阶段，但 API Key 错误、网络失败、SDK 异常或模型无响应，返回 500：

```json
{
  "error": "大模型判定失败: error detail"
}
```

---

## 7. HTTP 状态码

| 状态码 | 场景 | 说明 |
|---:|---|---|
| `200` | 分类成功 | 返回 `tags / result / svm_result` |
| `200` | README 可读取但关键词为空 | 返回空 `result` 和空 `svm_result` |
| `400` | 请求参数不合法 | 未提供有效仓库信息 |
| `500` | README 获取失败 | GitHub API、Token、网络或仓库 README 异常 |
| `500` | SVM 预测失败 | 模型文件、特征处理或预测逻辑异常 |
| `500` | LLM 判定失败 | 大模型 API 调用或响应解析失败 |
| `200` for `OPTIONS` | 跨域预检 | 浏览器插件调用前的 CORS 预检请求 |

---

## 8. Curl 调用示例

### 8.1 使用 `owner/repo` 调用

```bash
curl -X POST "http://127.0.0.1:8000/domain" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "facebook",
    "repo": "react"
  }'
```

### 8.2 使用 `repo_url` 调用

```bash
curl -X POST "http://127.0.0.1:8000/domain" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/facebook/react"
  }'
```

### 8.3 提供 LLM API Key

```bash
curl -X POST "http://127.0.0.1:8000/domain" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "microsoft",
    "repo": "vscode",
    "api_key": "your_api_key_here"
  }'
```

---

## 9. Python 调用示例

```python
import requests

payload = {
    "owner": "facebook",
    "repo": "react"
}

resp = requests.post(
    "http://127.0.0.1:8000/domain",
    json=payload,
    timeout=30,
)

resp.raise_for_status()
data = resp.json()

print("分类结果:", data.get("result"))
print("关键词:", data.get("tags"))
print("候选类别:", data.get("svm_result"))
```

---

## 10. Chrome Extension 调用逻辑

插件侧 `content.js` 会执行以下动作：

1. 判断当前页面是否为 GitHub 页面；
2. 从 URL 或列表链接中解析 `owner/repo`；
3. 从 `chrome.storage.local` 读取插件开关、OpenAI/Kimi Key 和 GitHub Token；
4. 向 `http://127.0.0.1:8000/domain` 发送 POST 请求；
5. 从响应中读取 `result` 字段；
6. 将分类结果渲染为 GitHub 页面中的徽标；
7. 使用 `sessionStorage` 缓存同一会话中的分类结果，避免重复请求。

请求体示例：

```json
{
  "owner": "facebook",
  "repo": "react",
  "api_key": "optional_key",
  "github_token": "optional_token"
}
```

当前插件主要消费响应中的：

```json
{
  "result": "网页应用"
}
```

如果 `result` 为空，插件不会插入最终徽标。

---

## 11. 接口兼容建议

为了提升前后端长期兼容性，建议后续将接口响应逐步标准化为以下结构：

```json
{
  "success": true,
  "owner": "facebook",
  "repo": "react",
  "category": "网页应用",
  "confidence": 0.8731,
  "source": "svm",
  "tags": "react javascript ui library component web frontend",
  "svm_result": [
    {
      "class": "网页应用",
      "prob": 0.8731
    }
  ],
  "warning": null,
  "error": null
}
```

推荐字段含义：

| 字段 | 说明 |
|---|---|
| `success` | 是否调用成功 |
| `category` | 最终分类结果，可作为 `result` 的别名 |
| `confidence` | 最终结果的置信度 |
| `source` | 分类来源，建议为 `svm`、`llm` 或 `fallback` |
| `warning` | 非致命问题，例如低置信回退 |
| `error` | 致命错误信息 |

在兼容期内，可同时返回 `result` 和 `category`：

```json
{
  "result": "网页应用",
  "category": "网页应用"
}
```

这样既能兼容当前插件，也便于后续 API 文档统一。

---

## 12. 安全与隐私注意事项

1. **不要提交真实 Token**  
   GitHub Token、OpenAI Key、Kimi Key 不应硬编码到代码仓库中。

2. **限制服务监听地址**  
   本地开发建议使用 `127.0.0.1`。如果使用 `0.0.0.0`，应确认局域网访问风险。

3. **避免打印完整 README 与密钥**  
   README 可能包含仓库介绍、示例配置甚至误提交的敏感内容，日志中应避免完整打印。

4. **为外部 API 设置超时**  
   GitHub API 和 LLM API 都应设置 timeout，避免请求长期阻塞。

5. **对错误信息脱敏**  
   返回给前端的错误信息应便于定位问题，但不应泄露本地路径、密钥或完整上游响应。

---

## 13. 常见问题

### Q1：接口返回 400，提示“请提供 owner/repo 或 repo_url”

检查请求体是否为 JSON，并确认至少提供以下任一组合：

```json
{
  "owner": "facebook",
  "repo": "react"
}
```

或：

```json
{
  "repo_url": "https://github.com/facebook/react"
}
```

### Q2：接口返回 README 获取失败

可能原因：

- 仓库不存在；
- 仓库没有 README；
- GitHub API 请求受限；
- GitHub Token 无效；
- 网络无法访问 GitHub；
- README 文件不在默认路径或默认分支异常。

### Q3：接口返回 SVM 预测失败

可能原因：

- `.pkl` 模型文件缺失；
- 运行目录不正确；
- `keyword_dict.pkl` 与模型训练时使用的关键词字典不一致；
- `scaler.pkl` 与当前特征维度不匹配；
- Python 依赖版本不兼容。

### Q4：接口可以用 curl 调通，但插件页面不显示徽标

建议排查：

1. 后端是否运行在 `http://127.0.0.1:8000`；
2. 插件是否已在 `chrome://extensions/` 中加载；
3. 插件开关是否开启；
4. 当前页面是否为 GitHub 仓库页、搜索仓库页或 Explore/Trending/Topics 页面；
5. 浏览器控制台是否有 CORS 或 fetch 错误；
6. 接口响应中 `result` 是否为空。

---

## 14. 后续优化方向

| 方向 | 建议 |
|---|---|
| 响应结构统一 | 同时保留 `result` 和 `category`，逐步过渡到标准响应 |
| Token 管理 | 后端优先读取环境变量，前端 Token 只作为可选覆盖项 |
| 错误码细分 | 将 README 缺失、GitHub 限流、模型文件缺失等错误区分为不同错误码 |
| 缓存机制 | 对相同 `owner/repo` 的 README 和分类结果进行服务端缓存 |
| 批量接口 | 为搜索页批量分类增加 `/domains/batch` 接口，减少请求数 |
| 可观测性 | 增加请求耗时、分类来源、LLM 调用次数等日志指标 |
