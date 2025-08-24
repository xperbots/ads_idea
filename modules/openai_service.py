"""
OpenAI LLM 服务模块
提供通用的 OpenAI API 调用功能，支持多种模型和任务
"""

import os
import logging
import json
from typing import List, Dict, Optional, Union, Any
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
env_path = os.path.join(project_dir, '.env')
load_dotenv(env_path)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI LLM服务类"""
    
    # 支持的模型配置
    MODELS = {
        'gpt-5-nano': {
            'name': 'GPT-5 Nano',
            'max_tokens': 128000,
            'cost_per_1k_input': 0.05,
            'cost_per_1k_output': 0.40,
            'best_for': ['翻译', '轻量级任务', '快速响应'],
            'reasoning_effort': ['minimal', 'low']
        },
        'gpt-5-mini': {
            'name': 'GPT-5 Mini',
            'max_tokens': 128000,
            'cost_per_1k_input': 0.25,
            'cost_per_1k_output': 2.0,
            'best_for': ['复杂推理', '创意生成', '深度分析'],
            'reasoning_effort': ['minimal', 'low', 'medium']
        },
        'gpt-5': {
            'name': 'GPT-5',
            'max_tokens': 128000,
            'cost_per_1k_input': 1.25,
            'cost_per_1k_output': 10.0,
            'best_for': ['最复杂任务', '高质量内容', '专业分析'],
            'reasoning_effort': ['minimal', 'low', 'medium', 'high']
        },
        'gpt-4o-mini': {
            'name': 'GPT-4o Mini (备用)',
            'max_tokens': 128000,
            'cost_per_1k_input': 0.00015,
            'cost_per_1k_output': 0.0006,
            'best_for': ['备用翻译', '轻量级任务']
        },
        'gpt-4o': {
            'name': 'GPT-4o (备用)',
            'max_tokens': 128000,
            'cost_per_1k_input': 0.005,
            'cost_per_1k_output': 0.015,
            'best_for': ['备用复杂任务', '创意生成']
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化OpenAI服务
        
        Args:
            api_key: OpenAI API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        if not self.api_key:
            logger.error("OpenAI API Key未找到，请在.env文件中设置OPENAI_API_KEY")
            return
        
        try:
            # 2025年标准初始化方式
            self.client = OpenAI(
                api_key=self.api_key,
                max_retries=3,
                timeout=30.0
            )
            logger.info("OpenAI客户端初始化成功 (v1.101+)")
                
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查OpenAI服务是否可用"""
        return self.client is not None
    
    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: str = 'gpt-5-nano',
                       max_tokens: Optional[int] = None,
                       temperature: float = 0.7,
                       response_format: Optional[Dict] = None,
                       reasoning_effort: str = 'low') -> Dict[str, Any]:
        """
        通用的聊天完成API调用
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            max_tokens: 最大令牌数
            temperature: 温度参数 (0-2)
            response_format: 响应格式 (如: {"type": "json_object"})
        
        Returns:
            Dict: API响应结果
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'OpenAI服务不可用，请检查API Key配置',
                'content': None
            }
        
        if model not in self.MODELS:
            return {
                'success': False,
                'error': f'不支持的模型: {model}，支持的模型: {list(self.MODELS.keys())}',
                'content': None
            }
        
        try:
            # 构建请求参数
            request_params = {
                'model': model,
                'messages': messages
            }
            
            # GPT-5系列不支持自定义temperature，只支持默认值1
            if not model.startswith('gpt-5'):
                request_params['temperature'] = temperature
            
            if max_tokens:
                # GPT-5系列使用max_completion_tokens，其他模型使用max_tokens
                if model.startswith('gpt-5'):
                    request_params['max_completion_tokens'] = max_tokens
                else:
                    request_params['max_tokens'] = max_tokens
                
            if response_format:
                request_params['response_format'] = response_format
            
            # GPT-5系列支持reasoning_effort参数
            if model.startswith('gpt-5') and reasoning_effort:
                model_config = self.MODELS.get(model, {})
                supported_efforts = model_config.get('reasoning_effort', [])
                if reasoning_effort in supported_efforts:
                    request_params['reasoning_effort'] = reasoning_effort
            
            # 调用API
            response = self.client.chat.completions.create(**request_params)
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'model_used': model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def translate_to_chinese(self, 
                           texts: Union[str, List[str]], 
                           model: str = 'gpt-5-nano',
                           preserve_context: bool = True,
                           source_language: str = 'English',
                           country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        将文本翻译为中文
        
        Args:
            texts: 要翻译的文本或文本列表
            model: 使用的模型
            preserve_context: 是否保持语境(广告/营销相关)
            source_language: 源语言（如：'Tiếng Việt', 'ภaษาไทย', 'English'等）
            country_code: 国家代码，用于自动识别源语言
        
        Returns:
            Dict: 翻译结果
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return {'success': True, 'translations': []}
        
        # 国家代码到本地语言名称的映射
        local_language_map = {
            'VN': 'Tiếng Việt',
            'TH': 'ภาษาไทย', 
            'SG': 'English',
            'MY': 'English',
            'ID': 'Bahasa Indonesia',
            'PH': 'English'
        }
        
        # 根据国家代码确定源语言
        if country_code and country_code in local_language_map:
            detected_language = local_language_map[country_code]
        else:
            detected_language = source_language
        
        texts_str = '\n'.join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        messages = [
            {
                "role": "system", 
                "content": f"You are an expert linguist, specializing in translation from {detected_language} to 简体中文. translate directly without explanation"
            },
            {
                "role": "user",
                "content": f"请翻译以下{len(texts)}个热门话题：\n\n{texts_str}"
            }
        ]
        
        result = self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=1000,
            temperature=0.3,  # 较低温度确保翻译一致性
            reasoning_effort='minimal'  # 翻译任务使用最小推理
        )
        
        if result['success']:
            # 解析翻译结果 - 更健壮的处理
            raw_content = result['content'].strip()
            translations = []
            
            # 按行分割并清理
            lines = raw_content.split('\n')
            for line in lines:
                cleaned_line = line.strip()
                # 移除可能的编号前缀（如"1. ", "- ", "• "等）
                cleaned_line = cleaned_line.lstrip('0123456789.- •\t')
                if cleaned_line:
                    translations.append(cleaned_line)
            
            # 确保翻译数量匹配
            if len(translations) != len(texts):
                logger.warning(f"批量翻译数量不匹配: 原文{len(texts)}个，译文{len(translations)}个")
                logger.debug(f"原文: {texts}")
                logger.debug(f"译文: {translations}")
                
                # 智能修复：补齐或截取
                if len(translations) < len(texts):
                    # 补齐缺失的翻译（使用原文）
                    missing_count = len(texts) - len(translations)
                    logger.warning(f"补齐{missing_count}个缺失的翻译")
                    for i in range(missing_count):
                        idx = len(translations) + i
                        if idx < len(texts):
                            translations.append(texts[idx])
                else:
                    # 截取多余的翻译
                    translations = translations[:len(texts)]
                    logger.warning(f"截取到{len(texts)}个翻译结果")
            
            logger.info(f"✅ 批量翻译成功: {len(texts)}个话题 -> {len(translations)}个中文结果")
            
            return {
                'success': True,
                'translations': translations,
                'original_texts': texts,
                'model_used': result['model_used'],
                'usage': result['usage'],
                'batch_size': len(texts)
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'translations': texts,  # 返回原文作为备用
                'fallback': True
            }
    
    def generate_creative_content(self,
                                prompt: str,
                                style: str = "professional",
                                model: str = 'gpt-5-mini',
                                max_tokens: int = 1000) -> Dict[str, Any]:
        """
        生成创意内容
        
        Args:
            prompt: 创意提示
            style: 风格 (professional, casual, creative, etc.)
            model: 使用的模型
            max_tokens: 最大令牌数
        
        Returns:
            Dict: 生成结果
        """
        style_prompts = {
            'professional': '请用专业、正式的语调',
            'casual': '请用轻松、亲切的语调',
            'creative': '请用富有创意、想象力的语调',
            'persuasive': '请用有说服力、吸引人的语调'
        }
        
        style_instruction = style_prompts.get(style, style_prompts['professional'])
        
        messages = [
            {
                "role": "system",
                "content": f"""你是专业的广告创意专家。{style_instruction}生成内容。
                
要求：
1. 内容要有吸引力和创意性
2. 适合目标受众
3. 符合广告营销规范
4. 语言简洁有力"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        return self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=0.8,  # 较高温度增加创意性
            reasoning_effort='medium'  # 创意任务使用中等推理
        )
    
    def analyze_content(self,
                       content: str,
                       analysis_type: str = "sentiment",
                       model: str = 'gpt-5-mini') -> Dict[str, Any]:
        """
        内容分析功能
        
        Args:
            content: 要分析的内容
            analysis_type: 分析类型 (sentiment, keywords, topics, quality)
            model: 使用的模型
        
        Returns:
            Dict: 分析结果
        """
        analysis_prompts = {
            'sentiment': '分析这段内容的情感倾向（正面/负面/中性）',
            'keywords': '提取这段内容的关键词',
            'topics': '识别这段内容的主要话题',
            'quality': '评估这段内容作为广告创意的质量'
        }
        
        analysis_instruction = analysis_prompts.get(analysis_type, analysis_prompts['sentiment'])
        
        messages = [
            {
                "role": "system",
                "content": f"""你是专业的内容分析专家。请{analysis_instruction}。
                
请以JSON格式返回结果，包含：
- analysis_type: 分析类型
- result: 分析结果
- confidence: 置信度(0-1)
- explanation: 分析说明"""
            },
            {
                "role": "user",
                "content": f"请分析以下内容：\n\n{content}"
            }
        ]
        
        return self.chat_completion(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
            temperature=0.1,  # 较低温度确保分析准确性
            reasoning_effort='medium'  # 分析任务使用中等推理
        )
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """获取模型信息"""
        return self.MODELS.get(model_name)
    
    def list_available_models(self) -> Dict[str, Dict]:
        """列出所有可用模型"""
        return self.MODELS

# 创建全局实例
openai_service = OpenAIService()

def translate_topics_to_chinese(topics: List[str], model: str = 'gpt-5-nano') -> Dict[str, Any]:
    """
    API接口函数：翻译话题为中文
    
    Args:
        topics: 话题列表
        model: 使用的模型
    
    Returns:
        dict: 翻译结果
    """
    try:
        result = openai_service.translate_to_chinese(
            texts=topics,
            model=model,
            preserve_context=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"translate_topics_to_chinese error: {e}")
        return {
            'success': False,
            'error': str(e),
            'translations': topics,  # 返回原文
            'fallback': True
        }

def generate_creative_with_ai(prompt: str, 
                            style: str = "professional",
                            model: str = 'gpt-5-mini') -> Dict[str, Any]:
    """
    API接口函数：生成创意内容
    
    Args:
        prompt: 创意提示
        style: 风格
        model: 使用的模型
    
    Returns:
        dict: 生成结果
    """
    try:
        result = openai_service.generate_creative_content(
            prompt=prompt,
            style=style,
            model=model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"generate_creative_with_ai error: {e}")
        return {
            'success': False,
            'error': str(e),
            'content': None
        }

def test_openai_service() -> Dict[str, Any]:
    """测试OpenAI服务状态"""
    try:
        if not openai_service.is_available():
            return {
                'success': False,
                'message': 'OpenAI服务不可用，请检查API Key配置'
            }
        
        # 进行简单的测试调用
        test_result = openai_service.translate_to_chinese(
            texts=["Hello World"],
            model='gpt-5-nano'
        )
        
        if test_result['success']:
            return {
                'success': True,
                'message': 'OpenAI服务正常',
                'test_translation': test_result['translations'][0]
            }
        else:
            return {
                'success': False,
                'message': f'OpenAI服务测试失败: {test_result["error"]}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'OpenAI服务测试异常: {str(e)}'
        }