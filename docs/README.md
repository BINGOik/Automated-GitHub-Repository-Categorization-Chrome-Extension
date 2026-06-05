# 项目文档总览

> 项目：GitHub Repository Domain Classifier  
> 定位：基于 Chrome Extension + Flask 后端 + SVM/LLM 协同分类的 GitHub 仓库领域自动分类工具  
> 文档语言：中文  
> 维护建议：代码结构或接口字段发生变化时，同步更新本目录下相关文档。

---

## 1. 文档目录

| 文档 | 主要内容 | 推荐阅读对象 |
|---|---|---|
| [`api.md`](./api.md) | 后端 `/domain` 分类接口、请求字段、响应字段、错误处理、调用示例 | 前端开发、后端开发、接口联调人员 |
| [`method.md`](./method.md) | 交互式蒸馏分类流程、README 获取、关键词抽取、SVM 推理、LLM 二次判定、插件渲染流程 | 研究者、答辩评审、算法/后端开发 |
| [`categories.md`](./categories.md) | 12 类仓库领域分类体系、判定标准、易混淆边界、标注建议 | 数据标注人员、模型训练人员、项目使用者 |
| [`testing.md`](./testing.md) | 测试体系、运行命令、覆盖范围、Mock 策略、CI 建议、常见问题 | 测试人员、维护者、贡献者 |

---

## 2. 推荐阅读顺序

### 2.1 快速体验项目

如果只是想安装并体验插件，建议按以下顺序阅读：

1. 项目根目录 `README.md`
2. [`api.md`](./api.md) 中的“快速调用示例”
3. [`method.md`](./method.md) 中的“端到端工作流”
4. [`testing.md`](./testing.md) 中的“运行测试”

### 2.2 参与后端开发

如果需要修改后端分类服务，建议重点阅读：

1. [`api.md`](./api.md)：确认接口契约和响应格式。
2. [`method.md`](./method.md)：理解 README 获取、关键词抽取、SVM 推理和 LLM 修正逻辑。
3. [`testing.md`](./testing.md)：了解如何用 Mock 隔离 GitHub API、模型文件和 LLM 调用。

### 2.3 参与前端插件开发

如果需要修改 Chrome Extension，建议重点阅读：

1. [`api.md`](./api.md)：确认前端向后端发送的字段。
2. [`method.md`](./method.md)：理解仓库详情页、搜索页、Trending/Topics 页的渲染流程。
3. [`testing.md`](./testing.md)：了解当前插件测试方式和后续 JS 测试 Runner 配置建议。

### 2.4 参与模型或数据研究

如果需要扩展分类体系、重新训练模型或做实验对比，建议重点阅读：

1. [`categories.md`](./categories.md)：确认类别定义和边界规则。
2. [`method.md`](./method.md)：理解特征构造和交互式蒸馏框架。
3. [`testing.md`](./testing.md)：确认模型推理输出、低置信样本判断和回归测试方法。

---

## 3. 项目核心模块概览

```text
Automated-GitHub-Repository-Categorization-Chrome-Extension/
├── extension/                 # Chrome 插件前端
│   ├── manifest.json          # 插件声明、权限、content script 配置
│   ├── popup.html             # 插件弹窗页面
│   ├── popup.js               # 开关与 API Key 配置逻辑
│   └── content.js             # GitHub 页面解析、接口请求、徽标渲染
│
├── backend/                   # Flask 后端分类服务
│   ├── domain_get.py          # Flask 应用入口与 /domain 路由
│   ├── readme_words.py        # README 文本清洗与关键词抽取
│   ├── svm_predictor.py       # SVM 模型加载、关键词编码、概率输出
│   ├── kimi_predictor.py      # Kimi / Moonshot 兼容 OpenAI SDK 的二次判定
│   ├── gpt_predictor.py       # GPT 二次判定模块
│   └── *.pkl                  # 模型、标准化器、标签映射、关键词字典等
│
├── experiments/               # 论文实验、特征工程、模型训练与结果分析
├── tests/                     # 自动化测试
├── docs/                      # 中文项目文档
└── README.md                  # 项目首页说明
```

---

## 4. 系统一句话说明

本项目会在用户浏览 GitHub 仓库时，由 Chrome 插件识别当前页面中的仓库名，并请求本地 Flask 后端；后端获取仓库 README、抽取关键词、使用 SVM 完成初步领域分类；当 SVM Top1 与 Top2 概率差小于阈值时，可调用 Kimi/GPT 等大模型进行二次判定；最终分类结果会以徽标形式显示在 GitHub 页面中。

---

## 5. 关键概念速查

| 概念 | 含义 |
|---|---|
| 仓库领域分类 | 将 GitHub 仓库归入“网页应用”“服务器应用”“代码开发工具或插件”等预定义类别 |
| README | GitHub 仓库通常用于介绍项目用途、安装方式、技术栈和使用方式的主文档 |
| 关键词抽取 | 从 README 文本中清洗、分词、过滤停用词，并保留高频关键词作为模型输入 |
| SVM | 支持向量机模型，用于根据关键词特征快速输出类别候选和概率分布 |
| 置信度差值 | `Top1 概率 - Top2 概率`，用于判断小模型是否足够确定 |
| LLM 二次判定 | 当小模型低置信时，将 README 和候选类别交给大模型做语义判断 |
| 分类徽标 | 插件插入到 GitHub 仓库标题或列表项旁边的领域标签 |
| 交互式蒸馏 | 小模型优先处理高置信样本，大模型只参与低置信样本修正的协同策略 |

---

## 6. 文档维护规范

为了保证文档长期可用，建议遵循以下规则：

1. **接口字段变更时更新 `api.md`**  
   例如新增请求字段、修改响应结构、调整错误码，都应同步更新接口文档。

2. **分类类别变更时更新 `categories.md`**  
   如果新增、合并或删除类别，需要同时更新类别定义、边界规则和示例。

3. **算法流程变更时更新 `method.md`**  
   例如更换模型、调整阈值、修改关键词抽取方式或 LLM Prompt，都应记录在方法文档中。

4. **测试结构变更时更新 `testing.md`**  
   如果新增测试目录、测试命令、CI 流程或覆盖率要求，应同步修改测试文档。

5. **避免在文档中提交真实密钥**  
   GitHub Token、OpenAI Key、Kimi Key 等敏感信息只应写成示例占位符，例如 `your_api_key_here`。

---

## 7. 常用命令速查

### 7.1 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 7.2 启动后端服务

```bash
cd backend
python domain_get.py
```

服务默认监听：

```text
http://127.0.0.1:8000
```

分类接口：

```text
POST http://127.0.0.1:8000/domain
```

### 7.3 调用分类接口

```bash
curl -X POST "http://127.0.0.1:8000/domain" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "facebook",
    "repo": "react"
  }'
```

### 7.4 运行测试

```bash
pytest tests/ -v
```

### 7.5 生成覆盖率报告

```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing
```

---

## 8. 版本说明

本文档按照当前仓库结构与已有实现整理，重点服务于：

- 项目展示；
- 代码维护；
- 测试补全；
- 后续答辩或课程设计材料整理；
- 模型方法复现与扩展。

如后续代码实现与文档描述不一致，应以实际代码为准，并及时修正文档。
