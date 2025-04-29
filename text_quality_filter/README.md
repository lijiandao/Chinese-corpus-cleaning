# 文本质量过滤系统

一个基于多种过滤方法的中文文本质量评估和过滤系统，用于筛选高质量文本，提高语料库质量。

## 功能特点

- **基础规则过滤**：基于文本特征的规则过滤（`rule_filter.py`）
  - 文本长度检查
  - 中文字符比例检查
  - 符号和数字比例检查
  - 英文比例检查
  - 行长度检查
  - 重复行检测
  - 段落长度控制

- **特征词检测**：（`feature_words.py`，`sensitive_filter.py`）
  - 基于DFA算法的高效特征词检测
  - 支持敏感词和广告词检测
  - 特征词密度评估

- **困惑度计算**：（`lmppl_perplexity.py`）
  - 使用预训练语言模型计算困惑度
  - 支持自定义困惑度阈值
  - 文本流畅度评估

- **文本聚类**：（`clustering.py`）
  - 基于文本嵌入的相似度计算
  - 重复内容检测
  - 支持增量聚类

## 安装依赖

```bash
# 基础依赖
pip install numpy tqdm

# 困惑度计算依赖（必需）
pip install torch transformers

# 文本嵌入依赖（必需）
pip install sentence-transformers
```

## 使用方法

系统提供了命令行工具，支持以下功能：

### 1. 文本质量过滤

```bash
python -m text_quality_filter.main filter --input_dir <输入目录> --output_dir <输出目录> --file_pattern "*.txt"
```

### 2. 敏感内容过滤

```bash
python -m text_quality_filter.main sensitive --input_dir <输入目录> --output_dir <输出目录> --file_pattern "*.txt"
```

### 3. 训练聚类模型

```bash
python -m text_quality_filter.main train --train_dir <训练数据目录> [--skip_clustering]
```

## 配置说明

配置文件位于 `config/config.py`，包含以下主要配置：

### 规则过滤配置
```python
RULE_FILTER_CONFIG = {
    "min_text_length": 100,        # 最小文本长度
    "min_chinese_ratio": 0.6,      # 最小中文字符比例
    "max_symbol_ratio": 0.2,       # 最大符号比例
    "max_number_ratio": 0.2,       # 最大数字比例
    "max_english_ratio": 0.3,      # 最大英文比例
    "min_avg_line_length": 5,      # 最小平均行长度
    "max_max_line_length": 10000,  # 最大行长度
    "max_duplicate_line_ratio": 0.3,# 最大重复行比例
    "max_avg_paragraph_length": 2000# 最大段落长度
}
```

### 特征词配置
```python
FEATURE_WORDS_CONFIG = {
    "feature_words_path": "data/all_sensitive_words.txt",  # 特征词文件路径
    "max_feature_words_per_line": 0.2,                     # 每行最大特征词数量
    "use_dfa_filter": True                                 # 使用DFA过滤器
}
```

### 困惑度配置
```python
PERPLEXITY_CONFIG = {
    "use_external_library": True,                          # 使用外部预训练模型
    "model_name": "uer/gpt2-chinese-cluecorpussmall",     # 预训练模型名称
    "ppl_threshold": 200.0                                 # 困惑度阈值
}
```

### 总体配置
```python
GENERAL_CONFIG = {
    "enable_rule_filter": True,    # 启用规则过滤
    "enable_feature_words": True,  # 启用特征词检测
    "enable_perplexity": False,    # 启用困惑度过滤
    "enable_clustering": False,    # 启用文本聚类
    "quality_threshold": 0.8,      # 质量阈值
    "component_weights": {         # 各组件权重
        "rule_score": 0.3,        # 规则过滤权重
        "feature_score": 0.4,     # 特征词权重
        "perplexity_score": 0.3,  # 困惑度权重
        "clustering_score": 0.0    # 聚类权重
    }
}
```

## 输出说明

系统处理后会生成以下输出：

1. 高质量文本文件：直接保存在输出目录
2. 评估结果：保存在 `output_dir/results/` 目录，每个文件对应一个JSON格式的评估结果
3. 统计信息：保存在 `output_dir/stats.json`，包含处理统计数据

## 注意事项

1. 特征词文件格式要求：
   - 每行一个词
   - 使用UTF-8编码
   - 支持从多个来源合并（敏感词、广告词等）

2. 性能优化：
   - 使用DFA算法进行特征词匹配，保证高效处理
   - 支持批量处理文件
   - 文本聚类支持增量更新

3. 错误处理：
   - 系统会自动跳过处理失败的文件
   - 详细错误信息会记录在控制台输出中
   - 统计信息中包含错误文件数量

4. 配置调优：
   - 可以根据实际需求调整各项阈值
   - 权重配置允许灵活调整各组件的重要性
   - 建议先用小批量数据测试配置效果 