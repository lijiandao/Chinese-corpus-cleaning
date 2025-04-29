"""
特征词检测模块，包括各类特征词（敏感词、广告词等）
"""
import os
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# 修复导入路径
from text_quality_filter.utils.sensitive_filter import DFAFilter

class AhoCorasick:
    """
    Aho-Corasick算法实现，用于高效多模式匹配
    """
    def __init__(self):
        self.trie = {}
        self.fail = {}
        self.output = defaultdict(set)
        self.depth = {}
        self.built = False
    
    def add_pattern(self, pattern: str, pattern_id=None):
        """
        添加模式串
        """
        node = self.trie
        for i, char in enumerate(pattern):
            if char not in node:
                node[char] = {}
            node = node[char]
            self.depth[id(node)] = i + 1
        
        # 设置输出
        pattern_id = pattern_id if pattern_id is not None else pattern
        self.output[id(node)].add(pattern_id)
    
    def build(self):
        """
        构建失败指针
        """
        if self.built:
            return
        
        # 构建BFS队列
        queue = []
        for k, v in self.trie.items():
            self.fail[id(v)] = self.trie
            queue.append(v)
        
        # BFS构建失败指针
        while queue:
            current = queue.pop(0)
            for char, node in current.items():
                queue.append(node)
                
                # 获取父节点的失败指针
                failure = self.fail[id(current)]
                
                # 沿着失败指针回溯，直到找到一个节点有相同的出边
                while failure != self.trie and char not in failure:
                    failure = self.fail[id(failure)]
                
                # 如果找到了这样的节点，设置失败指针
                self.fail[id(node)] = failure[char] if char in failure else self.trie
                
                # 合并输出
                if id(self.fail[id(node)]) in self.output:
                    self.output[id(node)].update(self.output[id(self.fail[id(node)])])
        
        self.built = True
    
    def search(self, text: str) -> List[Tuple[int, str]]:
        """
        在文本中搜索所有模式串
        Returns:
            List of (position, pattern)
        """
        if not self.built:
            self.build()
        
        results = []
        node = self.trie
        
        for i, char in enumerate(text):
            # 回溯失败指针直到找到匹配或回到根节点
            while node != self.trie and char not in node:
                node = self.fail[id(node)]
            
            # 如果找到匹配，更新节点
            if char in node:
                node = node[char]
            else:
                continue
            
            # 检查是否有匹配的模式
            if id(node) in self.output:
                for pattern in self.output[id(node)]:
                    depth = self.depth[id(node)]
                    start_pos = i - depth + 1
                    results.append((start_pos, pattern))
        
        return results

class FeatureWordsDetector:
    """
    特征词检测类，统一处理所有特征词
    """
    def __init__(self, config: Dict):
        """
        初始化
        Args:
            config: 配置字典
        """
        self.feature_words_path = config.get("feature_words_path", "")
        self.max_feature_words_per_line = config.get("max_feature_words_per_line", 0.1)
        self.use_dfa_filter = config.get("use_dfa_filter", True)
        
        # 加载特征词
        self.feature_words = self._load_words(self.feature_words_path)
        
        # 根据配置决定使用哪种特征词过滤方式
        if self.use_dfa_filter:
            self.feature_filter = DFAFilter()
            self.feature_filter.parse_list(list(self.feature_words))
            self.feature_ac = None
        else:
            self.feature_ac = self._build_ac(self.feature_words)
            self.feature_filter = None
    
    def _load_words(self, path: str) -> Set[str]:
        """
        从文件加载词汇
        """
        words = set()
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        words.add(word)
        return words
    
    def _build_ac(self, words: Set[str]) -> AhoCorasick:
        """
        构建AC自动机
        """
        ac = AhoCorasick()
        for word in words:
            ac.add_pattern(word)
        ac.build()
        return ac
    
    def detect_feature_words(self, text: str) -> List[Tuple[int, str]]:
        """
        检测特征词
        """
        if not self.feature_words:
            return []
        
        if self.use_dfa_filter:
            # 使用DFA过滤器
            _, feature_words = self.feature_filter.count_sensitive_words(text)
            # 转换格式为 (0, word) 以保持API兼容
            return [(0, word) for word in feature_words]
        else:
            # 使用AC自动机
            return self.feature_ac.search(text)
    
    def check_feature_words(self, text: str) -> Tuple[bool, Dict]:
        """
        检查是否包含过多特征词
        """
        if not self.feature_words:
            return True, {"feature_count": 0, "feature_words": []}
        
        feature_matches = self.detect_feature_words(text)
        feature_words = [word for _, word in feature_matches]
        
        # 计算每行特征词数量
        lines = text.split('\n')
        line_feature_counts = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if self.use_dfa_filter:
                # 使用DFA过滤器直接检测每行
                count, _ = self.feature_filter.count_sensitive_words(line)
                line_feature_counts.append(count)
            else:
                # 使用AC自动机结果，需要计算每行的特征词
                count = 0
                for _, word in feature_matches:
                    if word in line:
                        count += 1
                line_feature_counts.append(count)
        
        # 有效行数(至少5个字符)
        valid_lines = [line for line in lines if len(line.strip()) >= 5]
        valid_line_count = len(valid_lines)
        
        # 计算平均每行特征词数量
        avg_feature_per_line = sum(line_feature_counts) / valid_line_count if valid_line_count > 0 else 0
        
        # 判断是否超过阈值
        is_good = avg_feature_per_line <= self.max_feature_words_per_line
        
        return is_good, {
            "feature_count": len(feature_words),
            "feature_words": feature_words,
            "avg_per_line": avg_feature_per_line
        }
    
    def filter(self, text: str) -> Tuple[bool, Dict]:
        """
        过滤特征词
        """
        # 检查特征词
        passed, results = self.check_feature_words(text)
        
        # 返回结果
        return passed, {
            "feature_check": {
                "pass": passed,
                "details": results
            }
        }
    
    def get_feature_score(self, text: str) -> float:
        """
        获取特征词得分，范围0-1，越高越好
        """
        if not text or len(text) == 0:
            return 0.0
        
        passed, results = self.check_feature_words(text)
        
        # 特征词得分
        feature_count = results.get("feature_count", 0)
        feature_words = results.get("feature_words", [])
        avg_per_line = results.get("avg_per_line", 0)
        
        # 有些关键词权重更高，代表更可能是垃圾文本
        high_weight_keywords = ['色情', '赌博', '特价', '促销', '优惠', '免费', '限时',
                               '加QQ', '加微信', 'http://', 'www.', '点击', '链接',
                               '联系电话', '约炮', '一夜情']
        
        # 某些常见词可能是误伤，权重较低
        common_words = ['系统', '手机', '电话', '网络', '联系', '人才', '招聘']
        
        # 计算文本总字数和特征词占比
        total_chars = len(text)
        unique_feature_words = set(feature_words)
        
        # 调整特征词计数（去除常见词）
        adjusted_feature_words = []
        for word in unique_feature_words:
            if word in common_words:
                continue  # 跳过常见词
            adjusted_feature_words.append(word)
        
        unique_feature_count = len(adjusted_feature_words)
        
        # 对高权重词汇计数
        high_weight_count = 0
        for word in high_weight_keywords:
            if word in text.lower():
                high_weight_count += 3  # 高权重词计3倍
        
        # 修正后的特征词计数（包含权重）
        adjusted_feature_count = unique_feature_count + high_weight_count
        
        # 计算特征词比例
        feature_ratio = adjusted_feature_count / (total_chars / 10) if total_chars > 0 else 1.0
        
        # 检测是否是"正常文本"提及敏感词的情况，比如讨论"此网站不会出现色情和赌博内容"
        # 这种情况下我们应该给更高分数
        negative_context_patterns = [
            r'不包含.*?(色情|赌博|广告)',
            r'没有.*?(色情|赌博|广告)',
            r'禁止.*?(色情|赌博|广告)',
            r'反对.*?(色情|赌博|广告)',
            r'拒绝.*?(色情|赌博|广告)'
        ]
        
        is_negative_context = False
        for pattern in negative_context_patterns:
            if re.search(pattern, text):
                is_negative_context = True
                break
        
        # 如果是否定上下文，降低特征词比例
        if is_negative_context:
            feature_ratio = feature_ratio * 0.3
        
        # 反转评分:更多特征词应该得到更低的分数
        if feature_ratio > 0.2:
            feature_score = 0.0  # 非常多的特征词，明显是垃圾内容
        elif feature_ratio > 0.1:
            feature_score = 0.2  # 较多特征词
        elif feature_ratio > 0.05:
            feature_score = 0.5  # 中等特征词
        elif feature_ratio > 0.01:
            feature_score = 0.8  # 少量特征词
        else:
            feature_score = 1.0  # 几乎没有特征词
        
        # 如果匹配到否定上下文且特征词比例很低，给予高分
        if is_negative_context and feature_ratio < 0.05:
            feature_score = max(feature_score, 0.8)
            
        return feature_score



if __name__ == "__main__":
    
    # 测试
    config = {
        "feature_words_path": "../data/all_sensitive_words.txt",
        "max_feature_words_per_line": 0.3,
        "use_dfa_filter": True  # 使用DFA过滤器
    }
    
    detector = FeatureWordsDetector(config)
    
    test_text = """
    这是一个测试文本，用于测试特征词检测功能。
    这里有一些广告词：特价促销，限时优惠，免费咨询，联系电话：12345678。
    这里有一些敏感词：赌博，色情，暴力内容。
    """
    
    passed, results = detector.filter(test_text)
    score = detector.get_feature_score(test_text)
    
    print(f"文本通过检测: {passed}")
    print(f"特征词: {results['feature_check']['details']['feature_words']}")
    print(f"特征词得分: {score:.2f}")
    
    # 使用DFA过滤器过滤特征词
    if detector.use_dfa_filter:
        filtered_text = detector.feature_filter.filter(test_text)
        print(f"\n过滤后的文本:\n{filtered_text}") 