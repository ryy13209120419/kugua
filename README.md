[README.md](https://github.com/user-attachments/files/28662530/README.md)
<p align="center">
  <img src="icons/icon-192.svg" width="80" alt="logo">
  <h1 align="center">🥒 苦瓜大王交易复盘工具</h1>
  <p align="center"><strong>TradeLens Pro</strong> · 你的专属交易日志分析平台</p>
  <p align="center">
    <img src="https://img.shields.io/badge/状态-稳定-green" alt="状态">
    <img src="https://img.shields.io/badge/版本-3.1-blue" alt="版本">
    <img src="https://img.shields.io/badge/许可-MIT-orange" alt="许可">
  </p>
</p>

---

## 📖 简介

**苦瓜大王交易复盘工具** 是一款面向加密货币交易者的纯前端复盘分析工具。支持手动记账、截图分析、AI 智能解读、实时行情监控，帮助你系统化地回顾每一笔交易，不断优化交易策略。

> 🎯 **谁适合用？** 合约交易者、现货交易者、任何想认真复盘的人

---

## ✨ 功能亮点

### 📊 交易仪表盘
- **盈亏总览**：总盈亏、胜率、盈亏比、最大回撤一目了然
- **交易评级**：系统自动为每笔交易打分（A-D 级）
- **情绪分析**：识别你的交易情绪模式（FOMO、贪婪、冷静…）
- **待复盘标记**：标记需要回顾的交易，不遗漏任何成长机会

### 📋 交易记录
- **手动记账**：记录交易对、方向、入场/出场价、数量、盈亏
- **信号与错误标记**：勾选入场信号（趋势突破、RSI、ICT…）和交易错误（扛单、重仓、FOMO…）
- **情绪记录**：记录每笔交易时的情绪状态
- **筛选与搜索**：按交易对、方向、交易所、时间范围快速筛选

### 📅 日历视图
- 盈亏日历可视化，一眼看出哪段时间表现最好/最差
- 点击日期查看当日交易详情

### 🧠 AI 智能分析
#### 截图分析
- 上传交易截图，AI 自动解读信号和入场时机
- 支持 ICT / 价格行为 / SMC / 谐波 四种分析框架
- 历史分析记录保存，随时回顾

#### 市场分析
- **实时行情**：接入 Binance API，获取主流币实时价格和涨跌幅
- **恐惧贪婪指数**：辅助判断市场情绪
- **AI 市场解读**：基于实时数据生成五个板块的分析报告
  - 📈 走势预测
  - ⚡ 异动监测
  - 🎯 机会提示
  - 📋 具体点位与建议

### ⚙️ 设置
- **API 配置**：支持 DeepSeek / OpenAI 自定义 API
- **双币种支持**：USD / CNY 切换
- **数据管理**：CSV 导入（Binance 持仓历史 / 通用格式）、JSON 导出备份
- **主题切换**：深色 / 浅色模式

### 💖 赞助与联系
- 支付宝打赏支持
- QQ 交流群

---

## 🚀 快速开始

### 在线使用
部署到 GitHub Pages 后打开网页即可使用，无需安装任何软件。

### 本地使用
直接双击 `index.html` 在浏览器中打开即可，所有数据存储在浏览器本地（localStorage）。

### 添加到主屏幕
支持 PWA，可在浏览器菜单中点击「添加到主屏幕」，像 APP 一样离线使用。

---

## 🛠 技术栈

- **纯前端**：HTML5 + CSS3 + JavaScript（ES6）
- **图标**：Lucide Icons
- **PWA**：支持离线访问、添加到主屏幕
- **数据存储**：localStorage（浏览器本地，不上传服务器）
- **AI 接口**：OpenAI / DeepSeek API（浏览器直连）
- **实时数据**：Binance API（浏览器直连）

---

## 🔒 隐私声明

- ✅ 所有交易数据存储在**你的浏览器本地**，不会上传到任何服务器
- ✅ 截图分析使用本地图片上传，AI 分析仅发送图片描述
- ✅ 无需注册账号，无需后端服务
- ✅ 纯静态部署，零数据泄露风险

---

## 📦 部署

### GitHub Pages（推荐）
1. Fork 或上传本项目到你的 GitHub 仓库
2. 进入仓库 Settings → Pages
3. Branch 选择 `main`，文件夹选择 `/ (root)`
4. 等待几分钟，访问 `https://你的用户名.github.io/仓库名/`

### 其他静态托管
支持任何静态文件托管服务（Vercel、Netlify、Cloudflare Pages 等），直接上传 `index.html` 及所有文件即可。

---

## ⚠️ 注意事项

- 删除浏览器缓存会丢失数据，请定期在设置页中导出备份
- AI 分析需要自行配置 API Key（支持 DeepSeek / OpenAI）
- 建议使用 Chrome / Edge 最新版浏览器以获得最佳体验

---

## 📝 License

MIT License

---

<p align="center">Made with ❤️ for every trader who wants to improve</p>
