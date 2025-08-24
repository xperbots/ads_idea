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
from .openai_service import translate_topics_to_chinese

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
        获取指定国家的热门话题
        
        Args:
            country_code: 国家代码 (VN, TH, SG, MY, ID, PH)
            time_range: 时间范围 (today, week, month)
            top_n: 返回前N个结果
            translate_to_chinese: 是否翻译为中文
        
        Returns:
            Tuple[List[str], str]: (热门话题列表, 错误信息)
        """
        if not self.pytrends:
            return [], "pytrends客户端未初始化"
        
        # 验证参数
        if country_code not in self.SOUTHEAST_ASIA_COUNTRIES:
            return [], f"不支持的国家代码: {country_code}"
        
        if time_range not in self.TIME_RANGES:
            return [], f"不支持的时间范围: {time_range}"
        
        if not (1 <= top_n <= 50):
            return [], "top_n必须在1-50之间"
        
        country_info = self.SOUTHEAST_ASIA_COUNTRIES[country_code]
        
        try:
            # 方法1: 尝试trending_searches (实时热门搜索)
            trending_topics = self._get_trending_searches(country_info['trending_code'])
            
            if trending_topics:
                logger.info(f"成功获取{country_info['name']}的{len(trending_topics)}个热门话题")
                # 限制返回数量
                topics = trending_topics[:top_n]
                
                # 如果需要翻译为中文
                if translate_to_chinese:
                    topics = self._translate_topics_to_chinese(topics)
                
                return topics, ""
            
            # 方法2: 回退到模拟数据
            logger.warning(f"无法获取{country_info['name']}的实时数据，使用模拟数据")
            fallback_topics = self._get_fallback_topics(country_code, top_n)
            
            # 翻译备用数据
            if translate_to_chinese:
                fallback_topics = self._translate_topics_to_chinese(fallback_topics)
            
            return fallback_topics, ""
            
        except Exception as e:
            error_msg = f"获取{country_info['name']}热门话题失败: {str(e)}"
            logger.error(error_msg)
            
            # 提供备用数据
            fallback_topics = self._get_fallback_topics(country_code, top_n)
            
            # 翻译备用数据
            if translate_to_chinese:
                fallback_topics = self._translate_topics_to_chinese(fallback_topics)
            
            return fallback_topics, f"API调用失败，使用备用数据: {str(e)}"
    
    def _get_trending_searches(self, country_trending_code: str) -> List[str]:
        """
        获取trending searches数据
        
        Args:
            country_trending_code: 国家的trending搜索代码
        
        Returns:
            List[str]: 热门话题列表
        """
        try:
            # 尝试不同的国家代码格式
            country_formats = [
                country_trending_code,  # 'vietnam'
                country_trending_code.upper(),  # 'VIETNAM'
                country_trending_code[:2].upper()  # 'VN'
            ]
            
            for country_format in country_formats:
                try:
                    # 尝试trending_searches方法
                    df = self.pytrends.trending_searches(pn=country_format)
                    if df is not None and not df.empty:
                        # 返回搜索词列表
                        topics = df[0].tolist() if hasattr(df, 'tolist') else df.values.flatten().tolist()
                        return [str(topic).strip() for topic in topics if str(topic).strip()]
                except Exception as e:
                    logger.debug(f"尝试国家格式 {country_format} 失败: {e}")
                    continue
                
                # 添加请求间隔避免被限制
                time.sleep(0.5)
            
            # 如果trending_searches失败，尝试realtime_trending_searches
            try:
                df = self.pytrends.realtime_trending_searches(pn=country_trending_code[:2].upper())
                if df is not None and not df.empty:
                    topics = df[0].tolist() if hasattr(df, 'tolist') else df.values.flatten().tolist()
                    return [str(topic).strip() for topic in topics if str(topic).strip()]
            except Exception as e:
                logger.debug(f"realtime_trending_searches失败: {e}")
            
            return []
            
        except Exception as e:
            logger.error(f"获取trending searches失败: {e}")
            return []
    
    def _get_fallback_topics(self, country_code: str, top_n: int) -> List[str]:
        """
        获取备用热门话题数据
        
        Args:
            country_code: 国家代码
            top_n: 返回数量
        
        Returns:
            List[str]: 备用热门话题列表
        """
        # 各国备用热门话题数据
        fallback_data = {
            'VN': [
                "Tết Nguyên Đán", "Du lịch Việt Nam", "Ẩm thực truyền thống", 
                "Thời trang", "Công nghệ", "Giáo dục", "Sức khỏe", 
                "Làm đẹp", "Mua sắm online", "Game mobile", "K-pop", 
                "Phim Việt", "Bóng đá", "Crypto", "Bất động sản"
            ],
            'TH': [
                "สงกรานต์", "อาหารไทย", "ท่องเที่ยว", "แฟชั่น", 
                "เทคโนโลยี", "การศึกษา", "สุขภาพ", "ความงาม", 
                "ช้อปปิ้งออนไลน์", "เกมมือถือ", "K-pop", "ละครไทย", 
                "ฟุตบอล", "คริปโตเคอร์เรนซี", "อสังหาริมทรัพย์"
            ],
            'SG': [
                "Singapore Food", "Travel Singapore", "Fashion", "Technology", 
                "Education", "Health", "Beauty", "Online Shopping", 
                "Mobile Games", "K-pop", "Singapore Drama", "Football", 
                "Cryptocurrency", "Real Estate", "Hawker Centers"
            ],
            'MY': [
                "Malaysian Food", "Travel Malaysia", "Fashion", "Technology", 
                "Education", "Health", "Beauty", "Online Shopping", 
                "Mobile Games", "K-pop", "Malaysian Drama", "Football", 
                "Cryptocurrency", "Property", "Raya Celebration"
            ],
            'ID': [
                "Makanan Indonesia", "Wisata Indonesia", "Fashion", "Teknologi", 
                "Pendidikan", "Kesehatan", "Kecantikan", "Belanja Online", 
                "Game Mobile", "K-pop", "Drama Indonesia", "Sepak Bola", 
                "Cryptocurrency", "Properti", "Lebaran"
            ],
            'PH': [
                "Filipino Food", "Travel Philippines", "Fashion", "Technology", 
                "Education", "Health", "Beauty", "Online Shopping", 
                "Mobile Games", "K-pop", "Filipino Drama", "Basketball", 
                "Cryptocurrency", "Real Estate", "Christmas"
            ]
        }
        
        topics = fallback_data.get(country_code, fallback_data['VN'])
        return topics[:top_n]
    
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
    
    def _translate_topics_to_chinese(self, topics: List[str]) -> List[str]:
        """
        使用OpenAI API将话题翻译为中文
        
        Args:
            topics: 话题列表
        
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
            
            # 调用OpenAI翻译服务
            translation_result = translate_topics_to_chinese(
                topics=needs_translation,
                model='gpt-5-nano'
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
    API接口函数：获取热门话题
    
    Args:
        country_code: 国家代码
        time_range: 时间范围  
        top_n: 返回数量
        translate_to_chinese: 是否翻译为中文
    
    Returns:
        dict: API响应格式
    """
    try:
        topics, error = trends_service.get_trending_topics(
            country_code=country_code,
            time_range=time_range,
            top_n=top_n,
            translate_to_chinese=translate_to_chinese
        )
        
        if error:
            return {
                'success': False,
                'message': error,
                'data': topics,  # 返回备用数据
                'fallback': True,
                'translated': translate_to_chinese
            }
        
        return {
            'success': True,
            'message': f'成功获取{trends_service.SOUTHEAST_ASIA_COUNTRIES[country_code]["name"]}热门话题',
            'data': topics,
            'fallback': False,
            'translated': translate_to_chinese,
            'country': trends_service.SOUTHEAST_ASIA_COUNTRIES[country_code]['name'],
            'time_range': trends_service.TIME_RANGES[time_range]['name'],
            'count': len(topics)
        }
        
    except Exception as e:
        logger.error(f"get_trending_topics_api error: {e}")
        # 返回备用数据
        fallback_topics = trends_service._get_fallback_topics(country_code, top_n)
        
        # 如果需要翻译备用数据
        if translate_to_chinese:
            try:
                fallback_topics = trends_service._translate_topics_to_chinese(fallback_topics)
            except Exception as trans_e:
                logger.error(f"备用数据翻译失败: {trans_e}")
        
        return {
            'success': False,
            'message': f'API调用失败: {str(e)}',
            'data': fallback_topics,
            'fallback': True,
            'translated': translate_to_chinese
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