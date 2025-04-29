import os
import random
import time
from tqdm import tqdm
from warcio.archiveiterator import ArchiveIterator
from warcio.warcwriter import WARCWriter
import gzip
from tools.lang import is_chinese_fasttext
from tools.clear_redundancy import remove_html_tags, clean_text
import threading

# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

def read_with_timeout(content_stream, timeout=1.0):
    result = {}
    def target():
        try:
            result['data'] = content_stream.read()
        except Exception as e:
            result['error'] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        # 超时
        return None, 'timeout'
    if 'error' in result:
        return None, result['error']
    return result.get('data', None), None

def subsample_chinese_warc(input_warc_path):
    """
    对输入的WARC文件筛选所有中文response网页，返回筛选后WARC文件路径
    """
    # 生成输出文件路径
    base, ext = os.path.splitext(input_warc_path)
    if ext == ".gz":
        base, ext2 = os.path.splitext(base)
        output_warc_path = f"{base}-chinese{ext2}{ext}"
    else:
        output_warc_path = f"{base}-chinese{ext}"

    chinese_offsets = []

    with gzip.open(input_warc_path, 'rb') as stream:
        offset = stream.tell()
        for record in tqdm(ArchiveIterator(stream, arc2warc=True), desc="遍历WARC记录", miniters=1):
            if record.rec_type == 'response':
                try:
                    payload, err = read_with_timeout(record.content_stream(), timeout=1.0)
                    if err == 'timeout':
                        print(f"第{offset}个网页读取超时，已跳过")
                        continue
                    elif err is not None:
                        print(f"第{offset}个网页读取异常: {err}，已跳过")
                        continue
                    text = payload.decode('utf-8', errors='ignore')
                    text = remove_html_tags(text)
                    text = clean_text(text)
                    if len(text.strip()) == 0:
                        continue
                    else:
                        if is_chinese_fasttext(text):
                            chinese_offsets.append(offset)
                except Exception as e:
                    pass  # 解码失败或其他异常直接跳过
            offset = stream.tell()

    print(f"检测到的中文网页数量: {len(chinese_offsets)}")

    if len(chinese_offsets) == 0:
        print("没有检测到中文网页，未生成筛选文件。")
        return None

    chinese_offsets_set = set(chinese_offsets)

    # 重新遍历一遍，写入所有中文response网页到新warc文件
    with gzip.open(input_warc_path, 'rb') as instream, open(output_warc_path, 'wb') as outstream:
        writer = WARCWriter(outstream, gzip=True)
        offset = instream.tell()
        for record in ArchiveIterator(instream, arc2warc=True):
            if offset in chinese_offsets_set and record.rec_type == 'response':
                writer.write_record(record)
            offset = instream.tell()

    print(f"已筛选并写入 {len(chinese_offsets)} 个中文response网页到 {output_warc_path}")
    return output_warc_path

# 示例用法
if __name__ == "__main__":
    input_warc_path = './warc/warc_files/CC-MAIN-20250315031626-20250315061626-00000.warc.gz'
    result_path = subsample_chinese_warc(input_warc_path)
    print("筛选后的WARC文件路径:", result_path)

# 遍历WARC记录: 83575it [18:04, 77.08it/s]
# 检测到的中文网页数量: 1400
# 已筛选并写入 1400 个中文response网页到 ./warc_files/CC-MAIN-20250315031626-20250315061626-00000-chinese.warc.gz    