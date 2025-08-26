from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Creative, ABTest, ABTestCreative, CreativeDimension, CreativeOption
from modules.creative_generator import CreativeGenerator
from modules.trends_service import (
    get_trending_topics_api, 
    get_countries_list, 
    get_time_ranges_list, 
    test_trends_service
)
import os
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

# 在应用上下文中初始化创意生成器
with app.app_context():
    generator = CreativeGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/step1')
def step1_generate():
    return render_template('step1_generate.html')

@app.route('/step2')
def step2_deduplicate():
    selected_creatives = Creative.query.filter_by(is_selected=True).all()
    return render_template('step2_deduplicate.html', creatives=[c.to_dict() for c in selected_creatives])

@app.route('/step3')
def step3_score():
    deduplicated_creatives = Creative.query.filter_by(is_representative=True).all()
    return render_template('step3_score.html', creatives=[c.to_dict() for c in deduplicated_creatives])

@app.route('/step4')
def step4_abtest():
    scored_creatives = Creative.query.filter(Creative.total_score > 0).all()
    tests = ABTest.query.all()
    return render_template('step4_abtest.html', 
                         creatives=[c.to_dict() for c in scored_creatives],
                         tests=[t.to_dict() for t in tests])

# API接口
@app.route('/api/dimensions', methods=['GET'])
def api_get_dimensions():
    """获取维度配置"""
    try:
        dimensions_config = generator.get_dimensions_config()
        return jsonify({'success': True, 'data': dimensions_config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/generate-creatives', methods=['POST'])
def api_generate_creatives():
    """生成创意 - 简化版本"""
    try:
        data = request.get_json()
        game_background = data.get('game_background', '').strip()  # 游戏背景介绍
        count = data.get('count', 5)
        ai_model = data.get('ai_model', 'gpt-5-nano').strip()  # AI模型选择
        
        # 验证输入：需要游戏背景介绍
        if not game_background:
            return jsonify({
                'success': False, 
                'message': '请输入游戏背景介绍'
            }), 400
        
        # 验证AI模型选择
        valid_models = ['gpt-5-nano', 'gpt-5-mini']
        if ai_model not in valid_models:
            ai_model = 'gpt-5-nano'  # 默认使用便宜模型
            
        # 验证生成数量限制
        if ai_model == 'gpt-5-mini':
            # GPT-5-mini限制1-3个
            if count not in [1, 2, 3]:
                count = 2  # 默认2个
        elif ai_model == 'gpt-5-nano':
            # GPT-5-nano限制1,3,5或10个
            if count not in [1, 3, 5, 10]:
                count = 5  # 默认5个
        
        # 使用固定模板生成创意
        template = f"请生成{count}组在越南落地的{game_background}静态图片广告创意。每组都包含：核心概念、建议图片的画面、镜头/光线处理、色彩与道具等细节，便于AI生成图片、关键注意事项（统一强调：画面中严禁出现任何文字、Logo、字幕与标识）"
        
        # 调用简化的创意生成
        creatives = generator.generate_simple_creatives(
            template=template,
            count=count,
            game_background=game_background,
            ai_model=ai_model
        )
        return jsonify({'success': True, 'data': creatives})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/save-creatives', methods=['POST'])
def api_save_creatives():
    """保存选中的创意"""
    try:
        data = request.get_json()
        creatives_data = data.get('creatives', [])
        
        if not creatives_data:
            return jsonify({'success': False, 'message': '没有要保存的创意'}), 400
        
        saved_creatives = generator.save_creatives_to_db(creatives_data)
        
        # 标记为已选择
        for creative in saved_creatives:
            creative.is_selected = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'成功保存 {len(saved_creatives)} 个创意',
            'data': [c.to_dict() for c in saved_creatives]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dimensions/<int:dimension_id>/options', methods=['POST'])
def api_add_dimension_option(dimension_id):
    """添加维度选项"""
    try:
        data = request.get_json()
        name = data.get('name', '')
        description = data.get('description', '')
        keywords = data.get('keywords', [])
        visual_hints = data.get('visual_hints', [])
        templates = data.get('templates', [])
        
        if not name:
            return jsonify({'success': False, 'message': '选项名称不能为空'}), 400
        
        option = generator.add_dimension_option(
            dimension_id, name, description, keywords, visual_hints, templates
        )
        
        return jsonify({
            'success': True, 
            'message': '选项添加成功',
            'data': option.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dimensions/<int:dimension_id>', methods=['PUT'])
def api_update_dimension(dimension_id):
    """更新维度配置"""
    try:
        data = request.get_json()
        
        success = generator.update_dimension_config(dimension_id, **data)
        
        if success:
            return jsonify({'success': True, 'message': '维度更新成功'})
        else:
            return jsonify({'success': False, 'message': '维度不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/creatives/selected', methods=['GET'])
def api_get_selected_creatives():
    """获取已选择的创意"""
    try:
        selected_creatives = Creative.query.filter_by(is_selected=True).all()
        return jsonify({
            'success': True, 
            'data': [c.to_dict() for c in selected_creatives]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 热门话题相关API
@app.route('/api/trending-topics', methods=['POST'])
def api_get_trending_topics():
    """获取热门话题（自动翻译为中文）"""
    try:
        data = request.get_json()
        country_code = data.get('country_code', 'VN')
        time_range = data.get('time_range', 'week')
        top_n = data.get('top_n', 10)
        translate_to_chinese = data.get('translate_to_chinese', True)  # 默认翻译为中文
        
        # 验证参数
        if not isinstance(top_n, int) or not (1 <= top_n <= 50):
            return jsonify({'success': False, 'message': 'top_n必须是1-50之间的整数'}), 400
        
        result = get_trending_topics_api(
            country_code=country_code,
            time_range=time_range,
            top_n=top_n,
            translate_to_chinese=translate_to_chinese
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/trending-topics/countries', methods=['GET'])
def api_get_countries():
    """获取支持的国家列表"""
    try:
        result = get_countries_list()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/trending-topics/time-ranges', methods=['GET'])
def api_get_time_ranges():
    """获取支持的时间范围列表"""
    try:
        result = get_time_ranges_list()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/trending-topics/test', methods=['GET'])
def api_test_trends_service():
    """测试trends服务状态"""
    try:
        result = test_trends_service()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)