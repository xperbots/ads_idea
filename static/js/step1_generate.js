// 现代化广告创意生成器 JavaScript 功能
let dimensionsConfig = [];
let generatedCreatives = [];
let selectedCreatives = new Set();
let currentCreativeIndex = -1;
let collapsedDimensions = new Set();
let editingElement = null;
let customInputs = {};
let trendsCountdownTimer = null;
let trendsCountdownSeconds = 0;

document.addEventListener('DOMContentLoaded', function() {
    // 简化的初始化
    checkTrendsCountdownState(); // 检查并恢复倒计时状态
    updateStats();
    updateCreativeCountOptions(); // 初始化数量选项
    
    // 监听模型选择变化
    document.querySelectorAll('input[name="ai-model"]').forEach(radio => {
        radio.addEventListener('change', updateCreativeCountOptions);
    });
    
    // 监听数量选择变化以更新成本
    const countSelect = document.getElementById('creative-count');
    if (countSelect) {
        countSelect.addEventListener('change', function() {
            const selectedModel = document.querySelector('input[name="ai-model"]:checked')?.value || 'gpt-5-nano';
            updateCostHint(selectedModel, parseInt(this.value));
        });
    }
    
    // 绑定基础事件
    document.getElementById('generate-btn').addEventListener('click', handleGenerateCreatives);
    document.getElementById('batch-select-btn').addEventListener('click', selectAllCreatives);
    document.getElementById('batch-deselect-btn').addEventListener('click', deselectAllCreatives);
    document.getElementById('save-selected-btn').addEventListener('click', saveSelectedCreatives);
    
    // 绑定新功能事件
    document.getElementById('fetch-trends-btn').addEventListener('click', fetchTrendingTopics);
    document.getElementById('game-background-input').addEventListener('input', updateIdeaInput);
    
    // 绑定模态框事件
    const modal = document.getElementById('creativeDetailModal');
    if (modal) {
        document.getElementById('toggle-creative-selection').addEventListener('click', toggleCurrentCreativeSelection);
    }
    
    // 页面卸载时保存倒计时状态
    window.addEventListener('beforeunload', saveTrendsCountdownState);
});

// 加载维度配置
async function loadDimensionsConfig() {
    try {
        const response = await makeRequest('/api/dimensions', 'GET');
        if (response.success) {
            dimensionsConfig = response.data;
            renderDimensionsConfig();
        } else {
            showMessage('加载维度配置失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showMessage('加载维度配置失败: ' + error.message, 'danger');
    }
}

// 检查是否在冷却期间
function isTrendsOnCooldown() {
    return trendsCountdownSeconds > 0;
}

// 保存倒计时状态到本地存储
function saveTrendsCountdownState() {
    try {
        const state = {
            endTime: trendsCountdownSeconds > 0 ? Date.now() + (trendsCountdownSeconds * 1000) : null,
            lastRequest: Date.now()
        };
        localStorage.setItem('trends-countdown-state', JSON.stringify(state));
    } catch (error) {
        console.error('Failed to save countdown state:', error);
    }
}

// 检查并恢复倒计时状态
function checkTrendsCountdownState() {
    try {
        const saved = localStorage.getItem('trends-countdown-state');
        if (!saved) return;
        
        const state = JSON.parse(saved);
        const now = Date.now();
        
        if (state.endTime && state.endTime > now) {
            // 倒计时未结束，恢复倒计时
            const remainingSeconds = Math.ceil((state.endTime - now) / 1000);
            startTrendsCountdown(remainingSeconds);
        } else if (state.lastRequest && (now - state.lastRequest) < 60000) {
            // 最后一次请求在60秒内，继续倒计时
            const remainingSeconds = 60 - Math.floor((now - state.lastRequest) / 1000);
            if (remainingSeconds > 0) {
                startTrendsCountdown(remainingSeconds);
            }
        }
    } catch (error) {
        console.error('Failed to load countdown state:', error);
        // 清除损坏的数据
        localStorage.removeItem('trends-countdown-state');
    }
}

// 开始倒计时
function startTrendsCountdown(seconds = 60) {
    trendsCountdownSeconds = seconds;
    const btn = document.getElementById('fetch-trends-btn');
    
    // 清除之前的计时器
    if (trendsCountdownTimer) {
        clearInterval(trendsCountdownTimer);
    }
    
    // 保存状态
    saveTrendsCountdownState();
    
    // 开始倒计时
    trendsCountdownTimer = setInterval(() => {
        if (trendsCountdownSeconds <= 0) {
            // 倒计时结束
            clearInterval(trendsCountdownTimer);
            trendsCountdownTimer = null;
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-search me-2"></i>获取热门话题';
            btn.className = 'btn btn-primary';
            
            // 清除本地存储状态
            localStorage.removeItem('trends-countdown-state');
            
            // 提示用户可以再次请求
            showMessage('✅ 冷却时间结束，现在可以再次获取热门话题', 'success');
            return;
        }
        
        // 更新按钮显示
        const minutes = Math.floor(trendsCountdownSeconds / 60);
        const seconds = trendsCountdownSeconds % 60;
        const timeDisplay = minutes > 0 ? `${minutes}:${seconds.toString().padStart(2, '0')}` : `${seconds}s`;
        
        btn.disabled = true;
        btn.innerHTML = `<i class="bi bi-clock me-2"></i>请等待 ${timeDisplay}`;
        btn.className = 'btn btn-warning countdown-pulse';
        
        trendsCountdownSeconds--;
        
        // 每5秒保存一次状态
        if (trendsCountdownSeconds % 5 === 0) {
            saveTrendsCountdownState();
        }
    }, 1000);
}

// 增强的流行主题获取功能
async function fetchTrendingTopics() {
    // 检查是否在冷却期
    if (isTrendsOnCooldown()) {
        const minutes = Math.floor(trendsCountdownSeconds / 60);
        const seconds = trendsCountdownSeconds % 60;
        const timeDisplay = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
        showMessage(`🕐 请等待 ${timeDisplay} 后再次获取热门话题（防止API限制）`, 'info');
        return;
    }
    
    const btn = document.getElementById('fetch-trends-btn');
    const originalText = btn.innerHTML;
    
    // 获取用户选择的参数
    const countryCode = document.getElementById('country-select').value;
    const timeRange = document.getElementById('timerange-select').value;
    const topN = parseInt(document.getElementById('topn-select').value);
    
    // 获取国家名称用于显示
    const countryName = document.getElementById('country-select').selectedOptions[0].textContent;
    const timeRangeName = document.getElementById('timerange-select').selectedOptions[0].textContent;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>获取中...';
    btn.className = 'btn btn-primary';
    
    try {
        const response = await makeRequest('/api/trending-topics', 'POST', {
            country_code: countryCode,
            time_range: timeRange,
            top_n: topN
        });
        
        if (response.success) {
            const topics = response.data || [];
            displayTrendingTopics(topics, {
                country: countryName,
                timeRange: timeRangeName,
                isFallback: false,
                actualCount: topics.length,
                dataSource: response.data_source
            });
            
            showMessage(`🎉 ${response.message}`, 'success');
            
            // 成功后开始60秒倒计时
            startTrendsCountdown(60);
            showMessage('🕐 为保护API稳定，下次请求需等待60秒', 'info');
        } else {
            // 处理错误情况 - 不显示任何模拟数据
            const errorType = response.error_type || 'unknown';
            displayTrendingError(response.message, {
                country: countryName,
                timeRange: timeRangeName,
                errorType: errorType,
                suggestion: response.suggestion
            });
            
            showMessage(`❌ ${response.message}`, 'danger');
            
            // 即使失败也要开始倒计时，防止频繁重试导致被封IP
            startTrendsCountdown(60);
        }
    } catch (error) {
        console.error('Fetch trending topics error:', error);
        showMessage('获取流行主题失败: ' + error.message, 'danger');
        
        // 显示网络错误信息，不显示模拟数据
        displayTrendingError('网络连接错误，无法获取热门话题数据', {
            country: countryName,
            timeRange: timeRangeName,
            errorType: 'network_error',
            suggestion: '请检查网络连接后重试'
        });
        
        // 网络错误也要倒计时，避免频繁请求
        startTrendsCountdown(60);
    } finally {
        // 注意：这里不再直接恢复按钮，因为要等倒计时结束
        if (!isTrendsOnCooldown()) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            btn.className = 'btn btn-primary';
        }
    }
}

// 获取备用主题数据
function getFallbackTopics(countryCode, topN) {
    const fallbackData = {
        'VN': ["营销活动", "生活方式", "科技创新", "教育培训", "健康养生"],
        'TH': ["สินค้าไทย", "การตลาด", "เทคโนโลยี", "การศึกษา", "สุขภาพ"],
        'SG': ["Singapore Brands", "Technology", "Education", "Health", "Lifestyle"],
        'MY': ["Malaysian Products", "Technology", "Education", "Health", "Tourism"],
        'ID': ["Produk Indonesia", "Teknologi", "Pendidikan", "Kesehatan", "Wisata"],
        'PH': ["Filipino Products", "Technology", "Education", "Health", "Tourism"]
    };
    
    const topics = fallbackData[countryCode] || fallbackData['VN'];
    return topics.slice(0, topN);
}

// 显示真实热门话题
function displayTrendingTopics(topics, metadata = {}) {
    const container = document.getElementById('topics-container');
    const topicsDiv = document.getElementById('trending-topics');
    const headerElement = topicsDiv.querySelector('p.fw-bold');
    const sourceInfoElement = topicsDiv.querySelector('.source-info p');
    
    // 更新头部信息
    const {country, timeRange, actualCount, dataSource} = metadata;
    let headerText = `✅ 热门话题：`;
    if (country && timeRange) {
        headerText += `${country} ${timeRange}`;
    }
    if (actualCount) {
        headerText += ` <span class="badge bg-success ms-2">${actualCount}个</span>`;
    }
    
    if (headerElement) {
        headerElement.innerHTML = headerText;
    }
    
    // 渲染话题标签
    if (topics && topics.length > 0) {
        container.innerHTML = topics.map((topic, index) => `
            <span class="topic-badge real-data" 
                  onclick="selectTopic('${topic.replace(/'/g, "\\'")}', '${country || ''}')"
                  title="来自Google Trends的实时数据 - 点击使用">
                ${getRealTopicIcon(index)} ${topic}
            </span>
        `).join('');
    } else {
        container.innerHTML = '<p class="text-muted text-center m-0">暂无热门话题数据</p>';
    }
    
    // 更新数据来源说明
    if (sourceInfoElement) {
        const timestamp = new Date().toLocaleString('zh-CN');
        sourceInfoElement.innerHTML = `
            <i class="bi bi-check-circle text-success me-1"></i>
            <span class="text-success">🔍 来自 Google Trends</span> | 
            📊 实时数据 | 
            🕒 ${timestamp}
        `;
    }
    
    // 显示热门话题区域
    topicsDiv.style.display = 'block';
    
    // 添加成功动画
    topicsDiv.className = 'trends-card success';
    topicsDiv.style.opacity = '0';
    topicsDiv.style.transform = 'translateY(10px)';
    setTimeout(() => {
        topicsDiv.style.transition = 'all 0.5s ease';
        topicsDiv.style.opacity = '1';
        topicsDiv.style.transform = 'translateY(0)';
    }, 50);
}

// 显示错误信息（不显示模拟数据）
function displayTrendingError(errorMessage, metadata = {}) {
    const container = document.getElementById('topics-container');
    const topicsDiv = document.getElementById('trending-topics');
    const headerElement = topicsDiv.querySelector('p.fw-bold');
    const sourceInfoElement = topicsDiv.querySelector('.source-info p');
    
    // 更新头部信息
    const {country, timeRange, errorType, suggestion} = metadata;
    let headerText = `❌ 无法获取热门话题`;
    if (country && timeRange) {
        headerText += `：${country} ${timeRange}`;
    }
    
    if (headerElement) {
        headerElement.innerHTML = headerText;
    }
    
    // 显示错误信息和建议
    const errorTypeText = {
        'data_unavailable': '📭 数据暂时不可用',
        'network_error': '🌐 网络连接错误', 
        'system_error': '⚙️ 系统错误',
        'unknown': '❓ 未知错误'
    };
    
    container.innerHTML = `
        <div class="error-message">
            <div class="error-icon">${errorTypeText[errorType] || errorTypeText['unknown']}</div>
            <div class="error-details">
                <p class="error-text">${errorMessage}</p>
                ${suggestion ? `<p class="error-suggestion"><i class="bi bi-lightbulb"></i> ${suggestion}</p>` : ''}
                <div class="error-actions mt-3">
                    <button class="btn btn-primary btn-sm" onclick="retryFetchTrendingTopics()">
                        <i class="bi bi-arrow-clockwise me-1"></i>重试
                    </button>
                    <button class="btn btn-secondary btn-sm ms-2" onclick="showTrendingHelp()">
                        <i class="bi bi-question-circle me-1"></i>帮助
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // 更新数据来源说明
    if (sourceInfoElement) {
        const timestamp = new Date().toLocaleString('zh-CN');
        sourceInfoElement.innerHTML = `
            <i class="bi bi-exclamation-triangle text-warning me-1"></i>
            <span class="text-warning">数据获取失败</span> | 
            🕒 ${timestamp} |
            <span class="text-muted">请稍后重试</span>
        `;
    }
    
    // 显示错误区域
    topicsDiv.style.display = 'block';
    topicsDiv.className = 'trends-card error';
    
    // 添加错误动画
    topicsDiv.style.opacity = '0';
    topicsDiv.style.transform = 'translateY(10px)';
    setTimeout(() => {
        topicsDiv.style.transition = 'all 0.5s ease';
        topicsDiv.style.opacity = '1';
        topicsDiv.style.transform = 'translateY(0)';
    }, 50);
}

// 重试获取热门话题（检查冷却期）
function retryFetchTrendingTopics() {
    if (isTrendsOnCooldown()) {
        const minutes = Math.floor(trendsCountdownSeconds / 60);
        const seconds = trendsCountdownSeconds % 60;
        const timeDisplay = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
        showMessage(`🕒 请等待 ${timeDisplay} 后再次尝试（pytrends API限制）`, 'warning');
        return;
    }
    fetchTrendingTopics();
}

// 获取真实话题图标
function getRealTopicIcon(index) {
    const icons = ['🔥', '📈', '🌟', '💫', '⚡', '🎯', '📊', '🔍'];
    return icons[index % icons.length];
}

// 显示帮助信息
function showTrendingHelp() {
    const helpModal = new bootstrap.Modal(document.getElementById('helpModal') || createHelpModal());
    helpModal.show();
}

// 创建帮助模态框
function createHelpModal() {
    const modalHtml = `
        <div class="modal fade" id="helpModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">热门话题获取帮助</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h6>📊 数据来源</h6>
                        <p>热门话题数据来自 Google Trends API，提供各国实时搜索趋势。</p>
                        
                        <h6>🔧 常见问题</h6>
                        <ul>
                            <li><strong>数据不可用</strong>：可能该地区搜索数据不足，请尝试其他国家</li>
                            <li><strong>网络错误</strong>：检查网络连接，稍后重试</li>
                            <li><strong>加载时间长</strong>：Google Trends API响应较慢，请耐心等待</li>
                            <li><strong>按钮不可点击</strong>：为防止API限制，每次请求后需等待60秒</li>
                        </ul>
                        
                        <h6>💡 使用建议</h6>
                        <ul>
                            <li>选择不同的国家和时间范围获取更多话题</li>
                            <li>点击话题标签可直接添加到创意输入</li>
                            <li>如遇错误可点击重试按钮，但需等待冷却时间</li>
                            <li><strong>重要</strong>：为避免被Google封禁，请耐心等待60秒间隔</li>
                        </ul>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">了解了</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    return document.getElementById('helpModal');
}

// 选择主题
function selectTopic(topic, country = '') {
    const input = document.getElementById('game-background-input');
    input.value = topic;
    input.focus();
    updateIdeaInput();
    
    // 添加选择反馈
    const selectedTopic = document.querySelector(`[onclick*="${topic}"]`);
    if (selectedTopic) {
        selectedTopic.style.background = '#0066cc';
        selectedTopic.style.color = 'white';
        selectedTopic.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            selectedTopic.style.background = '';
            selectedTopic.style.color = '';
            selectedTopic.style.transform = '';
        }, 300);
    }
    
    showMessage(`已选择话题：${topic}`, 'info');
}

// 更新创意输入
function updateIdeaInput() {
    // 可以在这里添加实时验证或建议功能
    const input = document.getElementById('game-background-input');
    if (input.value.length > 100) {
        input.style.borderColor = '#ffc107';
    } else {
        input.style.borderColor = '';
    }
}

// 本地存储自定义输入
function loadCustomInputs() {
    try {
        const saved = localStorage.getItem('creative-generator-custom-inputs');
        if (saved) {
            customInputs = JSON.parse(saved);
        }
    } catch (error) {
        console.error('Failed to load custom inputs:', error);
        customInputs = {};
    }
}

function saveCustomInputs() {
    try {
        localStorage.setItem('creative-generator-custom-inputs', JSON.stringify(customInputs));
    } catch (error) {
        console.error('Failed to save custom inputs:', error);
    }
}

// 现代化维度配置界面渲染
function renderDimensionsConfig() {
    const container = document.getElementById('dimensions-container');
    container.innerHTML = '';
    
    dimensionsConfig.forEach((dimension, dimensionIndex) => {
        const isCollapsed = collapsedDimensions.has(dimension.name);
        const dimensionLetter = String.fromCharCode(65 + dimensionIndex);
        const customInput = customInputs[dimension.name] || '';
        
        const dimensionHtml = `
            <div class="dimension-group" data-dimension="${dimension.name}">
                <div class="dimension-header ${isCollapsed ? 'collapsed' : ''}" 
                     onclick="toggleDimensionCollapse('${dimension.name}')">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-chevron-${isCollapsed ? 'down' : 'up'} me-2"></i>
                            <span class="badge bg-primary me-2">${dimensionLetter}</span>
                            <h6 class="mb-0 me-2">${dimension.display_name}</h6>
                            <span class="badge bg-secondary">${dimension.options.length}</span>
                            <span class="badge bg-info ms-2" id="selected-count-${dimension.name}">
                                已选择 0
                            </span>
                        </div>
                        <div onclick="event.stopPropagation()">
                            <button type="button" class="btn btn-outline-primary btn-sm me-1" 
                                    onclick="selectAllInDimension('${dimension.name}')">全选</button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" 
                                    onclick="clearDimension('${dimension.name}')">清空</button>
                        </div>
                    </div>
                    <div class="text-muted small mt-2">${dimension.description}</div>
                </div>
                
                <div class="dimension-content" style="display: ${isCollapsed ? 'none' : 'block'}">
                    <!-- 自定义输入区域 -->
                    <div class="custom-input-section">
                        <label class="form-label fw-bold text-primary small">
                            自定义${dimension.display_name}内容：
                        </label>
                        <textarea class="form-control" rows="2" 
                                placeholder="输入您的自定义${dimension.display_name}内容..."
                                onchange="updateCustomInput('${dimension.name}', this.value)"
                        >${customInput}</textarea>
                    </div>
                    
                    <!-- 选项列表 -->
                    <div class="options-container">
                        ${dimension.options.map(option => `
                            <div class="option-item" data-option-id="${option.id}" 
                                 onclick="toggleOptionSelection('${dimension.name}', ${option.id})">
                                <div class="form-check">
                                    <input class="form-check-input dimension-option" type="checkbox" 
                                           id="option-${option.id}" 
                                           data-dimension="${dimension.name}" 
                                           data-option-id="${option.id}"
                                           onchange="updateStats(); updateDimensionStats('${dimension.name}')">
                                    <div class="option-content ms-3">
                                        <div class="d-flex justify-content-between align-items-start">
                                            <div class="option-name">${option.name}</div>
                                            <button type="button" class="btn btn-link btn-sm p-0" 
                                                    onclick="event.stopPropagation(); startEditingOption(${option.id})"
                                                    title="编辑选项">
                                                <i class="bi bi-pencil-square text-primary"></i>
                                            </button>
                                        </div>
                                        <div class="option-desc">${option.description}</div>
                                        <div class="option-keywords">
                                            🏷️ ${option.keywords.slice(0, 3).join(', ')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', dimensionHtml);
    });
    
    // 更新各维度统计
    dimensionsConfig.forEach(dimension => {
        updateDimensionStats(dimension.name);
    });
}

// 选择维度中的所有选项
function selectAllInDimension(dimensionName) {
    const checkboxes = document.querySelectorAll(`input[data-dimension="${dimensionName}"]`);
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateStats();
}

// 清空维度选择
function clearDimension(dimensionName) {
    const checkboxes = document.querySelectorAll(`input[data-dimension="${dimensionName}"]`);
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateStats();
}

// 清空所有选择
function clearAllSelections() {
    const checkboxes = document.querySelectorAll('.dimension-option');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateStats();
}

// 新功能函数
function toggleDimensionCollapse(dimensionName) {
    const content = document.querySelector(`[data-dimension="${dimensionName}"] .dimension-content`);
    const header = document.querySelector(`[data-dimension="${dimensionName}"] .dimension-header`);
    const icon = header.querySelector('i');
    
    if (collapsedDimensions.has(dimensionName)) {
        collapsedDimensions.delete(dimensionName);
        content.style.display = 'block';
        header.classList.remove('collapsed');
        icon.className = icon.className.replace('bi-chevron-down', 'bi-chevron-up');
    } else {
        collapsedDimensions.add(dimensionName);
        content.style.display = 'none';
        header.classList.add('collapsed');
        icon.className = icon.className.replace('bi-chevron-up', 'bi-chevron-down');
    }
}

function toggleOptionSelection(dimensionName, optionId) {
    const checkbox = document.getElementById(`option-${optionId}`);
    const optionItem = document.querySelector(`[data-option-id="${optionId}"]`);
    
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        optionItem.classList.add('selected');
    } else {
        optionItem.classList.remove('selected');
    }
    
    updateStats();
    updateDimensionStats(dimensionName);
}

function updateCustomInput(dimensionName, value) {
    customInputs[dimensionName] = value;
    saveCustomInputs();
}

function startEditingOption(optionId) {
    // 这里可以实现选项编辑功能
    console.log('编辑选项', optionId);
    showMessage('选项编辑功能正在开发中', 'info');
}

function updateDimensionStats(dimensionName) {
    const checkboxes = document.querySelectorAll(`input[data-dimension="${dimensionName}"]:checked`);
    const badge = document.getElementById(`selected-count-${dimensionName}`);
    if (badge) {
        badge.textContent = `已选择 ${checkboxes.length}`;
        badge.className = checkboxes.length > 0 ? 'badge bg-success ms-2' : 'badge bg-info ms-2';
    }
}

// 增强的统计信息更新
function updateStats() {
    // 简化的统计更新
    document.getElementById('generated-count').textContent = generatedCreatives.length;
    document.getElementById('selected-creatives-count').textContent = selectedCreatives.size;
    
    // 更新保存按钮计数
    const saveCountElement = document.getElementById('save-count');
    if (saveCountElement) {
        saveCountElement.textContent = selectedCreatives.size;
    }
    
    // 显示/隐藏批量操作按钮
    const batchActions = document.getElementById('batch-actions');
    if (generatedCreatives.length > 0) {
        batchActions.classList.add('show');
        batchActions.style.display = 'flex';
    } else {
        batchActions.classList.remove('show');
        batchActions.style.display = 'none';
    }
}

// 简化的处理生成创意请求
async function handleGenerateCreatives(event) {
    event.preventDefault();
    
    // 获取游戏背景输入
    const gameBackgroundInput = document.getElementById('game-background-input').value.trim();
    
    // 获取AI模型选择
    const aiModel = document.querySelector('input[name="ai-model"]:checked')?.value || 'gpt-5-nano';
    
    // 验证输入
    if (!gameBackgroundInput) {
        showMessage('请输入游戏背景介绍', 'warning');
        return;
    }
    
    const count = parseInt(document.getElementById('creative-count').value);
    
    // 显示加载状态
    showLoading('generation-progress');
    document.getElementById('loading-spinner').style.display = 'inline-block';
    document.getElementById('generate-btn').disabled = true;
    
    try {
        const requestData = {
            game_background: gameBackgroundInput,
            count: count,
            ai_model: aiModel
        };
        
        const response = await makeRequest('/api/generate-creatives', 'POST', requestData);
        
        if (response.success) {
            
            generatedCreatives = response.data;
            selectedCreatives.clear();
            renderCreatives();
            updateStats();
            showMessage(`🎉 成功生成 ${generatedCreatives.length} 个创意！`, 'success');
        } else {
            showMessage('生成创意失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showMessage('生成创意失败: ' + error.message, 'danger');
    } finally {
        // 隐藏加载状态
        hideLoading('generation-progress');
        document.getElementById('loading-spinner').style.display = 'none';
        document.getElementById('generate-btn').disabled = false;
    }
}

// 获取选中的维度配置
function getSelectedDimensions() {
    const result = {};
    const checkboxes = document.querySelectorAll('.dimension-option:checked');
    
    checkboxes.forEach(checkbox => {
        const dimension = checkbox.dataset.dimension;
        const optionId = parseInt(checkbox.dataset.optionId);
        
        if (!result[dimension]) {
            result[dimension] = [];
        }
        result[dimension].push(optionId);
    });
    
    return result;
}

// 现代化创意列表渲染
function renderCreatives() {
    const container = document.getElementById('creatives-container');
    
    if (generatedCreatives.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="display-1">🎨</div>
                <h4 class="mt-3">准备开始创作</h4>
                <p>输入您的想法或选择创意元素，然后点击"生成创意方案"</p>
            </div>
        `;
        return;
    }
    
    const creativesHtml = generatedCreatives.map((creative, index) => {
        return `
        <div class="creative-card ${selectedCreatives.has(index) ? 'selected' : ''}" 
             data-index="${index}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-3">
                        <span class="badge bg-primary me-2">#${creative.index || index + 1}</span>
                        <h5 class="creative-title mb-0">${creative.core_concept || creative.title || '无标题'}</h5>
                    </div>
                    <div class="creative-content mb-3">
                        <div class="mb-2"><strong>画面描述:</strong> ${creative.scene_description || creative.content || '暂无描述'}</div>
                        ${creative.camera_lighting ? `<div class="mb-2"><strong>镜头/光线:</strong> ${creative.camera_lighting}</div>` : ''}
                        ${creative.color_props ? `<div class="mb-2"><strong>色彩道具:</strong> ${creative.color_props}</div>` : ''}
                    </div>
                    <div class="row creative-meta">
                        <div class="col-md-6 mb-2">
                            <div class="d-flex flex-wrap">
                                <small class="text-muted me-2">选用维度:</small>
                                ${(creative.chosen_dimensions || []).map(dim => 
                                    `<span class="badge bg-light text-dark me-1">${dim}</span>`
                                ).join('') || '<span class="text-muted">无</span>'}
                            </div>
                        </div>
                        <div class="col-md-6 mb-2">
                            <div class="d-flex flex-wrap">
                                <small class="text-muted me-2">关键提示:</small>
                                ${creative.key_notes ? `<span class="badge bg-warning text-dark">${creative.key_notes}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    ${creative.keywords ? `
                    <div class="d-flex flex-wrap mt-2">
                        <small class="text-muted me-2">关键词:</small>
                        ${creative.keywords.slice(0, 4).map(keyword => 
                            `<span class="badge bg-secondary me-1">${keyword}</span>`
                        ).join('')}
                    </div>
                    ` : ''}
                </div>
                <div class="ms-3 creative-actions">
                    <button class="btn btn-outline-primary btn-sm mb-2" 
                            onclick="showCreativeDetail(${index})" 
                            title="查看详情">
                        <i class="bi bi-eye me-1"></i>详情
                    </button>
                    <button class="btn btn-sm ${selectedCreatives.has(index) ? 'btn-success' : 'btn-outline-success'}" 
                            onclick="toggleCreativeSelection(${index})"
                            title="${selectedCreatives.has(index) ? '取消选择' : '选择创意'}">
                        <i class="bi bi-${selectedCreatives.has(index) ? 'check-circle-fill' : 'circle'} me-1"></i>
                        ${selectedCreatives.has(index) ? '已选' : '选择'}
                    </button>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    container.innerHTML = creativesHtml;
    
    // 添加动画效果
    container.querySelectorAll('.creative-card').forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 50);
    });
}

// 切换创意选择状态
function toggleCreativeSelection(index) {
    if (selectedCreatives.has(index)) {
        selectedCreatives.delete(index);
    } else {
        selectedCreatives.add(index);
    }
    
    renderCreatives();
    updateStats();
}

// 全选创意
function selectAllCreatives() {
    generatedCreatives.forEach((_, index) => {
        selectedCreatives.add(index);
    });
    renderCreatives();
    updateStats();
}

// 取消全选创意
function deselectAllCreatives() {
    selectedCreatives.clear();
    renderCreatives();
    updateStats();
}

// 显示创意详情
function showCreativeDetail(index) {
    currentCreativeIndex = index;
    const creative = generatedCreatives[index];
    
    const detailHtml = `
        <div class="row">
            <div class="col-12">
                <div class="mb-3">
                    <h6>核心概念</h6>
                    <div class="bg-light p-2 rounded">${creative.core_concept || creative.title || '暂无概念'}</div>
                </div>
                <div class="mb-3">
                    <h6>画面描述</h6>
                    <div class="bg-light p-3 rounded">${creative.scene_description || creative.content || '暂无描述'}</div>
                </div>
                ${creative.camera_lighting ? `
                <div class="mb-3">
                    <h6>镜头/光线处理</h6>
                    <div class="bg-light p-3 rounded">${creative.camera_lighting}</div>
                </div>
                ` : ''}
                ${creative.color_props ? `
                <div class="mb-3">
                    <h6>色彩与道具细节</h6>
                    <div class="bg-light p-3 rounded">${creative.color_props}</div>
                </div>
                ` : ''}
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <h6>使用维度</h6>
                    <div class="d-flex flex-wrap">
                        ${(creative.chosen_dimensions || []).map(dim => `
                            <span class="badge bg-primary me-1 mb-1">${dim}</span>
                        `).join('') || '<span class="text-muted">无选定维度</span>'}
                    </div>
                </div>
                ${creative.keywords ? `
                <div class="mb-3">
                    <h6>关键词</h6>
                    <div class="d-flex flex-wrap">
                        ${creative.keywords.map(keyword => `
                            <span class="badge bg-secondary me-1 mb-1">${keyword}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
            <div class="col-md-6">
                ${creative.key_notes ? `
                <div class="mb-3">
                    <h6>关键注意事项</h6>
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        ${creative.key_notes}
                    </div>
                </div>
                ` : ''}
                ${creative.visual_hints && creative.visual_hints.length > 0 ? `
                <div class="mb-3">
                    <h6>视觉提示</h6>
                    <div class="d-flex flex-wrap">
                        ${creative.visual_hints.map(hint => `
                            <span class="badge bg-info me-1 mb-1">${hint}</span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                ${creative.dimension_details ? `
                <div class="mb-3">
                    <h6>维度详细信息</h6>
                    <div class="small text-muted">
                        ${Object.entries(creative.dimension_details).map(([dimName, dimInfo]) => `
                            <div class="mb-2">
                                <strong>${dimName}:</strong> ${dimInfo.name}
                                <div class="text-muted">${dimInfo.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.getElementById('creative-detail-content').innerHTML = detailHtml;
    
    // 更新模态框按钮状态
    const toggleBtn = document.getElementById('toggle-creative-selection');
    toggleBtn.className = selectedCreatives.has(index) ? 
        'btn btn-success' : 'btn btn-outline-success';
    toggleBtn.textContent = selectedCreatives.has(index) ? '✅ 已选择' : '⭕ 选择';
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('creativeDetailModal'));
    modal.show();
}

// 切换当前查看创意的选择状态
function toggleCurrentCreativeSelection() {
    if (currentCreativeIndex >= 0) {
        toggleCreativeSelection(currentCreativeIndex);
        // 更新模态框按钮状态
        const toggleBtn = document.getElementById('toggle-creative-selection');
        toggleBtn.className = selectedCreatives.has(currentCreativeIndex) ? 
            'btn btn-success' : 'btn btn-outline-success';
        toggleBtn.textContent = selectedCreatives.has(currentCreativeIndex) ? '✅ 已选择' : '⭕ 选择';
    }
}

// 保存选中的创意
async function saveSelectedCreatives() {
    if (selectedCreatives.size === 0) {
        showMessage('请先选择要保存的创意', 'warning');
        return;
    }
    
    const selectedData = Array.from(selectedCreatives).map(index => generatedCreatives[index]);
    
    try {
        const response = await makeRequest('/api/save-creatives', 'POST', {
            creatives: selectedData
        });
        
        if (response.success) {
            showMessage(`成功保存 ${selectedCreatives.size} 个创意！`, 'success');
            // 可以选择清空当前生成的创意或保持现状
            // selectedCreatives.clear();
            // renderCreatives();
            // updateStats();
        } else {
            showMessage('保存创意失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showMessage('保存创意失败: ' + error.message, 'danger');
    }
}

// 更新创意数量选项（根据选择的模型）
function updateCreativeCountOptions() {
    const creativeCountSelect = document.getElementById('creative-count');
    
    if (!creativeCountSelect) {
        console.error('❌ 找不到 creative-count 元素');
        return;
    }
    
    const selectedModel = document.querySelector('input[name="ai-model"]:checked')?.value || 'gpt-5-nano';
    
    // 清空现有选项
    creativeCountSelect.innerHTML = '';
    
    // 根据模型添加选项
    let options = [];
    if (selectedModel === 'gpt-5-mini') {
        // GPT-5-mini: 1, 2, 3个选项
        options = [
            { value: 1, text: '1个', selected: false },
            { value: 2, text: '2个', selected: true },  // 默认选择2个
            { value: 3, text: '3个', selected: false }
        ];
    } else if (selectedModel === 'gpt-5-nano') {
        // GPT-5-nano: 1, 3, 5, 10个选项
        options = [
            { value: 1, text: '1个', selected: false },
            { value: 3, text: '3个', selected: false },
            { value: 5, text: '5个', selected: true },  // 默认选择5个
            { value: 10, text: '10个', selected: false }
        ];
    }
    
    // 添加选项到select元素
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        if (opt.selected) option.selected = true;
        creativeCountSelect.appendChild(option);
    });
    
    // 更新成本提示（可选）
    updateCostHint(selectedModel, creativeCountSelect.value);
}

// 更新成本提示（可选功能）
function updateCostHint(model, count) {
    const costHint = document.getElementById('cost-hint');
    if (costHint) {
        const costs = {
            'gpt-5-nano': { min: 0.01, max: 0.02 },  // 每个创意的估计成本
            'gpt-5-mini': { min: 0.05, max: 0.10 }   // 每个创意的估计成本
        };
        
        const modelCost = costs[model] || costs['gpt-5-nano'];
        const estimatedMin = (modelCost.min * count).toFixed(2);
        const estimatedMax = (modelCost.max * count).toFixed(2);
        
        costHint.textContent = `预计成本约$${estimatedMin}-${estimatedMax}`;
    }
}

// 这个函数已经在主DOMContentLoaded中处理了，不需要重复