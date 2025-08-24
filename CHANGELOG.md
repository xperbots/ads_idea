# 更新日志 / Changelog

## [1.2.0] - 2025-08-24

### 🚀 新功能 / New Features
- **优化翻译系统**: 实现更精准的多语言翻译支持
- **本地化语言识别**: 自动识别源语言并使用本地语言名称
- **批量翻译优化**: 单次API调用处理多个话题，提高效率
- **真实数据保证**: 移除模拟数据，确保用户获取真实的热门话题

### 🔧 改进 / Improvements
- **翻译Prompt优化**: 使用简洁高效的翻译指令格式
  ```
  "You are an expert linguist, specializing in translation from {源语言} to 简体中文. translate directly without explanation"
  ```
- **语言映射增强**: 支持东南亚各国本地语言名称
  - 🇻🇳 越南: "Tiếng Việt"
  - 🇹🇭 泰国: "ภาषาไทย"
  - 🇸🇬 新加坡: "English"
  - 🇲🇾 马来西亚: "English"  
  - 🇮🇩 印尼: "Bahasa Indonesia"
  - 🇵🇭 菲律宾: "English"

### 🏗️ 技术改进 / Technical Improvements
- **OpenAI集成优化**: 
  - 支持GPT-5系列模型 (gpt-5-nano, gpt-5-mini)
  - 修复urllib3兼容性问题
  - 优化API调用参数和错误处理
- **趋势服务增强**:
  - 实现真实数据获取，移除误导性模拟数据
  - 改进错误处理和用户反馈
  - 增加重试机制和详细错误信息
- **UI/UX优化**:
  - 重新设计热门话题配置界面
  - 从下拉菜单改为清晰的4列布局
  - 增加错误状态显示和帮助功能

### 🐛 修复 / Bug Fixes
- 修复OpenAI Client初始化错误: "got an unexpected keyword argument 'proxies'"
- 修复pytrends兼容性问题: "got an unexpected keyword argument 'method_whitelist'"
- 解决trending_searches API弃用问题，改用related_queries方法
- 修复批量翻译数量不匹配的问题

### 📦 依赖更新 / Dependencies
- `openai==1.101.0` - 升级到最新版本支持GPT-5
- `urllib3<2.0` - 限制版本以确保pytrends兼容性
- `pandas==2.2.3` - 更新数据处理库

### 🔄 API变更 / API Changes
- `translate_to_chinese()` 方法新增 `country_code` 参数
- 趋势API返回格式优化，增加详细错误信息和建议
- 移除所有模拟数据相关的API返回

### 📊 性能优化 / Performance
- **翻译效率提升**: 单次调用处理所有话题，减少API请求次数
- **错误处理优化**: 快速失败机制，避免用户等待无效数据
- **内存使用优化**: 改进数据结构和处理流程

### 🗂️ 文件变更 / File Changes
```
修改文件:
├── modules/openai_service.py     # OpenAI服务优化和翻译Prompt改进
├── modules/trends_service.py     # 真实数据获取和错误处理
├── static/js/step1_generate.js   # UI交互和错误显示
├── static/css/style.css          # 错误状态样式和响应式设计
├── templates/step1_generate.html # UI重新设计
├── requirements.txt              # 依赖版本更新
└── .env                         # 模型配置更新

新增文件:
├── CHANGELOG.md                 # 更新日志文档
└── .gitignore                   # Git忽略规则
```

### 🎯 下一步计划 / Next Steps
1. **步骤2开发**: 创意去重功能实现
2. **数据库优化**: SQLite性能调优和索引优化  
3. **API稳定性**: 增加更多数据源作为Google Trends的备用
4. **用户体验**: 添加进度指示器和实时反馈
5. **测试覆盖**: 增加单元测试和集成测试

### 🔗 相关链接 / Related Links
- GitHub Repository: https://github.com/xperbots/ads_idea
- OpenAI API Documentation: https://platform.openai.com/docs
- Google Trends API: https://pypi.org/project/pytrends/

---

## [1.1.0] - 2025-08-23

### 初始版本 / Initial Release
- ✅ 步骤1: 创意发散功能基础实现
- ✅ 热门话题获取 (Google Trends集成)
- ✅ 基础UI界面搭建
- ✅ 数据库结构设计 (SQLite)
- ✅ Flask后端架构搭建