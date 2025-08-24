import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'creative-factory-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///creative_factory.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 创意生成配置
    DEFAULT_CREATIVE_COUNT = 20
    MAX_CREATIVE_COUNT = 100
    
    # 去重配置
    SIMILARITY_THRESHOLD = 0.8
    
    # 评分配置
    DEFAULT_SCORE_THRESHOLD = 0.6
    
    # A/B测试配置
    DEFAULT_TEST_DURATION = timedelta(days=7)