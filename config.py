"""
配置文件 - PPT模板分析系统
"""

# 日志配置
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "ppt_analyzer.log"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"]
    }
}

# 模板识别配置
TEMPLATE_CONFIG = {
    "confidence_threshold": 0.6,
    "min_slides": 1,
    "max_slides": 1000,
    "enable_advanced_analysis": True,
}

# 色彩分析配置
COLOR_CONFIG = {
    "primary_colors_count": 5,
    "color_sampling_rate": 0.8,
    "use_clustering": True,
    "harmony_threshold": 0.5,
}

# 文本分析配置
TEXT_CONFIG = {
    "min_text_length": 10,
    "keyword_count": 10,
    "use_nlp": False,
    "min_bullet_count": 0,
    "max_bullet_count": 15,
}

# 内容分析配置
CONTENT_CONFIG = {
    "analyze_images": True,
    "analyze_charts": True,
    "analyze_tables": True,
    "analyze_videos": True,
    "image_min_size": 10000,  # bytes
}

# 权重配置
WEIGHT_CONFIG = {
    "design_weight": 0.4,
    "content_weight": 0.3,
    "structure_weight": 0.3,
}

# 输出配置
OUTPUT_CONFIG = {
    "export_json": True,
    "export_html": False,
    "export_pdf": False,
    "output_dir": "./analysis_results/",
    "include_images": False,
}

# 性能配置
PERFORMANCE_CONFIG = {
    "enable_caching": True,
    "cache_dir": "./cache/",
    "max_cache_size": 100,  # MB
    "enable_threading": False,
    "thread_count": 4,
}
