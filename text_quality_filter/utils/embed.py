"""
文本嵌入模块
用于计算文本向量表示和相似度
"""
import sys
import os
import torch
from transformers import AutoTokenizer, AutoModel

# 将项目根目录添加到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 引用项目根目录的embed.py中的函数
from embed import get_text_embeddings as root_get_text_embeddings

# 加载中文通用的嵌入模型（如GanymedeNil/text2vec-large-chinese），可根据需要替换为其他支持GPU的模型
MODEL_NAME = "shibing624/text2vec-base-chinese"
# 其他备选模型: "GanymedeNil/text2vec-large-chinese" 或 "GanymedeNil/text2vec-base-chinese"

# 加载分词器和模型，并自动转到GPU（如果可用）
tokenizer = None
model = None
device = None

def init_model():
    global tokenizer, model, device
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        model.eval()

def get_text_embeddings(text_list):
    """
    获取文本嵌入向量
    Args:
        text_list: 文本列表
    
    Returns:
        嵌入向量列表
    """
    return root_get_text_embeddings(text_list)

# 计算文本相似度
def compute_similarity(text1, text2):
    """
    计算两个文本之间的余弦相似度
    """
    embs = get_text_embeddings([text1, text2])
    vec1 = torch.tensor(embs[0])
    vec2 = torch.tensor(embs[1])
    
    # 计算余弦相似度
    cos_sim = torch.nn.functional.cosine_similarity(vec1.unsqueeze(0), vec2.unsqueeze(0))
    return cos_sim.item()

def compute_similarity_matrix(texts):
    """
    计算文本间的相似度矩阵
    Args:
        texts: 文本列表
    
    Returns:
        相似度矩阵
    """
    if not texts:
        return []
    
    # 获取嵌入向量
    embeddings = get_text_embeddings(texts)
    
    # 转换为张量
    vecs = torch.tensor(embeddings)
    
    # 标准化向量
    vecs = torch.nn.functional.normalize(vecs, p=2, dim=1)
    
    # 计算相似度矩阵
    sim_matrix = torch.mm(vecs, vecs.transpose(0, 1))
    
    return sim_matrix.cpu().numpy().tolist()

# 示例用法
if __name__ == "__main__":
    texts = ["你好，世界！", "今天天气不错。", "This is an English sentence."]
    embs = get_text_embeddings(texts)
    for i, emb in enumerate(embs):
        print(f"文本: {texts[i]}\n嵌入向量前5维: {emb[:5]}\n") 