# 大规模Web中文文档处理系统

这个项目用于从大规模网页数据中筛选、处理和提取高质量中文内容。

## 功能特点

- 从HTML文档中筛选中文内容
- 自动评估文档质量
- 使用文本向量化和聚类技术区分高质量和低质量内容
- 去除低质量内容（广告、旁栏、垃圾信息等）
- 保留连续的高质量文本
- 支持断点续传，便于处理大规模数据集
- 基于文本连贯性、复杂度和凝聚性的质量评估

## 系统要求

- Python 3.6+
- 依赖库: torch, transformers, fasttext, scikit-learn, numpy, BeautifulSoup4, tqdm

## 安装依赖

```bash
pip install torch transformers fasttext scikit-learn numpy beautifulsoup4 tqdm
```

## 文件结构

- `embed.py`: 文本向量化工具
- `tool.py`: HTML处理和中文检测工具
- `process_documents.py`: 主处理脚本

## 使用方法

1. 将HTML文件放在`htmls`文件夹中
2. 运行处理脚本:

```bash
# 运行全部流程
python process_documents.py --stage all --batch_size 100

# 仅运行HTML处理阶段
python process_documents.py --stage html --batch_size 100

# 仅运行向量化和聚类阶段
python process_documents.py --stage vector --batch_size 20
```

3. 处理结果将保存在以下文件夹:
   - `chinese_docs`: 筛选后的中文文档
   - `processed_docs`: 处理后的高质量文档
   - `vector_data`: 文档向量数据
   - `checkpoints`: 处理检查点，用于断点续传

## 处理流程

1. **中文文档筛选**: 使用fasttext语言识别模型判断文档是否为中文
2. **文档分段**: 将文档分割成固定大小的段落
3. **质量评估**: 基于多个指标评估每个段落的质量
4. **向量化和聚类**: 使用预训练中文模型将段落转化为向量，并使用K-means聚类
5. **高质量内容提取**: 识别并保存高质量内容段落

## 文档质量评估指标

### 基本指标
- 中文字符比例
- 标点符号比例
- 文本重复度
- 段落长度

### 高级指标（参考论文）
- **连贯性(Coherence)**: 衡量文本中句子之间的逻辑连接，通过过渡词的使用情况来评估
- **复杂度(Complexity)**: 衡量文本的词汇多样性，使用类似TTR(Type-Token Ratio)的指标来评估
- **凝聚性(Cohesion)**: 衡量文本的主题一致性，通过分析主题词的分布来评估

## 断点续传功能

系统支持断点续传，可以在处理中断后继续上次的进度，避免重复处理已处理过的文件。

每个处理阶段会生成独立的检查点文件，保存在checkpoints目录下：
- html_processing_checkpoint.json: HTML处理阶段的检查点
- vectorize_clustering_checkpoint.json: 向量化和聚类阶段的检查点

## 自定义配置

可以在`process_documents.py`文件中修改以下参数:

- `HTML_FOLDER`: HTML文件所在文件夹
- `OUTPUT_FOLDER`: 中文文档输出文件夹
- `PROCESSED_FOLDER`: 处理后文档输出文件夹
- `VECTOR_FOLDER`: 向量数据保存文件夹
- `CHECKPOINT_FOLDER`: 检查点保存文件夹

# 中文文档处理与质量过滤工具

本项目提供了一系列用于中文文档处理和质量过滤的工具，帮助清洗和筛选高质量的中文语料。

## 主要功能

1. **HTML文档处理**：从HTML文件中提取中文文本内容
2. **文本质量过滤**：基于多种方法过滤文本质量
   - 基础规则过滤：长度、中文比例、符号比例、内部重复率等
   - 特征词检测：广告词、敏感词等
   - 困惑度计算：基于N-gram语言模型评估文本流畅性
   - 文本聚类：检测重复或相似内容

## 目录结构

```
.
├── text_quality_filter/       # 文本质量过滤工具
│   ├── config/                # 配置文件
│   ├── data/                  # 数据文件
│   ├── models/                # 模型文件
│   ├── output/                # 输出目录
│   └── utils/                 # 工具模块
├── chinese_docs/              # 中文文档目录
├── htmls/                     # HTML文件目录
├── processed_docs/            # 处理后的文档目录
├── vector_data/               # 向量数据目录
├── checkpoints/               # 检查点目录
├── process_documents.py       # 文档处理脚本
└── tool.py                    # 通用工具函数
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 文本质量过滤

对指定目录中的文本文件进行质量过滤：

```bash
python -m text_quality_filter.main filter --input_dir chinese_docs --output_dir filtered_docs
```

参数说明：
- `--input_dir`：输入目录，默认为 "chinese_docs"
- `--output_dir`：输出目录，默认使用配置文件中的输出目录
- `--file_pattern`：文件匹配模式，默认为 "*.txt"

### 2. 训练模型

使用高质量文本训练模型：

```bash
python -m text_quality_filter.main train --train_dir high_quality_docs
```

参数说明：
- `--train_dir`：训练数据目录
- `--file_pattern`：文件匹配模式，默认为 "*.txt"
- `--skip_ngram`：跳过N-gram模型训练
- `--skip_clustering`：跳过聚类模型构建

### 3. HTML文档处理

从HTML文件中提取中文文本：

```bash
python process_documents.py --stage html
```

### 4. 向量化与聚类

对中文文档进行向量化和聚类：

```bash
python process_documents.py --stage vector
```

### 5. 完整处理流程

执行完整处理流程（HTML处理 + 向量化聚类）：

```bash
python process_documents.py --stage all
```

## 质量过滤标准

文本质量过滤基于以下标准：

1. **基础规则**
   - 文本最小长度：200字符
   - 行最小平均长度：10字符
   - 中文字符最小比例：40%
   - 最大符号比例：30%
   - 最大内部重复率：50%

2. **特征词检测**
   - 广告词最大密度：2%
   - 每行敏感词最大出现次数：0.5个

3. **困惑度计算**
   - 困惑度阈值：500（大于此值视为低质量）

4. **文本聚类**
   - 相似度阈值：85%（大于此值视为相似）
   - 最小簇大小：3（小于此大小的簇被保留）

## 配置调整

可以通过修改 `text_quality_filter/config/config.py` 文件调整过滤标准和配置参数。
