"""
敏感词过滤模块
基于DFA算法实现的高效敏感词过滤
"""
import os
from typing import List, Set, Dict, Any, Optional, Tuple

class DFAFilter:
    """
    基于DFA算法的敏感词过滤器
    使用确定性有限自动机来保持算法性能稳定
    """

    def __init__(self):
        """初始化过滤器"""
        self.keyword_chains = {}
        self.delimit = '\x00'

    def add(self, keyword: str) -> None:
        """
        添加敏感词
        Args:
            keyword: 要添加的敏感词
        """
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        
        level = self.keyword_chains
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: 0}
                break
        if i == len(chars) - 1:
            level[self.delimit] = 0

    def parse_file(self, path: str) -> None:
        """
        从文件中批量加载敏感词
        Args:
            path: 敏感词文件路径，每行一个敏感词
        """
        if not os.path.exists(path):
            print(f"文件不存在: {path}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for keyword in f:
                    self.add(keyword.strip())
        except Exception as e:
            print(f"加载敏感词文件出错: {e}")

    def parse_list(self, keywords: List[str]) -> None:
        """
        从列表中批量加载敏感词
        Args:
            keywords: 敏感词列表
        """
        for keyword in keywords:
            self.add(keyword.strip())

    def filter(self, message: str, repl: str = "*") -> str:
        """
        过滤文本中的敏感词
        Args:
            message: 要过滤的文本
            repl: 替换字符，默认为*
            
        Returns:
            过滤后的文本
        """
        message = message.lower()
        ret = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        ret.append(repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return ''.join(ret)
    
    def detect(self, message: str) -> List[str]:
        """
        检测文本中的敏感词
        Args:
            message: 要检测的文本
            
        Returns:
            检测到的敏感词列表
        """
        message = message.lower()
        found_words = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        found_words.append(message[start:start+step_ins])
                        start += step_ins - 1
                        break
                else:
                    break
            start += 1
        
        return found_words
    
    def count_sensitive_words(self, message: str) -> Tuple[int, List[str]]:
        """
        统计敏感词数量和列表
        Args:
            message: 要检测的文本
            
        Returns:
            (敏感词数量, 敏感词列表)
        """
        sensitive_words = self.detect(message)
        return len(sensitive_words), sensitive_words 