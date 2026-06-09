# 派谱 / PairPulse

> 购物篮关联分析工具 — 导入 Excel 订单数据，自动输出商品关联规则 + 业务策略建议。

专为没有技术团队的战略咨询顾问、运营人员设计。也支持 JSON 输出，可被任何 AI 智能体（Claude Code / Codex / Trae / OpenClaw / WorkBuddy 等）调用。

---

## 它能做什么

- **推荐搭配** — 发现"买了 A 也买 B"的商品对，用于详情页推荐位
- **组合套餐** — 识别强关联商品，出捆绑套餐方案
- **陈列优化** — 找出该就近摆放的商品组合

---

## 五分钟快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成示例数据
pairpulse make-sample

# 3. 运行分析（使用示例数据）
pairpulse run
```

然后打开 `output/` 目录查看：

| 文件 | 内容 |
|------|------|
| `pairpulse_report.xlsx` | 关联规则明细表 |
| `network_graph.png` | 商品关联网络图 |
| `top_rules.png` | Top 关联规则条形图 |
| `pairpulse_result.json` | 结构化输出（--format json 时生成） |

---

## 三种使用方式

### 方式1：CLI 人类模式

```bash
pairpulse run                           # 用 config.yaml 配置运行
pairpulse run --input data/my.xlsx      # 指定 Excel 文件
pairpulse run --format json             # 输出纯 JSON
```

### 方式2：智能体模式（任何 AI Agent 均可调用）

```bash
pairpulse run --format json --input data.xlsx > result.json
```

输出的 JSON 可直接被 Claude Code / Codex / Trae / OpenClaw / WorkBuddy 等解析。

### 方式3：Python API

```python
from pairpulse import PairPulse

pp = PairPulse(config_path="config.yaml")
pp.run(fmt="json")
```

---

## 数据格式要求

每行 = 一笔订单中的一件商品。一单有多件商品，用相同订单号的多行表示。

| 订单编号 | 商品名称 | 商品单价 | 客户ID |
|---------|---------|---------|--------|
| ORD001 | iPhone 15 Pro Max | 7999 | C001 |
| ORD001 | 手机壳 | 49 | C001 |
| ORD002 | 拿铁咖啡 | 28 | C002 |

必填：`订单编号` + `商品名称`。其余列可选。

详细说明见 [docs/data_prep_guide.md](docs/data_prep_guide.md)。

---

## 没有客户ID怎么办？

系统会自动用**订单总金额**替代客户分层，将订单分为高/中/低消费组，分组跑关联分析。

有商品单价 → 用金额分群。没有单价 → 用订单商品数量分群。

---

## 商品名不统一怎么办？

客户 Excel 里同一商品可能有多种叫法（如"iPhone 15""苹果15""IP15"）。

```bash
# 第一步：生成映射建议表
pairpulse standardize --input data/my.xlsx

# 第二步：打开 output/standardization_mapping.xlsx，审核确认
# 第三步：用确认后的映射表运行
pairpulse run --mapping output/standardization_mapping.xlsx
```

---

## 配置说明

所有参数在 `config.yaml` 中修改，不碰代码：

```yaml
# 填入你 Excel 中的实际列名
columns:
  order_id: "订单编号"
  product_name: "商品名称"
  product_price: "商品单价"    # 有就填，没有留空
  customer_id: ""              # 有就填，没有留空

# 算法阈值（通常不用改）
algo:
  min_support: 0.01
  min_confidence: 0.15
  min_lift: 1.2
```

---

## 项目结构

```
PairPulse/
├── src/pairpulse/        # 源代码
│   ├── cli.py           # CLI 入口
│   ├── core.py          # 核心调度
│   ├── analyzer.py      # Apriori 算法
│   ├── segmenter.py     # 客户/品类分群
│   ├── standardizer.py  # 商品名标准化
│   ├── interpreter.py   # 规则 → 策略
│   ├── exporter.py      # 输出 (JSON/Excel/图表)
│   ├── errors.py        # 异常处理
│   └── utils.py         # 工具函数
├── config.yaml          # 配置文件
├── data/                # 示例数据
├── output/              # 输出目录
├── docs/                # 文档
└── README.md
```

---

## 安装为全局命令

```bash
# 从 PyPI 安装（推荐）
pip install pairpulse

# 或本地开发安装
cd PairPulse
pip install -e .

# 安装后即可在任何目录运行
pairpulse run --input /path/to/data.xlsx
```

---

## 发布新版本（作者参考）

每次更新代码后，按以下两步发布：

### 1️⃣ 更新到 GitHub

```bash
git add .
git commit -m "v0.2.0 更新说明"
git push
```

### 2️⃣ 发布到 PyPI

```bash
# 1. 修改 pyproject.toml 中的 version（如 "0.1.0" → "0.2.0"）

# 2. 构建 + 上传（需 PyPI API Token）
python -m build
twine upload dist/* --username __token__ --password 你的TOKEN

# 3. 更新后用户执行升级
pip install --upgrade pairpulse
```

> 💡 PyPI API Token 在 pypi.org → Account settings → API tokens 创建。Token 只需要创建一次，之后每次上传都能复用。

---

## License

MIT

---

## 支持的 AI 智能体

该工具支持被以下智能体直接调用（`--format json` 模式）：

| 智能体 | 调用方式 |
|--------|---------|
| **Claude Code** | `pairpulse run --format json --input data.xlsx` |
| **OpenAI Codex** | 同上 |
| **Trae** | 同上 |
| **GitHub Copilot Agent** | 同上 |
| **OpenClaw** | 同上 |
| **WorkBuddy** | 同上 |
| **OpenCode** | 同上，也可通过 Skill 声明调用 |
