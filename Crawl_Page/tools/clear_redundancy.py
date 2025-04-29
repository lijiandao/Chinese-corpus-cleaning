import re
from html import unescape
from bs4 import BeautifulSoup
import subprocess

def remove_html_tags(html_content):
    """
    使用 BeautifulSoup 移除 HTML 标签
    :param html_content: 包含 HTML 标签的字符串
    :return: 移除 HTML 标签后的文本
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def clean_text(text):
    """
    清理文本，保留中英文、数字、常见符号和空格，并移除特定 Unicode 范围的表情符号
    :param text: 待清理的文本
    :return: 清理后的文本
    """
    # 移除 emoji 表情
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\u2190-\u21FF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\U0001F600-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F900-\U0001F9FF"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # 允许的标点符号
    allowed_punctuation = " !~@#$%^&*()_+<>?:\"{}|,./;'[]\\-！￥……&*（）_+<>？：{}|，。，；【】—"

    # 保留中英文、数字、允许的标点
    cleaned_chars = []
    for char in text:
        if re.match(r'[\u4e00-\u9fffA-Za-z0-9]', char):
            cleaned_chars.append(char)
        elif char in allowed_punctuation:
            cleaned_chars.append(char)
        # 否则过滤掉

    cleaned_text = ''.join(cleaned_chars)
    # 合并多个连续空格为一个空格
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
    return cleaned_text.strip()

class SuffixAutomatonState:
    def __init__(self):
        self.length = 0
        self.link = -1
        self.next = dict()  # char -> stateId
        self.end_pos_set = set()  # 收集出现位置

class SuffixAutomaton:
    def __init__(self):
        self.states = [SuffixAutomatonState()]
        self.last = 0

    def extend(self, c, pos):
        cur = len(self.states)
        self.states.append(SuffixAutomatonState())
        self.states[cur].length = self.states[self.last].length + 1
        self.states[cur].end_pos_set.add(pos)

        p = self.last
        while p != -1 and c not in self.states[p].next:
            self.states[p].next[c] = cur
            p = self.states[p].link
        if p == -1:
            self.states[cur].link = 0
        else:
            q = self.states[p].next[c]
            if self.states[p].length + 1 == self.states[q].length:
                self.states[cur].link = q
            else:
                clone = len(self.states)
                self.states.append(SuffixAutomatonState())
                self.states[clone].length = self.states[p].length + 1
                self.states[clone].next = self.states[q].next.copy()
                self.states[clone].link = self.states[q].link
                self.states[clone].end_pos_set = set(self.states[q].end_pos_set)
                while p != -1 and self.states[p].next[c] == q:
                    self.states[p].next[c] = clone
                    p = self.states[p].link
                self.states[q].link = clone
                self.states[cur].link = clone
        self.last = cur

    def consolidate_end_pos(self):
        # 按长度从大到小排序
        order = list(range(len(self.states)))
        order.sort(key=lambda x: -self.states[x].length)
        for s in order:
            link = self.states[s].link
            if link != -1:
                self.states[link].end_pos_set.update(self.states[s].end_pos_set)

def remove_long_repeated_substrings(s):
    """
    从字符串 s 中，删除所有"长度≥21"的重复子串的第2+次出现；
    保留每个重复子串在文本中的第一次出现。
    返回删除后得到的字符串。
    """
    # 1) 构建后缀自动机
    automaton = SuffixAutomaton()
    for i, c in enumerate(s):
        automaton.extend(c, i)
    automaton.consolidate_end_pos()

    # 2) 遍历所有状态, 获取满足"length≥21 && 出现次数≥2"的子串的出现区间
    substring_occurrences_map = dict()
    states = automaton.states
    for st in states:
        if st.length < 21:
            continue
        if len(st.end_pos_set) < 2:
            continue
        substring_len = st.length
        link_len = 0 if st.link == -1 else states[st.link].length
        for end_pos in st.end_pos_set:
            start_pos = end_pos - substring_len + 1
            if start_pos < 0:
                continue
            sub = s[start_pos:end_pos + 1]
            if sub not in substring_occurrences_map:
                substring_occurrences_map[sub] = []
            substring_occurrences_map[sub].append((start_pos, end_pos))

    # 3) 对每个重复子串（sub）：
    #    - 出现区间按起始位置排序
    #    - 保留第一次出现(不删除)，把后续出现的区间都放进"待删除"的列表
    to_remove = []
    for sub, intervals in substring_occurrences_map.items():
        if len(intervals) < 2:
            continue
        intervals.sort(key=lambda x: x[0])
        for interval in intervals[1:]:
            to_remove.append(interval)

    if not to_remove:
        return s

    # 4) 合并区间
    to_remove.sort(key=lambda x: (x[0], x[1]))
    merged = []
    cur = list(to_remove[0])
    for nxt in to_remove[1:]:
        if nxt[0] <= cur[1] + 1:
            cur[1] = max(cur[1], nxt[1])
        else:
            merged.append(tuple(cur))
            cur = list(nxt)
    merged.append(tuple(cur))

    # 5) 跳过这些区间
    result_pieces = []
    index = 0
    for start, end in merged:
        if index < start:
            result_pieces.append(s[index:start])
        index = end + 1
    if index < len(s):
        result_pieces.append(s[index:])
    return ''.join(result_pieces)

def deduplicate_with_commoncrawl_dedupe(input_path, output_path, dedupe_path='./commoncrawl_dedupe'):
    """
    用 commoncrawl_dedupe 工具对文件去重
    :param input_path: 输入文件路径
    :param output_path: 输出文件路径
    :param dedupe_path: dedupe 可执行文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as fout:
        subprocess.run([dedupe_path], stdin=open(input_path, 'r', encoding='utf-8'), stdout=fout)


def remove_repeat(text):
    """
    使用 commoncrawl_dedupe 工具对文本去重
    """
    with open('temp.txt', 'w', encoding='utf-8') as fout:
        fout.write(text)
    deduplicate_with_commoncrawl_dedupe('temp.txt', 'temp_deduped.txt')
    return open('temp_deduped.txt', 'r', encoding='utf-8').read()
# ----------------------
# 简单测试与演示
# # ----------------------
# if __name__ == "__main__":
#     test_string = (
#         "abc...abc...这里构造一些重复子串...xyz...xyz"
#         "再拼接一大段文字，确保里面有超过20字符的重复"
#         "再拼接一大段文字，确保里面有超过20字符的重复"
#         "...结尾处也可能有重复..."
#     )
#     result = remove_long_repeated_substrings(test_string)
#     print("原字符串:", test_string)
#     print("删除重复子串后:", result)

#     my_string = "This is some 测试文本 🤔🙂😊😳,,,,,,行者.slideshare.net"
#     print(remove_html_tags(clean_text(my_string)))
import re
from html import unescape
from bs4 import BeautifulSoup
import subprocess

def remove_html_tags(html_content):
    """
    使用 BeautifulSoup 移除 HTML 标签
    :param html_content: 包含 HTML 标签的字符串
    :return: 移除 HTML 标签后的文本
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def clean_text(text):
    """
    清理文本，保留中英文、数字、常见符号和空格，并移除特定 Unicode 范围的表情符号
    :param text: 待清理的文本
    :return: 清理后的文本
    """
    # 移除 emoji 表情
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\u2190-\u21FF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\U0001F600-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F900-\U0001F9FF"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # 允许的标点符号
    allowed_punctuation = " !~@#$%^&*()_+<>?:\"{}|,./;'[]\\-！￥……&*（）_+<>？：{}|，。，；【】—"

    # 保留中英文、数字、允许的标点
    cleaned_chars = []
    for char in text:
        if re.match(r'[\u4e00-\u9fffA-Za-z0-9]', char):
            cleaned_chars.append(char)
        elif char in allowed_punctuation:
            cleaned_chars.append(char)
        # 否则过滤掉

    cleaned_text = ''.join(cleaned_chars)
    # 合并多个连续空格为一个空格
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
    return cleaned_text.strip()

class SuffixAutomatonState:
    def __init__(self):
        self.length = 0
        self.link = -1
        self.next = dict()  # char -> stateId
        self.end_pos_set = set()  # 收集出现位置

class SuffixAutomaton:
    def __init__(self):
        self.states = [SuffixAutomatonState()]
        self.last = 0

    def extend(self, c, pos):
        cur = len(self.states)
        self.states.append(SuffixAutomatonState())
        self.states[cur].length = self.states[self.last].length + 1
        self.states[cur].end_pos_set.add(pos)

        p = self.last
        while p != -1 and c not in self.states[p].next:
            self.states[p].next[c] = cur
            p = self.states[p].link
        if p == -1:
            self.states[cur].link = 0
        else:
            q = self.states[p].next[c]
            if self.states[p].length + 1 == self.states[q].length:
                self.states[cur].link = q
            else:
                clone = len(self.states)
                self.states.append(SuffixAutomatonState())
                self.states[clone].length = self.states[p].length + 1
                self.states[clone].next = self.states[q].next.copy()
                self.states[clone].link = self.states[q].link
                self.states[clone].end_pos_set = set(self.states[q].end_pos_set)
                while p != -1 and self.states[p].next[c] == q:
                    self.states[p].next[c] = clone
                    p = self.states[p].link
                self.states[q].link = clone
                self.states[cur].link = clone
        self.last = cur

    def consolidate_end_pos(self):
        # 按长度从大到小排序
        order = list(range(len(self.states)))
        order.sort(key=lambda x: -self.states[x].length)
        for s in order:
            link = self.states[s].link
            if link != -1:
                self.states[link].end_pos_set.update(self.states[s].end_pos_set)

def remove_long_repeated_substrings(s):
    """
    从字符串 s 中，删除所有"长度≥21"的重复子串的第2+次出现；
    保留每个重复子串在文本中的第一次出现。
    返回删除后得到的字符串。
    """
    # 1) 构建后缀自动机
    automaton = SuffixAutomaton()
    for i, c in enumerate(s):
        automaton.extend(c, i)
    automaton.consolidate_end_pos()

    # 2) 遍历所有状态, 获取满足"length≥21 && 出现次数≥2"的子串的出现区间
    substring_occurrences_map = dict()
    states = automaton.states
    for st in states:
        if st.length < 21:
            continue
        if len(st.end_pos_set) < 2:
            continue
        substring_len = st.length
        link_len = 0 if st.link == -1 else states[st.link].length
        for end_pos in st.end_pos_set:
            start_pos = end_pos - substring_len + 1
            if start_pos < 0:
                continue
            sub = s[start_pos:end_pos + 1]
            if sub not in substring_occurrences_map:
                substring_occurrences_map[sub] = []
            substring_occurrences_map[sub].append((start_pos, end_pos))

    # 3) 对每个重复子串（sub）：
    #    - 出现区间按起始位置排序
    #    - 保留第一次出现(不删除)，把后续出现的区间都放进"待删除"的列表
    to_remove = []
    for sub, intervals in substring_occurrences_map.items():
        if len(intervals) < 2:
            continue
        intervals.sort(key=lambda x: x[0])
        for interval in intervals[1:]:
            to_remove.append(interval)

    if not to_remove:
        return s

    # 4) 合并区间
    to_remove.sort(key=lambda x: (x[0], x[1]))
    merged = []
    cur = list(to_remove[0])
    for nxt in to_remove[1:]:
        if nxt[0] <= cur[1] + 1:
            cur[1] = max(cur[1], nxt[1])
        else:
            merged.append(tuple(cur))
            cur = list(nxt)
    merged.append(tuple(cur))

    # 5) 跳过这些区间
    result_pieces = []
    index = 0
    for start, end in merged:
        if index < start:
            result_pieces.append(s[index:start])
        index = end + 1
    if index < len(s):
        result_pieces.append(s[index:])
    return ''.join(result_pieces)

def deduplicate_with_commoncrawl_dedupe(input_path, output_path, dedupe_path='./commoncrawl_dedupe'):
    """
    用 commoncrawl_dedupe 工具对文件去重
    :param input_path: 输入文件路径
    :param output_path: 输出文件路径
    :param dedupe_path: dedupe 可执行文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as fout:
        subprocess.run([dedupe_path], stdin=open(input_path, 'r', encoding='utf-8'), stdout=fout)


def remove_repeat(text):
    """
    使用 commoncrawl_dedupe 工具对文本去重
    """
    with open('temp.txt', 'w', encoding='utf-8') as fout:
        fout.write(text)
    deduplicate_with_commoncrawl_dedupe('temp.txt', 'temp_deduped.txt')
    return open('temp_deduped.txt', 'r', encoding='utf-8').read()
# ----------------------
# 简单测试与演示
# # ----------------------
# if __name__ == "__main__":
#     test_string = (
#         "abc...abc...这里构造一些重复子串...xyz...xyz"
#         "再拼接一大段文字，确保里面有超过20字符的重复"
#         "再拼接一大段文字，确保里面有超过20字符的重复"
#         "...结尾处也可能有重复..."
#     )
#     result = remove_long_repeated_substrings(test_string)
#     print("原字符串:", test_string)
#     print("删除重复子串后:", result)

#     my_string = "This is some 测试文本 🤔🙂😊😳,,,,,,行者.slideshare.net"
#     print(remove_html_tags(clean_text(my_string)))