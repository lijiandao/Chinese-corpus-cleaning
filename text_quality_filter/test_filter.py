"""
测试文本质量过滤器
验证对含有大量"|"符号的垃圾文本的过滤效果
"""
import os
import sys
import json
from typing import Dict, List

# 将项目根目录添加到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_quality_filter.main import TextQualityFilter

def test_seo_spam_filter():
    """测试对SEO垃圾文本的过滤效果"""
    # 创建过滤器
    filter = TextQualityFilter()
    
    # 测试数据
    test_cases = [
        {
            "name": "正常文本",
            "text": """文本质量过滤是自然语言处理中的重要任务，旨在从大量文本数据中筛选出高质量的内容。
                    高质量的文本通常具有较高的中文比例、适当的符号使用、较低的内部重复率等特点。
                    通过多种过滤方法的组合，可以有效提高语料库的质量，为后续的自然语言处理任务提供更好的基础。
                    本项目实现了一套文本质量过滤系统，集成了基础规则过滤、特征词检测、困惑度计算和文本聚类等功能。"""
        },
        {
            "name": "含有大量|符号的垃圾文本",
            "text": """久久久久久日本一区99 | 欧美日韩a∨毛片一区 | 99国产精品视频久久久久 | 国产极品精频在线观看 | 
                    免费亚洲黄色 | 大量真实偷拍情侣视频野战 | 美国毛片一级视频在线aa | 97sese论坛 | 日韩成人小视频 | 
                    国产亚洲精品久久精品6 | 久久男人的天堂 | 中文字幕一区在线播放 | 亚洲午夜久久久久国产 | 
                    可以免费看黄色的网站 | 亚洲综合色一区二区三区小说 | 青木玲中文字幕一区二区 | 成年大片免费视频播放二级 | 
                    91视频一区 | 99精彩视频 | 日韩欧美一及在线播放 | 国产欧美亚洲精品 | 玖玖色视频 | 成人午夜影院在线观看 | 
                    国产一在线 | 亚洲综合网在线 | 久久久久久青草大香综合精品 | 欧美日韩另类综合 | 成人国产精品免费视频不卡 | 
                    九九99视频在线观看视频观看 | 丁香狠狠色婷婷久久综合 | 91久久国产口精品久久久久 | 欧美综合精品一区二区三区 | 
                    99九九国产精品免费视频 | 天天看片天天爽 | 自拍偷拍图区 | 日韩精品一区二区三区在线观看l | 国产在线视频h | 
                    国产成人精品一区二区视频 | 中文精品久久久久国产网址 | 日韩 国产 欧美视频一区二区三区 | 一级成人毛片 |"""
        },
        {
            "name": "低质量短文本",
            "text": "这是一个太短的文本"
        },
        {
            "name": "低中文比例文本", 
            "text": "This is a test text with very little Chinese content. 这只有一点点中文内容。"
        }
    ]
    
    # 运行测试
    results = []
    for case in test_cases:
        name = case["name"]
        text = case["text"]
        
        # 测试基础规则过滤
        rule_passed, rule_details = filter.rule_filter.filter(text)
        
        # 测试垂直线符号比例检测
        vbar_passed = rule_details["vbar_check"]["pass"]
        vbar_reason = rule_details["vbar_check"]["reason"]
        
        # 计算质量分数
        rule_score = filter.rule_filter.get_rule_score(text)
        
        # 添加到结果
        results.append({
            "name": name,
            "text_preview": text[:50] + "..." if len(text) > 50 else text,
            "rule_passed": rule_passed,
            "vertical_bar_check": {
                "passed": vbar_passed,
                "reason": vbar_reason
            },
            "rule_score": rule_score
        })
    
    # 打印结果
    print("文本质量过滤测试结果:")
    print("=" * 80)
    for result in results:
        print(f"测试用例: {result['name']}")
        print(f"文本预览: {result['text_preview']}")
        print(f"规则过滤结果: {'通过' if result['rule_passed'] else '未通过'}")
        print(f"垂直线检查: {'通过' if result['vertical_bar_check']['passed'] else '未通过'} - {result['vertical_bar_check']['reason']}")
        print(f"规则分数: {result['rule_score']:.4f}")
        print("-" * 80)

def test_feature_words_and_sensitive_filter():
    """测试特征词检测和敏感内容过滤功能"""
    print("\n特征词检测和敏感内容过滤测试:")
    print("=" * 80)
    
    # 创建过滤器
    filter = TextQualityFilter()
    
    # 测试数据
    test_cases = [
        {
            "name": "包含广告词的文本",
            "text": """这是一个测试文本，包含一些广告词。
                    限时特价促销！优惠活动仅限三天！
                    联系电话：13917340054，添加微信享受更多折扣。
                    访问我们的官网www.example.com，或扫码关注。"""
        },
        {
            "name": "包含敏感词的文本",
            "text": """这是一个测试文本，包含一些敏感内容。
                    涉及到色情、赌博、毒品等内容。
                    这类内容应该被过滤掉。"""
        },
        {
            "name": "混合特征词文本",
            "text": """这是一个混合了多种特征词的文本。
                    包含促销优惠等广告词，也有色情赌博等敏感词。
                    联系电话：13888888888，添加微信了解更多。
                    这种文本应该被标记为低质量。"""
        },
        {
            "name": "正常文本",
            "text": """这是一篇正常的文本，不包含广告和敏感内容。
                    它讨论了人工智能的发展和应用。
                    随着技术的进步，人工智能已经深入到我们生活的方方面面。
                    从智能手机助手到自动驾驶汽车，从推荐系统到智能家居，人工智能正在改变我们的生活方式。"""
        }
    ]
    
    for case in test_cases:
        name = case["name"]
        text = case["text"]
        
        print(f"测试用例: {name}")
        print(f"原文本预览: {text[:50]}...")
        
        # 特征词检测
        feature_passed, feature_results = filter.feature_detector.filter(text)
        feature_words = feature_results["feature_check"]["details"]["feature_words"]
        feature_score = filter.feature_detector.get_feature_score(text)
        
        print(f"特征词检测: {'通过' if feature_passed else '未通过'}")
        print(f"检测到的特征词: {feature_words}")
        print(f"特征词得分: {feature_score:.4f}")
        
        # 敏感内容过滤
        filtered_text = filter.filter_sensitive_content(text)
        print(f"过滤后文本预览: {filtered_text[:50]}...")
        
        # 对比原文本和过滤后文本
        words_filtered = len(text) - len(filtered_text)
        if words_filtered > 0:
            print(f"过滤了 {words_filtered} 个字符")
        else:
            print("没有内容被过滤")
        
        print("-" * 80)

def test_perplexity():
    """测试困惑度计算功能"""
    # 创建过滤器
    filter = TextQualityFilter()
    
    # 如果困惑度计算器未初始化成功，则跳过测试
    if filter.perplexity_calculator is None:
        print("困惑度计算器未初始化，跳过测试")
        return
    
    # 测试数据
    test_cases = [
        {
            "name": "高质量文本",
            "text": """文本质量过滤是自然语言处理中的重要任务，旨在从大量文本数据中筛选出高质量的内容。
                    高质量的文本通常具有较高的中文比例、适当的符号使用、较低的内部重复率等特点。
                    通过多种过滤方法的组合，可以有效提高语料库的质量，为后续的自然语言处理任务提供更好的基础。"""
        },
        {
            "name": "胡乱拼凑的文本",
            "text": """高质量文本 文本质量 质量高 文本好 好文本 文本质量高 高文本质量 质量文本高 文本高质量
                    质量 高质量 文本 好文本 优质 优质文本 文本优质 优质的文本 文本的优质 优质的文本的优质的文本"""
        },
        {
            "name": "含有大量|符号的垃圾文本",
            "text": """久久久久久日本一区99 | 欧美日韩a∨毛片一区 | 99国产精品视频久久久久 | 国产极品精频在线观看 | 
                    免费亚洲黄色 | 大量真实偷拍情侣视频野战 | 美国毛片一级视频在线aa | 97sese论坛 | 日韩成人小视频 | 
                    国产亚洲精品久久精品6 | 久久男人的天堂 | 中文字幕一区在线播放 | 亚洲午夜久久久久国产 |"""
        }
    ]
    
    # 运行测试
    results = []
    for case in test_cases:
        name = case["name"]
        text = case["text"]
        
        # 计算困惑度
        perplexity = filter.perplexity_calculator.calculate_perplexity(text)
        perplexity_passed, perplexity_details = filter.perplexity_calculator.check_perplexity(text)
        perplexity_score = filter.perplexity_calculator.get_perplexity_score(text)
        
        # 添加到结果
        results.append({
            "name": name,
            "text_preview": text[:50] + "..." if len(text) > 50 else text,
            "perplexity": perplexity,
            "perplexity_passed": perplexity_passed,
            "perplexity_score": perplexity_score
        })
    
    # 打印结果
    print("\n困惑度计算测试结果:")
    print("=" * 80)
    for result in results:
        print(f"测试用例: {result['name']}")
        print(f"文本预览: {result['text_preview']}")
        print(f"困惑度: {result['perplexity']:.2f}")
        print(f"困惑度检查: {'通过' if result['perplexity_passed'] else '未通过'}")
        print(f"困惑度分数: {result['perplexity_score']:.4f}")
        print("-" * 80)

def test_complete_filter():
    """测试完整的过滤流程"""
    # 创建过滤器
    filter = TextQualityFilter()
    
    # 测试数据 - 使用真实数据样例
    test_cases = [
        {
            "name": "正常文本",
            "text": """文本质量过滤是自然语言处理中的重要任务，旨在从大量文本数据中筛选出高质量的内容。
                    高质量的文本通常具有较高的中文比例、适当的符号使用、较低的内部重复率等特点。
                    通过多种过滤方法的组合，可以有效提高语料库的质量，为后续的自然语言处理任务提供更好的基础。
                    本项目实现了一套文本质量过滤系统，集成了基础规则过滤、特征词检测、困惑度计算和文本聚类等功能。"""
        },
        {
            "name": "垃圾网页内容",
            "text": """一级特黄录像绵费播放,亚洲黄色网址大全,在线不卡视频 不卡一区二区在线观看-不卡一区在线观看-不卡一级aaa全黄毛片-不卡一级毛片免费高清-丁香综合-丁香综合激情 首頁 走進珈偉 走進珈偉 珈偉新能是集風·光·儲·充、虛擬電廠、綜合能源管理等數字能源業務與智慧照明業務為一體的綜合性高新技術企業 公司簡介 發展歷程 創新研發 品牌賦能 合作伙伴 解決方案 解決方案 公司提供風·光·儲·充、虛擬電廠、綜合能源管理等數字能源業務解決方案，及景觀照明、智能家居、商業照明等多元化場景照明解決方案"""
        },
        {
            "name": "另一个垃圾网页",
            "text": """深夜大秀直播APP,国产成人精品久久,免费理论电线,一本一道AV无码中文字幕﹣百度 您好，歡進入上海創(chuàng)核儀器科技有限公司網(wǎng)站！ 一鍵分享網(wǎng)站到： 上海創(chuàng)核儀器科技有限公司 MENU 首頁 關于我們 新聞中心 產(chǎn)品展示 技術文章 成功案例 在線留言 聯(lián)系我們 產(chǎn)品目錄 / Product catalog 便攜式輻射檢測設備"""
        },
        {
            "name": "SEO垃圾链接",
            "text": """久久久久久日本一区99 | 欧美日韩a∨毛片一区 | 99国产精品视频久久久久 | 国产极品精频在线观看 | 
                    免费亚洲黄色 | 大量真实偷拍情侣视频野战 | 美国毛片一级视频在线aa | 97sese论坛 | 日韩成人小视频 | 
                    国产亚洲精品久久精品6 | 久久男人的天堂 | 中文字幕一区在线播放 | 亚洲午夜久久久久国产 | 
                    可以免费看黄色的网站 | 亚洲综合色一区二区三区小说 | 青木玲中文字幕一区二区 | 成年大片免费视频播放二级"""
        }
    ]
    
    # 运行测试
    results = []
    for case in test_cases:
        name = case["name"]
        text = case["text"]
        
        # 测试完整过滤
        is_high_quality, complete_results = filter.filter_text(text)
        
        # 添加到结果
        results.append({
            "name": name,
            "text_preview": text[:50] + "..." if len(text) > 50 else text,
            "is_high_quality": is_high_quality,
            "quality_score": complete_results["quality_score"],
            "component_scores": complete_results["component_scores"]
        })
    
    # 打印结果
    print("\n完整过滤测试结果:")
    print("=" * 80)
    for result in results:
        print(f"测试用例: {result['name']}")
        print(f"文本预览: {result['text_preview']}")
        print(f"质量评估: {'高质量' if result['is_high_quality'] else '低质量'}")
        print(f"总质量分数: {result['quality_score']:.4f}")
        print("组件分数:")
        for name, score in result["component_scores"].items():
            print(f"  - {name}: {score:.4f}")
        print("-" * 80)

if __name__ == "__main__":
    print("开始测试文本质量过滤器...")
    
    # 测试基础规则过滤
    test_seo_spam_filter()
    
    # 测试特征词检测和敏感内容过滤
    test_feature_words_and_sensitive_filter()
    
    # 测试困惑度计算
    test_perplexity()
    
    # 测试完整过滤流程
    test_complete_filter()
    
    print("测试完成！") 