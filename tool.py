import fasttext
from bs4 import BeautifulSoup
import re

# 加载预训练语言识别模型（模型文件路径自行替换）  
model = fasttext.load_model("lid.176.bin")  

def clean_text(text):
    """清理文本，去除无用字符"""
    # 去除换行符和多余空格
    text = re.sub(r'\s+', ' ', text)
    # 去除特殊控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

def is_chinese_fasttext(text, threshold=0.7):  
    if not text or len(text) < 10:
        return False
        
    # 清理文本
    text = clean_text(text)
    if not text:
        return False
        
    try:
        predictions = model.predict(text, k=1)  # 返回最可能的语言和置信度  
        lang_label, confidence = predictions[0][0], predictions[1][0]  
        return lang_label == '__label__zh' and confidence >= threshold
    except ValueError as e:
        # 如果文本仍然有问题，可能需要进一步清理
        print(f"预测错误: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False


def remove_html_tags(html_content):
    """使用 BeautifulSoup 移除 HTML 标签
    :param html_content: 包含 HTML 标签的字符串
    :return: 移除 HTML 标签后的文本
    """
    try:
        # 检查是否为有效的HTML内容
        if not html_content or not isinstance(html_content, str):
            return ""
            
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 移除脚本和样式元素
        for script in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
            script.extract()
            
        # 获取文本
        text = soup.get_text(separator=' ')
        
        # 清理文本
        text = clean_text(text)
        
        return text
    except Exception as e:
        print(f"HTML处理错误: {e}")
        return ""


# # 测试  
# text = "s iss is an English t"  
# print(is_chinese_fasttext(text))  # True 或 False（取决于置信度）  

# text2 = "这是中文"  
# print(is_chinese_fasttext(text2))  # False  

# # 测试
# html_content = """
# <html>
#     <body>
#         <h1>这是一个测试</h1>
#         <p>这是测试内容</p>
#     </body>
# </html>
# """

# print(remove_html_tags(html_content))
