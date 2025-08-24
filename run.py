#!/usr/bin/env python
"""
启动脚本
使用方法：
1. 激活虚拟环境：source venv/bin/activate
2. 运行：python run.py
"""

from app import app

if __name__ == '__main__':
    print("🎨 创意工厂启动中...")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000
    )