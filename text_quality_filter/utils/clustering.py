"""
文本聚类模块
用于检测文本库中的重复或相似内容
"""
import os
import numpy as np
from typing import Dict, List, Tuple, Set
from sklearn.cluster import DBSCAN
import pickle
import torch

# 导入我们的嵌入模块
from text_quality_filter.utils.embed import get_text_embeddings, compute_similarity_matrix


class TextClustering:
    """文本聚类类，用于检测重复或相似内容"""
    
    def __init__(self, config: Dict):
        """
        初始化
        Args:
            config: 配置字典
        """
        self.similarity_threshold = config.get("similarity_threshold", 0.85)
        self.embedding_model = config.get("embedding_model", "shibing624/text2vec-base-chinese")
        self.min_cluster_size = config.get("min_cluster_size", 3)
        
        # 存储文本及其嵌入
        self.texts = []
        self.embeddings = []
        self.clusters = {}
        
    def add_texts(self, texts: List[str]):
        """
        添加文本到聚类器
        Args:
            texts: 文本列表
        """
        if not texts:
            return
            
        # 获取文本嵌入
        new_embeddings = get_text_embeddings(texts)
        
        # 更新文本和嵌入
        self.texts.extend(texts)
        self.embeddings.extend(new_embeddings)
    
    def cluster(self) -> Dict:
        """
        对文本进行聚类
        Returns:
            聚类结果字典
        """
        if not self.embeddings:
            return {"clusters": {}, "noise": []}
        
        # 将嵌入转换为numpy数组
        embeddings_array = np.array(self.embeddings)
        
        # 计算相似度矩阵
        similarity_matrix = compute_similarity_matrix(self.texts)
        
        # 将相似度矩阵转换为距离矩阵（1 - 相似度）
        distance_matrix = 1 - np.array(similarity_matrix)
        
        # 使用DBSCAN进行聚类
        eps = 1 - self.similarity_threshold  # 转换相似度阈值为距离阈值
        dbscan = DBSCAN(eps=eps, min_samples=self.min_cluster_size, metric='precomputed')
        cluster_labels = dbscan.fit_predict(distance_matrix)
        
        # 整理聚类结果
        clusters = {}
        noise = []
        
        for i, label in enumerate(cluster_labels):
            if label == -1:  # 噪声点（独特文本）
                noise.append(i)
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)
        
        self.clusters = {
            "clusters": clusters,
            "noise": noise
        }
        
        return self.clusters
    
    def save(self, save_path: str):
        """
        保存聚类结果
        Args:
            save_path: 保存路径
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            pickle.dump({
                'texts': self.texts,
                'embeddings': self.embeddings,
                'clusters': self.clusters
            }, f)
    
    @classmethod
    def load(cls, load_path: str, config: Dict = None):
        """
        加载聚类结果
        Args:
            load_path: 加载路径
            config: 配置字典
            
        Returns:
            TextClustering实例
        """
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
        
        clustering = cls(config or {})
        clustering.texts = data['texts']
        clustering.embeddings = data['embeddings']
        clustering.clusters = data['clusters']
        
        return clustering
    
    def get_duplicate_ratio(self, text: str) -> float:
        """
        获取文本的重复率（与已有文本的最大相似度）
        Args:
            text: 输入文本
            
        Returns:
            重复率，范围0-1
        """
        if not self.texts:
            return 0.0
        
        # 获取文本嵌入
        embedding = get_text_embeddings([text])[0]
        
        # 计算与所有已有文本的相似度
        similarities = []
        for other_embedding in self.embeddings:
            # 计算余弦相似度
            sim = self._cosine_similarity(embedding, other_embedding)
            similarities.append(sim)
        
        # 返回最大相似度
        return max(similarities) if similarities else 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度
        """
        vec1 = torch.tensor(vec1)
        vec2 = torch.tensor(vec2)
        
        # 计算余弦相似度
        cos_sim = torch.nn.functional.cosine_similarity(vec1.unsqueeze(0), vec2.unsqueeze(0))
        return cos_sim.item()
    
    def check_duplicate(self, text: str) -> Tuple[bool, Dict]:
        """
        检查文本是否与已有文本重复
        Args:
            text: 输入文本
            
        Returns:
            (是否重复, 详细结果)
        """
        duplicate_ratio = self.get_duplicate_ratio(text)
        
        is_duplicate = duplicate_ratio >= self.similarity_threshold
        
        return is_duplicate, {
            "duplicate_ratio": duplicate_ratio,
            "threshold": self.similarity_threshold
        }
    
    def get_cluster_score(self, text: str) -> float:
        """
        获取基于聚类的质量分数，范围0-1
        分数越高表示文本越独特（不重复）
        Args:
            text: 输入文本
            
        Returns:
            质量分数
        """
        duplicate_ratio = self.get_duplicate_ratio(text)
        
        # 将重复率映射到0-1的分数，重复率越低分数越高
        if duplicate_ratio >= self.similarity_threshold:
            # 超过阈值，认为是重复文本
            normalized_score = 0.2 * (1 - (duplicate_ratio - self.similarity_threshold) / (1 - self.similarity_threshold))
            return max(0.0, normalized_score)
        else:
            # 低于阈值，认为是原创文本，分数随相似度降低而提高
            normalized_score = 0.8 + 0.2 * (1 - duplicate_ratio / self.similarity_threshold)
            return min(1.0, normalized_score)


def build_corpus_clustering(input_dir: str, output_path: str, file_pattern: str = "*.txt", config: Dict = None):
    """
    构建语料库聚类
    Args:
        input_dir: 输入目录
        output_path: 输出路径
        file_pattern: 文件匹配模式
        config: 配置字典
    """
    import glob
    from tqdm import tqdm
    
    # 获取所有文件
    files = glob.glob(os.path.join(input_dir, file_pattern))
    if not files:
        print(f"在 {input_dir} 中没有找到符合 {file_pattern} 的文件")
        return
    
    print(f"找到 {len(files)} 个文件")
    
    # 读取文本
    texts = []
    for filepath in tqdm(files, desc="读取文件"):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                if text.strip():
                    texts.append(text)
        except Exception as e:
            print(f"读取文件 {filepath} 出错: {e}")
    
    if not texts:
        print("没有读取到有效文本")
        return
    
    print(f"读取了 {len(texts)} 个有效文本")
    
    # 创建聚类器
    clustering = TextClustering(config or {})
    
    # 分批添加文本（避免内存问题）
    batch_size = 100
    for i in tqdm(range(0, len(texts), batch_size), desc="处理文本批次"):
        batch_texts = texts[i:i+batch_size]
        clustering.add_texts(batch_texts)
    
    # 执行聚类
    print("开始聚类...")
    clusters = clustering.cluster()
    
    # 打印聚类结果
    cluster_count = len(clusters["clusters"])
    unique_count = len(clusters["noise"])
    print(f"聚类完成: 找到 {cluster_count} 个聚类和 {unique_count} 个独特文本")
    
    # 保存聚类结果
    clustering.save(output_path)
    print(f"聚类结果已保存到: {output_path}")
    
    return clustering


if __name__ == "__main__":
    # 示例用法
    config = {
        "similarity_threshold": 0.85,
        "min_cluster_size": 2
    }
    
    # 构建语料库聚类
    # clustering = build_corpus_clustering("chinese_docs", "text_quality_filter/models/clustering.bin", config=config)
    
    # 示例：使用已有聚类检测重复
    # clustering = TextClustering.load("text_quality_filter/models/clustering.bin", config)
    
    # 测试文本
    test_texts = [
        "这是一个测试文本，用于演示文本聚类。",
        "这是另一个完全不同的文本，内容差异很大。",
        "这是一个测试文本，用来演示文本的聚类功能。"  # 与第一个文本相似
    ]
    
    # 创建临时聚类器进行演示
    clustering = TextClustering(config)
    clustering.add_texts(test_texts[:2])  # 只添加前两个文本
    
    # 检测第三个文本是否重复
    is_duplicate, result = clustering.check_duplicate(test_texts[2])
    score = clustering.get_cluster_score(test_texts[2])
    
    print(f"文本: {test_texts[2]}")
    print(f"是否重复: {is_duplicate}")
    print(f"重复率: {result['duplicate_ratio']:.2f}")
    print(f"质量分数: {score:.2f}") 