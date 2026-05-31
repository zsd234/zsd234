# PPT 模板自动识别系统 (Multi-Agent Skill)

## 概述

这是一个基于多智能体架构的PowerPoint模板自动识别系统。系统能够分析PPT文件的结构、设计元素、内容特征，自动识别模板类型并提供优化建议。

## 系统架构

### 多智能体组成

1. **文件分析智能体 (File Analyzer Agent)**
   - 解析PPT文件结构
   - 提取元数据和基本信息

2. **设计识别智能体 (Design Recognition Agent)**
   - 分析视觉设计元素
   - 识别色彩方案、字体、布局类型

3. **内容分析智能体 (Content Analysis Agent)**
   - 分析幻灯片内容
   - 识别内容模式和结构

4. **模板分类智能体 (Template Classification Agent)**
   - 综合前三个智能体的结果
   - 识别模板类型
   - 输出分类结果

5. **优化建议智能体 (Optimization Agent)**
   - 基于识别结果提供优化建议
   - 生成详细报告

## 功能特性

- ✅ 自动识别PPT模板类型
- ✅ 分析设计元素和色彩方案
- ✅ 识别内容结构模式
- ✅ 提供优化建议
- ✅ 生成详细分析报告
- ✅ 支持批量处理

## 安装依赖

```bash
pip install python-pptx pillow numpy scikit-learn requests
```

## 使用方法

```python
from ppt_template_analyzer import PPTTemplateAnalyzerSystem

# 初始化系统
analyzer = PPTTemplateAnalyzerSystem()

# 分析PPT文件
result = analyzer.analyze_ppt("path/to/presentation.pptx")

# 获取识别结果
print(f"模板类型: {result['template_type']}")
print(f"置信度: {result['confidence']:.2%}")
print(f"设计特征: {result['design_features']}")
print(f"优化建议: {result['recommendations']}")
```

## 项目结构

```
.
├── README.md
├── requirements.txt
├── ppt_template_analyzer.py          # 主系统文件
├── agents/
│   ├── __init__.py
│   ├── file_analyzer.py              # 文件分析智能体
│   ├── design_recognition.py         # 设计识别智能体
│   ├── content_analysis.py           # 内容分析智能体
│   ├── template_classifier.py        # 模板分类智能体
│   └── optimization.py               # 优化建议智能体
├── models/
│   ├── __init__.py
│   ├── templates.py                  # 模板定义
│   └── features.py                   # 特征定义
├── utils/
│   ├── __init__.py
│   ├── color_analyzer.py             # 色彩分析工具
│   ├── layout_analyzer.py            # 布局分析工具
│   └── logger.py                     # 日志工具
└── tests/
    ├── __init__.py
    ├── test_analyzer.py
    └── sample_presentations/
```

## 模板识别类型

系统可以识别以下PPT模板类型：

- **业务演示 (Business Presentation)**
- **教育培训 (Educational Training)**
- **学术报告 (Academic Presentation)**
- **销售推介 (Sales Pitch)**
- **产品发布 (Product Launch)**
- **财务报表 (Financial Report)**
- **技术文档 (Technical Documentation)**
- **创意展示 (Creative Showcase)**

## 许可证

MIT

## 作者

zsd234
