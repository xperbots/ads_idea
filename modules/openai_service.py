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
            'reasoning_effort': ['minimal', 'low'],
            'text_verbosity': ['low', 'medium'],  # 添加text verbosity支持
            'status': 'stable',  # 使用正确的API后应该稳定
            'fallback': 'gpt-4o-mini'
        },
        'gpt-5-mini': {
            'name': 'GPT-5 Mini', 
            'max_tokens': 128000,
            'cost_per_1k_input': 0.25,
            'cost_per_1k_output': 2.0,
            'best_for': ['复杂推理', '创意生成', '深度分析'],
            'reasoning_effort': ['minimal', 'low', 'medium'],
            'text_verbosity': ['low', 'medium', 'high'],  # 添加text verbosity支持
            'status': 'stable',  # 使用正确的API后应该稳定
            'fallback': 'gpt-4o'
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
            # 2025年标准初始化方式 - 增强重试和超时配置
            from openai import OpenAI
            import httpx
            
            # 创建自定义HTTP客户端，增强连接配置
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),  # 总超时60s，连接超时10s
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
                # 注意: httpx不支持retries参数，重试由OpenAI客户端处理
            )
            
            self.client = OpenAI(
                api_key=self.api_key,
                max_retries=5,  # 增加到5次重试
                timeout=60.0,   # 增加总超时时间
                http_client=http_client
            )
            logger.info("OpenAI客户端初始化成功 (v1.101+) - 增强重试配置")
                
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
            
            # GPT-5系列不支持temperature参数
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
            return self._handle_api_error(e, model, request_params)
    
    def _handle_api_error(self, e: Exception, model: str, request_params: dict) -> Dict[str, Any]:
        """统一处理API错误"""
        error_type = type(e).__name__
        error_message = str(e)
        
        # 记录详细的错误信息
        logger.error(f"OpenAI API调用失败 - 错误类型: {error_type}")
        logger.error(f"错误详情: {error_message}")
        logger.error(f"使用模型: {model}")
        
        # 分类错误并提供解决方案
        if 'Connection' in error_message or 'connection' in error_message.lower():
            detailed_error = f"网络连接错误: {error_message}. 请检查网络连接和OpenAI API服务状态"
            retry_suggested = True
        elif 'timeout' in error_message.lower() or 'timed out' in error_message.lower():
            detailed_error = f"请求超时: {error_message}. 请稍后重试或减少请求复杂度"
            retry_suggested = True
        elif 'API key' in error_message or 'Unauthorized' in error_message:
            detailed_error = f"API密钥错误: {error_message}. 请检查OPENAI_API_KEY配置"
            retry_suggested = False
        elif 'Rate limit' in error_message or 'rate_limit' in error_message.lower():
            detailed_error = f"API调用频率限制: {error_message}. 请稍后重试"
            retry_suggested = True
        elif 'model' in error_message.lower():
            detailed_error = f"模型错误: {error_message}. 模型'{model}'可能不可用"
            retry_suggested = False
        elif 'overloaded' in error_message.lower() or 'capacity' in error_message.lower():
            detailed_error = f"服务过载: {error_message}. OpenAI服务当前繁忙，请稍后重试"
            retry_suggested = True
        else:
            detailed_error = f"未知错误: {error_message}"
            retry_suggested = True
        
        logger.error(f"详细错误说明: {detailed_error}")
        if retry_suggested:
            logger.info("💡 建议: 可以重试此请求")
        
        # 记录请求参数（用于调试）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"失败的请求参数: {json.dumps(request_params, ensure_ascii=False, indent=2)}")
        
        return {
            'success': False,
            'error': detailed_error,
            'error_type': error_type,
            'original_error': error_message,
            'retry_suggested': retry_suggested,
            'content': None
        }
    
    def gpt5_responses_create(self,
                            input_text: str,
                            model: str = 'gpt-5-nano',
                            instructions: str = None,
                            reasoning_effort: str = 'low') -> Dict[str, Any]:
        """
        使用正确的GPT-5 responses.create API格式
        基于OpenAI官方cookbook示例
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'OpenAI服务不可用，请检查API Key配置',
                'content': None
            }
        
        try:
            # 构建GPT-5请求参数 - 基于成功的测试代码
            request_params = {
                'model': model,
                'input': input_text
            }
            
            # 添加推理努力参数 - 使用正确的格式
            if reasoning_effort in ['minimal', 'low', 'medium', 'high']:
                request_params['reasoning'] = {'effort': reasoning_effort}
            else:
                # 默认使用minimal以提高响应速度
                request_params['reasoning'] = {'effort': 'minimal'}
            
            # 添加text参数 - 使用推荐的medium模式
            request_params['text'] = {'verbosity': 'medium'}
            
            # 添加指令参数
            if instructions:
                request_params['instructions'] = instructions
            
            logger.info(f"🎯 GPT-5 API调用: {model}, reasoning_effort={reasoning_effort}")
            
            # 调用GPT-5专用API
            response = self.client.responses.create(**request_params)
            
            # 基于成功测试代码的响应解析逻辑
            output_texts = []
            if hasattr(response, 'output') and response.output:
                for message in response.output:
                    if hasattr(message, 'content') and message.content:
                        for content_item in message.content:
                            if hasattr(content_item, 'text') and content_item.text:
                                output_texts.append(content_item.text)
            
            # 合并所有文本内容
            content = '\n'.join(output_texts) if output_texts else None
            
            # 详细日志记录响应内容
            logger.info(f"🔍 GPT-5响应解析详情: {model}")
            logger.info(f"   找到的文本段数: {len(output_texts)}")
            logger.info(f"   响应内容长度: {len(content) if content else 0}字符")
            if content:
                logger.info(f"   响应内容预览: {content[:200]}...")
            else:
                logger.warning(f"   ⚠️ 响应内容为空!")
                # 尝试输出原始响应结构用于调试
                logger.info(f"   原始响应结构: {type(response)}")
                if hasattr(response, 'output'):
                    logger.info(f"   response.output类型: {type(response.output)}")
                    logger.info(f"   response.output长度: {len(response.output) if response.output else 0}")
            
            if not content:
                logger.warning(f"⚠️ GPT-5响应为空: {model}")
                return {
                    'success': False,
                    'error': 'GPT-5返回空响应',
                    'content': None
                }
            
            return {
                'success': True,
                'content': content,
                'model_used': model,
                'usage': getattr(response, 'usage', {})
            }
            
        except Exception as e:
            return self._handle_api_error(e, model, request_params)
    
    def chat_completion_with_retry(self,
                                 messages: List[Dict[str, str]],
                                 model: str = 'gpt-5-nano',
                                 max_tokens: Optional[int] = None,
                                 temperature: float = 0.7,
                                 response_format: Optional[Dict] = None,
                                 reasoning_effort: str = 'low',
                                 max_manual_retries: int = 2) -> Dict[str, Any]:
        """
        带手动重试逻辑的chat_completion
        在OpenAI客户端重试失败后，进行应用层重试
        """
        import time
        
        last_error = None
        retry_delays = [1, 2, 4]  # 指数退避：1秒, 2秒, 4秒
        
        for attempt in range(max_manual_retries + 1):
            try:
                if attempt > 0:
                    delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
                    logger.info(f"🔄 第 {attempt + 1} 次重试，等待 {delay} 秒...")
                    time.sleep(delay)
                
                result = self.chat_completion(
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format=response_format,
                    reasoning_effort=reasoning_effort
                )
                
                if result['success']:
                    if attempt > 0:
                        logger.info(f"✅ 重试成功！第 {attempt + 1} 次尝试")
                    return result
                else:
                    last_error = result
                    # 检查是否建议重试
                    if not result.get('retry_suggested', True):
                        logger.warning("❌ 错误不建议重试，停止重试")
                        break
                    
            except Exception as e:
                last_error = {
                    'success': False,
                    'error': f"重试过程中异常: {str(e)}",
                    'error_type': type(e).__name__,
                    'original_error': str(e),
                    'content': None
                }
        
        logger.error(f"❌ 所有重试尝试都失败了 (共 {max_manual_retries + 1} 次)")
        return last_error or {
            'success': False,
            'error': '未知的重试失败',
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
        
        # 对于GPT-5模型，使用优化的responses.create方法
        if model.startswith('gpt-5'):
            # 构建GPT-5格式的翻译prompt
            gpt5_prompt = f"""请翻译以下{len(texts)}个热门话题为准确的简体中文：

{texts_str}

请确保翻译准确、自然，符合中文表达习惯。"""
            
            result_gpt5 = self.gpt5_responses_create(
                input_text=gpt5_prompt,
                model=model,
                instructions=f"你是专业的语言学家，擅长从{detected_language}翻译到简体中文。请直接翻译，无需解释。",
                reasoning_effort='minimal'  # 翻译任务使用最小推理
            )
            
            if result_gpt5['success']:
                result = result_gpt5
            else:
                # GPT-5失败时降级到GPT-4o
                logger.warning(f"GPT-5翻译失败，降级到备用模型")
                result = self.chat_completion(
                    messages=messages,
                    model='gpt-4o-mini',
                    max_tokens=1000,
                    temperature=0.3,
                    reasoning_effort='minimal'
                )
        else:
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
                                prompt_data: Dict[str, Any] = None,
                                prompt: str = None,
                                style: str = "professional",
                                model: str = 'gpt-5-mini',
                                max_tokens: int = 4000) -> str:
        """
        生成创意内容，支持结构化的JSON prompt和传统文本prompt
        
        Args:
            prompt_data: 结构化的JSON prompt数据
            prompt: 传统文本提示（与prompt_data二选一）
            style: 风格 (professional, casual, creative, etc.)
            model: 使用的模型
            max_tokens: 最大令牌数
        
        Returns:
            str: 生成的创意内容（JSON字符串格式）
        """
        if prompt_data:
            # 使用优化的JSON prompt - 遵循OpenAI最佳实践
            
            # 提取和简化数据，设置默认值
            user_idea = prompt_data.get("user_input", {}).get("idea", "")
            custom_inputs = prompt_data.get("user_input", {}).get("custom_inputs", {})
            selected_dimensions = prompt_data.get("selected_dimensions", {})
            count = prompt_data.get("requirements", {}).get("count", 5)
            
            # 从UI获取或设置默认值 - 改为可选字段
            target_region = custom_inputs.get("target_region", "").strip()
            game_style = custom_inputs.get("game_style", "").strip()
            age_group = custom_inputs.get("age_group", "").strip()
            
            # 处理空值情况
            if not user_idea.strip():
                user_idea = "一款具有创新玩法的移动游戏"
            
            # 如果没有指定地区，使用默认
            if not target_region:
                target_region = "越南"  # 保留地区作为必需字段
            
            # 构建简化的维度信息
            dimension_summary = []
            for dim_name, options in selected_dimensions.items():
                if options:  # 只包含有选项的维度
                    option_names = [opt.get("name", "") for opt in options]
                    dimension_summary.append(f"{dim_name}: {', '.join(option_names)}")
            
            messages = [
                {
                    "role": "system",
                    "content": """你是专业的游戏广告图片创意专家。请根据用户的游戏背景生成丰富详细的静态图片广告创意描述。

创作要求：
- 每个创意都要有独特性和创新性
- 提供详细丰富的视觉描述，包括具体的场景、人物、动作、情感等
- 镜头和光线描述要专业，包括拍摄角度、光线类型、构图方式等
- 色彩和道具描述要具体，包括色彩搭配、材质质感、道具细节等
- 确保内容适合越南市场的文化和审美偏好
- 每个创意都要能够让AI图像生成工具准确理解并生成高质量图片

技术要求：
- 必须返回有效的JSON格式
- 严禁在画面中出现任何文字、Logo、字幕与标识

JSON格式：
{
  "creatives": [
    {
      "core_concept": "核心概念",
      "scene_description": "建议图片的画面描述",
      "camera_lighting": "镜头/光线处理",
      "color_props": "色彩与道具等细节",
      "key_notes": "关键注意事项（统一强调：画面中严禁出现任何文字、Logo、字幕与标识）"
    }
  ]
}"""
                },
                {
                    "role": "user", 
                    "content": f"""请生成{count}组在越南落地的{user_idea}静态图片广告创意。每组都包含：核心概念、建议图片的画面、镜头/光线处理、色彩与道具等细节，便于AI生成图片、关键注意事项（统一强调：画面中严禁出现任何文字、Logo、字幕与标识）。

用户游戏背景：{user_idea}

请基于以上信息生成{count}组不同的图片创意描述，确保每组都有独特性和视觉吸引力，符合越南市场特点。"""
                }
            ]
            
            # 详细日志打印 - 运行时检查用
            logger.info("="*80)
            logger.info("🎨 图片创意生成 - 完整Prompt内容")
            logger.info("="*80)
            logger.info("📋 输入参数:")
            logger.info(f"   用户想法: {user_idea}")
            logger.info(f"   目标地区: {target_region}")
            logger.info(f"   游戏风格: {game_style}")
            logger.info(f"   目标年龄: {age_group}")
            logger.info(f"   生成数量: {count}")
            logger.info(f"   使用模型: {model}")
            logger.info(f"   选择维度: {len(selected_dimensions)}个维度，{sum(len(opts) for opts in selected_dimensions.values())}个选项")
            
            logger.info("\n📨 System Message:")
            logger.info("-" * 60)
            logger.info(messages[0]['content'])
            
            logger.info("\n📨 User Message:")
            logger.info("-" * 60)
            logger.info(messages[1]['content'])
            
        else:
            # 使用传统文本prompt
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
4. 语言具有吸引力和感染力"""
                },
                {
                    "role": "user",
                    "content": prompt or "请生成一些创意内容"
                }
            ]
        
        # 动态计算max_tokens - 根据生成数量和prompt类型调整
        if prompt_data:
            # 图片创意生成需要更多tokens
            estimated_tokens_per_creative = 200  # 每个创意大约200 tokens
            base_tokens = 500  # 基础overhead
            dynamic_max_tokens = base_tokens + (count * estimated_tokens_per_creative)
            # 确保在模型限制内，最少2000，最多8000
            dynamic_max_tokens = min(max(dynamic_max_tokens, 2000), 8000)
            actual_max_tokens = dynamic_max_tokens
        else:
            actual_max_tokens = max_tokens
            
        logger.info(f"🎯 Token配置: 生成{count if prompt_data else '?'}个创意，使用{actual_max_tokens} max_tokens")
        
        # 显示最终API调用参数
        logger.info("\n🎯 最终API调用参数:")
        logger.info(f"   model: {model}")
        logger.info(f"   max_tokens: {actual_max_tokens}")
        logger.info(f"   temperature: 0.8") 
        logger.info(f"   response_format: {'json_object' if prompt_data else 'text'}")
        logger.info(f"   reasoning_effort: medium")
        logger.info("="*80)
        
        # 智能模型选择和自动降级
        result = self._generate_with_model_fallback(
            messages=messages,
            model=model,
            max_tokens=actual_max_tokens,
            prompt_data=prompt_data,
            reasoning_effort='medium'
        )
        
        if result['success']:
            return result['content']
        else:
            error_details = {
                'error': result.get('error', '未知错误'),
                'error_type': result.get('error_type', 'Unknown'),
                'original_error': result.get('original_error', ''),
                'model': model,
                'prompt_size': len(str(prompt_data)) if prompt_data else len(prompt or '')
            }
            
            # 记录创意生成特定的错误信息
            logger.error(f"创意生成失败 - 模型: {model}")
            logger.error(f"错误类型: {error_details['error_type']}")
            logger.error(f"详细错误: {error_details['error']}")
            
            raise Exception(f"AI创意生成失败 [{error_details['error_type']}]: {error_details['error']}")
    
    def _generate_with_model_fallback(self,
                                    messages: List[Dict[str, str]],
                                    model: str,
                                    max_tokens: int,
                                    prompt_data: Dict = None,
                                    reasoning_effort: str = 'medium') -> Dict[str, Any]:
        """
        带自动降级的创意生成
        GPT-5 -> GPT-4o 自动切换
        """
        # 首先尝试原始模型
        if model.startswith('gpt-5'):
            logger.info(f"🎯 尝试使用GPT-5模型: {model}")
            
            # 对于GPT-5，尝试使用正确的responses.create格式
            try:
                # 将messages转换为单个prompt
                if prompt_data:
                    # 使用结构化prompt
                    user_idea = prompt_data.get("user_input", {}).get("idea", "游戏创意")
                    custom_inputs = prompt_data.get("user_input", {}).get("custom_inputs", {})
                    selected_dimensions = prompt_data.get("selected_dimensions", {})
                    count = prompt_data.get("requirements", {}).get("count", 5)
                    target_region = custom_inputs.get("target_region", "越南")
                    
                    # 构建维度信息
                    dimension_summary = []
                    for dim_name, options in selected_dimensions.items():
                        if options:
                            option_names = [opt.get("name", "") for opt in options]
                            dimension_summary.append(f"{dim_name}: {', '.join(option_names)}")
                    
                    # GPT-5格式详细创意生成prompt
                    gpt5_prompt = f"""请生成{count}组在越南落地的{user_idea}静态图片广告创意。每组创意都需要包含丰富详细的内容：

• 核心概念：创意的核心思想和卖点
• 建议图片的画面：详细的视觉描述，包括场景、人物、物品等
• 镜头/光线处理：拍摄角度、光线设置、构图等专业细节
• 色彩与道具等细节：具体的色彩搭配、道具选择、材质质感等
• 关键注意事项：重要提醒（统一强调：画面中严禁出现任何文字、Logo、字幕与标识）

用户游戏背景：{user_idea}

请确保每个创意都有独特性和丰富的细节，让AI图片生成工具能够准确理解并生成高质量的广告图片。

请严格按照以下JSON格式返回：
{{
  "creatives": [
    {{
      "core_concept": "核心概念",
      "scene_description": "建议图片的画面描述",
      "camera_lighting": "镜头/光线处理",
      "color_props": "色彩与道具等细节",
      "key_notes": "关键注意事项（统一强调：画面中严禁出现任何文字、Logo、字幕与标识）"
    }}
  ]
}}"""
                else:
                    # 使用传统prompt - 也需要优化
                    original_prompt = messages[1]['content'] if len(messages) > 1 else messages[0]['content']
                    gpt5_prompt = f"请详细完成以下创意生成任务：\n\n{original_prompt}\n\n请确保每个创意都包含丰富的细节和独特性，帮助生成高质量的广告内容。"
                
                # 尝试GPT-5 responses.create - 使用minimal reasoning确保快速响应
                gpt5_result = self.gpt5_responses_create(
                    input_text=gpt5_prompt,
                    model=model,
                    instructions="你是专业的游戏广告图片创意专家。请生成内容丰富、细节详尽的创意描述，确保每个创意都有独特性和专业性。严格按照要求输出有效的JSON格式。",
                    reasoning_effort='minimal'  # 创意生成使用minimal以加快速度
                )
                
                if gpt5_result['success'] and gpt5_result['content'] and gpt5_result['content'].strip():
                    logger.info(f"✅ GPT-5模型成功: {model}")
                    logger.info(f"📄 GPT-5返回内容长度: {len(gpt5_result['content'])}字符")
                    logger.info(f"📄 GPT-5返回内容预览: {gpt5_result['content'][:300]}...")
                    return gpt5_result
                else:
                    logger.warning(f"⚠️  GPT-5模型返回空内容: {model}")
                    if gpt5_result.get('content'):
                        logger.warning(f"    内容长度: {len(gpt5_result['content'])}字符")
                        logger.warning(f"    内容预览: '{gpt5_result['content'][:100]}'")
                    
            except Exception as e:
                logger.warning(f"⚠️  GPT-5模型调用失败: {e}")
            
            # GPT-5失败，自动降级到GPT-4o
            fallback_model = self.MODELS[model].get('fallback', 'gpt-4o-mini')
            logger.info(f"🔄 自动降级到备用模型: {fallback_model}")
        else:
            fallback_model = model
        
        # 使用GPT-4o系列模型（传统chat.completions格式）
        logger.info(f"🎯 使用传统chat.completions格式: {fallback_model}")
        
        result = self.chat_completion_with_retry(
            messages=messages,
            model=fallback_model,
            max_tokens=max_tokens,
            temperature=0.8,
            response_format={"type": "json_object"} if prompt_data else None,
            max_manual_retries=2
        )
        
        if result['success']:
            result['model_used'] = f"{fallback_model} (fallback from {model})" if model.startswith('gpt-5') else fallback_model
            logger.info(f"✅ 备用模型成功: {result['model_used']}")
        
        return result
    
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