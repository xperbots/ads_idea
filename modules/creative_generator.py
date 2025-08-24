import random
import json
from datetime import datetime
from typing import List, Dict, Any, Set
from models import Creative, CreativeDimension, CreativeOption, db

class CreativeGenerator:
    """
    多维度可配置创意生成器
    支持6个核心维度的组合生成
    """
    
    def __init__(self):
        # 初始化时检查并创建默认维度配置
        self._ensure_default_dimensions()
    
    def _ensure_default_dimensions(self):
        """确保数据库中有默认的维度配置"""
        dimensions_data = {
            'emotion_motivation': {
                'display_name': '情绪/动机',
                'description': '情感驱动和用户动机层面的创意角度',
                'options': {
                    '胜利瞬间': {
                        'description': '凯旋/王冠/光锥奖章定格；低角度+对角动势',
                        'keywords': ['胜利', '王冠', '奖章', '凯旋', '荣耀'],
                        'visual_hints': ['低角度拍摄', '对角构图', '金色光效', '定格瞬间'],
                        'templates': [
                            '在{game}中获得{achievement}！{call_to_action}',
                            '成为{game}世界的{title}，体验胜利荣耀！'
                        ]
                    },
                    '成长蜕变': {
                        'description': '前后对照（新手→英雄），高对比色',
                        'keywords': ['成长', '蜕变', '进化', '升级', '突破'],
                        'visual_hints': ['前后对比', '高对比色', '进阶效果', '变化过程'],
                        'templates': [
                            '从{start_state}到{end_state}，见证你的成长！',
                            '每一次升级都是蜕变，{game}助你成为英雄！'
                        ]
                    },
                    '稀缺限时': {
                        'description': '倒计时徽章+限定配色；强中心视觉',
                        'keywords': ['限时', '稀缺', '独家', '倒计时', '限量'],
                        'visual_hints': ['倒计时元素', '限定配色', '中心构图', '紧迫感设计'],
                        'templates': [
                            '限时{time}！{item}即将绝版！',
                            '稀缺机会，错过再等{time}！'
                        ]
                    },
                    '归属团队': {
                        'description': '阵营旗帜/徽记拼阵；群像金字塔',
                        'keywords': ['团队', '公会', '联盟', '伙伴', '协作'],
                        'visual_hints': ['团队构图', '金字塔排列', '旗帜元素', '群像展示'],
                        'templates': [
                            '加入{guild}，与伙伴并肩作战！',
                            '团结就是力量，{game}等你来战！'
                        ]
                    },
                    '美学沉浸': {
                        'description': '史诗天空/体积光/雾；大留白渲染气场',
                        'keywords': ['美学', '沉浸', '氛围', '艺术', '诗意'],
                        'visual_hints': ['史诗天空', '体积光', '雾气效果', '大留白设计'],
                        'templates': [
                            '沉浸在{world}的美学世界中',
                            '艺术级画面，诗意般体验'
                        ]
                    }
                }
            },
            'value_proof': {
                'display_name': '价值证明',
                'description': '产品价值和可信度证明',
                'options': {
                    '三硬核卖点': {
                        'description': '三枚"能力徽章"（如清晰/流畅/适配）',
                        'keywords': ['性能', '清晰', '流畅', '稳定', '优化'],
                        'visual_hints': ['徽章设计', '三重展示', '技术指标', '性能标识'],
                        'templates': [
                            '三大核心优势：{feature1}+{feature2}+{feature3}',
                            '顶级{tech}技术，给你最佳体验！'
                        ]
                    },
                    '社证口碑': {
                        'description': '评分星+热评摘句（真实/可溯源）',
                        'keywords': ['评价', '口碑', '推荐', '好评', '用户'],
                        'visual_hints': ['星级评分', '用户评论', '社交证明', '推荐展示'],
                        'templates': [
                            '{star}星好评！{review_count}万用户推荐',
                            '用户都说好："{review_text}"'
                        ]
                    },
                    '权威背书': {
                        'description': '获奖/媒体 Logo 墙（依法务规范）',
                        'keywords': ['获奖', '权威', '认证', '媒体', '专业'],
                        'visual_hints': ['奖项展示', 'Logo墙', '认证标识', '权威背景'],
                        'templates': [
                            '荣获{award}，权威认证品质！',
                            '{media}强力推荐，品质保证！'
                        ]
                    },
                    '对比替代': {
                        'description': '一图说服（竞对/旧方案→本方案）',
                        'keywords': ['对比', '升级', '更好', '超越', '替代'],
                        'visual_hints': ['对比图表', '升级箭头', '优势展示', 'VS布局'],
                        'templates': [
                            '告别{old_way}，拥抱{new_way}！',
                            '比{competitor}更{advantage}的选择！'
                        ]
                    },
                    '零门槛': {
                        'description': '免费下载/新手礼包/返利角贴（图标化）',
                        'keywords': ['免费', '礼包', '新手', '福利', '零成本'],
                        'visual_hints': ['免费标识', '礼包图标', '福利角贴', '零门槛设计'],
                        'templates': [
                            '完全免费！新手礼包等你来拿！',
                            '零成本体验，{benefit}免费送！'
                        ]
                    }
                }
            },
            'visual_hook': {
                'display_name': '视觉钩子',
                'description': '吸引眼球的视觉表现手法',
                'options': {
                    '极近特写': {
                        'description': '眼神/武器纹理/装备材质微距',
                        'keywords': ['细节', '纹理', '特写', '质感', '微距'],
                        'visual_hints': ['特写镜头', '细节展示', '材质质感', '微距效果'],
                        'templates': [
                            '每个细节都精雕细琢，感受{item}的质感！',
                            '极致细节，{feature}尽在掌握！'
                        ]
                    },
                    '夸张透视': {
                        'description': '武器破画框+速度线',
                        'keywords': ['动感', '冲击', '破框', '速度', '力量'],
                        'visual_hints': ['破框效果', '速度线', '夸张透视', '冲击力设计'],
                        'templates': [
                            '破框而出的{weapon}，震撼登场！',
                            '超越边界，感受{power}的冲击！'
                        ]
                    },
                    '强互补色': {
                        'description': '品牌主色×互补撞色',
                        'keywords': ['撞色', '对比', '鲜明', '视觉', '冲击'],
                        'visual_hints': ['互补色搭配', '强烈对比', '撞色设计', '视觉冲击'],
                        'templates': [
                            '鲜明撞色，{brand}独特视觉体验！',
                            '色彩碰撞，创造视觉奇迹！'
                        ]
                    },
                    '图形构图': {
                        'description': '环形/三角/对角线引导',
                        'keywords': ['构图', '几何', '引导', '焦点', '平衡'],
                        'visual_hints': ['几何构图', '视线引导', '焦点设计', '平衡美学'],
                        'templates': [
                            '完美构图，聚焦{focus}！',
                            '几何美学，{game}的艺术之美！'
                        ]
                    },
                    '超现实反转': {
                        'description': '上下颠倒/镜面世界/反向光影',
                        'keywords': ['超现实', '颠倒', '镜面', '奇幻', '反转'],
                        'visual_hints': ['颠倒效果', '镜面世界', '反转设计', '超现实风格'],
                        'templates': [
                            '颠倒世界，发现{game}的奇幻！',
                            '镜面反转，体验不一样的{experience}！'
                        ]
                    }
                }
            },
            'benefit_narrative': {
                'display_name': '利益主叙事',
                'description': '核心利益点的叙事表达',
                'options': {
                    '一步到位': {
                        'description': '一键完成感的视觉隐喻（不谈操作）',
                        'keywords': ['简单', '一键', '便捷', '高效', '自动'],
                        'visual_hints': ['一键按钮', '简化流程', '高效标识', '便捷操作'],
                        'templates': [
                            '一键{action}，简单高效！',
                            '告别复杂操作，{game}让一切变简单！'
                        ]
                    },
                    '场景适配': {
                        'description': '地铁/夜灯/户外强光下也清晰可见',
                        'keywords': ['适配', '清晰', '任何场景', '随时随地', '灵活'],
                        'visual_hints': ['多场景展示', '清晰标识', '适配性强调', '场景切换'],
                        'templates': [
                            '无论{scene}，{game}都清晰流畅！',
                            '随时随地，完美适配你的生活！'
                        ]
                    },
                    '个性外观': {
                        'description': '皮肤/装扮/家园九宫格',
                        'keywords': ['个性', '定制', '皮肤', '装扮', '独特'],
                        'visual_hints': ['九宫格展示', '个性化元素', '定制选项', '外观变化'],
                        'templates': [
                            '{count}种{item}，打造专属{character}！',
                            '个性定制，展现独特的你！'
                        ]
                    },
                    '资源获取感': {
                        'description': '掉落雨/宝箱/稀有度边框',
                        'keywords': ['掉落', '奖励', '宝箱', '收获', '丰富'],
                        'visual_hints': ['掉落效果', '宝箱开启', '稀有边框', '奖励雨'],
                        'templates': [
                            '丰富{reward}掉落不停，收获满满！',
                            '开启{chest}，发现惊喜奖励！'
                        ]
                    },
                    '掌控策略感': {
                        'description': '上帝视角路径高亮/指挥手势剪影',
                        'keywords': ['策略', '掌控', '指挥', '全局', '智慧'],
                        'visual_hints': ['上帝视角', '路径高亮', '指挥手势', '策略图'],
                        'templates': [
                            '运筹帷幄，掌控{battlefield}！',
                            '策略制胜，{game}考验你的智慧！'
                        ]
                    }
                }
            },
            'event_seasonal': {
                'display_name': '事件/时令',
                'description': '时效性和事件性的创意角度',
                'options': {
                    '节日限定': {
                        'description': '中秋/万圣/圣诞主题配色+剪影',
                        'keywords': ['节日', '限定', '庆祝', '主题', '特别'],
                        'visual_hints': ['节日配色', '主题剪影', '庆祝元素', '限定设计'],
                        'templates': [
                            '{festival}特别版，限时体验！',
                            '节日狂欢，{game}陪你庆祝{holiday}！'
                        ]
                    },
                    '赛季更迭': {
                        'description': '世界变化前后景对照（不谈数值）',
                        'keywords': ['赛季', '更新', '变化', '新版本', '进化'],
                        'visual_hints': ['前后对比', '世界变化', '版本更新', '季节转换'],
                        'templates': [
                            '新赛季来临，{world}大变样！',
                            '版本更新，体验全新{content}！'
                        ]
                    },
                    '周年纪念': {
                        'description': '时间回顾拼贴（Logo年轮）',
                        'keywords': ['周年', '纪念', '历史', '经典', '里程碑'],
                        'visual_hints': ['年轮设计', '时间轴', '历史回顾', '纪念标识'],
                        'templates': [
                            '{years}年历程，感谢有你！',
                            '周年庆典，{game}与你共同成长！'
                        ]
                    },
                    '联动视觉': {
                        'description': '仅授权的"世界相遇"符号化元素',
                        'keywords': ['联动', '合作', '跨界', '相遇', '特别'],
                        'visual_hints': ['联动标识', '双品牌元素', '合作符号', '跨界设计'],
                        'templates': [
                            '{brand1}×{brand2}，史诗联动！',
                            '两个世界的相遇，{game}特别合作！'
                        ]
                    },
                    '地区化': {
                        'description': '在地节庆/色彩/符号（合规本地化）',
                        'keywords': ['本地', '地区', '文化', '符号', '特色'],
                        'visual_hints': ['地域色彩', '文化符号', '本地元素', '区域特色'],
                        'templates': [
                            '融入{region}文化，{game}更懂你！',
                            '本地化体验，感受{culture}魅力！'
                        ]
                    }
                }
            },
            'light_entertainment': {
                'display_name': '轻娱乐/梗化',
                'description': '轻松娱乐和网络梗文化',
                'options': {
                    '表情包化': {
                        'description': '夸张表情+大字报金句',
                        'keywords': ['表情包', '夸张', '搞笑', '梗', '有趣'],
                        'visual_hints': ['夸张表情', '大字体', '表情包风格', '幽默元素'],
                        'templates': [
                            '{expression}！{game}就是这么{adjective}！',
                            '这表情，玩{game}的都懂！'
                        ]
                    },
                    '三格剧照': {
                        'description': '前–中–后的连环画式',
                        'keywords': ['连环画', '剧情', '故事', '过程', '变化'],
                        'visual_hints': ['三格布局', '连环画风', '故事线', '时间推进'],
                        'templates': [
                            '三步走：{step1}→{step2}→{step3}',
                            '看图说话：{game}的精彩时刻！'
                        ]
                    },
                    '谐音押韵': {
                        'description': '地区化短句+配色（谨慎使用）',
                        'keywords': ['谐音', '押韵', '朗朗上口', '记忆点', '传播'],
                        'visual_hints': ['韵律感设计', '文字游戏', '音韵配色', '朗朗上口'],
                        'templates': [
                            '{rhyme1}，{rhyme2}，{game}真{rhyme3}！',
                            '{wordplay}，玩{game}就对了！'
                        ]
                    },
                    '手作纸艺': {
                        'description': '低饱和+颗粒营造亲近感',
                        'keywords': ['手作', '温暖', '亲切', '质朴', '自然'],
                        'visual_hints': ['纸艺质感', '低饱和度', '颗粒效果', '手工感'],
                        'templates': [
                            '手作质感，{game}的温暖陪伴',
                            '简单美好，{game}如纸艺般精致'
                        ]
                    },
                    '信息图式': {
                        'description': '极简图标+线框，像"说明书"',
                        'keywords': ['简洁', '图标', '说明', '清晰', '直观'],
                        'visual_hints': ['极简设计', '线框图标', '说明书风格', '信息图表'],
                        'templates': [
                            '{game}使用说明：{instruction}',
                            '一图看懂{game}的{feature}!'
                        ]
                    }
                }
            }
        }
        
        # 检查并创建维度配置
        for dimension_name, dimension_info in dimensions_data.items():
            dimension = CreativeDimension.query.filter_by(name=dimension_name).first()
            if not dimension:
                dimension = CreativeDimension(
                    name=dimension_name,
                    display_name=dimension_info['display_name'],
                    description=dimension_info['description'],
                    sort_order=list(dimensions_data.keys()).index(dimension_name)
                )
                db.session.add(dimension)
                db.session.flush()  # 获取ID
                
                # 添加选项
                for i, (option_name, option_info) in enumerate(dimension_info['options'].items()):
                    option = CreativeOption(
                        dimension_id=dimension.id,
                        name=option_name,
                        description=option_info['description'],
                        keywords=json.dumps(option_info['keywords'], ensure_ascii=False),
                        visual_hints=json.dumps(option_info['visual_hints'], ensure_ascii=False),
                        templates=json.dumps(option_info['templates'], ensure_ascii=False),
                        sort_order=i
                    )
                    db.session.add(option)
        
        db.session.commit()
    
    def get_dimensions_config(self) -> List[Dict[str, Any]]:
        """获取所有维度配置"""
        dimensions = CreativeDimension.query.filter_by(is_active=True).order_by(CreativeDimension.sort_order).all()
        return [dim.to_dict() for dim in dimensions]
    
    def generate_creatives(self, selected_dimensions: Dict[str, List[int]], count: int = 20) -> List[Dict[str, Any]]:
        """
        根据选中的维度生成创意
        selected_dimensions: {dimension_name: [option_id1, option_id2, ...]}
        """
        creatives = []
        generation_params = {
            'selected_dimensions': selected_dimensions,
            'count': count,
            'timestamp': datetime.now().isoformat()
        }
        
        # 获取选中的选项
        selected_options = self._get_selected_options(selected_dimensions)
        
        # 生成创意
        for i in range(count):
            creative = self._generate_single_creative(selected_options)
            creative['generation_params'] = generation_params
            creative['index'] = i + 1
            creative['selected_dimensions'] = selected_dimensions
            creatives.append(creative)
        
        return creatives
    
    def _get_selected_options(self, selected_dimensions: Dict[str, List[int]]) -> Dict[str, List[CreativeOption]]:
        """获取选中的选项对象"""
        result = {}
        
        for dimension_name, option_ids in selected_dimensions.items():
            if option_ids:  # 如果有选中的选项
                options = CreativeOption.query.filter(
                    CreativeOption.id.in_(option_ids),
                    CreativeOption.is_active == True
                ).all()
                result[dimension_name] = options
        
        return result
    
    def _generate_single_creative(self, selected_options: Dict[str, List[CreativeOption]]) -> Dict[str, Any]:
        """生成单个创意"""
        # 随机选择维度组合
        chosen_dimensions = random.sample(list(selected_options.keys()), 
                                        min(len(selected_options), random.randint(2, 4)))
        
        # 从每个选中的维度中随机选择选项
        chosen_options = []
        dimension_details = {}
        
        for dimension_name in chosen_dimensions:
            if selected_options[dimension_name]:
                option = random.choice(selected_options[dimension_name])
                chosen_options.append(option)
                dimension_details[dimension_name] = option.to_dict()
        
        # 构建创意内容
        content = self._build_creative_content(chosen_options)
        title = self._build_creative_title(content, chosen_options)
        
        return {
            'title': title,
            'content': content,
            'chosen_dimensions': chosen_dimensions,
            'dimension_details': dimension_details,
            'keywords': self._extract_keywords(chosen_options),
            'visual_hints': self._extract_visual_hints(chosen_options)
        }
    
    def _build_creative_content(self, options: List[CreativeOption]) -> str:
        """构建创意内容"""
        # 选择一个主模板
        main_option = random.choice(options)
        templates = json.loads(main_option.templates) if main_option.templates else []
        
        if templates:
            template = random.choice(templates)
            # 从其他选项中提取关键词来填充模板
            keywords = {}
            for option in options:
                option_keywords = json.loads(option.keywords) if option.keywords else []
                keywords.update({
                    'game': '这款游戏',
                    'achievement': random.choice(['王者荣耀', '传奇成就', '巅峰体验']),
                    'call_to_action': random.choice(['立即体验', '马上下载', '加入战斗']),
                    'feature': random.choice(option_keywords[:2]) if option_keywords else '精彩内容',
                    'world': random.choice(['游戏世界', '奇幻大陆', '冒险之地']),
                    'item': random.choice(option_keywords) if option_keywords else '神秘道具',
                    'power': random.choice(['力量', '技能', '能力']),
                    'experience': random.choice(['体验', '冒险', '旅程'])
                })
            
            try:
                content = template.format(**keywords)
            except KeyError:
                # 如果模板变量不匹配，使用备用方案
                content = f"体验{main_option.name}的魅力，感受{random.choice(['精彩', '刺激', '震撼'])}瞬间！"
        else:
            # 如果没有模板，基于选项名称组合
            option_names = [opt.name for opt in options]
            content = f"融合{'/'.join(option_names[:2])}，带来全新体验！"
        
        return content
    
    def _build_creative_title(self, content: str, options: List[CreativeOption]) -> str:
        """构建创意标题"""
        # 提取内容前20个字符作为标题
        title = content[:20] + '...' if len(content) > 20 else content
        return title
    
    def _extract_keywords(self, options: List[CreativeOption]) -> List[str]:
        """提取关键词"""
        keywords = []
        for option in options:
            option_keywords = json.loads(option.keywords) if option.keywords else []
            keywords.extend(option_keywords)
        return list(set(keywords))  # 去重
    
    def _extract_visual_hints(self, options: List[CreativeOption]) -> List[str]:
        """提取视觉提示"""
        hints = []
        for option in options:
            option_hints = json.loads(option.visual_hints) if option.visual_hints else []
            hints.extend(option_hints)
        return list(set(hints))  # 去重
    
    def save_creatives_to_db(self, creatives_data: List[Dict[str, Any]]) -> List[Creative]:
        """将生成的创意保存到数据库"""
        saved_creatives = []
        
        for creative_data in creatives_data:
            creative = Creative(
                title=creative_data['title'],
                content=creative_data['content'],
                selected_dimensions=json.dumps(creative_data.get('selected_dimensions', {}), ensure_ascii=False),
                status='generated',
                generation_params=json.dumps(creative_data.get('generation_params', {}), ensure_ascii=False)
            )
            
            db.session.add(creative)
            saved_creatives.append(creative)
        
        db.session.commit()
        return saved_creatives
    
    def update_dimension_config(self, dimension_id: int, **kwargs) -> bool:
        """更新维度配置"""
        dimension = CreativeDimension.query.get(dimension_id)
        if not dimension:
            return False
        
        for key, value in kwargs.items():
            if hasattr(dimension, key):
                setattr(dimension, key, value)
        
        dimension.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def add_dimension_option(self, dimension_id: int, name: str, description: str = '', 
                           keywords: List[str] = None, visual_hints: List[str] = None,
                           templates: List[str] = None) -> CreativeOption:
        """添加维度选项"""
        option = CreativeOption(
            dimension_id=dimension_id,
            name=name,
            description=description,
            keywords=json.dumps(keywords or [], ensure_ascii=False),
            visual_hints=json.dumps(visual_hints or [], ensure_ascii=False),
            templates=json.dumps(templates or [], ensure_ascii=False),
            sort_order=CreativeOption.query.filter_by(dimension_id=dimension_id).count()
        )
        
        db.session.add(option)
        db.session.commit()
        return option