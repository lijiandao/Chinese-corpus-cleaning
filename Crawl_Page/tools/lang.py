import fasttext
# 加载预训练语言识别模型（模型文件路径自行替换）  
model = fasttext.load_model(r"N:\program-files\nlp_learn\paper_craw\Crawl_Page\tools\lid.176.bin")  

def is_chinese_fasttext(text, threshold=0.7):  
    predictions = model.predict(text, k=1)  # 返回最可能的语言和置信度  
    lang_label, confidence = predictions[0][0], predictions[1][0]  
    return lang_label == '__label__zh' and confidence >= threshold  

# # 测试  
# text = "s iss is an English t"  
# print(is_chinese_fasttext(text))  # True 或 False（取决于置信度）  

# text2 = "This is an English text."  
# print(is_chinese_fasttext(text2))  # False  
