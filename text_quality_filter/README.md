# 文本质量过滤模块

本模块是中文语料库清理项目的一个子模块，主要用于对中文文本进行质量评估和过滤。

## 主要功能

1. **基础规则过滤**
   - 文本长度检查
   - 中文字符比例检查
   - 符号、数字、英文比例检查
   - 行长度和段落长度检查
   - 重复内容检测

2. **特征词检测**
   - 基于DFA算法的高效特征词匹配
   - 支持敏感词和广告词检测
   - 特征词密度评估

3. **困惑度评估**
   - 基于预训练语言模型的困惑度计算
   - 文本流畅度评估

4. **文本聚类**
   - 基于文本嵌入的相似度计算
   - 重复内容检测
   - 支持增量聚类

## 目录结构

```
text_quality_filter/
├── config/             # 配置文件
├── data/              # 词表和数据文件
├── models/            # 预训练模型
├── output/            # 输出目录
├── utils/             # 工具函数
│   ├── rule_filter.py     # 规则过滤
│   ├── feature_words.py   # 特征词检测
│   ├── sensitive_filter.py # 敏感词过滤
│   ├── lmppl_perplexity.py # 困惑度计算
│   ├── clustering.py       # 文本聚类
│   └── embed.py           # 文本嵌入
├── main.py            # 主程序
├── test_filter.py     # 测试脚本
└── README.md         # 说明文档
```

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行质量过滤：
```bash
python -m text_quality_filter.main filter --input_dir <输入目录> --output_dir <输出目录>
```

3. 过滤敏感内容：
```bash
python -m text_quality_filter.main sensitive --input_dir <输入目录> --output_dir <输出目录>
```

4. 训练聚类模型：
```bash
python -m text_quality_filter.main train --train_dir <训练数据目录>
```

## 配置说明

配置文件位于`config/config.py`，包含以下主要配置：

1. 规则过滤配置（RULE_FILTER_CONFIG）
2. 特征词配置（FEATURE_WORDS_CONFIG）
3. 困惑度配置（PERPLEXITY_CONFIG）
4. 聚类配置（CLUSTERING_CONFIG）
5. 总体配置（GENERAL_CONFIG）

详细配置说明请参考配置文件中的注释。

## 注意事项

1. 首次使用需要下载预训练模型
2. 特征词文件需要UTF-8编码
3. 建议先使用小规模数据测试配置效果 