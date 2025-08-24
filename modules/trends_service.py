"""
Google Trends热门话题服务
支持东南亚国家的热门搜索话题获取
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from pytrends.request import TrendReq
from .openai_service import translate_topics_to_chinese, openai_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendsService:
    """Google Trends API服务类"""
    
    # 东南亚国家配置
    SOUTHEAST_ASIA_COUNTRIES = {
        'VN': {'name': '越南', 'code': 'VN', 'trending_code': 'vietnam'},
        'TH': {'name': '泰国', 'code': 'TH', 'trending_code': 'thailand'},
        'SG': {'name': '新加坡', 'code': 'SG', 'trending_code': 'singapore'},
        'MY': {'name': '马来西亚', 'code': 'MY', 'trending_code': 'malaysia'},
        'ID': {'name': '印尼', 'code': 'ID', 'trending_code': 'indonesia'},
        'PH': {'name': '菲律宾', 'code': 'PH', 'trending_code': 'philippines'}
    }
    
    # 时间范围配置
    TIME_RANGES = {
        'today': {'name': '今日', 'timeframe': 'now 1-d'},
        'week': {'name': '本周', 'timeframe': 'now 7-d'},
        'month': {'name': '本月', 'timeframe': 'today 1-m'}
    }
    
    def __init__(self):
        """初始化Trends服务"""
        self.pytrends = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化pytrends客户端"""
        try:
            # 使用更简单的初始化参数，避免兼容性问题
            self.pytrends = TrendReq(
                hl='en-US',  # 语言设置
                tz=360       # 时区设置 (越南时区)
            )
            logger.info("pytrends客户端初始化成功")
        except Exception as e:
            logger.error(f"pytrends客户端初始化失败: {e}")
            self.pytrends = None
    
    def get_trending_topics(self, 
                          country_code: str = 'VN', 
                          time_range: str = 'week',
                          top_n: int = 10,
                          translate_to_chinese: bool = True) -> Tuple[List[str], str]:
        """
        获取指定国家的热门话题（只返回真实数据，不使用模拟数据）
        
        Args:
            country_code: 国家代码 (VN, TH, SG, MY, ID, PH)
            time_range: 时间范围 (today, week, month)
            top_n: 返回前N个结果
            translate_to_chinese: 是否翻译为中文
        
        Returns:
            Tuple[List[str], str]: (热门话题列表, 错误信息)
        """
        if not self.pytrends:
            return [], "Google Trends服务未初始化，请检查网络连接"
        
        # 验证参数
        if country_code not in self.SOUTHEAST_ASIA_COUNTRIES:
            return [], f"不支持的国家代码: {country_code}，支持的国家: {', '.join(self.SOUTHEAST_ASIA_COUNTRIES.keys())}"
        
        if time_range not in self.TIME_RANGES:
            return [], f"不支持的时间范围: {time_range}，支持的范围: {', '.join(self.TIME_RANGES.keys())}"
        
        if not (1 <= top_n <= 50):
            return [], "请求数量必须在1-50之间"
        
        country_info = self.SOUTHEAST_ASIA_COUNTRIES[country_code]
        
        try:
            # 尝试获取真实的热门话题数据
            logger.info(f"开始获取{country_info['name']}的热门话题...")
            trending_topics = self._get_trending_searches(country_code, max_retries=2)
            
            if trending_topics and len(trending_topics) > 0:
                logger.info(f"✅ 成功获取{country_info['name']}的{len(trending_topics)}个真实热门话题")
                
                # 限制返回数量并去重
                unique_topics = list(dict.fromkeys(trending_topics))  # 保持顺序的去重
                topics = unique_topics[:top_n]
                
                # 如果需要翻译为中文
                if translate_to_chinese:
                    topics = self._translate_topics_to_chinese(topics, country_code)
                
                return topics, ""
            else:
                # 无法获取真实数据，返回错误信息
                error_msg = f"❌ 无法获取{country_info['name']}的实时热门话题数据。这可能由于以下原因：\n" + \
                           f"• Google Trends API限制或变更\n" + \
                           f"• 网络连接问题\n" + \
                           f"• 该地区暂时没有足够的搜索数据\n" + \
                           f"\n建议：稍后重试或选择其他国家"
                logger.error(error_msg)
                return [], error_msg
            
        except Exception as e:
            error_msg = f"❌ 获取{country_info['name']}热门话题时发生错误：{str(e)}\n" + \
                       f"\n可能的解决方案：\n" + \
                       f"• 检查网络连接\n" + \
                       f"• 稍后重试\n" + \
                       f"• 联系技术支持"
            logger.error(error_msg)
            return [], error_msg
    
    def _get_trending_searches(self, country_code: str, max_retries: int = 2) -> List[str]:
        """
        获取trending searches数据（使用可行的pytrends方法）
        
        Args:
            country_code: 国家代码 (如: VN, TH, SG)
            max_retries: 最大重试次数
        
        Returns:
            List[str]: 热门话题列表，如果获取失败则返回空列表
        """
        
        # 方法1: 尝试基于热门关键词的相关话题搜索
        popular_seeds = {
            'VN': ['Vietnam', 'game', 'mobile', 'technology', 'food'],
            'TH': ['Thailand', 'game', 'mobile', 'technology', 'food'], 
            'SG': ['Singapore', 'game', 'mobile', 'technology', 'food'],
            'MY': ['Malaysia', 'game', 'mobile', 'technology', 'food'],
            'ID': ['Indonesia', 'game', 'mobile', 'technology', 'food'],
            'PH': ['Philippines', 'game', 'mobile', 'technology', 'food']
        }
        
        seed_keywords = popular_seeds.get(country_code, ['game', 'mobile', 'technology'])
        all_topics = set()
        
        for retry in range(max_retries):
            try:
                logger.info(f"尝试获取{country_code}的热门话题 (第{retry + 1}次)")
                
                # 对每个种子关键词获取相关话题
                for seed in seed_keywords:
                    try:
                        # 构建查询
                        self.pytrends.build_payload(
                            kw_list=[seed],
                            cat=0,
                            timeframe='now 7-d',
                            geo=country_code,
                            gprop=''
                        )
                        
                        # 获取相关查询
                        related_queries = self.pytrends.related_queries()
                        
                        if seed in related_queries:
                            # 获取上升查询（更能反映当前热门趋势）
                            if related_queries[seed]['rising'] is not None:
                                rising_queries = related_queries[seed]['rising']['query'].tolist()
                                all_topics.update(rising_queries[:3])  # 取前3个
                            
                            # 获取热门查询作为备用
                            if related_queries[seed]['top'] is not None and len(all_topics) < 5:
                                top_queries = related_queries[seed]['top']['query'].tolist()
                                all_topics.update(top_queries[:2])  # 取前2个
                        
                        time.sleep(1)  # 避免请求过快
                        
                    except Exception as e:
                        logger.debug(f"处理种子关键词 {seed} 失败: {e}")
                        continue
                
                # 如果获取到足够的话题，返回结果
                if len(all_topics) >= 3:
                    topics_list = list(all_topics)[:10]  # 最多返回10个
                    logger.info(f"成功获取到{len(topics_list)}个相关热门话题")
                    return topics_list
                
                # 如果话题不够，继续重试
                if retry < max_retries - 1:
                    logger.warning(f"第{retry + 1}次尝试获取话题数量不足({len(all_topics)}个)，等待后重试")
                    time.sleep(3)
                    
            except Exception as e:
                logger.error(f"第{retry + 1}次尝试获取热门话题失败: {e}")
                if retry < max_retries - 1:
                    time.sleep(5)  # 重试前等待
        
        # 所有尝试都失败了
        logger.error(f"经过{max_retries}次尝试，仍无法获取{country_code}的真实热门话题数据")
        return []
    
    def _analyze_search_interest(self, country_code: str, keywords: List[str]) -> List[str]:
        """
        分析指定关键词的搜索趋势，用于补充热门话题
        
        Args:
            country_code: 国家代码
            keywords: 关键词列表
        
        Returns:
            List[str]: 有搜索热度的关键词列表
        """
        trending_keywords = []
        
        try:
            # 构建查询获取搜索趋势
            self.pytrends.build_payload(
                kw_list=keywords[:5],  # 最多5个关键词
                cat=0,
                timeframe='now 7-d',
                geo=country_code,
                gprop=''
            )
            
            # 获取搜索兴趣数据
            interest_df = self.pytrends.interest_over_time()
            
            if not interest_df.empty:
                # 计算平均搜索兴趣并排序
                avg_interest = interest_df.drop('isPartial', axis=1).mean().sort_values(ascending=False)
                
                # 只返回有一定搜索量的关键词（>10）
                for keyword, score in avg_interest.items():
                    if score > 10:
                        trending_keywords.append(keyword)
                        
            return trending_keywords
            
        except Exception as e:
            logger.debug(f"分析搜索兴趣失败: {e}")
            return []
    
    def get_available_countries(self) -> Dict[str, Dict]:
        """
        获取支持的国家列表
        
        Returns:
            Dict: 国家信息字典
        """
        return self.SOUTHEAST_ASIA_COUNTRIES
    
    def get_available_time_ranges(self) -> Dict[str, Dict]:
        """
        获取支持的时间范围列表
        
        Returns:
            Dict: 时间范围信息字典
        """
        return self.TIME_RANGES
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试pytrends连接状态
        
        Returns:
            Tuple[bool, str]: (是否成功, 状态信息)
        """
        if not self.pytrends:
            return False, "pytrends客户端未初始化"
        
        try:
            # 尝试获取美国热门搜索作为连接测试
            df = self.pytrends.trending_searches(pn='united_states')
            if df is not None and not df.empty:
                return True, "连接正常"
            else:
                return False, "无法获取测试数据"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def get_trending_keywords_for_topic(self, 
                                      topic: str, 
                                      country_code: str = 'VN',
                                      time_range: str = 'week') -> List[str]:
        """
        获取特定话题的相关关键词趋势
        
        Args:
            topic: 话题关键词
            country_code: 国家代码
            time_range: 时间范围
        
        Returns:
            List[str]: 相关关键词列表
        """
        if not self.pytrends:
            return []
        
        try:
            country_geo = self.SOUTHEAST_ASIA_COUNTRIES[country_code]['code']
            timeframe = self.TIME_RANGES[time_range]['timeframe']
            
            # 构建查询
            self.pytrends.build_payload(
                kw_list=[topic],
                cat=0,
                timeframe=timeframe,
                geo=country_geo,
                gprop=''
            )
            
            # 获取相关查询
            related_queries = self.pytrends.related_queries()
            
            if topic in related_queries and related_queries[topic]['top'] is not None:
                queries_df = related_queries[topic]['top']
                return queries_df['query'].head(10).tolist()
            
            return []
            
        except Exception as e:
            logger.error(f"获取相关关键词失败: {e}")
            return []
    
    def _translate_topics_to_chinese(self, topics: List[str], country_code: str = 'VN') -> List[str]:
        """
        使用OpenAI API将话题翻译为中文
        
        Args:
            topics: 话题列表
            country_code: 国家代码，用于识别源语言
        
        Returns:
            List[str]: 翻译后的中文话题列表
        """
        if not topics:
            return topics
        
        # 检查是否需要翻译（如果已经是中文则跳过）
        needs_translation = []
        chinese_topics = []
        
        for topic in topics:
            # 简单检测：如果包含中文字符则认为不需要翻译
            if any('\u4e00' <= char <= '\u9fff' for char in topic):
                chinese_topics.append(topic)
            else:
                needs_translation.append(topic)
                chinese_topics.append(topic)  # 临时占位
        
        # 如果没有需要翻译的内容，直接返回
        if not needs_translation:
            logger.info("所有话题已是中文，无需翻译")
            return topics
        
        try:
            logger.info(f"正在翻译{len(needs_translation)}个话题为中文...")
            
            # 调用OpenAI翻译服务，传入country_code用于识别源语言
            translation_result = openai_service.translate_to_chinese(
                texts=needs_translation,
                model='gpt-5-nano',
                preserve_context=True,
                country_code=country_code
            )
            
            if translation_result['success']:
                translated_topics = translation_result['translations']
                
                # 将翻译结果替换回原位置
                translation_index = 0
                final_topics = []
                
                for original_topic in topics:
                    if any('\u4e00' <= char <= '\u9fff' for char in original_topic):
                        # 已是中文，保持原样
                        final_topics.append(original_topic)
                    else:
                        # 使用翻译结果
                        if translation_index < len(translated_topics):
                            final_topics.append(translated_topics[translation_index])
                            translation_index += 1
                        else:
                            final_topics.append(original_topic)  # 备用
                
                logger.info(f"成功翻译{len(translated_topics)}个话题为中文")
                return final_topics
            else:
                logger.warning(f"翻译失败: {translation_result.get('error')}")
                return topics  # 返回原文
                
        except Exception as e:
            logger.error(f"翻译过程出错: {e}")
            return topics  # 返回原文

    def _is_chinese_text(self, text: str) -> bool:
        """
        检测文本是否为中文
        
        Args:
            text: 检测的文本
        
        Returns:
            bool: 是否为中文
        """
        if not text:
            return False
        
        # 计算中文字符比例
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.replace(' ', ''))  # 不计算空格
        
        if total_chars == 0:
            return False
        
        chinese_ratio = chinese_chars / total_chars
        return chinese_ratio > 0.3  # 如果中文字符超过30%则认为是中文

# 创建全局实例
trends_service = TrendsService()

def get_trending_topics_api(country_code='VN', time_range='week', top_n=10, translate_to_chinese=True):
    """
    API接口函数：获取热门话题（仅返回真实数据）
    
    Args:
        country_code: 国家代码
        time_range: 时间范围  
        top_n: 返回数量
        translate_to_chinese: 是否翻译为中文
    
    Returns:
        dict: API响应格式
    """
    try:
        topics, error_message = trends_service.get_trending_topics(
            country_code=country_code,
            time_range=time_range,
            top_n=top_n,
            translate_to_chinese=translate_to_chinese
        )
        
        # 如果有错误信息，说明获取失败
        if error_message:
            return {
                'success': False,
                'message': error_message,
                'data': [],
                'error_type': 'data_unavailable',
                'country': trends_service.SOUTHEAST_ASIA_COUNTRIES.get(country_code, {}).get('name', country_code),
                'time_range': trends_service.TIME_RANGES.get(time_range, {}).get('name', time_range),
                'requested_count': top_n,
                'actual_count': 0,
                'translated': translate_to_chinese,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'suggestion': '请稍后重试，或尝试选择其他国家/地区'
            }
        
        # 成功获取到真实数据
        return {
            'success': True,
            'message': f'✅ 成功获取{trends_service.SOUTHEAST_ASIA_COUNTRIES[country_code]["name"]}的实时热门话题',
            'data': topics,
            'error_type': None,
            'country': trends_service.SOUTHEAST_ASIA_COUNTRIES[country_code]['name'],
            'time_range': trends_service.TIME_RANGES[time_range]['name'],
            'requested_count': top_n,
            'actual_count': len(topics),
            'translated': translate_to_chinese,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'real_time_google_trends'
        }
        
    except Exception as e:
        logger.error(f"get_trending_topics_api系统错误: {e}")
        
        return {
            'success': False,
            'message': f'❌ 系统错误：{str(e)}',
            'data': [],
            'error_type': 'system_error',
            'country': trends_service.SOUTHEAST_ASIA_COUNTRIES.get(country_code, {}).get('name', country_code),
            'time_range': trends_service.TIME_RANGES.get(time_range, {}).get('name', time_range),
            'requested_count': top_n,
            'actual_count': 0,
            'translated': translate_to_chinese,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'suggestion': '请检查网络连接或联系技术支持'
        }

def get_countries_list():
    """获取支持的国家列表"""
    return {
        'success': True,
        'data': trends_service.get_available_countries()
    }

def get_time_ranges_list():
    """获取支持的时间范围列表"""
    return {
        'success': True,
        'data': trends_service.get_available_time_ranges()
    }

def test_trends_service():
    """测试trends服务状态"""
    success, message = trends_service.test_connection()
    return {
        'success': success,
        'message': message
    }