"""
文本质量过滤主程序
用于对中文文档库进行质量过滤，去除低质量内容
"""
import os
import glob
import json
import argparse
import traceback
from tqdm import tqdm
from typing import Dict, List, Tuple

# 导入质量过滤模块
from text_quality_filter.utils.rule_filter import RuleFilter
from text_quality_filter.utils.feature_words import FeatureWordsDetector
from text_quality_filter.utils.clustering import TextClustering, build_corpus_clustering
from text_quality_filter.utils.sensitive_filter import DFAFilter
from text_quality_filter.config.config import (
    RULE_FILTER_CONFIG, 
    FEATURE_WORDS_CONFIG, 
    PERPLEXITY_CONFIG,
    CLUSTERING_CONFIG,
    GENERAL_CONFIG,
    BASE_DIR
)


class TextQualityFilter:
    """文本质量过滤类，集成多种过滤方法"""
    
    def __init__(self, config: Dict = None):
        """
        初始化文本质量过滤器
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        # 加载配置
        self.config = GENERAL_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # 初始化各组件
        self.rule_filter = RuleFilter(RULE_FILTER_CONFIG)
        print(f"初始化特征词检测器，使用特征词文件: {FEATURE_WORDS_CONFIG['feature_words_path']}")
        if os.path.exists(FEATURE_WORDS_CONFIG['feature_words_path']):
            print(f"特征词文件存在，开始加载...")
            self.feature_detector = FeatureWordsDetector(FEATURE_WORDS_CONFIG)
            feature_words_count = len(self.feature_detector.feature_words)
            print(f"成功加载特征词 {feature_words_count} 个")
        else:
            print(f"特征词文件不存在: {FEATURE_WORDS_CONFIG['feature_words_path']}")
            # 使用备用方案
            print("使用备用方案，直接初始化DFA过滤器")
            self.feature_detector = FeatureWordsDetector({
                "feature_words_path": "",  # 空路径，不从文件加载
                "use_dfa_filter": True
            })
            # 如果特征词文件不存在但有其他敏感词文件，尝试加载
            sensitive_words_path = os.path.join(BASE_DIR, "data", "sensitive_words.txt")
            ad_words_path = os.path.join(BASE_DIR, "data", "ad_words.txt")
            
            # 初始化DFA过滤器
            self.feature_detector.feature_filter = DFAFilter()
            
            # 加载敏感词和广告词
            if os.path.exists(sensitive_words_path):
                print(f"加载敏感词文件: {sensitive_words_path}")
                self.feature_detector.feature_filter.parse_file(sensitive_words_path)
            
            if os.path.exists(ad_words_path):
                print(f"加载广告词文件: {ad_words_path}")
                self.feature_detector.feature_filter.parse_file(ad_words_path)
        
        # 初始化困惑度计算器
        if self.config["enable_perplexity"]:
            if PERPLEXITY_CONFIG.get("use_external_library", False):
                # 使用外部预训练模型计算困惑度
                try:
                    # 尝试导入新的困惑度计算模块
                    from text_quality_filter.utils.lmppl_perplexity import LMPPLPerplexityCalculator
                    self.perplexity_calculator = LMPPLPerplexityCalculator(PERPLEXITY_CONFIG)
                    print("使用预训练语言模型计算困惑度")
                except ImportError as e:
                    print(f"警告：缺少依赖库，无法使用预训练语言模型计算困惑度: {e}")
                    print("请安装所需依赖: pip install torch transformers")
                    self.perplexity_calculator = None
            else:
                self.perplexity_calculator = None
        else:
            self.perplexity_calculator = None
        
        # 初始化文本聚类
        if self.config["enable_clustering"]:
            clustering_model_path = os.path.join(
                os.path.dirname(PERPLEXITY_CONFIG["model_path"]), 
                "clustering.bin"
            )
            if os.path.exists(clustering_model_path):
                try:
                    self.text_clustering = TextClustering.load(clustering_model_path, CLUSTERING_CONFIG)
                    print(f"成功加载聚类模型: {clustering_model_path}")
                except Exception as e:
                    print(f"加载聚类模型出错: {e}")
                    self.text_clustering = TextClustering(CLUSTERING_CONFIG)
            else:
                print(f"聚类模型不存在: {clustering_model_path}")
                self.text_clustering = TextClustering(CLUSTERING_CONFIG)
        else:
            self.text_clustering = None
        
        # 确保输出目录存在
        os.makedirs(self.config["output_dir"], exist_ok=True)
        
    def filter_file(self, filepath: str) -> Tuple[bool, Dict]:
        """
        对单个文件进行质量过滤
        Args:
            filepath: 文件路径
            
        Returns:
            (是否为高质量文本, 详细评估结果)
        """
        try:
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                
            return self.filter_text(text)
            
        except Exception as e:
            print(f"处理文件 {filepath} 时出错: {e}")
            traceback.print_exc()
            return False, {"error": str(e)}
    
    def filter_text(self, text: str) -> Tuple[bool, Dict]:
        """
        对文本进行质量过滤
        Args:
            text: 输入文本
            
        Returns:
            (是否为高质量文本, 详细评估结果)
        """
        results = {}
        scores = {}
        
        # 基础规则过滤
        if self.config["enable_rule_filter"]:
            rule_passed, rule_results = self.rule_filter.filter(text)
            rule_score = self.rule_filter.get_rule_score(text)
            
            results["rule_filter"] = {
                "passed": rule_passed,
                "details": rule_results
            }
            scores["rule_score"] = rule_score
        
        # 特征词检测
        if self.config["enable_feature_words"]:
            feature_passed, feature_results = self.feature_detector.filter(text)
            feature_score = self.feature_detector.get_feature_score(text)
            
            results["feature_words"] = {
                "passed": feature_passed,
                "details": feature_results
            }
            scores["feature_score"] = feature_score
        
        # 计算困惑度
        if self.config["enable_perplexity"] and self.perplexity_calculator:
            try:
                perplexity_passed, perplexity_results = self.perplexity_calculator.check_perplexity(text)
                perplexity_score = self.perplexity_calculator.get_perplexity_score(text)
                
                results["perplexity"] = {
                    "passed": perplexity_passed,
                    "details": perplexity_results
                }
                scores["perplexity_score"] = perplexity_score
            except Exception as e:
                print(f"计算困惑度出错: {e}")
                results["perplexity"] = {
                    "passed": True,  # 出错时默认通过
                    "details": {"error": str(e)}
                }
                scores["perplexity_score"] = 0.5  # 出错时给中等分数
        
        # 文本聚类（检测重复）
        if self.config["enable_clustering"] and self.text_clustering:
            try:
                duplicate_passed, duplicate_results = self.text_clustering.check_duplicate(text)
                duplicate_score = self.text_clustering.get_cluster_score(text)
                
                results["clustering"] = {
                    "passed": not duplicate_passed,  # 不重复为通过
                    "details": duplicate_results
                }
                scores["clustering_score"] = duplicate_score
            except Exception as e:
                print(f"检测重复内容出错: {e}")
                results["clustering"] = {
                    "passed": True,  # 出错时默认通过
                    "details": {"error": str(e)}
                }
                scores["clustering_score"] = 0.5  # 出错时给中等分数
        
        # 计算综合质量得分
        quality_score = self._calculate_quality_score(scores)
        is_high_quality = quality_score >= self.config["quality_threshold"]
        
        # 返回综合结果
        return is_high_quality, {
            "quality_score": quality_score,
            "is_high_quality": is_high_quality,
            "component_results": results,
            "component_scores": scores
        }
    
    def _calculate_quality_score(self, scores: Dict) -> float:
        """
        计算综合质量得分
        Args:
            scores: 各组件的得分字典
            
        Returns:
            综合质量得分，范围0-1
        """
        if not scores:
            return 0.0
        
        # 从配置文件获取权重
        weights = GENERAL_CONFIG.get("component_weights", {
            "rule_score": 0.3,      # 规则过滤分数权重
            "feature_score": 0.4,   # 特征词分数权重
            "perplexity_score": 0.3, # 困惑度分数权重
            "clustering_score": 0.0  # 聚类分数权重
        })
        
        # 计算加权平均分
        total_weight = 0.0
        weighted_sum = 0.0
        
        for key, weight in weights.items():
            if key in scores:
                weighted_sum += scores[key] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
            
        return weighted_sum / total_weight
    
    def batch_process(self, input_dir: str, output_dir: str = None, file_pattern: str = "*.txt") -> Dict:
        """
        批量处理文件
        Args:
            input_dir: 输入目录
            output_dir: 输出目录，默认使用配置中的输出目录
            file_pattern: 文件匹配模式
            
        Returns:
            处理结果统计
        """
        output_dir = output_dir or self.config["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有符合模式的文件
        files = glob.glob(os.path.join(input_dir, file_pattern))
        print(f"找到 {len(files)} 个文件需要处理")
        
        # 统计信息
        stats = {
            "total": len(files),
            "high_quality": 0,
            "low_quality": 0,
            "error": 0
        }
        
        # 批量处理文件
        for filepath in tqdm(files, desc="处理文件"):
            try:
                is_high_quality, results = self.filter_file(filepath)
                
                filename = os.path.basename(filepath)
                
                if is_high_quality:
                    # 保存高质量文本
                    output_path = os.path.join(output_dir, filename)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    stats["high_quality"] += 1
                else:
                    stats["low_quality"] += 1
                    
                # 保存评估结果
                results_dir = os.path.join(output_dir, "results")
                os.makedirs(results_dir, exist_ok=True)
                results_path = os.path.join(results_dir, f"{filename}.json")
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                print(f"处理文件 {filepath} 失败: {e}")
                traceback.print_exc()
                stats["error"] += 1
        
        # 保存统计信息
        stats_path = os.path.join(output_dir, "stats.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        print(f"处理完成：共 {stats['total']} 个文件，高质量 {stats['high_quality']} 个，低质量 {stats['low_quality']} 个，错误 {stats['error']} 个")
        return stats
    
    def filter_sensitive_content(self, text: str) -> str:
        """
        过滤文本中的敏感内容和广告内容
        Args:
            text: 输入文本
            
        Returns:
            过滤后的文本
        """
        if not text:
            return text
            
        # 使用特征词检测器的feature_filter过滤特征词（同时包含敏感词和广告词）
        try:
            if self.feature_detector and hasattr(self.feature_detector, "feature_filter") and self.feature_detector.feature_filter is not None:
                filtered_text = self.feature_detector.feature_filter.filter(text)
                return filtered_text
            else:
                # 如果特征词过滤器不可用，尝试重新初始化
                print("特征词过滤器不可用，尝试重新初始化")
                dfa_filter = DFAFilter()
                
                # 尝试加载敏感词和广告词
                sensitive_words_path = os.path.join(BASE_DIR, "data", "sensitive_words.txt")
                ad_words_path = os.path.join(BASE_DIR, "data", "ad_words.txt")
                all_words_path = os.path.join(BASE_DIR, "data", "all_sensitive_words.txt")
                
                if os.path.exists(all_words_path):
                    print(f"加载特征词文件: {all_words_path}")
                    dfa_filter.parse_file(all_words_path)
                else:
                    if os.path.exists(sensitive_words_path):
                        print(f"加载敏感词文件: {sensitive_words_path}")
                        dfa_filter.parse_file(sensitive_words_path)
                    
                    if os.path.exists(ad_words_path):
                        print(f"加载广告词文件: {ad_words_path}")
                        dfa_filter.parse_file(ad_words_path)
                
                # 使用临时过滤器过滤文本
                return dfa_filter.filter(text)
        except Exception as e:
            print(f"过滤特征词出错: {e}")
            traceback.print_exc()
            return text
    
    def batch_filter_sensitive(self, input_dir: str, output_dir: str = None, file_pattern: str = "*.txt") -> Dict:
        """
        批量过滤文件中的敏感内容
        Args:
            input_dir: 输入目录
            output_dir: 输出目录，默认使用配置中的输出目录
            file_pattern: 文件匹配模式
            
        Returns:
            处理结果统计
        """
        output_dir = output_dir or self.config["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有符合模式的文件
        files = glob.glob(os.path.join(input_dir, file_pattern))
        print(f"找到 {len(files)} 个文件需要处理")
        
        # 统计信息
        stats = {
            "total": len(files),
            "processed": 0,
            "error": 0
        }
        
        # 批量处理文件
        for filepath in tqdm(files, desc="过滤敏感内容"):
            try:
                filename = os.path.basename(filepath)
                output_path = os.path.join(output_dir, filename)
                
                # 读取文件内容
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                # 过滤敏感内容
                filtered_text = self.filter_sensitive_content(text)
                
                # 保存过滤后的文本
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(filtered_text)
                
                stats["processed"] += 1
                
            except Exception as e:
                print(f"处理文件 {filepath} 失败: {e}")
                traceback.print_exc()
                stats["error"] += 1
        
        # 保存统计信息
        stats_path = os.path.join(output_dir, "filter_stats.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        print(f"处理完成：共 {stats['total']} 个文件，成功处理 {stats['processed']} 个，错误 {stats['error']} 个")
        return stats


def train_models(args):
    """训练模型"""
    print("开始训练模型...")
    

    
    # 构建语料库聚类
    if not args.skip_clustering:
        print("构建语料库聚类...")
        try:
            clustering_model_path = os.path.join(
                os.path.dirname(PERPLEXITY_CONFIG["model_path"]), 
                "clustering.bin"
            )
            build_corpus_clustering(
                args.train_dir,
                clustering_model_path,
                file_pattern=args.file_pattern,
                config=CLUSTERING_CONFIG
            )
        except Exception as e:
            print(f"构建语料库聚类出错: {e}")
            traceback.print_exc()
    
    print("模型训练完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文本质量过滤工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 过滤文本命令
    filter_parser = subparsers.add_parser("filter", help="过滤文本")
    filter_parser.add_argument("--input_dir", type=str, default="chinese_docs", help="输入目录")
    filter_parser.add_argument("--output_dir", type=str, default=None, help="输出目录")
    filter_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    
    # 训练模型命令
    train_parser = subparsers.add_parser("train", help="训练模型")
    train_parser.add_argument("--train_dir", type=str, required=True, help="训练数据目录")
    train_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    train_parser.add_argument("--skip_ngram", action="store_true", help="跳过N-gram模型训练")
    train_parser.add_argument("--skip_clustering", action="store_true", help="跳过聚类模型构建")
    
    # 敏感词过滤命令
    sensitive_parser = subparsers.add_parser("sensitive", help="过滤敏感内容")
    sensitive_parser.add_argument("--input_dir", type=str, default="chinese_docs", help="输入目录")
    sensitive_parser.add_argument("--output_dir", type=str, default="filtered_sensitive", help="输出目录")
    sensitive_parser.add_argument("--file_pattern", type=str, default="*.txt", help="文件匹配模式")
    
    args = parser.parse_args()
    
    # 创建过滤器
    filter = TextQualityFilter()
    
    if args.command == "filter":
        # 批量处理
        filter.batch_process(args.input_dir, args.output_dir, args.file_pattern)
    
    elif args.command == "train":
        # 训练模型
        train_models(args)
        
    elif args.command == "sensitive":
        # 批量过滤敏感内容
        filter.batch_filter_sensitive(args.input_dir, args.output_dir, args.file_pattern)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 