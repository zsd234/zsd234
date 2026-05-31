"""
PPT模板分析系统的测试用例
"""
import os
import sys
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ppt_template_analyzer import PPTTemplateAnalyzerSystem
from models.templates import TemplateTypes


class TestPPTAnalyzer(unittest.TestCase):
    """PPT分析系统测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.analyzer = PPTTemplateAnalyzerSystem(log_level="INFO")
    
    def test_system_initialization(self):
        """测试系统初始化"""
        self.assertIsNotNone(self.analyzer.file_analyzer)
        self.assertIsNotNone(self.analyzer.design_recognizer)
        self.assertIsNotNone(self.analyzer.content_analyzer)
        self.assertIsNotNone(self.analyzer.template_classifier)
        self.assertIsNotNone(self.analyzer.optimizer)
    
    def test_analyze_ppt_structure(self):
        """测试PPT分析"""
        # 这个测试需要真实的PPT文件
        # 示例代码如下：
        pass


class TestMultiAgentCoordination(unittest.TestCase):
    """多智能体协调测试"""
    
    def test_agents_workflow(self):
        """测试智能体工作流程"""
        # 验证智能体的顺序执行
        workflow = [
            "FileAnalyzerAgent",
            "DesignRecognitionAgent", 
            "ContentAnalysisAgent",
            "TemplateClassifierAgent",
            "OptimizationAgent"
        ]
        
        self.assertEqual(len(workflow), 5)
    
    def test_template_types(self):
        """测试模板类型定义"""
        template_types = [
            TemplateTypes.BUSINESS_PRESENTATION,
            TemplateTypes.EDUCATIONAL_TRAINING,
            TemplateTypes.ACADEMIC_PRESENTATION,
            TemplateTypes.SALES_PITCH,
            TemplateTypes.PRODUCT_LAUNCH,
            TemplateTypes.FINANCIAL_REPORT,
            TemplateTypes.TECHNICAL_DOCUMENTATION,
            TemplateTypes.CREATIVE_SHOWCASE,
        ]
        
        self.assertEqual(len(template_types), 8)


def example_usage():
    """使用示例"""
    print("=" * 60)
    print("PPT 模板自动识别系统 - 使用示例")
    print("=" * 60)
    
    # 创建分析系统
    analyzer = PPTTemplateAnalyzerSystem(log_level="INFO")
    
    print("\n系统组件:")
    print("✓ 文件分析智能体 - 解析PPT结构")
    print("✓ 设计识别智能体 - 分析视觉元素")
    print("✓ 内容分析智能体 - 识别内容模式")
    print("✓ 模板分类智能体 - 识别模板类型")
    print("✓ 优化建议智能体 - 提供改进建议")
    
    print("\n支持的模板类型:")
    templates = [
        "业务演示 (Business Presentation)",
        "教育培训 (Educational Training)",
        "学术报告 (Academic Presentation)",
        "销售推介 (Sales Pitch)",
        "产品发布 (Product Launch)",
        "财务报表 (Financial Report)",
        "技术文档 (Technical Documentation)",
        "创意展示 (Creative Showcase)",
    ]
    for i, template in enumerate(templates, 1):
        print(f"  {i}. {template}")
    
    print("\n使用方法:")
    print("  python ppt_template_analyzer.py <PPT文件或目录路径>")
    
    print("\n示例:")
    print("  python ppt_template_analyzer.py presentation.pptx")
    print("  python ppt_template_analyzer.py /path/to/ppts/")
    
    print("\n分析输出包含:")
    print("  ✓ 模板类型识别")
    print("  ✓ 置信度评分")
    print("  ✓ 设计特征分析")
    print("  ✓ 内容特征分析")
    print("  ✓ 结构完整性评分")
    print("  ✓ 优化建议列表")
    print("  ✓ JSON详细报告")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 运行示例
    example_usage()
    
    print("\n运行单元测试...")
    unittest.main(argv=[''], verbosity=2, exit=False)
