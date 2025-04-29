"""
基础规则过滤模块
"""
import re
import string
from typing import Dict, Tuple, List, Set, Union

class RuleFilter:
    """
    基础规则过滤类，实现文本的基本质量过滤功能
    """
    def __init__(self, config: Dict):
        """
        初始化
        Args:
            config: 配置字典，包含过滤规则的参数
        """
        self.min_text_length = config.get("min_text_length", 200)
        self.min_avg_line_length = config.get("min_avg_line_length", 10)
        self.min_chinese_ratio = config.get("min_chinese_ratio", 0.4)
        self.max_symbol_ratio = config.get("max_symbol_ratio", 0.3)
        self.max_internal_dup_ratio = config.get("max_internal_dup_ratio", 0.5)
        self.max_vertical_bar_ratio = config.get("max_vertical_bar_ratio", 0.005)
        self.max_comma_ratio = config.get("max_comma_ratio", 0.05)  # 最大逗号比例
        self.max_url_density = config.get("max_url_density", 0.01)  # 最大URL密度
        self.max_emoji_ratio = config.get("max_emoji_ratio", 0.02)  # 最大表情符号比例
        
        # 编译正则表达式，提高性能
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        self.symbol_pattern = re.compile(r'[^\w\s\u4e00-\u9fff]')
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+|[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}')
        self.emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        
    def check_text_length(self, text: str) -> Tuple[bool, str]:
        """
        检查文本长度是否符合要求
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if len(text) < self.min_text_length:
            return False, f"文本长度({len(text)})小于最小长度要求({self.min_text_length})"
        return True, ""
    
    def check_avg_line_length(self, text: str) -> Tuple[bool, str]:
        """
        检查文本平均行长度是否符合要求
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        lines = [line for line in text.split('\n') if line.strip()]
        if not lines:
            return False, "文本没有非空行"
        
        avg_length = sum(len(line) for line in lines) / len(lines)
        if avg_length < self.min_avg_line_length:
            return False, f"平均行长度({avg_length:.2f})小于最小要求({self.min_avg_line_length})"
        return True, ""
    
    def check_chinese_ratio(self, text: str) -> Tuple[bool, str]:
        """
        检查中文字符比例是否符合要求
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        chinese_chars = self.chinese_pattern.findall(text)
        chinese_ratio = len(chinese_chars) / len(text)
        
        if chinese_ratio < self.min_chinese_ratio:
            return False, f"中文字符比例({chinese_ratio:.2f})小于最小要求({self.min_chinese_ratio})"
        return True, ""
    
    def check_symbol_ratio(self, text: str) -> Tuple[bool, str]:
        """
        检查符号比例是否符合要求
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        symbols = self.symbol_pattern.findall(text)
        symbol_ratio = len(symbols) / len(text)
        
        if symbol_ratio > self.max_symbol_ratio:
            return False, f"符号比例({symbol_ratio:.2f})大于最大要求({self.max_symbol_ratio})"
        return True, ""
    
    def check_vertical_bar_ratio(self, text: str) -> Tuple[bool, str]:
        """
        检查"|"符号的比例是否过高，通常用于检测SEO垃圾文本
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        vertical_bars = text.count("|")
        vertical_bar_ratio = vertical_bars / len(text)
        
        if vertical_bar_ratio > self.max_vertical_bar_ratio:
            return False, f"'|'符号比例({vertical_bar_ratio:.4f})超过阈值({self.max_vertical_bar_ratio})"
        return True, ""
    
    def check_comma_ratio(self, text: str) -> Tuple[bool, str]:
        """
        检查逗号的比例是否过高，通常SEO垃圾文本中逗号比例较高
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        commas = text.count(",")
        comma_ratio = commas / len(text)
        
        if comma_ratio > self.max_comma_ratio:
            return False, f"','符号比例({comma_ratio:.4f})超过阈值({self.max_comma_ratio})"
        return True, ""
    
    def check_url_density(self, text: str) -> Tuple[bool, str]:
        """
        检查URL密度是否过高，通常垃圾文本含有较多URL
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        urls = self.url_pattern.findall(text)
        url_density = len(urls) / len(text)
        
        if url_density > self.max_url_density:
            return False, f"URL密度({url_density:.4f})超过阈值({self.max_url_density})"
        return True, ""
    
    def check_emoji_ratio(self, text: str) -> Tuple[bool, str]:
        """
        检查表情符号比例是否过高
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if not text:
            return False, "文本为空"
        
        emojis = self.emoji_pattern.findall(text)
        emoji_ratio = len(emojis) / len(text) if text else 0
        
        if emoji_ratio > self.max_emoji_ratio:
            return False, f"表情符号比例({emoji_ratio:.4f})超过阈值({self.max_emoji_ratio})"
        return True, ""
    
    def check_internal_duplication(self, text: str) -> Tuple[bool, str]:
        """
        检查内部重复率是否符合要求，使用13-gram检测
        Args:
            text: 输入文本
        
        Returns:
            (是否通过, 失败原因)
        """
        if len(text) < 13:
            return True, ""  # 文本太短，不检查重复
        
        # 使用13-gram检测重复
        n = 13
        ngrams = [text[i:i+n] for i in range(len(text)-n+1)]
        unique_ngrams = set(ngrams)
        
        if not ngrams:
            return True, ""
        
        # 计算重复率
        dup_ratio = 1 - len(unique_ngrams) / len(ngrams)
        
        if dup_ratio > self.max_internal_dup_ratio:
            return False, f"内部重复率({dup_ratio:.2f})大于最大要求({self.max_internal_dup_ratio})"
        return True, ""
    
    def filter(self, text: str) -> Tuple[bool, Dict]:
        """
        对文本应用所有规则过滤
        Args:
            text: 输入文本
        
        Returns:
            (是否通过所有规则, 详细结果字典)
        """
        results = {}
        
        # 应用所有规则
        length_check, length_reason = self.check_text_length(text)
        results["length_check"] = {"pass": length_check, "reason": length_reason}
        
        avg_line_check, avg_line_reason = self.check_avg_line_length(text)
        results["avg_line_check"] = {"pass": avg_line_check, "reason": avg_line_reason}
        
        chinese_check, chinese_reason = self.check_chinese_ratio(text)
        results["chinese_check"] = {"pass": chinese_check, "reason": chinese_reason}
        
        symbol_check, symbol_reason = self.check_symbol_ratio(text)
        results["symbol_check"] = {"pass": symbol_check, "reason": symbol_reason}
        
        dup_check, dup_reason = self.check_internal_duplication(text)
        results["dup_check"] = {"pass": dup_check, "reason": dup_reason}
        
        # 检查"|"符号比例
        vbar_check, vbar_reason = self.check_vertical_bar_ratio(text)
        results["vbar_check"] = {"pass": vbar_check, "reason": vbar_reason}
        
        # 新增检查项
        comma_check, comma_reason = self.check_comma_ratio(text)
        results["comma_check"] = {"pass": comma_check, "reason": comma_reason}
        
        url_check, url_reason = self.check_url_density(text)
        results["url_check"] = {"pass": url_check, "reason": url_reason}
        
        emoji_check, emoji_reason = self.check_emoji_ratio(text)
        results["emoji_check"] = {"pass": emoji_check, "reason": emoji_reason}
        
        # 整体结果
        all_passed = all([
            length_check, 
            avg_line_check, 
            chinese_check, 
            symbol_check, 
            dup_check,
            vbar_check,  # 添加新检查条件
            comma_check,
            url_check,
            emoji_check
        ])
        
        return all_passed, results
    
    def get_rule_score(self, text: str) -> float:
        """
        获取规则评分，范围0-1，越高越好
        Args:
            text: 输入文本
            
        Returns:
            规则评分，0-1之间
        """
        passed, results = self.filter(text)
        if passed:
            return 1.0
        
        # 计算各个规则的得分
        scores = []
        weights = []
        
        # 长度得分 (权重低)
        if results["length_check"]["pass"]:
            scores.append(1.0)
        else:
            text_len = len(text)
            scores.append(min(1.0, text_len / self.min_text_length))
        weights.append(0.05)
        
        # 平均行长度得分
        if results["avg_line_check"]["pass"]:
            scores.append(1.0)
        else:
            lines = [line for line in text.split('\n') if line.strip()]
            if lines:
                avg_length = sum(len(line) for line in lines) / len(lines)
                scores.append(min(1.0, avg_length / self.min_avg_line_length))
            else:
                scores.append(0.0)
        weights.append(0.1)
        
        # 中文比例得分 (权重高)
        if results["chinese_check"]["pass"]:
            scores.append(1.0)
        else:
            chinese_chars = self.chinese_pattern.findall(text)
            chinese_ratio = len(chinese_chars) / len(text) if text else 0
            scores.append(min(1.0, chinese_ratio / self.min_chinese_ratio))
        weights.append(0.15)
        
        # 符号比例得分
        if results["symbol_check"]["pass"]:
            scores.append(1.0)
        else:
            symbols = self.symbol_pattern.findall(text)
            symbol_ratio = len(symbols) / len(text) if text else 0
            if symbol_ratio == 0:
                scores.append(1.0)
            else:
                scores.append(max(0.0, min(1.0, self.max_symbol_ratio / symbol_ratio)))
        weights.append(0.1)
        
        # 内部重复率得分
        if results["dup_check"]["pass"]:
            scores.append(1.0)
        else:
            if len(text) < 13:
                scores.append(1.0)
            else:
                n = 13
                ngrams = [text[i:i+n] for i in range(len(text)-n+1)]
                unique_ngrams = set(ngrams)
                dup_ratio = 1 - len(unique_ngrams) / len(ngrams) if ngrams else 0
                scores.append(max(0.0, min(1.0, self.max_internal_dup_ratio / dup_ratio if dup_ratio > 0 else 1.0)))
        weights.append(0.1)
        
        # 垂直线符号比例得分 (权重高)
        if results["vbar_check"]["pass"]:
            scores.append(1.0)
        else:
            vertical_bars = text.count("|")
            vertical_bar_ratio = vertical_bars / len(text) if text else 0
            # 垂直线是严重的垃圾内容指标，失败时得分应该很低
            scores.append(max(0.0, min(0.5, self.max_vertical_bar_ratio / vertical_bar_ratio if vertical_bar_ratio > 0 else 1.0)))
        weights.append(0.2)
        
        # 逗号比例得分
        if results["comma_check"]["pass"]:
            scores.append(1.0)
        else:
            commas = text.count(",")
            comma_ratio = commas / len(text) if text else 0
            scores.append(max(0.0, min(1.0, self.max_comma_ratio / comma_ratio if comma_ratio > 0 else 1.0)))
        weights.append(0.1)
        
        # URL密度得分 (权重高)
        if results["url_check"]["pass"]:
            scores.append(1.0)
        else:
            urls = self.url_pattern.findall(text)
            url_density = len(urls) / len(text) if text else 0
            # URL过多是垃圾内容的强指标
            scores.append(max(0.0, min(0.3, self.max_url_density / url_density if url_density > 0 else 1.0)))
        weights.append(0.1)
        
        # 表情符号比例得分
        if results["emoji_check"]["pass"]:
            scores.append(1.0)
        else:
            emojis = self.emoji_pattern.findall(text)
            emoji_ratio = len(emojis) / len(text) if text else 0
            scores.append(max(0.0, min(1.0, self.max_emoji_ratio / emoji_ratio if emoji_ratio > 0 else 1.0)))
        weights.append(0.1)
        
        # 计算加权平均分
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # 特殊处理：如果存在明显垃圾文本特征，大幅降低得分
        is_obvious_spam = False
        
        # 检查垂直线符号
        if "|" in text and text.count("|") / len(text) > self.max_vertical_bar_ratio * 2:
            is_obvious_spam = True
            
        # 检查URL数量
        if len(self.url_pattern.findall(text)) / len(text) > self.max_url_density * 3:
            is_obvious_spam = True
            
        # 检查SEO垃圾文本特征
        seo_spam_patterns = [
            r'\d+\s*区\s*\d+',  # 例如 "99区99"
            r'在线\s*播放',
            r'视频\s*一区\s*二区',
            r'久久+久+',
            r'不卡\s*一区\s*二区',
            r'精品\s*视频\s*在线',
            r'日本\s*韩国\s*欧美'
        ]
        
        for pattern in seo_spam_patterns:
            if re.search(pattern, text):
                is_obvious_spam = True
                break
                
        if is_obvious_spam:
            weighted_score = weighted_score * 0.3  # 如果是明显垃圾文本，分数大幅降低
            
        return weighted_score 