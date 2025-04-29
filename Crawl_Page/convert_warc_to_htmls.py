<<<<<<< HEAD
import os
from warcio.archiveiterator import ArchiveIterator
import gzip
from clear_redundancy import remove_long_repeated_substrings, remove_html_tags, clean_text
import re
from tqdm import tqdm

# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

def url_to_filename(url):
    # 去除协议头
    filename = re.sub(r'^https?://', '', url)
    # 替换所有非字母数字的字符为下划线
    filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)
    # 限制文件名长度，防止过长
    return filename[:100] + ".html"

def convert_warc_to_htmls(warc_path, htmls_dir):
    """
    将指定的 WARC 文件中的网页内容提取并保存为 HTML 文件到指定目录
    :param warc_path: 采样后的 WARC 文件路径
    :param htmls_dir: 保存 HTML 文件的目标目录
    """
    urls = []
    os.makedirs(htmls_dir, exist_ok=True)
    # 先统计 response 记录总数
    total = 0
    with gzip.open(warc_path, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                total += 1
    # 再次遍历并处理
    with gzip.open(warc_path, 'rb') as stream:
        for record in tqdm(ArchiveIterator(stream), total=total, desc="提取HTML"):
            if record.rec_type == 'response':
                url = record.rec_headers.get_header('WARC-Target-URI')
                payload = record.content_stream().read()
                try:
                    html = payload.decode('utf-8', errors='ignore')
                    html = remove_html_tags(html)
                    html = clean_text(html)
                    html = remove_long_repeated_substrings(html)
                    if len(html.strip()) == 0:
                        continue
                except Exception as e:
                    print("解析正文失败：", e)
                    continue
                urls.append(url)
                filename = url_to_filename(url)
                # 保存HTML内容到文件
                with open(os.path.join(htmls_dir, filename), "wb") as f:
                    f.write(payload)
    print(f"已保存 {len(urls)} 个网页到 {htmls_dir}")
    return urls

# 示例用法
if __name__ == "__main__":
    warc_path = './warc/warc_files/CC-MAIN-20250315031626-20250315061626-00000-sample3000.warc.gz'
    htmls_dir = '../htmls'
=======
import os
from warcio.archiveiterator import ArchiveIterator
import gzip
from clear_redundancy import remove_long_repeated_substrings, remove_html_tags, clean_text
import re
from tqdm import tqdm

# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

def url_to_filename(url):
    # 去除协议头
    filename = re.sub(r'^https?://', '', url)
    # 替换所有非字母数字的字符为下划线
    filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)
    # 限制文件名长度，防止过长
    return filename[:100] + ".html"

def convert_warc_to_htmls(warc_path, htmls_dir):
    """
    将指定的 WARC 文件中的网页内容提取并保存为 HTML 文件到指定目录
    :param warc_path: 采样后的 WARC 文件路径
    :param htmls_dir: 保存 HTML 文件的目标目录
    """
    urls = []
    os.makedirs(htmls_dir, exist_ok=True)
    # 先统计 response 记录总数
    total = 0
    with gzip.open(warc_path, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                total += 1
    # 再次遍历并处理
    with gzip.open(warc_path, 'rb') as stream:
        for record in tqdm(ArchiveIterator(stream), total=total, desc="提取HTML"):
            if record.rec_type == 'response':
                url = record.rec_headers.get_header('WARC-Target-URI')
                payload = record.content_stream().read()
                try:
                    html = payload.decode('utf-8', errors='ignore')
                    html = remove_html_tags(html)
                    html = clean_text(html)
                    html = remove_long_repeated_substrings(html)
                    if len(html.strip()) == 0:
                        continue
                except Exception as e:
                    print("解析正文失败：", e)
                    continue
                urls.append(url)
                filename = url_to_filename(url)
                # 保存HTML内容到文件
                with open(os.path.join(htmls_dir, filename), "wb") as f:
                    f.write(payload)
    print(f"已保存 {len(urls)} 个网页到 {htmls_dir}")
    return urls

# 示例用法
if __name__ == "__main__":
    warc_path = './warc/warc_files/CC-MAIN-20250315031626-20250315061626-00000-sample3000.warc.gz'
    htmls_dir = '../htmls'
>>>>>>> 8f019371d2553e62d8f0ac92a7aaa5c3567f92a7
    convert_warc_to_htmls(warc_path, htmls_dir)