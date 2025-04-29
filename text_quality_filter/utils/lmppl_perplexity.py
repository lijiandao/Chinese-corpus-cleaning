"""
使用预训练语言模型计算困惑度
无需训练自己的模型，直接使用Huggingface提供的预训练中文语言模型
"""
import os
import math
import re
import torch
from typing import Dict, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer

class LMPPLPerplexityCalculator:
    """使用预训练语言模型计算困惑度的计算器"""
    
    def __init__(self, config: Dict):
        """
        初始化
        Args:
            config: 配置字典
        """
        self.model_name = config.get("model_name", "uer/gpt2-chinese-cluecorpussmall")
        self.ppl_threshold = config.get("ppl_threshold", 200.0)  # 降低阈值，使判断更严格
        self.max_ppl = config.get("max_ppl", 10000.0)
        self.max_length = config.get("max_length", 512)
        
        print(f"正在加载预训练语言模型: {self.model_name}")
        
        # 加载模型和分词器
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # 如果有GPU则使用GPU
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"使用设备: {self.device}")
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"加载预训练语言模型失败: {e}")
            raise
    
    def calculate_perplexity(self, text: str) -> float:
        """
        计算文本的困惑度
        Args:
            text: 输入文本
        
        Returns:
            困惑度值
        """
        # 预处理文本，去除一些不影响语义但会增加困惑度的字符
        text = self._preprocess_text(text)
        
        # 截取较长文本，避免OOM
        if len(text) > 500:
            # 不是简单截断，而是选取有意义的片段
            text = self._extract_meaningful_segments(text, 500)
            
        try:
            # 编码文本
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            input_ids = inputs["input_ids"]
            
            # 设置标签，计算语言模型的perplexity
            labels = input_ids.clone()
            
            # 使用no_grad，避免计算梯度
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, labels=labels)
                loss = outputs.loss
                
            try:
                # 困惑度计算公式: exp(loss)
                perplexity = torch.exp(loss).item()
            except OverflowError:
                # 处理数值溢出的情况
                perplexity = self.max_ppl
            
            # 限制最大困惑度
            perplexity = min(perplexity, self.max_ppl)
            
            # 额外检查：垃圾文本特征
            if self._has_spam_patterns(text):
                # 如果文本包含垃圾文本特征，提高其困惑度
                perplexity = max(perplexity * 1.5, self.ppl_threshold * 1.2)
            
            return perplexity
        except Exception as e:
            print(f"计算困惑度时出错: {e}")
            return self.max_ppl
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本，去除不影响语义但会增加困惑度的字符
        """
        # 去除多余空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 去除URL，它们会增加困惑度
        text = re.sub(r'https?://\S+|www\.\S+', '[URL]', text)
        
        # 去除特殊符号序列
        text = re.sub(r'[!?]{2,}', '!', text)  # 多个感叹号替换为一个
        text = re.sub(r'[.]{3,}', '...', text)  # 保留省略号
        
        # 去除表情符号
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 表情符号
            "\U0001F300-\U0001F5FF"  # 符号和象形文字
            "\U0001F680-\U0001F6FF"  # 交通和地图符号
            "\U0001F700-\U0001F77F"  # 炼金术符号
            "\U0001F780-\U0001F7FF"  # 几何形状
            "\U0001F800-\U0001F8FF"  # 补充箭头
            "\U0001F900-\U0001F9FF"  # 补充符号和象形文字
            "\U0001FA00-\U0001FA6F"  # 国际象棋符号
            "\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展-A
            "\U00002702-\U000027B0"  # 装饰符号
            "\U000024C2-\U0001F251"  # 封闭字母和封闭符号
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        
        return text
    
    def _extract_meaningful_segments(self, text: str, max_length: int) -> str:
        """
        从长文本中提取有意义的片段
        """
        # 按句子分割
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s for s in sentences if len(s.strip()) > 0]
        
        # 如果句子太少，直接截取前max_length个字符
        if len(sentences) <= 3:
            return text[:max_length]
        
        # 选取文章前部、中部和后部的句子
        front = sentences[:len(sentences)//3]
        middle = sentences[len(sentences)//3:2*len(sentences)//3]
        end = sentences[2*len(sentences)//3:]
        
        # 从每部分选择一些句子
        selected = []
        selected.extend(front[:2])
        selected.extend(middle[:2])
        selected.extend(end[:2])
        
        # 拼接选取的句子
        combined = "。".join(selected)
        
        # 确保不超过最大长度
        return combined[:max_length]
    
    def _has_spam_patterns(self, text: str) -> bool:
        """
        检查文本是否包含常见垃圾文本特征
        """
        spam_patterns = [
            r'\d+\s*区\s*\d+',  # 例如 "99区99"
            r'在线\s*播放',
            r'视频\s*一区\s*二区',
            r'久久+久+',
            r'不卡\s*一区\s*二区',
            r'精品\s*视频\s*在线',
            r'日本\s*韩国\s*欧美',
            r'激情\s*小说',
            r'成人\s*视频',
            r'在线\s*观看',
            r'一本\s*道',
            r'中文\s*字幕'
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, text):
                return True
        
        # 检查垂直线分隔的文本
        if "|" in text and text.count("|") / len(text) > 0.01:
            return True
            
        # 检查不正常的标点符号比例
        punctuation = '.。,，!！?？:：;；'
        punct_count = sum(text.count(c) for c in punctuation)
        if punct_count / len(text) > 0.15:  # 正常文本标点符号比例通常不会太高
            return True
            
        return False
        
    def check_perplexity(self, text: str) -> Tuple[bool, Dict]:
        """
        检查文本困惑度是否在阈值内
        Args:
            text: 输入文本
        
        Returns:
            (是否在阈值内, 详细结果)
        """
        perplexity = self.calculate_perplexity(text)
        
        is_good = perplexity <= self.ppl_threshold
        
        # 额外检查：如果文本中包含垃圾特征，即使困惑度较低也判定为不通过
        if is_good and self._has_spam_patterns(text):
            is_good = False
        
        return is_good, {
            "perplexity": perplexity,
            "threshold": self.ppl_threshold,
            "has_spam_patterns": self._has_spam_patterns(text)
        }
    
    def get_perplexity_score(self, text: str) -> float:
        """
        获取基于困惑度的质量分数，范围0-1
        Args:
            text: 输入文本
        
        Returns:
            质量分数
        """
        perplexity = self.calculate_perplexity(text)
        
        # 检查是否包含垃圾文本特征
        has_spam = self._has_spam_patterns(text)
        
        # 将困惑度映射到0-1的分数，困惑度越低分数越高
        if perplexity >= self.max_ppl:
            base_score = 0.0
        elif perplexity <= self.ppl_threshold / 2:  # 远低于阈值，接近完美
            base_score = 1.0
        else:
            # 线性映射
            base_score = max(0.0, 1.0 - (perplexity - self.ppl_threshold/2) / (self.max_ppl - self.ppl_threshold/2))
        
        # 如果包含垃圾文本特征，降低分数
        final_score = base_score * (0.5 if has_spam else 1.0)
        
        return final_score 