# GitHub README Domain Classifier

一个 Chrome 浏览器扩展，自动对 GitHub 仓库进行开发领域分类，并在项目名称旁显示分类徽标。

## 功能特性

- 在 GitHub 仓库页面标题旁自动显示领域分类徽标
- 支持 Explore、Trending、Topics、Search 等列表页面批量展示分类
- 弹窗开关一键启用/禁用
- 可选配置 ChatGPT API Key 或 Kimi API Key，启用 LLM 辅助判定
- 基于 SVM + LLM 的混合分类策略：置信度高时直接用 SVM，低时回退 LLM

### 支持的分类类别

桌面应用、AI 与机器学习、微信小程序开发、企业应用、Web 应用、移动应用、代码开发工具或插件、服务端应用、游戏开发、应用插件、其他、未分类

## 项目结构

```
├── 前端代码/
│   ├── manifest.json          # Chrome 扩展清单
│   ├── popup.html             # 弹出窗口界面
│   ├── popup.js               # 弹出窗口逻辑（开关、设置）
│   ├── content.js             # 内容脚本（注入 GitHub 页面）
├── 后端代码/
│   ├── domain_get.py          # Flask 服务入口（API 路由）
│   ├── svm_predictor.py       # SVM 模型预测器
│   ├── readme_words.py        # README 关键词提取
│   ├── gpt_predictor.py       # GPT 分类器
│   ├── kimi_predictor.py      # Kimi/Moonshot 分类器
│   ├── linear_svc_model.pkl   # 训练好的 SVM 模型
│   ├── scaler.pkl             # 特征标准化器
│   ├── label_mapping.pkl      # 标签映射
│   ├── keyword_dict.pkl       # 关键词字典
│   └── label_encoder.pkl      # 标签编码器
└── readme.md
```

## 工作原理

1. 用户浏览 GitHub 仓库页面时，扩展的 content script 检测页面类型
2. 将仓库的 owner/repo 发送到本地 Flask 后端 `POST /domain`
3. 后端通过 GitHub API 获取仓库 README 内容
4. 从 README 中提取高频关键词，送入 SVM 模型预测分类
5. 若 SVM Top1 与 Top2 概率差 >= 0.15，直接采用 SVM 结果
6. 若差值不足且配置了 API Key，调用 LLM（Kimi/GPT）进行二次判定
7. 返回最终分类结果，前端在仓库名旁渲染徽标

## 后端部署

### 环境要求

- Python 3.12+
- 可访问 GitHub API 的网络环境

### 安装依赖

```bash
pip install flask flask-cors openai joblib numpy scipy scikit-learn
```

### 配置

1. 在 `domain_get.py` 中设置 `GITHUB_TOKEN`（用于调用 GitHub API 获取 README）
2. （可选）如需 LLM 判定，在前端弹窗设置中填入 API Key：
   - Kimi：使用 `kimi_predictor.py`，默认模型 `kimi-k2-turbo-preview`，endpoint `https://api.moonshot.cn/v1`
   - GPT：使用 `gpt_predictor.py`，默认模型 `gpt-4o-mini`

### 启动服务

```bash
cd 后端代码
python domain_get.py
```

启动后控制台输出示例：

```
* Running on http://127.0.0.1:8000
* Running on http://192.168.1.36:8000
```

默认监听 `0.0.0.0:8000`，前端扩展默认连接 `http://127.0.0.1:8000/domain`。

## 浏览器扩展安装

1. 打开 Chrome 浏览器，进入 `chrome://extensions/`
2. 开启右上角 **开发者模式**
3. 点击 **加载未打包的扩展程序**
4. 选择 `前端代码/` 目录
5. 扩展安装完成，工具栏出现 Domain Classifier 图标

## 使用说明

1. 确保后端服务已启动
2. 点击扩展图标，打开 **插件开关**
3. （可选）点击齿轮图标进入设置，填入 API Key
4. 访问任意 GitHub 仓库页面或列表页，即可看到分类徽标

## 注意事项

- 后端默认连接 `http://127.0.0.1:8000`，如需修改请编辑 `content.js` 中的 `API_URL`
- GitHub API 有频率限制，建议配置 GitHub Token 以提高限额
- LLM 判定需要有效的 API Key，未配置时仅使用 SVM 预测
- 模型文件（`.pkl`）需与 `domain_get.py` 在同一目录下
