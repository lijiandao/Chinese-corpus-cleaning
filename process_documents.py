import os
from tool import remove_html_tags, is_chinese_fasttext
from tqdm import tqdm

def process_html_files(input_dir="htmls", output_dir="chinese_docs", min_length=100):
    """
    处理HTML文件，提取中文内容并保存
    
    Args:
        input_dir: HTML文件目录
        output_dir: 输出目录
        min_length: 最小文本长度
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有HTML文件
    html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
    print(f"找到 {len(html_files)} 个HTML文件")
    
    # 统计信息
    stats = {
        "total": len(html_files),
        "chinese": 0,
        "non_chinese": 0,
        "error": 0,
        "too_short": 0
    }
    
    # 处理每个文件
    for filename in tqdm(html_files, desc="处理HTML文件"):
        try:
            input_path = os.path.join(input_dir, filename)
            
            # 读取HTML文件
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # 提取文本内容
            text = remove_html_tags(html_content)
            
            # 检查文本长度
            if len(text) < min_length:
                stats["too_short"] += 1
                continue
            
            # 检查是否为中文
            if is_chinese_fasttext(text):
                # 生成输出文件名
                output_filename = os.path.splitext(filename)[0] + '.txt'
                output_path = os.path.join(output_dir, output_filename)
                
                # 保存文本
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                stats["chinese"] += 1
            else:
                stats["non_chinese"] += 1
                
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")
            stats["error"] += 1
    
    # 打印统计信息
    print("\n处理完成！统计信息：")
    print(f"总文件数: {stats['total']}")
    print(f"中文文件数: {stats['chinese']}")
    print(f"非中文文件数: {stats['non_chinese']}")
    print(f"文本过短: {stats['too_short']}")
    print(f"处理出错: {stats['error']}")
    
    return stats

if __name__ == "__main__":
    # 处理HTML文件
    stats = process_html_files() 