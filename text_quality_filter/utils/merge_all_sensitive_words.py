#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
敏感词库批量合并工具
自动合并指定目录下的所有txt文件，并去除重复条目
"""

import os
import glob
import argparse
from typing import Set

def read_words_from_file(filepath: str) -> Set[str]:
    """
    从文件中读取敏感词，返回一个集合
    Args:
        filepath: 文件路径
    Returns:
        敏感词集合
    """
    words = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                word = line.strip()
                if word:  # 忽略空行
                    words.add(word)
        print(f"从 {filepath} 读取了 {len(words)} 个敏感词")
    except Exception as e:
        print(f"读取文件 {filepath} 出错: {e}")
    return words

def merge_all_txt_files(input_dir: str, output_file: str, sort: bool = True) -> None:
    """
    合并指定目录下的所有txt文件，并去除重复条目
    Args:
        input_dir: 输入目录路径
        output_file: 输出文件路径
        sort: 是否按字母顺序排序
    """
    all_words = set()
    
    # 获取目录下所有的txt文件，排除输出文件
    output_basename = os.path.basename(output_file)
    txt_files = [f for f in glob.glob(os.path.join(input_dir, "*.txt")) 
                if os.path.basename(f) != output_basename]
    
    print(f"在 {input_dir} 目录下找到 {len(txt_files)} 个txt文件（排除输出文件）")
    
    # 从每个文件读取敏感词并合并到集合中
    for file_path in txt_files:
        words = read_words_from_file(file_path)
        all_words.update(words)
    
    # 统计合并结果
    print(f"合并后共有 {len(all_words)} 个不重复的敏感词")
    
    # 排序（如果需要）
    if sort:
        sorted_words = sorted(all_words)
    else:
        sorted_words = list(all_words)
    
    # 写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in sorted_words:
                f.write(word + '\n')
        print(f"成功将 {len(sorted_words)} 个去重后的敏感词写入 {output_file}")
    except Exception as e:
        print(f"写入文件 {output_file} 出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="敏感词库批量合并工具")
    parser.add_argument('--input-dir', '-i', default='./text_quality_filter/data', 
                        help="包含txt文件的输入目录路径，默认为./text_quality_filter/data")
    parser.add_argument('--output', '-o', default='./text_quality_filter/data/all_sensitive_words.txt',
                        help="输出文件路径，默认为./text_quality_filter/data/all_sensitive_words.txt")
    parser.add_argument('--no-sort', action='store_true', help="不按字母顺序排序")
    
    args = parser.parse_args()
    
    merge_all_txt_files(args.input_dir, args.output, not args.no_sort)

if __name__ == "__main__":
    main() 