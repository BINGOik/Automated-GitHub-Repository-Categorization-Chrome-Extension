# 方法设计文档

> 本文档说明项目的核心方法：如何从 GitHub 仓库页面识别仓库，如何获取 README，如何抽取特征，如何使用 SVM 进行初步分类，以及如何在低置信场景下调用大模型完成二次判定。

---

## 1. 方法目标

本项目的目标不是简单地给仓库打一个关键词标签，而是面向 GitHub 开源仓库浏览场景，自动判断仓库所属的软件开发领域，并将结果直接展示在 GitHub 页面中。

核心目标包括：

1. **自动化**：用户浏览 GitHub 页面时，不需要手动复制仓库地址或 README。
2. **细粒度**：将仓库划分到 12 个较细的软件应用领域。
3. **低延迟**：大部分仓库由本地 SVM 小模型快速完成分类。
4. **低成本**：避免每个仓库都调用大模型，减少 API 成本。
5. **可解释**：返回关键词、候选类别和概率，便于调试。
6. **可扩展**：后端 API 可被插件、脚本或批量处理任务复用。

---

## 2. 总体流程

系统采用“Chrome 插件 + Flask 后端 + SVM 小模型 + LLM 二次判定”的组合架构。

```text
用户浏览 GitHub 页面
        │
        ▼
Chrome Extension 解析 owner/repo
        │
        ▼
POST /domain 到本地 Flask 后端
        │
        ▼
后端请求 GitHub API 获取 README
        │
        ▼
README 文本清洗与关键词抽取
        │
        ▼
SVM 模型输出类别概率分布
        │
        ▼
计算 Top1 与 Top2 概率差
        │
        ├── 概率差 >= 0.15：直接采用 SVM Top1
        │
        └── 概率差 < 0.15：进入低置信处理
                    │
                    ├── 有 API Key：调用 LLM 二次判定
                    └── 无 API Key：回退 SVM Top1 并返回 warning
        │
        ▼
返回 result / tags / svm_result
        │
        ▼
插件在 GitHub 页面渲染分类徽标
```

---

## 3. 交互式蒸馏思想

项目 README 中提到的“交互式蒸馏”可以理解为一种工程化的模型协同策略：

| 角色 | 作用 | 优点 | 局限 |
|---|---|---|---|
| SVM 小模型 | 对大多数样本快速给出候选类别和概率 | 本地运行、速度快、成本低、输出稳定 | 对语义复杂或多领域仓库可能不确定 |
| LLM 大模型 | 对低置信样本进行语义二次判断 | 语义理解能力强，适合边界样本 | 调用成本高、延迟高、依赖外部 API |
| 阈值控制器 | 根据 Top1/Top2 概率差决定是否调用 LLM | 在准确性和成本之间平衡 | 阈值需要根据实验调优 |

该方法的核心思想是：

> 让小模型处理简单、确定的样本；让大模型只处理小模型不确定的样本。

这样可以避免两种极端：

1. **完全依赖 SVM**：速度快，但复杂样本容易误判。
2. **完全依赖 LLM**：语义强，但成本高、速度慢、输出不稳定。

---

## 4. Chrome 插件侧流程

### 4.1 页面类型识别

插件在 `content.js` 中判断当前页面是否属于可分类场景。

支持的页面类型包括：

| 页面类型 | URL 示例 | 处理方式 |
|---|---|---|
| 仓库详情页 | `https://github.com/facebook/react` | 在仓库标题旁插入分类徽标 |
| Search 仓库结果页 | `https://github.com/search?q=react&type=repositories` | 为搜索结果中的仓库链接插入徽标 |
| Explore 页面 | `https://github.com/explore` | 为可识别的仓库链接插入徽标 |
| Trending 页面 | `https://github.com/trending` | 为 Trending 仓库插入徽标 |
| Topics 页面 | `https://github.com/topics/javascript` | 为 Topic 下的仓库插入徽标 |
| Collections 页面 | `https://github.com/collections/...` | 为集合页仓库链接插入徽标 |

插件会过滤以下路径，避免误把 GitHub 功能页当成仓库：

```text
settings
notifications
login
join
pricing
marketplace
explore
organizations
apps
features
topics
trending
collections
events
sponsors
orgs
search
```

### 4.2 仓库信息解析

插件从链接或当前路径中提取：

```text
owner/repo
```

例如：

```text
https://github.com/facebook/react
```

解析为：

```json
{
  "owner": "facebook",
  "repo": "react"
}
```

在列表页中，插件要求链接路径必须恰好为两段：

```text
/owner/repo
```

这样可以避免将用户主页、组织主页或 Issues/Pull Requests 等操作链接误判为仓库。

### 4.3 插件配置读取

插件使用 `chrome.storage.local` 存储以下配置：

| Key | 说明 |
|---|---|
| `dc_enabled` | 插件是否启用 |
| `dc_openai_key` | 大模型 API Key，低置信样本时传给后端 |
| `dc_github_token` | GitHub Token 预留字段，可用于提高 GitHub API 请求额度 |

### 4.4 请求后端

插件向本地后端发送请求：

```json
{
  "owner": "facebook",
  "repo": "react",
  "api_key": "optional_api_key",
  "github_token": "optional_github_token"
}
```

请求地址固定为：

```text
http://127.0.0.1:8000/domain
```

### 4.5 前端缓存与并发控制

为了减少重复请求，插件使用了两个优化：

#### 4.5.1 Session 缓存

同一浏览器会话中，同一个仓库的分类结果会缓存到：

```text
sessionStorage
```

缓存 Key 形式为：

```text
dc_cache_owner/repo
```

#### 4.5.2 请求队列

列表页可能一次出现很多仓库，如果同时请求后端，会造成卡顿或触发 GitHub API 限流。因此插件限制最大并发数：

```text
MAX_CONCURRENCY = 3
```

超过并发上限的请求会进入队列等待。

### 4.6 列表页懒加载

对于搜索页、Trending 页等列表场景，插件使用 `IntersectionObserver`，只对进入视口附近的仓库链接进行分类。

这样可以避免：

- 页面刚加载就请求所有仓库；
- 用户没有看到的仓库也触发分类；
- GitHub API 请求量过大；
- 本地后端短时间承压。

### 4.7 徽标渲染

插件会在仓库标题或仓库链接后插入一个 `span` 元素作为分类徽标。

渲染策略：

| 场景 | 行为 |
|---|---|
| 150ms 内返回结果 | 直接显示最终分类，避免 Loading 闪烁 |
| 超过 150ms | 先显示 `⏳ Loading…` |
| 返回有效 `result` | 替换为分类结果 |
| 返回空结果 | 移除 Loading，不显示徽标 |
| 请求失败 | 打印 warning，移除徽标 |

---

## 5. 后端服务流程

后端核心入口为 `backend/domain_get.py` 中的 `/domain` 路由。

### 5.1 接收请求

后端接收 JSON 请求体：

```json
{
  "owner": "facebook",
  "repo": "react"
}
```

也兼容：

```json
{
  "repo_url": "https://github.com/facebook/react"
}
```

如果缺少有效仓库信息，返回：

```json
{
  "error": "请提供 owner/repo 或 repo_url"
}
```

### 5.2 获取 README

后端优先调用 GitHub README API：

```text
GET https://api.github.com/repos/{owner}/{repo}/readme
```

请求头中使用：

```text
Accept: application/vnd.github.v3.raw
```

如果该接口失败，会兜底请求：

```text
GET https://api.github.com/repos/{owner}/{repo}/contents/README.md
```

该接口返回的 `content` 通常是 Base64 编码，因此后端会进行解码。

### 5.3 README 获取失败处理

如果两个接口都失败，后端抛出错误并返回 500。

常见原因包括：

- 仓库不存在；
- 仓库没有 README；
- README 文件名或路径不标准；
- GitHub Token 无效；
- GitHub API 限流；
- 网络连接失败；
- 私有仓库无权限访问。

---

## 6. README 关键词抽取

关键词抽取位于 `backend/readme_words.py`。

### 6.1 输入与输出

输入：

```text
README 原始 Markdown 文本
```

输出：

```text
空格分隔的关键词字符串
```

示例：

```text
react javascript component ui library frontend hooks virtual dom
```

该字符串会直接传入 SVM 预测模块。

### 6.2 清洗步骤

当前实现的文本处理流程如下：

| 步骤 | 处理内容 | 目的 |
|---:|---|---|
| 1 | 移除 Markdown 代码块 | 避免变量名、路径、安装命令干扰关键词 |
| 2 | 移除行内代码 | 减少代码片段噪声 |
| 3 | 移除 URL | 避免链接文本影响分类 |
| 4 | 将 Markdown 链接 `[text](url)` 转为 `text` | 保留链接文本语义 |
| 5 | 转为小写 | 统一词形 |
| 6 | 只保留字母、数字和空格 | 简化英文分词 |
| 7 | 按空格分词 | 得到 token 列表 |
| 8 | 过滤停用词、短词和纯数字 | 去除低价值词 |
| 9 | 统计词频 | 识别 README 中高频主题词 |
| 10 | 保留 Top K 高频词 | 控制输入长度，默认最多 400 个关键词 |

### 6.3 停用词设计

停用词包括：

- 冠词：`a / an / the`
- 连词：`and / or / but`
- 介词：`of / in / on / at / by`
- 代词：`you / your / we / our`
- 助动词：`can / could / should / will`
- 通用项目词：`project / repo / repository / readme / documentation / example`

这些词通常无法体现仓库领域，因此会被过滤。

### 6.4 关键词抽取局限

当前关键词抽取偏向英文 README，对中文 README 或多语言 README 的处理能力有限。

可能问题：

| 问题 | 影响 |
|---|---|
| 中文无法按词语正确分词 | 中文仓库关键词可能被过滤或切分不理想 |
| 只保留字母数字 | 表情符号、特殊技术符号可能丢失 |
| 高频词不一定最有区分度 | 某些重要但低频的领域词可能被忽略 |
| 未使用 TF-IDF | 高频通用技术词可能权重过高 |
| 未保留 README 结构 | 标题、安装命令、示例代码之间没有区分权重 |

后续可考虑加入：

- 中文分词；
- TF-IDF；
- README 标题加权；
- topic / language / description 特征；
- GitHub topics 特征；
- 文件结构特征。

---

## 7. SVM 初步分类

SVM 预测逻辑位于 `backend/svm_predictor.py`。

### 7.1 模型文件

后端加载以下文件：

| 文件 | 用途 |
|---|---|
| `linear_svc_model.pkl` | 训练好的 LinearSVC 分类模型 |
| `label_mapping.pkl` | 类别编号到类别名称的映射 |
| `scaler.pkl` | 特征标准化器 |
| `keyword_dict.pkl` | 关键词到向量位置的映射 |

### 7.2 特征编码

输入关键词字符串：

```text
react javascript component ui library frontend
```

处理方式：

1. 按空格切分关键词；
2. 对每个关键词查询 `keyword_dict`；
3. 如果关键词存在于字典中，则对应位置置为 `1`；
4. 得到 one-hot 风格的关键词向量；
5. 使用 `scaler` 进行标准化；
6. 转为稀疏矩阵或稠密数组用于模型推理。

### 7.3 模型输出

LinearSVC 原始输出不是概率，而是 `decision_function` 分数。当前实现对分数做 softmax 转换，得到近似概率分布：

```python
x_exp = np.exp(x - np.max(x))
probs = x_exp / np.sum(x_exp)
```

然后按概率从高到低排序，返回：

```json
[
  {
    "class": "网页应用",
    "prob": 0.8731
  },
  {
    "class": "代码开发工具或插件",
    "prob": 0.0612
  }
]
```

### 7.4 TopN 输出

当前 `predict_from_keyword` 支持 `topn` 参数：

```python
predictor.predict_from_keyword(keywords, topn=3)
```

如果未指定 `topn`，则返回所有类别的排序结果。

---

## 8. 低置信样本判断

### 8.1 判定公式

系统计算：

```text
confidence_gap = P(top1) - P(top2)
```

其中：

- `P(top1)` 是 SVM 排名第一的类别概率；
- `P(top2)` 是 SVM 排名第二的类别概率。

### 8.2 当前阈值

当前阈值为：

```text
PROB_GAP_THRESHOLD = 0.15
```

### 8.3 判定规则

```text
if P(top1) - P(top2) >= 0.15:
    使用 SVM Top1
else:
    进入低置信处理
```

### 8.4 低置信样本常见场景

| 场景 | 示例 |
|---|---|
| 多领域项目 | 一个项目既是 Web 应用，又提供服务端 API |
| 工具与插件边界模糊 | VS Code 插件、Chrome 插件、CLI 工具 |
| README 描述泛化 | README 只写 “a powerful framework” |
| 技术栈相似 | Web 应用、企业应用、服务器应用都可能包含 API、dashboard、database |
| 项目名称误导 | 名称包含 “game”，但实际是游戏开发工具 |
| README 太短 | 关键词不足，SVM 无法形成稳定判断 |

---

## 9. LLM 二次判定

### 9.1 触发条件

LLM 二次判定需要同时满足：

1. `Top1 - Top2 < 0.15`；
2. 请求体中提供了 `api_key`；
3. `kimi_predictor.py` 或 `gpt_predictor.py` 能正常调用外部模型；
4. 外部模型返回可解析结果。

### 9.2 输入信息

传给 LLM 的主要信息包括：

| 输入 | 说明 |
|---|---|
| README 文本 | 项目的完整说明文本 |
| SVM Top1 ~ Top12 候选 | 小模型认为可能的类别 |
| 每个候选类别概率 | 让 LLM 知道模型倾向 |
| 类别体系说明 | 限定输出范围，减少开放式生成 |

### 9.3 Prompt 约束

当前 Kimi 版本的 Prompt 约束模型：

- 作为开源项目领域分类器；
- 根据 README 和项目描述判断实际应用范围；
- 在给定类别范围内选择；
- 输出 `Result:`；
- 可附带 `Reasons:`，但后端只提取 `Result:` 后的内容。

### 9.4 输出解析

后端从模型响应中查找第一行以 `Result:` 开头的内容。

例如模型返回：

```text
Result: 应用插件
Reasons: 该项目是 Chrome Extension，依赖浏览器宿主运行。
```

后端提取：

```text
应用插件
```

### 9.5 LLM 阶段风险

| 风险 | 说明 | 建议 |
|---|---|---|
| 输出不规范 | 模型没有输出 `Result:` | 加强 Prompt 或做兜底解析 |
| 类别名称不一致 | 输出英文或别名 | 做类别别名映射 |
| 延迟较高 | 外部 API 可能需要数秒 | 前端显示 Loading，并设置 timeout |
| 成本不可控 | 大量低置信样本会触发调用 | 增加缓存和批量控制 |
| API Key 泄露 | 前端传输 Key 风险较高 | 本地开发可接受，生产环境建议后端统一管理 |
| 网络失败 | 外部 API 不可用 | 回退 SVM Top1 并返回 warning |

---

## 10. 分类结果返回与展示

### 10.1 后端返回

后端返回：

```json
{
  "tags": "extension github repository classify chrome backend",
  "result": "应用插件",
  "svm_result": [
    {
      "class": "应用插件",
      "prob": 0.42
    },
    {
      "class": "代码开发工具或插件",
      "prob": 0.35
    }
  ]
}
```

### 10.2 插件展示

插件读取 `result` 字段，将其作为徽标文本插入页面。

展示位置：

| 页面 | 展示位置 |
|---|---|
| 仓库详情页 | 仓库标题旁 |
| Search 仓库结果页 | 仓库链接旁 |
| Trending/Explore/Topics 页面 | 仓库链接旁 |

### 10.3 空结果处理

如果 `result` 为空：

- 插件不展示最终徽标；
- 如果已显示 Loading，会移除 Loading；
- 后端可继续返回 `tags`，便于调试。

---

## 11. 方法优势

| 优势 | 说明 |
|---|---|
| 速度快 | SVM 在本地推理，适合页面实时显示 |
| 成本低 | 只在低置信样本调用 LLM |
| 可解释 | 返回关键词、候选类别、概率 |
| 易部署 | Flask 后端和 Chrome 插件结构简单 |
| 可扩展 | 后端接口可扩展为批量分类、数据标注、研究分析 |
| 适合演示 | 插件直接在 GitHub 页面显示效果，展示直观 |

---

## 12. 当前局限

| 局限 | 影响 |
|---|---|
| README 依赖较强 | README 太短或缺失时分类困难 |
| 中文 README 支持不足 | 当前分词主要面向英文文本 |
| 类别边界存在主观性 | 例如“代码开发工具或插件”和“应用插件”容易混淆 |
| Softmax 概率并非严格校准概率 | LinearSVC 的 decision score 转概率只是近似 |
| LLM 输出依赖 Prompt | Prompt 质量会影响二次判定稳定性 |
| API Key 管理仍可优化 | 当前前端可传 Key，生产环境建议后端集中管理 |
| GitHub API 限流 | 搜索页批量请求可能触发限制 |
| 模型文件依赖运行目录 | 在不同目录启动后端可能找不到 `.pkl` 文件 |

---

## 13. 后续优化建议

### 13.1 数据特征优化

可新增以下特征：

| 特征 | 说明 |
|---|---|
| GitHub topics | 仓库维护者手动标注的主题词 |
| primary language | GitHub 识别的主语言 |
| description | 仓库简介 |
| 文件结构 | 是否存在 `package.json`、`pom.xml`、`Dockerfile`、`manifest.json` |
| Star / Fork | 作为辅助非语义特征 |
| README 标题权重 | 标题、列表项、安装说明等区域区分权重 |

### 13.2 模型优化

可考虑：

- 使用校准后的概率模型；
- 引入 TF-IDF + LinearSVC；
- 使用 LightGBM / XGBoost；
- 使用文本嵌入模型；
- 使用小型 Transformer 做本地推理；
- 对低置信阈值做验证集调优。

### 13.3 LLM 优化

可考虑：

- 强制 JSON 输出；
- 限定类别枚举；
- 增加 few-shot 示例；
- 加入输出校验与重试；
- 将 LLM 结果缓存到本地；
- 记录 LLM 修正样本，用于后续再训练 SVM。

### 13.4 插件优化

可考虑：

- 支持用户自定义后端地址；
- 增加徽标颜色映射；
- 悬浮展示 Top3 候选类别；
- 增加“重新分类”按钮；
- 为 GitHub 新版 DOM 增加更多兼容选择器；
- 使用批量接口减少搜索页请求数量。

---

## 14. 适用场景

| 场景 | 价值 |
|---|---|
| GitHub 日常浏览 | 快速判断项目类型 |
| 开源项目检索 | 在搜索页快速筛选目标领域 |
| 开源生态研究 | 批量构造带领域标签的数据集 |
| 技术选型 | 辅助判断候选项目用途 |
| 课程设计 / 比赛展示 | 展示完整的前后端、机器学习和 LLM 协同系统 |
| 数据标注辅助 | 先由模型预标注，再由人工复核 |

---

## 15. 小结

本项目的方法设计可以概括为：

> 前端负责识别 GitHub 页面和展示结果，后端负责获取 README 和执行分类，小模型负责快速初判，大模型负责低置信修正，阈值机制负责在速度、成本和准确性之间取得平衡。

这种架构适合本地运行、课程展示、开源生态研究，也便于后续扩展为批量分类平台或更完整的仓库智能分析工具。
