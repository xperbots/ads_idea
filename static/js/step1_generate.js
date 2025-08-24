// 现代化广告创意生成器 JavaScript 功能
let dimensionsConfig = [];
let generatedCreatives = [];
let selectedCreatives = new Set();
let currentCreativeIndex = -1;
let collapsedDimensions = new Set();
let editingElement = null;
let customInputs = {};

document.addEventListener('DOMContentLoaded', function() {
    // 初始化
    loadDimensionsConfig();
    loadCustomInputs();
    updateStats();
    
    // 绑定基础事件
    document.getElementById('generate-btn').addEventListener('click', handleGenerateCreatives);
    document.getElementById('clear-all-btn').addEventListener('click', clearAllSelections);
    document.getElementById('batch-select-btn').addEventListener('click', selectAllCreatives);
    document.getElementById('batch-deselect-btn').addEventListener('click', deselectAllCreatives);
    document.getElementById('save-selected-btn').addEventListener('click', saveSelectedCreatives);
    
    // 绑定新功能事件
    document.getElementById('fetch-trends-btn').addEventListener('click', fetchTrendingTopics);
    document.getElementById('idea-input').addEventListener('input', updateIdeaInput);
    
    // 绑定模态框事件
    const modal = document.getElementById('creativeDetailModal');
    if (modal) {
        document.getElementById('toggle-creative-selection').addEventListener('click', toggleCurrentCreativeSelection);
    }
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

// 增强的流行主题获取功能
async function fetchTrendingTopics() {
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
    
    try {
        const response = await makeRequest('/api/trending-topics', 'POST', {
            country_code: countryCode,
            time_range: timeRange,
            top_n: topN
        });
        
        if (response.success || response.fallback) {
            const topics = response.data || [];
            displayTrendingTopics(topics, {
                country: countryName,
                timeRange: timeRangeName,
                isFallback: response.fallback,
                actualCount: topics.length
            });
            
            if (response.fallback) {
                showMessage(`⚠️ ${response.message}`, 'warning');
            } else {
                showMessage(`🎉 成功获取${countryName}${timeRangeName}热门话题！`, 'success');
            }
        } else {
            showMessage('获取热门话题失败: ' + response.message, 'danger');
        }
    } catch (error) {
        console.error('Fetch trending topics error:', error);
        showMessage('获取流行主题失败: ' + error.message, 'danger');
        
        // 显示备用数据
        const fallbackTopics = getFallbackTopics(countryCode, topN);
        displayTrendingTopics(fallbackTopics, {
            country: countryName,
            timeRange: timeRangeName,
            isFallback: true,
            actualCount: fallbackTopics.length
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
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

// 增强的显示流行主题功能
function displayTrendingTopics(topics, metadata = {}) {
    const container = document.getElementById('topics-container');
    const topicsDiv = document.getElementById('trending-topics');
    const headerElement = topicsDiv.querySelector('p.fw-bold');
    const sourceInfoElement = topicsDiv.querySelector('.source-info p');
    
    // 更新头部信息
    const {country, timeRange, isFallback, actualCount} = metadata;
    let headerText = `热门话题：`;
    if (country && timeRange) {
        headerText += `${country} ${timeRange}`;
    }
    if (isFallback) {
        headerText += ` <span class="text-warning">(备用数据)</span>`;
    }
    if (actualCount) {
        headerText += ` <span class="badge bg-primary ms-2">${actualCount}个</span>`;
    }
    
    if (headerElement) {
        headerElement.innerHTML = headerText;
    }
    
    // 渲染话题标签
    if (topics && topics.length > 0) {
        container.innerHTML = topics.map((topic, index) => `
            <span class="topic-badge ${isFallback ? 'fallback' : ''}" 
                  onclick="selectTopic('${topic.replace(/'/g, "\\'")}', '${country || ''}')"
                  title="${isFallback ? '备用数据 - 点击使用' : '来自Google Trends - 点击使用'}">
                ${getTopicIcon(index, isFallback)} ${topic}
            </span>
        `).join('');
    } else {
        container.innerHTML = '<p class="text-muted text-center m-0">暂无热门话题数据</p>';
    }
    
    // 更新数据来源说明
    if (sourceInfoElement) {
        sourceInfoElement.innerHTML = `
            <i class="bi bi-info-circle me-1"></i>
            ${isFallback ? 
                '<span class="text-warning">⚠️ 当前显示备用数据</span> | 请检查网络连接后重试' :
                '<span class="text-success">🔍 来自 Google Trends</span> | 📊 实时数据 | ' + new Date().toLocaleString('zh-CN')
            }
        `;
    }
    
    // 显示热门话题区域
    topicsDiv.style.display = 'block';
    
    // 添加淡入动画
    topicsDiv.style.opacity = '0';
    topicsDiv.style.transform = 'translateY(10px)';
    setTimeout(() => {
        topicsDiv.style.transition = 'all 0.5s ease';
        topicsDiv.style.opacity = '1';
        topicsDiv.style.transform = 'translateY(0)';
    }, 50);
}

// 获取话题图标
function getTopicIcon(index, isFallback) {
    if (isFallback) {
        return '💡'; // 备用数据图标
    }
    return index % 2 === 0 ? '🔍' : '📱'; // 交替显示图标
}

// 选择主题
function selectTopic(topic, country = '') {
    const input = document.getElementById('idea-input');
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
    const input = document.getElementById('idea-input');
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
    const checkboxes = document.querySelectorAll('.dimension-option:checked');
    const selectedDimensions = new Set();
    
    checkboxes.forEach(checkbox => {
        selectedDimensions.add(checkbox.dataset.dimension);
    });
    
    // 更新统计数字
    document.getElementById('selected-dimensions-count').textContent = selectedDimensions.size;
    document.getElementById('selected-options-count').textContent = checkboxes.length;
    document.getElementById('selected-elements-count').textContent = checkboxes.length;
    document.getElementById('generated-count').textContent = generatedCreatives.length;
    document.getElementById('selected-creatives-count').textContent = selectedCreatives.size;
    document.getElementById('save-count').textContent = selectedCreatives.size;
    
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

// 增强的处理生成创意请求
async function handleGenerateCreatives(event) {
    event.preventDefault();
    
    // 获取创意想法
    const ideaInput = document.getElementById('idea-input').value.trim();
    
    // 获取选中的维度和选项
    const selectedDimensions = getSelectedDimensions();
    
    // 获取自定义输入内容
    const customInputsData = {};
    for (const [dimensionName, content] of Object.entries(customInputs)) {
        if (content && content.trim()) {
            customInputsData[dimensionName] = content.trim();
        }
    }
    
    // 验证输入
    if (!ideaInput && Object.keys(selectedDimensions).length === 0 && Object.keys(customInputsData).length === 0) {
        showMessage('请输入创意想法、选择元素或填写自定义内容', 'warning');
        return;
    }
    
    const count = parseInt(document.getElementById('creative-count').value);
    
    // 显示加载状态
    showLoading('generation-progress');
    document.getElementById('loading-spinner').style.display = 'inline-block';
    document.getElementById('generate-btn').disabled = true;
    
    try {
        const requestData = {
            idea: ideaInput,
            selected_dimensions: selectedDimensions,
            custom_inputs: customInputsData,
            count: count
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
    
    const creativesHtml = generatedCreatives.map((creative, index) => `
        <div class="creative-card ${selectedCreatives.has(index) ? 'selected' : ''}" 
             data-index="${index}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-3">
                        <span class="badge bg-primary me-2">#${creative.index}</span>
                        <h5 class="creative-title mb-0">${creative.title}</h5>
                    </div>
                    <div class="creative-content mb-3">${creative.content}</div>
                    <div class="row creative-meta">
                        <div class="col-md-6 mb-2">
                            <div class="d-flex flex-wrap">
                                <small class="text-muted me-2">选用维度:</small>
                                ${creative.chosen_dimensions.map(dim => 
                                    `<span class="badge bg-light text-dark me-1">${dim}</span>`
                                ).join('')}
                            </div>
                        </div>
                        <div class="col-md-6 mb-2">
                            <div class="d-flex flex-wrap">
                                <small class="text-muted me-2">关键词:</small>
                                ${creative.keywords.slice(0, 4).map(keyword => 
                                    `<span class="badge bg-secondary me-1">${keyword}</span>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="d-flex flex-wrap mt-2">
                        <small class="text-muted me-2">视觉提示:</small>
                        ${creative.visual_hints.slice(0, 3).map(hint => 
                            `<span class="badge bg-info text-dark me-1">${hint}</span>`
                        ).join('')}
                    </div>
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
    `).join('');
    
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
                    <h6>创意标题</h6>
                    <div class="bg-light p-2 rounded">${creative.title}</div>
                </div>
                <div class="mb-3">
                    <h6>创意内容</h6>
                    <div class="bg-light p-3 rounded">${creative.content}</div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <h6>使用维度</h6>
                    <div class="d-flex flex-wrap">
                        ${creative.chosen_dimensions.map(dim => `
                            <span class="badge bg-primary me-1 mb-1">${dim}</span>
                        `).join('')}
                    </div>
                </div>
                <div class="mb-3">
                    <h6>关键词</h6>
                    <div class="d-flex flex-wrap">
                        ${creative.keywords.map(keyword => `
                            <span class="badge bg-secondary me-1 mb-1">${keyword}</span>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <h6>视觉提示</h6>
                    <div class="d-flex flex-wrap">
                        ${creative.visual_hints.map(hint => `
                            <span class="badge bg-info me-1 mb-1">${hint}</span>
                        `).join('')}
                    </div>
                </div>
                <div class="mb-3">
                    <h6>详细信息</h6>
                    <div class="small text-muted">
                        ${Object.entries(creative.dimension_details).map(([dimName, dimInfo]) => `
                            <div class="mb-2">
                                <strong>${dimName}:</strong> ${dimInfo.name}
                                <div class="text-muted">${dimInfo.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
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