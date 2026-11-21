# V2EX 外包买家信号雷达

实时聚合 [V2EX 外包节点](https://www.v2ex.com/go/outsourcing) 真实买家帖子，自动提取预算、技术栈、联系方式、紧急度。零 KYC，零人工运营，USDC (Base 网络) 小费罐维护。

## 🎯 核心价值

- **真实买家信号**：仅保留含「求、找人、需要、预算、报价、雇佣、招募、looking for、need、hire、budget」等明确买家意图的帖子
- **关键信息提取**：自动识别预算金额（支持 万/k/K）、技术栈（50+ 关键词）、联系方式（微信/QQ/邮箱/Telegram/Base64）、紧急度
- **零成本运行**：GitHub Actions 每日自动更新，GitHub Pages 免费托管
- **零 KYC 变现**：页面内置 USDC (Base) 小费地址，100% 到账无手续费

## 🚀 在线演示

**GitHub Pages**: `https://qikekika.github.io/v2ex-outsourcing-radar/`

## 📊 数据来源

| 来源 | 方式 | 更新频率 |
|------|------|----------|
| V2EX JSON API | `https://www.v2ex.com/api/topics/show.json?node_name=outsourcing` | 每日 UTC 02:00 |
| V2EX RSS Feed | `https://www.v2ex.com/feed/outsourcing.xml` | 备用来源 |
| Jina AI Reader | `https://r.jina.ai/http://<URL>` | 详情页内容增强 |

## 🛠️ 本地运行

```bash
# 克隆仓库
git clone https://github.com/qikekika/v2ex-outsourcing-radar.git
cd v2ex-outsourcing-radar

# 安装依赖
pip install requests

# 抓取数据
python fetch_data.py

# 本地预览（任意静态服务器）
python -m http.server 8080
# 打开 http://localhost:8080
```

## 📁 项目结构

```
v2ex-outsourcing-radar/
├── index.html          # 前端页面（单文件，无构建）
├── fetch_data.py       # 数据抓取脚本
├── data.json           # 生成的数据文件（自动更新）
├── .github/workflows/
│   └── fetch-data.yml  # GitHub Actions 自动化
└── README.md
```

## ⚙️ 配置说明

### 修改 USDC 小费地址

编辑 `index.html` 中的 `tipAddress` 元素：

```html
<span id="tipAddress">0xYourUSDCBaseAddressHere</span>
```

### 调度时间

修改 `.github/workflows/fetch-data.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 2 * * *'  # UTC 02:00 = 北京时间 10:00
```

### 启用 GitHub Pages

1. 仓库 Settings → Pages
2. Source: "GitHub Actions"
3. 推送触发 workflow 后自动部署

## 🔍 筛选逻辑

### 买家判定（必须满足）
- 标题或内容包含买家关键词（求、找人、需要、预算、报价、雇佣、招募、looking for、need、hire、budget 等）
- 买家关键词得分 > 卖家关键词得分

### 卖家过滤（排除）
- 包含：接单、承接、提供服务、代做、代写、团队、工作室、个人开发、全栈、作品集、案例、报价单

### 信息提取
| 字段 | 方法 | 示例 |
|------|------|------|
| 预算 | 正则匹配 ¥/￥/万/k/K + 数字 | "预算 2万" → 20000 |
| 技术栈 | 关键词词典匹配 (50+) | "Python, React, Docker" |
| 联系方式 | 正则匹配微信/QQ/邮箱/TG/Base64 | "微信: abc123" |
| 紧急度 | 关键词匹配 (急、ASAP、urgent 等) | true/false |

## 💰 变现模式

**USDC (Base) 小费罐** - 零门槛、零 KYC、即时到账

```
地址: 0xYourUSDCBaseAddressHere
网络: Base (Layer 2)
代币: USDC
最小打赏: 1 USDC
手续费: < $0.01 (Base 网络)
```

> 如果这个工具帮你省下了找单时间、发现了高质量买家，请考虑打赏 1 USDC 支持维护。

## 📈 数据样例

```json
{
  "id": 1234567,
  "title": "求一个懂 SEO 的帮忙诊断一下独立站，预算 2k",
  "url": "https://www.v2ex.com/t/1234567",
  "author": "buyer123",
  "created": 1699999999,
  "daysAgo": 0,
  "budget": 20000,
  "techs": ["SEO", "Python"],
  "contacts": ["微信: seo_expert_2024", "邮箱: buyer@example.com"],
  "urgent": true,
  "snippet": "独立站流量上不去，需要专业 SEO 诊断..."
}
```

## 🤝 贡献

欢迎 PR 改进：
- 更多买家/卖家关键词
- 更准确的预算解析
- 新的数据源（如其他技术论坛）
- UI/UX 优化

## ⚠️ 免责声明

- 仅聚合公开信息，不存储私密数据
- 联系方式为帖子原文公开内容，使用前请自行核实
- 本工具不参与任何交易、担保或中介
- 请遵守 V2EX 社区规则和平台条款

## 📄 License

MIT License - 免费用于个人和商业用途