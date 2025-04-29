# 文本质量过滤系统

一个基于多种过滤方法的中文文本质量评估和过滤系统，可用于筛选高质量文本，提高语料库质量。

## 功能特点

- **基础规则过滤**：根据文本长度、平均行长度、中文比例、符号比例、内部重复率等指标进行过滤
- **垂直线符号检测**：特别针对含有大量"|"等分隔符的SEO垃圾文本进行识别
- **特征词检测**：检测文本中的敏感词和广告词，使用高效的DFA算法和Aho-Corasick算法
- **困惑度计算**：使用预训练中文语言模型计算文本的困惑度，评估文本流畅度
- **文本聚类**：使用文本嵌入和相似度计算来识别重复或相似的内容（可选功能）

## 安装依赖

### 基础依赖

```bash
pip install numpy tqdm jieba
```

### 困惑度计算依赖

要使用预训练语言模型计算困惑度，需要安装以下依赖：

```bash
pip install torch transformers
```

### 文本聚类依赖（可选）

如果需要启用文本聚类功能，请安装：

```bash
pip install scikit-learn
```

## 配置说明

配置文件位于`config/config.py`，可以调整以下关键参数：

### 基础规则过滤配置

```python
RULE_FILTER_CONFIG = {
    "min_text_length": 500,             # 文本最小长度
    "min_avg_line_length": 20,          # 行最小平均长度
    "min_chinese_ratio": 0.7,           # 中文字符最小比例
    "max_symbol_ratio": 0.2,            # 最大符号比例
    "max_internal_dup_ratio": 0.3,      # 最大内部重复率
    "max_vertical_bar_ratio": 0.005,    # 最大垂直线"|"符号比例
}
```

### 困惑度计算配置

```python
PERPLEXITY_CONFIG = {
    "ppl_threshold": 500.0,             # 困惑度阈值，大于此值视为低质量
    "model_name": "uer/gpt2-chinese-cluecorpussmall",  # 预训练模型名称
    "max_ppl": 10000.0,                 # 最大困惑度上限
    "max_length": 512,                  # 最大处理长度
    "use_external_library": True,       # 使用外部库计算困惑度
}
```

### 功能启用配置

```python
GENERAL_CONFIG = {
    "quality_threshold": 0.80,          # 质量分数阈值，小于此值视为低质量
    "enable_rule_filter": True,         # 是否启用基础规则过滤
    "enable_feature_words": True,       # 是否启用特征词检测
    "enable_perplexity": True,          # 是否启用困惑度计算
    "enable_clustering": False,         # 是否启用文本聚类
    "output_dir": "text_quality_filter/output/",  # 输出路径
}
```

## 使用示例

### 基本用法

```python
from text_quality_filter.main import TextQualityFilter

# 创建过滤器
filter = TextQualityFilter()

# 过滤单个文本
is_high_quality, results = filter.filter_text("要过滤的文本内容")
print(f"是否为高质量文本: {is_high_quality}")
print(f"质量分数: {results['quality_score']}")

# 批量处理文件
stats = filter.batch_process("输入目录", "输出目录", "*.txt")
print(f"总文件数: {stats['total']}")
print(f"高质量文件数: {stats['high_quality']}")
print(f"低质量文件数: {stats['low_quality']}")
```

### 运行测试

```bash
python text_quality_filter/test_filter.py
```

## 特征词库

系统使用以下特征词库：

- 敏感词库：`data/all_sensitive_words.txt`
- 广告词库：`data/ad_words.txt`

可以根据需要添加或修改这些词库。

## 注意事项

1. 首次使用预训练模型计算困惑度时会自动下载模型，请确保网络连接正常
2. 如果遇到内存不足问题，可以减小`max_length`参数或禁用部分功能
3. 建议先使用少量文本测试系统效果，再进行大规模数据处理 