import torch
from transformers import AutoTokenizer, AutoModel
import os

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

# 加载中文通用的嵌入模型（如GanymedeNil/text2vec-large-chinese），可根据需要替换为其他支持GPU的模型
MODEL_NAME = "shibing624/text2vec-base-chinese"
# "GanymedeNil/text2vec-large-chinese"
# shibing624/text2vec-base-chinese" 或 "GanymedeNil/text2vec-base-chinese



# 加载分词器和模型，并自动转到GPU（如果可用）
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
model.eval()

@torch.no_grad()
def get_text_embeddings(text_list):
    """
    输入: text_list (List[str])，一组文本
    输出: embeddings (List[List[float]])，每个文本的向量表示
    """
    # 批量编码
    encoded = tokenizer(
        text_list,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )
    # 移动到GPU
    for k in encoded:
        encoded[k] = encoded[k].to(device)
    # 前向传播
    output = model(**encoded)
    # 取[CLS]向量（也可根据模型文档选择mean pooling等方式）
    embeddings = output.last_hidden_state[:, 0, :]  # (batch, hidden_size)
    # 转为CPU和list
    embeddings = embeddings.cpu().numpy().tolist()
    return embeddings

# 示例用法
if __name__ == "__main__":
    texts = ["你好，世界！", "今天天气不错。", "This is an English sentence."]
    embs = get_text_embeddings(texts)
    for i, emb in enumerate(embs):
        print(f"文本: {texts[i]}\n嵌入向量前5维: {emb[:5]}\n")
