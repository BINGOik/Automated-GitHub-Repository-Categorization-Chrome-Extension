# 分类体系文档

> 本文档说明 GitHub 仓库领域分类器使用的 12 类分类体系，包括类别定义、判定依据、典型关键词、易混淆边界和标注建议。

---

## 1. 分类目标

本项目的分类目标是判断一个 GitHub 仓库主要属于哪一类软件开发领域。

分类时优先关注：

1. 仓库最终面向的应用场景；
2. README 中描述的核心用途；
3. 项目运行方式和使用对象；
4. 技术栈与项目结构；
5. 是否依赖某个宿主环境；
6. 是否主要服务开发者、企业用户、普通终端用户或研究人员。

不应只根据单个关键词判断，例如：

- 出现 `api` 不一定是服务器应用；
- 出现 `plugin` 不一定是应用插件，也可能是代码开发工具插件；
- 出现 `web` 不一定是网页应用，也可能只是提供 Web 文档；
- 出现 `ai` 不一定是 AI 应用，也可能只是调用了一个 AI API。

---

## 2. 12 类分类总表

| 序号 | 中文类别 | 英文参考名 | 简要定义 |
|---:|---|---|---|
| 1 | 桌面应用 | Desktop Applications | 运行在 Windows、macOS、Linux 等桌面操作系统上的独立应用 |
| 2 | 人工智能和机器学习应用 | AI and Machine Learning Applications | 使用、训练、部署或服务 AI/ML 模型的应用或工具 |
| 3 | 微信应用开发 | WeChat Application Development | 微信小程序、公众号、企业微信、微信插件或微信 API 集成项目 |
| 4 | 企业应用 | Enterprise Applications | 面向企业管理、业务流程、组织协同或内部系统的软件 |
| 5 | 网页应用 | Web Applications | 运行在浏览器中的 Web 应用，通常包含前端页面和用户交互 |
| 6 | 移动应用 | Mobile Applications | 面向 Android、iOS 或跨平台移动端的应用 |
| 7 | 代码开发工具或插件 | Code Development Tools or Plugins | 辅助开发者编码、构建、调试、测试、部署或 IDE 扩展的工具 |
| 8 | 服务器应用 | Server Applications | 运行在服务端，提供 API、后台服务、任务调度或基础能力的项目 |
| 9 | 游戏软件 | Game Development / Game Software | 游戏、游戏引擎、图形渲染、游戏工具链或互动娱乐项目 |
| 10 | 应用插件 | Application Plugins | 依赖浏览器、CMS、设计软件、办公软件等宿主应用运行的插件 |
| 11 | 其他 | Others | 具有明确用途但不适合归入上述类别的项目 |
| 12 | 未分类 | Unclassified | README 或项目信息不足，无法可靠判断类别 |

---

## 3. 分类优先级原则

当一个项目同时符合多个类别时，建议按以下原则判断：

### 3.1 看最终用户，而不是实现技术

例如一个企业后台系统使用 React 和 Flask 实现：

- 技术上包含网页前端；
- 运行上包含服务器后端；
- 但最终用途是企业业务管理。

更适合归为：

```text
企业应用
```

### 3.2 看主要功能，而不是辅助功能

例如一个移动 App 后端仓库：

- README 提到 Android/iOS 客户端；
- 但仓库本身是服务端 API。

如果仓库主要代码是后端服务，应归为：

```text
服务器应用
```

### 3.3 看宿主依赖

如果项目必须安装到某个宿主应用中才能发挥作用，例如 Chrome Extension、WordPress 插件、Figma 插件，优先考虑：

```text
应用插件
```

如果插件主要服务于代码开发环境，例如 VS Code 插件、ESLint 插件、Babel 插件，则优先考虑：

```text
代码开发工具或插件
```

### 3.4 信息不足时谨慎分类

如果 README 非常短，只包含项目名、徽章或安装命令，无法判断用途，应归为：

```text
未分类
```

---

## 4. 类别详细定义

## 4.1 桌面应用

### 定义

桌面应用是指直接运行在 Windows、macOS、Linux 等桌面操作系统上的独立图形界面应用或命令行配套桌面软件。

### 典型特征

| 特征 | 示例 |
|---|---|
| 桌面运行环境 | Windows、macOS、Linux |
| 桌面框架 | Electron、Qt、GTK、WPF、WinUI、Tauri |
| 安装包 | `.exe`、`.dmg`、`.AppImage`、`.deb`、`.rpm` |
| 功能定位 | 编辑器、播放器、客户端、桌面工具 |

### 典型关键词

```text
desktop
electron
qt
gtk
windows
macos
linux
tauri
native app
cross-platform desktop
tray
menubar
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个跨平台 Markdown 编辑器 | 桌面应用 |
| 一个 Electron 写的本地笔记软件 | 桌面应用 |
| 一个 Windows 截图工具 | 桌面应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 网页应用 | 桌面应用通常需要安装到本机，不是通过浏览器访问 |
| 代码开发工具或插件 | 如果主要服务于编码流程，且是 IDE/CLI 工具，可能归为开发工具 |
| 应用插件 | 如果必须依赖宿主软件运行，则应归为应用插件 |

---

## 4.2 人工智能和机器学习应用

### 定义

人工智能和机器学习应用是指以 AI/ML 模型、算法、训练、推理、数据处理或智能能力为核心的软件项目。

### 典型特征

| 特征 | 示例 |
|---|---|
| AI 框架 | PyTorch、TensorFlow、JAX、Keras |
| 任务类型 | NLP、CV、语音识别、推荐系统、生成式 AI |
| 模型行为 | 训练、微调、推理、评估、部署 |
| 数据处理 | 数据集处理、特征工程、向量检索 |
| LLM 相关 | ChatGPT、OpenAI、LangChain、RAG、Agent |

### 典型关键词

```text
machine learning
deep learning
neural network
pytorch
tensorflow
llm
rag
embedding
inference
training
fine-tuning
computer vision
nlp
recommendation
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个图像分类训练框架 | 人工智能和机器学习应用 |
| 一个基于 LLM 的问答系统 | 人工智能和机器学习应用 |
| 一个用于模型部署的推理服务 | 人工智能和机器学习应用，若主要是通用 API 服务可考虑服务器应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 服务器应用 | 如果 AI 只是服务中的一个功能，而主体是通用后端，可能是服务器应用 |
| 网页应用 | 如果只是一个调用 AI API 的 Web UI，要看项目核心是否是 AI 能力 |
| 代码开发工具或插件 | AI 编程助手、代码补全插件可归为开发工具或插件 |

---

## 4.3 微信应用开发

### 定义

微信应用开发类项目是指围绕微信生态构建的软件，包括微信小程序、公众号、企业微信、微信支付、微信登录和微信 API 集成等。

### 典型特征

| 特征 | 示例 |
|---|---|
| 微信平台 | WeChat、微信小程序、公众号、企业微信 |
| 微信 API | login、payment、message、mini program |
| 文件结构 | `app.json`、`pages/`、`miniprogram/` |
| 业务场景 | 小程序商城、公众号机器人、企业微信通知 |

### 典型关键词

```text
wechat
weixin
mini program
miniprogram
wx
wxapp
official account
wechat pay
enterprise wechat
work wechat
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 微信小程序商城 | 微信应用开发 |
| 企业微信机器人通知服务 | 微信应用开发 |
| 微信支付 SDK 示例项目 | 微信应用开发 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 移动应用 | 小程序不是原生 Android/iOS App，应归为微信应用开发 |
| 网页应用 | 微信网页授权项目如果核心是公众号/微信登录，也可归为微信应用开发 |
| 服务器应用 | 如果只是一个通用后端，同时支持微信登录，要看微信是否为核心功能 |

---

## 4.4 企业应用

### 定义

企业应用是指服务于组织、公司、团队或业务流程的软件系统，通常用于管理、协同、运营、流程审批、客户关系、资源计划或内部平台。

### 典型特征

| 特征 | 示例 |
|---|---|
| 业务管理 | ERP、CRM、OA、HRM、SCM |
| 企业流程 | 审批、工单、权限、报表、组织架构 |
| 后台系统 | Admin Dashboard、Management System |
| 多角色 | 管理员、员工、客户、部门、租户 |
| 组织级部署 | SaaS、多租户、私有化部署 |

### 典型关键词

```text
enterprise
crm
erp
oa
admin
dashboard
management system
workflow
approval
tenant
permission
rbac
report
business
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 企业客户关系管理系统 | 企业应用 |
| 后台管理系统模板 | 企业应用 |
| 多租户 SaaS 平台 | 企业应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 网页应用 | 企业应用通常强调业务管理和组织流程，而不仅是 Web 前端 |
| 服务器应用 | 如果是纯 API 服务，无明确企业业务，则可能是服务器应用 |
| 代码开发工具或插件 | DevOps 平台如果核心服务开发流程，可能归为开发工具 |

---

## 4.5 网页应用

### 定义

网页应用是指通过浏览器访问，具有用户界面和交互能力的 Web 项目。它可以是前端单页应用，也可以包含前后端整合。

### 典型特征

| 特征 | 示例 |
|---|---|
| 前端框架 | React、Vue、Angular、Svelte、Next.js |
| 浏览器运行 | Browser、SPA、PWA |
| 用户界面 | 页面、组件、路由、表单 |
| Web 技术 | HTML、CSS、JavaScript、TypeScript |
| 部署方式 | Vercel、Netlify、静态站点、Web Server |

### 典型关键词

```text
web app
frontend
react
vue
angular
svelte
next.js
spa
pwa
website
browser
ui
component
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 React 在线白板应用 | 网页应用 |
| 一个 Vue 博客系统前端 | 网页应用 |
| 一个 PWA 待办事项应用 | 网页应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 企业应用 | 如果明确面向企业业务流程，应归为企业应用 |
| 服务器应用 | 如果没有前端页面，主要提供 API，则应归为服务器应用 |
| 应用插件 | Chrome Extension 虽然使用 JS/HTML，但应归为应用插件 |

---

## 4.6 移动应用

### 定义

移动应用是指运行在 Android、iOS 或跨平台移动端环境中的应用程序。

### 典型特征

| 特征 | 示例 |
|---|---|
| 平台 | Android、iOS |
| 框架 | Flutter、React Native、SwiftUI、Kotlin、Jetpack Compose |
| 安装包 | APK、IPA |
| 移动特性 | 相机、定位、通知、移动端 UI |
| 应用商店 | App Store、Google Play |

### 典型关键词

```text
android
ios
mobile
flutter
react native
swift
kotlin
apk
ipa
app store
google play
jetpack compose
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 Flutter 记账 App | 移动应用 |
| 一个 iOS 健身应用 | 移动应用 |
| 一个 Android 文件管理器 | 移动应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 微信应用开发 | 微信小程序不属于原生移动应用 |
| 网页应用 | 响应式 Web 页面不是移动应用 |
| 桌面应用 | 跨平台项目要看主要部署目标 |

---

## 4.7 代码开发工具或插件

### 定义

代码开发工具或插件是指主要服务于开发者编写、调试、构建、测试、部署、分析代码的软件工具，或集成到 IDE / 编辑器 / 构建系统中的扩展。

### 典型特征

| 特征 | 示例 |
|---|---|
| IDE 插件 | VS Code、JetBrains、Vim、Emacs |
| 构建工具 | Webpack、Vite、Babel、Rollup |
| 代码质量 | ESLint、Prettier、Formatter、Linter |
| 测试工具 | Test Runner、Mock、Coverage |
| DevOps 工具 | CLI、CI/CD、Docker 辅助工具 |

### 典型关键词

```text
developer tool
cli
sdk
vscode
ide
plugin
extension
linter
formatter
compiler
debugger
testing
build tool
devops
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 VS Code 代码补全插件 | 代码开发工具或插件 |
| 一个 ESLint 规则包 | 代码开发工具或插件 |
| 一个命令行项目脚手架 | 代码开发工具或插件 |
| 一个 GitHub Action 工具 | 代码开发工具或插件 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 应用插件 | 如果插件服务普通用户或浏览器功能，通常是应用插件；如果服务编码流程，则是开发工具 |
| 服务器应用 | CLI 调用远程服务不代表项目主体是服务器应用 |
| 桌面应用 | 桌面 IDE 本身可能是桌面应用，但 IDE 插件是开发工具 |

---

## 4.8 服务器应用

### 定义

服务器应用是指运行在服务器端，为客户端、其他服务或系统提供 API、后台任务、数据处理、消息通信、业务逻辑或基础服务的软件。

### 典型特征

| 特征 | 示例 |
|---|---|
| 后端框架 | Flask、Django、FastAPI、Express、Spring Boot |
| API | REST、GraphQL、RPC、WebSocket |
| 服务端能力 | 认证、数据库、缓存、任务队列 |
| 部署 | Docker、Kubernetes、Nginx、Gunicorn |
| 后台任务 | Worker、Scheduler、Consumer |

### 典型关键词

```text
server
backend
api
rest
graphql
service
microservice
database
redis
queue
worker
docker
kubernetes
spring boot
fastapi
flask
express
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 Flask API 服务 | 服务器应用 |
| 一个消息队列消费服务 | 服务器应用 |
| 一个认证授权服务 | 服务器应用 |
| 一个爬虫调度平台后端 | 服务器应用 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 网页应用 | 如果包含明显浏览器前端和用户交互，可能归为网页应用 |
| 企业应用 | 如果服务于企业业务流程，可能归为企业应用 |
| AI 应用 | 如果核心是模型训练/推理，可能归为 AI/ML 应用 |

---

## 4.9 游戏软件

### 定义

游戏软件类项目包括可玩的游戏、游戏引擎、游戏开发工具、图形渲染、互动娱乐和游戏相关资源管理工具。

### 典型特征

| 特征 | 示例 |
|---|---|
| 游戏引擎 | Unity、Unreal、Godot |
| 游戏类型 | 2D、3D、RPG、FPS、Puzzle |
| 图形技术 | Rendering、OpenGL、Vulkan、WebGL |
| 游戏机制 | Physics、Animation、Level、Player |
| 游戏开发工具 | 地图编辑器、资源打包、关卡设计 |

### 典型关键词

```text
game
game engine
unity
unreal
godot
2d
3d
rendering
opengl
vulkan
webgl
physics
sprite
level editor
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 2D 平台跳跃游戏 | 游戏软件 |
| 一个 Godot 插件式地图编辑器 | 游戏软件，若主要作为 Godot 插件也可考虑应用插件 |
| 一个 WebGL 游戏引擎 | 游戏软件 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 网页应用 | WebGL 游戏虽然在浏览器运行，但核心是游戏 |
| 代码开发工具或插件 | 如果是通用开发工具，不只服务游戏开发，可能归为开发工具 |
| 桌面应用 | 桌面游戏优先归为游戏软件 |

---

## 4.10 应用插件

### 定义

应用插件是指依赖某个宿主应用、平台或运行环境才能发挥作用的软件扩展。它通常增强宿主应用功能，而不是独立运行。

### 典型宿主

| 宿主类型 | 示例 |
|---|---|
| 浏览器 | Chrome Extension、Firefox Add-on |
| CMS | WordPress Plugin、Drupal Plugin |
| 设计工具 | Figma Plugin、Sketch Plugin |
| 办公软件 | Excel Add-in、Notion 插件 |
| 平台软件 | Obsidian Plugin、Jira Plugin、Slack App |

### 典型关键词

```text
chrome extension
browser extension
firefox addon
plugin
addon
extension
wordpress plugin
figma plugin
obsidian plugin
slack app
jira plugin
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| 一个 Chrome Extension | 应用插件 |
| 一个 WordPress SEO 插件 | 应用插件 |
| 一个 Figma 设计辅助插件 | 应用插件 |
| 一个 Obsidian 笔记插件 | 应用插件 |

### 易混淆类别

| 容易混淆 | 区分方式 |
|---|---|
| 代码开发工具或插件 | VS Code 插件、Babel 插件等开发者工具优先归为代码开发工具或插件 |
| 网页应用 | Chrome Extension 使用 HTML/JS，但不是普通网页应用 |
| 桌面应用 | 如果插件依赖桌面软件运行，不是独立桌面应用 |

---

## 4.11 其他

### 定义

其他类用于表示项目有明确用途，但不适合归入前面 10 个主要类别。

### 可能场景

| 场景 | 示例 |
|---|---|
| 数据集 | 只发布数据，不包含明显应用逻辑 |
| 文档集合 | 技术笔记、教程、学习资料 |
| 配置集合 | dotfiles、主题、模板 |
| 资源库 | 图标、字体、图片、列表清单 |
| 算法示例 | 不构成完整 AI/ML 应用的零散算法实现 |
| 学习项目 | 练习代码、课程实验 |

### 典型关键词

```text
awesome
list
dataset
template
boilerplate
notes
tutorial
resources
collection
examples
cheatsheet
```

### 判定示例

| 项目描述 | 分类 |
|---|---|
| awesome-python 资源列表 | 其他 |
| 一组配置文件 dotfiles | 其他 |
| 一个仅包含学习笔记的仓库 | 其他 |

### 与未分类的区别

| 类别 | 区别 |
|---|---|
| 其他 | 能看出项目用途，但不属于主要应用类别 |
| 未分类 | 信息不足，无法判断用途 |

---

## 4.12 未分类

### 定义

未分类用于表示 README 或仓库信息过少，无法做出可靠判断。

### 常见情况

| 情况 | 示例 |
|---|---|
| README 缺失 | 仓库没有 README |
| README 太短 | 只有项目名，没有描述 |
| 内容无意义 | 只有 badge、空标题或占位文字 |
| 信息冲突 | README 与代码结构严重不一致 |
| 私有或访问失败 | 无法获取 README |
| 语言处理失败 | 文本无法被当前清洗逻辑正确解析 |

### 判定示例

| 项目描述 | 分类 |
|---|---|
| README 只有 `# test` | 未分类 |
| README 只有 `TODO` | 未分类 |
| GitHub API 无法读取 README | 未分类或接口错误 |
| 关键词抽取结果为空 | 未分类 |

---

## 5. 易混淆类别对照表

| 类别 A | 类别 B | 区分要点 |
|---|---|---|
| 网页应用 | 企业应用 | 是否强调企业业务流程、权限、组织、管理后台 |
| 网页应用 | 服务器应用 | 是否有浏览器用户界面；纯 API 通常是服务器应用 |
| 桌面应用 | 应用插件 | 是否能独立运行；依赖宿主软件通常是插件 |
| 应用插件 | 代码开发工具或插件 | 插件是否主要服务代码开发流程 |
| 移动应用 | 微信应用开发 | 是否是 Android/iOS App；微信小程序归微信应用开发 |
| AI/ML 应用 | 服务器应用 | AI 是否是核心功能，而不是普通 API 的一部分 |
| 游戏软件 | 网页应用 | Web 游戏仍优先归游戏软件 |
| 其他 | 未分类 | 是否能看出用途；能看出但不入类为其他，完全看不出为未分类 |

---

## 6. 标注建议

### 6.1 标注流程

人工标注或复核时建议按以下步骤：

1. 阅读仓库名称和 description；
2. 阅读 README 的标题、简介、功能列表；
3. 查看安装和使用方式；
4. 查看技术栈和运行环境；
5. 判断项目最终服务对象；
6. 对照 12 类定义选择主类别；
7. 如果两个类别都合理，选择更能体现项目用途的类别；
8. 如果信息不足，选择“未分类”。

### 6.2 优先级建议

当多个类别同时出现时，可参考：

```text
明确宿主插件 > 明确开发工具 > 明确企业业务 > 明确平台应用 > 通用服务端/网页应用 > 其他 > 未分类
```

但这不是绝对规则，应以 README 的主旨为准。

### 6.3 关键词不能单独决定分类

以下关键词需结合上下文判断：

| 关键词 | 可能类别 |
|---|---|
| `plugin` | 应用插件、代码开发工具或插件 |
| `extension` | 应用插件、代码开发工具或插件 |
| `api` | 服务器应用、AI/ML 应用、企业应用 |
| `dashboard` | 企业应用、网页应用、服务器应用 |
| `ai` | AI/ML 应用、网页应用、代码开发工具 |
| `game` | 游戏软件、游戏开发工具、资源集合 |
| `mobile` | 移动应用、响应式网页应用 |
| `admin` | 企业应用、网页应用、服务器应用 |

---

## 7. 输出类别规范

为了保证模型、后端和前端一致，建议统一使用中文类别名称作为最终展示结果：

```text
桌面应用
人工智能和机器学习应用
微信应用开发
企业应用
网页应用
移动应用
代码开发工具或插件
服务器应用
游戏软件
应用插件
其他
未分类
```

如果大模型返回英文类别，建议在后端增加映射：

| 英文输出 | 中文标准类别 |
|---|---|
| `desktop applications` | 桌面应用 |
| `ai and machine learning applications` | 人工智能和机器学习应用 |
| `WeChat application development` | 微信应用开发 |
| `enterprise applications` | 企业应用 |
| `web applications` | 网页应用 |
| `mobile applications` | 移动应用 |
| `code development tools or plugins` | 代码开发工具或插件 |
| `server application` | 服务器应用 |
| `game development` | 游戏软件 |
| `application plugins` | 应用插件 |
| `others` | 其他 |
| `unclassified` | 未分类 |

---

## 8. 复核样例

| 仓库描述 | 推荐类别 | 理由 |
|---|---|---|
| “A Chrome extension that shows repository category badges on GitHub.” | 应用插件 | 依赖 Chrome 浏览器运行，扩展 GitHub 页面能力 |
| “A VS Code extension for Python auto-completion.” | 代码开发工具或插件 | 插件服务代码编写流程 |
| “A React dashboard for internal CRM management.” | 企业应用 | 主要服务企业客户管理 |
| “A Flask REST API for user authentication.” | 服务器应用 | 主要提供后端 API |
| “A PyTorch implementation of image segmentation.” | 人工智能和机器学习应用 | 核心是 ML 模型实现 |
| “A Flutter app for personal finance.” | 移动应用 | 面向移动端运行 |
| “A WebGL racing game.” | 游戏软件 | 核心是游戏 |
| “A collection of useful shell aliases.” | 其他 | 有用途但不属于主要应用类 |
| “TODO: add README.” | 未分类 | 信息不足 |

---

## 9. 与模型训练的关系

分类体系不仅用于前端展示，也影响模型训练和评估。

在训练或更新模型时，应保证：

1. 训练数据标签与本文档类别完全一致；
2. `label_mapping.pkl` 中的类别顺序稳定；
3. LLM Prompt 中的类别列表与本文档一致；
4. 测试用例覆盖所有 12 类；
5. 新增类别时同步更新：
   - `categories.md`
   - LLM Prompt
   - 训练数据标签
   - `label_mapping.pkl`
   - 测试 fixtures
   - 前端展示样式

---

## 10. 小结

本分类体系的重点是“仓库主要用途”，而不是单一技术栈。判断时应综合 README、项目结构、运行环境和目标用户。

一句话原则：

> 看项目最终解决什么问题、服务谁、在哪里运行，再选择最能代表它主用途的类别。
