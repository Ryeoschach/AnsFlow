/**
 * 并行组步骤关联调试脚本
 * 在浏览器控制台中运行，用于调试步骤关联问题
 */

// 调试工具对象
window.AnsFlowDebugger = {
    
    // 检查当前页面的并行组数据
    checkParallelGroupData() {
        console.log('🔍 检查当前页面并行组数据...');
        
        // 尝试从React DevTools获取组件状态
        const reactFiber = document.querySelector('[data-reactroot]')?._reactInternalFiber;
        if (reactFiber) {
            console.log('✅ React应用已找到');
        } else {
            console.log('⚠️ 无法找到React应用');
        }
        
        // 检查localStorage中的数据
        const authToken = localStorage.getItem('authToken');
        console.log('🔑 认证令牌:', authToken ? '已设置' : '未设置');
        
        return true;
    },
    
    // 模拟API调用测试
    async testApiCalls() {
        console.log('🔄 测试API调用...');
        
        const baseUrl = 'http://localhost:8000/api/v1/pipelines';
        const headers = {
            'Content-Type': 'application/json'
        };
        
        try {
            // 测试获取流水线
            const pipelineResponse = await fetch(`${baseUrl}/pipelines/`, { headers });
            if (pipelineResponse.ok) {
                const pipelines = await pipelineResponse.json();
                console.log('✅ 流水线API正常，共', pipelines.length, '个流水线');
                
                if (pipelines.length > 0) {
                    const pipeline = pipelines[0];
                    console.log('📋 选择流水线:', pipeline.name, '(ID:', pipeline.id, ')');
                    
                    // 测试获取并行组
                    const groupResponse = await fetch(`${baseUrl}/parallel-groups/?pipeline=${pipeline.id}`, { headers });
                    if (groupResponse.ok) {
                        const groupData = await groupResponse.json();
                        const groups = groupData.results || groupData;
                        console.log('✅ 并行组API正常，共', groups.length, '个并行组');
                        
                        groups.forEach(group => {
                            console.log(`  - ${group.name} (${group.steps?.length || 0} 个步骤)`);
                        });
                    } else {
                        console.log('❌ 并行组API失败:', groupResponse.status);
                    }
                }
            } else {
                console.log('❌ 流水线API失败:', pipelineResponse.status);
            }
        } catch (error) {
            console.log('❌ API调用错误:', error.message);
        }
    },
    
    // 检查表单数据
    checkFormData() {
        console.log('📝 检查表单数据...');
        
        // 查找并行组管理表单
        const modalForms = document.querySelectorAll('.ant-modal form');
        if (modalForms.length > 0) {
            console.log('✅ 找到', modalForms.length, '个模态框表单');
            
            modalForms.forEach((form, index) => {
                console.log(`表单 ${index + 1}:`);
                
                // 查找步骤选择器
                const stepSelectors = form.querySelectorAll('.ant-select[aria-label*="步骤"], .ant-select[placeholder*="步骤"]');
                stepSelectors.forEach((selector, sIndex) => {
                    console.log(`  步骤选择器 ${sIndex + 1}:`, selector);
                    
                    // 获取选中的值
                    const selectedValues = selector.querySelectorAll('.ant-select-selection-item');
                    console.log(`    已选择 ${selectedValues.length} 个步骤`);
                    selectedValues.forEach((item, vIndex) => {
                        console.log(`      ${vIndex + 1}. ${item.textContent}`);
                    });
                });
            });
        } else {
            console.log('⚠️ 没有找到活动的表单');
        }
    },
    
    // 监听表单提交
    monitorFormSubmit() {
        console.log('👀 开始监听表单提交...');
        
        // 监听所有fetch请求
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const [url, options] = args;
            
            if (url.includes('parallel-groups')) {
                console.log('🔄 并行组API调用:', options?.method || 'GET', url);
                
                if (options?.body) {
                    try {
                        const data = JSON.parse(options.body);
                        console.log('📤 请求数据:', data);
                        
                        if (data.steps) {
                            console.log('📋 包含步骤:', data.steps);
                        }
                    } catch (e) {
                        console.log('📤 请求数据 (非JSON):', options.body);
                    }
                }
            }
            
            return originalFetch.apply(this, args).then(response => {
                if (url.includes('parallel-groups')) {
                    console.log('📥 响应状态:', response.status);
                    
                    // 克隆响应以读取内容
                    const clonedResponse = response.clone();
                    clonedResponse.json().then(data => {
                        console.log('📥 响应数据:', data);
                    }).catch(() => {
                        console.log('📥 响应不是JSON格式');
                    });
                }
                
                return response;
            });
        };
        
        console.log('✅ 表单监听已启动');
    },
    
    // 停止监听
    stopMonitoring() {
        // 恢复原始fetch（如果之前被替换过）
        if (window.originalFetch) {
            window.fetch = window.originalFetch;
            delete window.originalFetch;
            console.log('✅ 监听已停止');
        }
    },
    
    // 运行完整诊断
    async runFullDiagnosis() {
        console.log('🧪 运行完整诊断...');
        console.log('=' * 50);
        
        this.checkParallelGroupData();
        await this.testApiCalls();
        this.checkFormData();
        this.monitorFormSubmit();
        
        console.log('✅ 诊断完成');
        console.log('💡 提示:');
        console.log('  1. 打开并行组管理界面');
        console.log('  2. 尝试创建或编辑并行组');
        console.log('  3. 观察控制台输出的调试信息');
        console.log('  4. 使用 AnsFlowDebugger.checkFormData() 检查表单状态');
    },
    
    // 显示帮助信息
    help() {
        console.log('🔧 AnsFlow 并行组调试工具');
        console.log('可用命令:');
        console.log('  AnsFlowDebugger.checkParallelGroupData() - 检查页面数据');
        console.log('  AnsFlowDebugger.testApiCalls() - 测试API调用');
        console.log('  AnsFlowDebugger.checkFormData() - 检查表单数据');
        console.log('  AnsFlowDebugger.monitorFormSubmit() - 监听表单提交');
        console.log('  AnsFlowDebugger.stopMonitoring() - 停止监听');
        console.log('  AnsFlowDebugger.runFullDiagnosis() - 运行完整诊断');
        console.log('  AnsFlowDebugger.help() - 显示此帮助');
    }
};

// 自动运行基本检查
console.log('🔧 AnsFlow 并行组调试工具已加载');
console.log('输入 AnsFlowDebugger.help() 查看可用命令');
console.log('输入 AnsFlowDebugger.runFullDiagnosis() 运行完整诊断');

// 自动检查基本状态
AnsFlowDebugger.checkParallelGroupData();
