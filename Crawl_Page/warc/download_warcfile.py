import os
import requests
from tqdm import tqdm
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
BASE_URL = r'https://data.commoncrawl.org/'

def download_warcfile(output_dir, download_numbers=1):
    urls = []
    downloaded_files = []
    with open('./warc.paths', 'r') as f:
        for line in f:
            url = line.strip()
            urls.append(url)
    for url in urls[:download_numbers]:
        try:
            file_name = os.path.basename(url)
            file_path = os.path.join(output_dir, file_name)
            # 获取已下载的文件大小
            resume_byte_pos = 0
            if os.path.exists(file_path):
                resume_byte_pos = os.path.getsize(file_path)
            headers = {}
            if resume_byte_pos > 0:
                headers['Range'] = f'bytes={resume_byte_pos}-'
            # 流式下载
            with requests.get(BASE_URL + url, headers=headers, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('Content-Length', 0))
                # 如果是断点续传，Content-Range 里有总长度
                if 'Content-Range' in response.headers:
                    total_size = int(response.headers['Content-Range'].split('/')[-1])
                mode = 'ab' if resume_byte_pos > 0 else 'wb'
                with open(file_path, mode) as f, tqdm(
                    total=total_size,
                    initial=resume_byte_pos,
                    unit='B',
                    unit_scale=True,
                    desc=file_name,
                    ascii=True
                ) as bar:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return downloaded_files

if __name__ == "__main__":
    output_dir = "./warc_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    downloaded_files = download_warcfile(output_dir, 1)
    print("下载的文件路径列表:", downloaded_files)
