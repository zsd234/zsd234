"""模板分类智能体 - 综合其他智能体的结果进行模板识别"""
import logging
from typing import Dict, Any, Optional, Tuple
from models.features import PPTAnalysisResult, DesignFeatures, ContentFeatures
from models.templates import TemplateTypes, TEMPLATE_DEFINITIONS
import numpy as np


class TemplateClassifierAgent:
    """
    模板分类智能体
    
    职责:
    - 综合设计和内容特征
    - 计算模板匹配得分
    - 识别最可能的模板类型
    - 提供置信度评分
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化模板分类智能体"""
        self.logger = logger or logging.getLogger(__name__)
    
    def classify(
        self,
        design_features: DesignFeatures,
        content_features: ContentFeatures,
        analysis_result: PPTAnalysisResult
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        分类PPT模板类型
        
        Args:
            design_features: 设计特征
            content_features: 内容特征
            analysis_result: 分析结果对象
            
        Returns:
            (模板类型, 置信度, 所有模板的评分字典)
        """
        try:
            # 计算每个模板类型的匹配度
            scores = {}
            
            for template_type, template_def in TEMPLATE_DEFINITIONS.items():
                score = self._calculate_template_score(
                    template_type,
                    design_features,
                    content_features,
                    template_def
                )
                scores[template_type.value] = score
            
            # 找到最高分的模板
            best_template = max(scores, key=scores.get)
            best_score = scores[best_template]
            
            # 获取模板类型
            template_type = TemplateTypes(best_template)
            
            # 检查是否满足置信度阈值
            template_def = TEMPLATE_DEFINITIONS[template_type]
            confidence = best_score
            
            if confidence < template_def.confidence_threshold:
                template_type = TemplateTypes.UNKNOWN
                confidence = best_score
            
            self.logger.info(f"模板分类完成: {template_type.value}, 置信度: {confidence:.2%}")
            
            return template_type.value, confidence, scores
            
        except Exception as e:
            self.logger.error(f"模板分类失败: {str(e)}")
            raise
    
    def _calculate_template_score(
        self,
        template_type: TemplateTypes,
        design_features: DesignFeatures,
        content_features: ContentFeatures,
        template_def
    ) -> float:
        """
        计算特定模板类型的匹配得分
        
        Args:
            template_type: 模板类型
            design_features: 设计特征
            content_features: 内容特征
            template_def: 模板定义
            
        Returns:
            匹配得分 (0-1)
        """
        # 初始化得分
        design_score = 0.0
        content_score = 0.0
        structure_score = 0.0
        
        # 计算设计匹配度
        design_score = self._calculate_design_score(design_features, template_def)
        
        # 计算内容匹配度
        content_score = self._calculate_content_score(content_features, template_def)
        
        # 计算结构匹配度
        structure_score = self._calculate_structure_score(content_features, template_def)
        
        # 加权平均
        total_score = (
            design_score * 0.4 +
            content_score * 0.3 +
            structure_score * 0.3
        )
        
        return total_score
    
    def _calculate_design_score(self, design_features: DesignFeatures, template_def) -> float:
        """计算设计匹配度"""
        score = 0.0
        
        # 检查字体匹配
        font_match = 0
        if design_features.primary_font and design_features.primary_font in template_def.typical_fonts:
            font_match += 0.5
        if design_features.secondary_font and design_features.secondary_font in template_def.typical_fonts:
            font_match += 0.5
        score += min(font_match, 1.0) * 0.3
        
        # 检查风格匹配
        if template_def.template_type == TemplateTypes.BUSINESS_PRESENTATION:
            if design_features.style in ["corporate", "minimalist"]:
                score += 0.3
        elif template_def.template_type == TemplateTypes.EDUCATIONAL_TRAINING:
            if design_features.style in ["creative", "corporate"]:
                score += 0.3
        elif template_def.template_type == TemplateTypes.ACADEMIC_PRESENTATION:
            if design_features.style in ["minimalist", "corporate"]:
                score += 0.3
        elif template_def.template_type == TemplateTypes.SALES_PITCH:
            if design_features.style in ["creative", "complex"]:
                score += 0.3
        
        # 检查颜色方案匹配
        if design_features.primary_colors:
            color_hex = design_features.primary_colors[0].hex_code
            palette_match = self._check_color_palette_match(
                color_hex,
                template_def.color_palettes
            )
            score += palette_match * 0.4
        
        return min(score, 1.0)
    
    def _calculate_content_score(self, content_features: ContentFeatures, template_def) -> float:
        """计算内容匹配度"""
        score = 0.0
        
        # 检查目标受众匹配
        audience_mapping = {
            TemplateTypes.BUSINESS_PRESENTATION: "business",
            TemplateTypes.EDUCATIONAL_TRAINING: "educational",
            TemplateTypes.ACADEMIC_PRESENTATION: "academic",
            TemplateTypes.SALES_PITCH: "business",
            TemplateTypes.CREATIVE_SHOWCASE: "creative",
        }
        
        if template_def.template_type in audience_mapping:
            if content_features.target_audience == audience_mapping[template_def.template_type]:
                score += 0.4
            elif content_features.target_audience == "general":
                score += 0.2
        
        # 检查专业度匹配
        if template_def.template_type == TemplateTypes.ACADEMIC_PRESENTATION:
            if content_features.professionalism_score > 0.7:
                score += 0.3
        elif template_def.template_type == TemplateTypes.BUSINESS_PRESENTATION:
            if content_features.professionalism_score > 0.6:
                score += 0.3
        
        # 检查复杂度匹配
        if template_def.template_type == TemplateTypes.CREATIVE_SHOWCASE:
            if content_features.content_complexity > 0.6:
                score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_structure_score(self, content_features: ContentFeatures, template_def) -> float:
        """计算结构匹配度"""
        score = 0.0
        structure = content_features.structure_analysis
        
        # 检查典型结构元素
        for element in template_def.typical_structure:
            if element == "标题页" and structure.has_title_slide:
                score += 0.15
            elif element == "议程" and structure.has_agenda:
                score += 0.15
            elif element == "结论页" and structure.has_conclusion:
                score += 0.15
            elif element == "参考文献" and structure.has_references:
                score += 0.15
        
        # 检查一致性
        if structure.consistency_score > 0.7:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_color_palette_match(self, color_hex: str, palettes: list) -> float:
        """检查颜色是否与调色板匹配"""
        if not color_hex or not palettes:
            return 0.0
        
        best_match = 0.0
        
        for palette in palettes:
            for palette_color in palette:
                similarity = self._color_similarity(color_hex, palette_color)
                best_match = max(best_match, similarity)
        
        return best_match
    
    @staticmethod
    def _color_similarity(color1: str, color2: str) -> float:
        """计算两个颜色的相似度"""
        # 将十六进制转为RGB
        rgb1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # 计算欧几里得距离
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
        
        # 转换为相似度分数(0-1)
        max_distance = np.sqrt(255 ** 2 * 3)
        similarity = 1 - (distance / max_distance)
        
        return max(0, min(similarity, 1.0))
