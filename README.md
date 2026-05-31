# PPT Template Deck Builder

一个用于 **深度识别 PPT 模板并自动生成高质量演示文稿** 的 Codex Skill。

它不是简单替换文字，而是先理解模板：每一页是什么类型、能放几个观点、文本框和图片框分别代表什么、字体字号和版式规则是什么；再理解用户文档的逻辑，自动把内容匹配到合适的模板页中，并进行动画、字号、文件兼容和无障碍检查。

## 核心能力

- **模板深度识别**：解析 `.pptx` 的页面、母版、版式、文本框、图片框、图表、字体、字号、颜色、坐标和层级。
- **内页类型判断**：识别封面、目录、章节页、2 点页、3 点页、4 点页、指标页、图文页、流程页、时间线页等。
- **内容容量判断**：判断某页适合放 2 个点、3 个点、4 个点，还是应该拆页或生成模板变体。
- **文档逻辑提炼**：从 `.docx`、`.md`、`.txt`、`.json` 中提炼章节、观点、含义、证据和逻辑关系。
- **模板匹配规划**：生成 `final_slide_plan.json`，记录每段内容应该进入哪一页、哪个元素、用什么变换方式。
- **动画规划**：生成保守、适合课堂/汇报的动画计划，避免乱加飞入、旋转、弹跳等干扰效果。
- **字号与放映检查**：检查课堂展示和普通汇报的最低字号、标题长度、正文行数、bullet 数量。
- **交付兼容性检查**：检查 PPTX 文件大小、媒体大小、图片像素、外链、嵌入字体、非通用字体。
- **无障碍结构检查**：检查 slide title、alt text、reading order 风险和文件名式无效 alt text。

## 一键安装

下载或克隆本仓库后，在 PowerShell 中运行：

```powershell
.\scripts\install.ps1
```

安装后，在 Codex 里这样调用：

```text
使用 $ppt-template-deck-builder，分析这个 PPT 模板，并根据我提供的文档生成一份课堂展示用 PPT。
```

## 快速校验

```powershell
.\scripts\validate.ps1
```

校验内容包括：

- Skill 必需文件是否存在
- `SKILL.md` 元数据是否有效
- Python 脚本是否能通过语法检查

GitHub Actions 也会自动执行基础校验：

```text
.github/workflows/validate.yml
```

## 直接跑一次模板分析

```powershell
.\scripts\run_existing_template.ps1 `
  -TemplatePptx "C:\path\to\template.pptx" `
  -SourceDocument "C:\path\to\source.docx"
```

输出会放到 `outputs/`，包括：

- `template_model.json`
- `template_semantics.json`
- `content_outline.json`
- `final_slide_plan.json`
- `animation_plan.json`
- `qa_report.json`

这些是后续生成高质量 PPT 的结构化中间结果。

## 仓库结构

```text
.
├── README.md
├── GITHUB_UPLOAD_GUIDE.md
├── requirements.txt
├── scripts/
│   ├── install.ps1
│   ├── validate.ps1
│   └── run_existing_template.ps1
├── examples/
│   ├── source.example.md
│   └── content.example.json
└── skills/
    └── ppt-template-deck-builder/
        ├── SKILL.md
        ├── agents/
        ├── references/
        └── scripts/
```

真正的 Codex Skill 在：

```text
skills/ppt-template-deck-builder/
```

## 适合的使用场景

- 想用公司/学校/课程 PPT 模板自动生成新 PPT。
- 模板没有规范占位符，但每页有不同卡片、图文、流程、指标结构。
- 想把长文档、课程内容、报告、讲稿整理成 PPT。
- 希望避免字体太小、内容太密、动画太乱、换电脑后变形。
- 希望在最终交付前检查文件大小、图片清晰度、字体兼容和无障碍结构。

## 依赖

```bash
pip install -r requirements.txt
```

主要依赖：

- `lxml`
- `Pillow`

## 说明

这个仓库提供的是 Codex Skill 和配套分析/QA 脚本。最终 PPTX 的高质量生成建议在 Codex 中调用此 skill，并结合可用的 PowerPoint/Presentations 生成能力完成。

## 作者

zsd234
