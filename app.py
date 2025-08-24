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
    """生成创意"""
    try:
        data = request.get_json()
        selected_dimensions = data.get('selected_dimensions', {})
        count = data.get('count', 20)
        
        if not selected_dimensions:
            return jsonify({'success': False, 'message': '请选择至少一个维度的选项'}), 400
        
        creatives = generator.generate_creatives(selected_dimensions, count)
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