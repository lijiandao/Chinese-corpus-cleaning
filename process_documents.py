#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文文档处理工具
处理文档、过滤低质量内容、过滤敏感词
"""

import os
import sys
import argparse
import glob
import json
import traceback
from tqdm import tqdm
from typing import List, Dict, Optional

# 导入文本质量过滤器
from text_quality_filter.main import TextQualityFilter

# 导入向量化相关功能
from embed import create_vector_index


def get_files(input_dir: str, file_pattern: str = "*.txt") -> List[str]:
    """
    获取符合条件的文件列表
    """
    files = glob.glob(os.path.join(input_dir, file_pattern))
    print(f"找到 {len(files)} 个文件")
    return files


def process_documents(args):
    """处理文档：过滤低质量内容，提取向量嵌入"""
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 步骤1：使用文本质量过滤器（如果启用）
    if args.filter_quality:
        print("第1步：文本质量过滤")
        filter = TextQualityFilter()
        stats = filter.batch_process(args.input_dir, args.output_dir, args.file_pattern)
        print(f"质量过滤结果：共 {stats['total']} 个文件，高质量 {stats['high_quality']} 个，"
              f"低质量 {stats['low_quality']} 个，错误 {stats['error']} 个")
    
    # 步骤2：过滤敏感内容（如果启用）
    if args.filter_sensitive:
        print("第2步：敏感内容过滤")
        sensitive_dir = os.path.join(args.output_dir, "sensitive_filtered")
        os.makedirs(sensitive_dir, exist_ok=True)
        
        # 根据步骤1是否执行，决定输入目录
        input_dir = args.output_dir if args.filter_quality else args.input_dir
        
        filter = TextQualityFilter()
        stats = filter.batch_filter_sensitive(input_dir, sensitive_dir, args.file_pattern)
        print(f"敏感内容过滤结果：共 {stats['total']} 个文件，成功处理 {stats['processed']} 个，"
              f"错误 {stats['error']} 个")
        
        # 更新输出目录为敏感词过滤后的目录
        filtered_dir = sensitive_dir
    else:
        # 如果没有过滤敏感内容，使用质量过滤的输出或原始输入
        filtered_dir = args.output_dir if args.filter_quality else args.input_dir
    
    # 步骤3：向量化嵌入（如果启用）
    if args.vectorize:
        print("第3步：向量嵌入")
        vector_index = create_vector_index(
            filtered_dir, 
            index_name=args.index_name,
            model_name=args.model_name,
            batch_size=args.batch_size,
            file_pattern=args.file_pattern
        )
        print(f"向量化嵌入完成，索引保存在：{vector_index.index_dir}")


def train_models(args):
    """训练模型"""
    from text_quality_filter.main import train_models as train
    train(args)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="中文文档处理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 处理文档命令
    process_parser = subparsers.add_parser("process", help="处理文档")
    process_parser.add_argument("--input_dir", type=str, default="chinese_docs", help="输入目录")
    process_parser.add_argument("--output_dir", type=str, default="processed_docs", help="输出目录")
    process_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    process_parser.add_argument("--filter_quality", action="store_true", help="启用质量过滤")
    process_parser.add_argument("--filter_sensitive", action="store_true", help="启用敏感内容过滤")
    process_parser.add_argument("--vectorize", action="store_true", help="启用向量嵌入")
    process_parser.add_argument("--index_name", type=str, default="cn_docs", help="向量索引名称")
    process_parser.add_argument("--model_name", type=str, default="text2vec-large-chinese", help="向量模型名称")
    process_parser.add_argument("--batch_size", type=int, default=32, help="批处理大小")
    
    # 过滤敏感内容命令
    sensitive_parser = subparsers.add_parser("sensitive", help="过滤敏感内容")
    sensitive_parser.add_argument("--input_dir", type=str, default="chinese_docs", help="输入目录")
    sensitive_parser.add_argument("--output_dir", type=str, default="filtered_sensitive", help="输出目录")
    sensitive_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    
    # 质量过滤命令
    filter_parser = subparsers.add_parser("filter", help="过滤低质量内容")
    filter_parser.add_argument("--input_dir", type=str, default="chinese_docs", help="输入目录")
    filter_parser.add_argument("--output_dir", type=str, default="filtered_quality", help="输出目录")
    filter_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    
    # 训练模型命令
    train_parser = subparsers.add_parser("train", help="训练模型")
    train_parser.add_argument("--train_dir", type=str, required=True, help="训练数据目录")
    train_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    train_parser.add_argument("--skip_ngram", action="store_true", help="跳过N-gram模型训练")
    train_parser.add_argument("--skip_clustering", action="store_true", help="跳过聚类模型构建")
    
    # 向量化命令
    vectorize_parser = subparsers.add_parser("vectorize", help="向量嵌入")
    vectorize_parser.add_argument("--input_dir", type=str, default="processed_docs", help="输入目录")
    vectorize_parser.add_argument("--index_name", type=str, default="cn_docs", help="向量索引名称")
    vectorize_parser.add_argument("--model_name", type=str, default="text2vec-large-chinese", help="向量模型名称")
    vectorize_parser.add_argument("--batch_size", type=int, default=32, help="批处理大小")
    vectorize_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    
    args = parser.parse_args()
    
    if args.command == "process":
        # 处理文档
        process_documents(args)
    
    elif args.command == "sensitive":
        # 过滤敏感内容
        filter = TextQualityFilter()
        filter.batch_filter_sensitive(args.input_dir, args.output_dir, args.file_pattern)
    
    elif args.command == "filter":
        # 过滤低质量内容
        filter = TextQualityFilter()
        filter.batch_process(args.input_dir, args.output_dir, args.file_pattern)
    
    elif args.command == "train":
        # 训练模型
        train_models(args)
    
    elif args.command == "vectorize":
        # 向量嵌入
        create_vector_index(
            args.input_dir, 
            index_name=args.index_name,
            model_name=args.model_name,
            batch_size=args.batch_size,
            file_pattern=args.file_pattern
        )
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 