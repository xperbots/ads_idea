from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class CreativeDimension(db.Model):
    """创意维度配置表"""
    __tablename__ = 'creative_dimensions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 维度名称
    display_name = db.Column(db.String(100), nullable=False)  # 显示名称
    description = db.Column(db.Text)  # 维度描述
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'options': [opt.to_dict() for opt in self.options]
        }

class CreativeOption(db.Model):
    """创意选项配置表"""
    __tablename__ = 'creative_options'
    
    id = db.Column(db.Integer, primary_key=True)
    dimension_id = db.Column(db.Integer, db.ForeignKey('creative_dimensions.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 选项名称
    description = db.Column(db.Text)  # 选项描述
    keywords = db.Column(db.Text)  # 关键词，JSON格式
    visual_hints = db.Column(db.Text)  # 视觉提示，JSON格式
    templates = db.Column(db.Text)  # 模板，JSON格式
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    dimension = db.relationship('CreativeDimension', backref='options')
    
    def to_dict(self):
        return {
            'id': self.id,
            'dimension_id': self.dimension_id,
            'name': self.name,
            'description': self.description,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'visual_hints': json.loads(self.visual_hints) if self.visual_hints else [],
            'templates': json.loads(self.templates) if self.templates else [],
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }

class Creative(db.Model):
    __tablename__ = 'creatives'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # 多维度选择字段 - JSON格式存储选中的选项ID
    selected_dimensions = db.Column(db.Text)  # JSON: {'emotion_motivation': [1,2], 'value_proof': [3]}
    
    # 兼容旧版本字段（可选）
    game_type = db.Column(db.String(50))
    target_audience = db.Column(db.String(100))
    emotion_appeal = db.Column(db.String(50))
    
    # 状态字段
    status = db.Column(db.String(20), default='generated')  # generated, selected, deduplicated, scored, tested
    is_selected = db.Column(db.Boolean, default=False)
    
    # 评分字段
    creativity_score = db.Column(db.Float, default=0.0)
    appeal_score = db.Column(db.Float, default=0.0)
    relevance_score = db.Column(db.Float, default=0.0)
    total_score = db.Column(db.Float, default=0.0)
    
    # 去重字段
    duplicate_group_id = db.Column(db.Integer)
    is_representative = db.Column(db.Boolean, default=False)
    
    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generation_params = db.Column(db.Text)  # JSON字符串存储生成参数
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'selected_dimensions': json.loads(self.selected_dimensions) if self.selected_dimensions else {},
            'game_type': self.game_type,
            'target_audience': self.target_audience,
            'emotion_appeal': self.emotion_appeal,
            'status': self.status,
            'is_selected': self.is_selected,
            'creativity_score': self.creativity_score,
            'appeal_score': self.appeal_score,
            'relevance_score': self.relevance_score,
            'total_score': self.total_score,
            'duplicate_group_id': self.duplicate_group_id,
            'is_representative': self.is_representative,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'generation_params': json.loads(self.generation_params) if self.generation_params else {}
        }

class ABTest(db.Model):
    __tablename__ = 'ab_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, running, completed, paused
    
    # 测试配置
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    traffic_split = db.Column(db.Float, default=0.5)  # A组流量占比
    
    # 测试结果
    total_impressions_a = db.Column(db.Integer, default=0)
    total_impressions_b = db.Column(db.Integer, default=0)
    total_clicks_a = db.Column(db.Integer, default=0)
    total_clicks_b = db.Column(db.Integer, default=0)
    
    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def ctr_a(self):
        return (self.total_clicks_a / self.total_impressions_a) if self.total_impressions_a > 0 else 0
    
    def ctr_b(self):
        return (self.total_clicks_b / self.total_impressions_b) if self.total_impressions_b > 0 else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'traffic_split': self.traffic_split,
            'total_impressions_a': self.total_impressions_a,
            'total_impressions_b': self.total_impressions_b,
            'total_clicks_a': self.total_clicks_a,
            'total_clicks_b': self.total_clicks_b,
            'ctr_a': self.ctr_a(),
            'ctr_b': self.ctr_b(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ABTestCreative(db.Model):
    __tablename__ = 'ab_test_creatives'
    
    id = db.Column(db.Integer, primary_key=True)
    ab_test_id = db.Column(db.Integer, db.ForeignKey('ab_tests.id'), nullable=False)
    creative_id = db.Column(db.Integer, db.ForeignKey('creatives.id'), nullable=False)
    variant = db.Column(db.String(1), nullable=False)  # 'A' or 'B'
    
    # 关系
    ab_test = db.relationship('ABTest', backref='test_creatives')
    creative = db.relationship('Creative', backref='test_assignments')