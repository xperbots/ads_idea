# 🎨 Creative Factory - 游戏图片广告创意生成器

一个基于多维度配置的广告创意生成和优化系统，专为游戏行业设计。

## 🚀 快速开始

### 环境准备
```bash
# 1. 克隆项目到本地
cd /Users/pangpanghu007/Documents/Python\ Project/ads_idea

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install Flask SQLAlchemy Flask-SQLAlchemy Werkzeug

# 4. 启动服务
python run.py
```

### 访问系统
打开浏览器访问：http://127.0.0.1:5000

## 🎯 系统功能

### 四步产线流程
1. **🌟 系统化发散** - 多维度创意生成
2. **🔄 规模化去重** - 智能相似度检测  
3. **⭐ 规则化收敛** - 多维度评分筛选
4. **📊 快速A/B测试** - 效果验证优化

### 创意维度体系（6大维度30个选项）
- **A. 情绪/动机**：胜利瞬间、成长蜕变、稀缺限时、归属团队、美学沉浸
- **B. 价值证明**：三硬核卖点、社证口碑、权威背书、对比替代、零门槛  
- **C. 视觉钩子**：极近特写、夸张透视、强互补色、图形构图、超现实反转
- **D. 利益主叙事**：一步到位、场景适配、个性外观、资源获取感、掌控策略感
- **E. 事件/时令**：节日限定、赛季更迭、周年纪念、联动视觉、地区化
- **F. 轻娱乐/梗化**：表情包化、三格剧照、谐音押韵、手作纸艺、信息图式

## 📁 项目结构

```
creative_factory/
├── venv/                     # 虚拟环境
├── app.py                    # Flask主应用
├── run.py                    # 启动脚本  
├── config.py                 # 配置文件
├── models.py                 # 数据模型
├── modules/                  # 核心模块
│   └── creative_generator.py # 创意生成器
├── templates/                # HTML模板
├── static/                   # 静态资源
├── requirements.txt          # 依赖清单
├── DEVELOPMENT.md           # 开发记录
└── README.md               # 项目说明
```

## 🔧 技术栈

- **后端**：Flask + SQLAlchemy + SQLite
- **前端**：Bootstrap + JavaScript
- **算法**：TF-IDF、余弦相似度、聚类分析
- **部署**：Python虚拟环境

## 📖 使用说明

### 第一步：创意发散
1. 访问 `/step1` 创意生成页面
2. 选择多个维度的创意选项
3. 设置生成数量（10-100个）
4. 点击"生成创意"查看结果
5. 人工筛选保留有价值的创意

### 数据持久化
- 所有维度配置存储在SQLite数据库
- 支持动态添加新维度和选项
- 用户选择的创意自动保存

### API接口
- `GET /api/dimensions` - 获取维度配置
- `POST /api/generate-creatives` - 生成创意
- `POST /api/save-creatives` - 保存创意

## 🛠️ 开发状态

- ✅ **第一步完成**：系统化发散模块
- ⏳ **开发中**：规模化去重模块  
- ⏳ **计划中**：规则化收敛模块
- ⏳ **计划中**：快速A/B测试模块

详细开发记录请查看 [DEVELOPMENT.md](DEVELOPMENT.md)

## 🎨 特色功能

### 多维度智能组合
基于6大创意维度进行智能组合，每次生成都会产生不同的创意角度

### 人工交互筛选  
每个生成的创意都可以人工选择是否保留到下一阶段

### 可配置可扩展
支持添加新的创意维度和选项，系统会自动适应

### 直观的用户界面
清晰的步骤指引、实时统计、批量操作等用户友好功能

## 📝 版本历史

- **v1.0** - 第一步系统化发散模块完成
- **v0.1** - 项目初始化和架构搭建

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证

---

**开发团队**：Creative Factory Team  
**最后更新**：2025-08-23