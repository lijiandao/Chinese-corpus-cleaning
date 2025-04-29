from warc.download_warcfile import download_warcfile
from subsample_warc_warc import subsample_chinese_warc
from convert_warc_to_htmls import convert_warc_to_htmls

htmls_dir = '../htmls'
output_dir = './warc_files'  # 默认值
downloaded_file_paths = download_warcfile(output_dir, 2)  # 下载两个warc文件
for downloaded_file_path in downloaded_file_paths: 
    result_path = subsample_chinese_warc(downloaded_file_path)  # 直接筛选所有中文网页
    print("筛选后的WARC文件路径:", result_path)
    # 将筛选后的文件转换为html文件
    convert_warc_to_htmls(result_path, htmls_dir)

