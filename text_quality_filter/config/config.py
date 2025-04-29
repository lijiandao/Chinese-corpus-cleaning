"""
配置文件
"""
import os

# 获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 规则过滤配置
RULE_FILTER_CONFIG = {
    "min_text_length": 100,  # 最小文本长度
    "min_chinese_ratio": 0.6,  # 最小中文字符比例
    "max_symbol_ratio": 0.2,  # 最大符号比例
    "max_number_ratio": 0.2,  # 最大数字比例
    "max_english_ratio": 0.3,  # 最大英文比例
    "min_avg_line_length": 5,  # 最小平均行长度（字符数）
    "max_max_line_length": 10000,  # 最大行长度（字符数）
    "max_duplicate_line_ratio": 0.3,  # 最大重复行比例
    "max_avg_paragraph_length": 2000,  # 最大段落长度（字符数）
}

# 特征词配置
FEATURE_WORDS_CONFIG = {
    "feature_words_path": os.path.join(BASE_DIR, "data", "all_sensitive_words.txt"),  # 使用绝对路径
    "max_feature_words_per_line": 0.2,  # 每行最大特征词数量
    "use_dfa_filter": True,  # 是否使用DFA过滤器
}

# 困惑度配置
PERPLEXITY_CONFIG = {
    "model_path": os.path.join(BASE_DIR, "models", "chinese_srilm.arpa"),  # 使用绝对路径
    "max_perplexity": 5000,  # 最大困惑度
    "order": 5,  # 提高n-gram的n值，从3提高到5
    "use_external_library": True,  # 使用预训练语言模型计算困惑度
    "model_name": "uer/gpt2-chinese-cluecorpussmall",  # 预训练模型名称
    "ppl_threshold": 200.0,  # 降低困惑度阈值，使评判更严格
}

# 文本聚类配置
CLUSTERING_CONFIG = {
    "embedding_model": "distiluse-base-multilingual-cased-v1",  # 嵌入模型
    "min_quality_cluster_ratio": 0.6,  # 最小高质量簇比例
    "max_outlier_distance": 0.8,  # 最大离群点距离
}

# 总体配置
GENERAL_CONFIG = {
    "enable_rule_filter": True,  # 启用规则过滤
    "enable_feature_words": True,  # 启用特征词检测
    "enable_perplexity": False,  # 启用困惑度过滤
    "enable_clustering": False,  # 启用文本聚类
    "output_dir": os.path.join(BASE_DIR, "output"),  # 使用绝对路径
    "quality_threshold": 0.8,  # 质量阈值
    # 各组件的权重
    "component_weights": {
        "rule_score": 0.3,      # 规则过滤分数权重
        "feature_score": 0.5,   # 特征词分数权重
        "perplexity_score": 0.1, # 困惑度分数权重
        "clustering_score": 0.1  # 聚类分数权重
    }
}

# 组合所有配置
CONFIG = {
    "rule": RULE_FILTER_CONFIG,
    "feature_words": FEATURE_WORDS_CONFIG,
    "perplexity": PERPLEXITY_CONFIG,
    "clustering": CLUSTERING_CONFIG,
    "general": GENERAL_CONFIG,
} 