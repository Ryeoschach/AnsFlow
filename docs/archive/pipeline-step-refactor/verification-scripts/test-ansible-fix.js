console.log('Testing Ansible step fix...')

// 模拟一个ansible步骤数据
const mockAnsibleStep = {
  id: 1,
  name: 'Deploy Nginx',
  step_type: 'ansible',
  description: '使用Ansible自动化部署Nginx',
  parameters: {
    playbook_id: 4,
    inventory_id: 3,
    credential_id: 3,
    extra_vars: { nginx_port: 80 },
    check_mode: false
  },
  order: 1,
  pipeline: 1,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z'
}

console.log('Original step:', mockAnsibleStep)

// 测试保存逻辑
const formValues = {
  name: 'Deploy Nginx Updated',
  step_type: 'ansible',
  description: '使用Ansible自动化部署Nginx - 更新版',
  order: 1,
  parameters: '{"extra_vars": {"nginx_port": 8080}, "check_mode": true}',
  ansible_playbook_id: 5,
  ansible_inventory_id: 4,
  ansible_credential_id: 4
}

console.log('Form values:', formValues)

// 模拟handleStepSubmit逻辑
let parameters = {}
if (formValues.parameters) {
  try {
    parameters = JSON.parse(formValues.parameters)
  } catch (e) {
    console.error('参数格式错误')
  }
}

// 处理ansible步骤的特殊字段
if (formValues.step_type === 'ansible') {
  // 将ansible相关字段添加到parameters中（主要存储方式）
  parameters = {
    ...parameters,
    playbook_id: formValues.ansible_playbook_id,
    inventory_id: formValues.ansible_inventory_id,
    credential_id: formValues.ansible_credential_id
  }
}

const stepData = {
  ...formValues,
  parameters,
  // 同时保存为独立字段（兼容性）
  ansible_playbook: formValues.step_type === 'ansible' ? formValues.ansible_playbook_id : undefined,
  ansible_inventory: formValues.step_type === 'ansible' ? formValues.ansible_inventory_id : undefined,
  ansible_credential: formValues.step_type === 'ansible' ? formValues.ansible_credential_id : undefined
}

console.log('Processed step data:', stepData)

// 模拟更新后的步骤
const updatedStep = {
  ...mockAnsibleStep,
  ...stepData
}

console.log('Updated step:', updatedStep)

// 测试加载逻辑
console.log('\n--- Testing load logic ---')
const loadFormValues = {
  name: updatedStep.name,
  step_type: updatedStep.step_type,
  description: updatedStep.description,
  order: updatedStep.order,
  parameters: JSON.stringify(updatedStep.parameters, null, 2)
}

// 如果是ansible步骤，从parameters中提取ansible相关字段
if (updatedStep.step_type === 'ansible' && updatedStep.parameters) {
  // 优先从parameters中读取（主要存储方式）
  loadFormValues.ansible_playbook_id = updatedStep.parameters.playbook_id || 
                                       updatedStep.ansible_playbook || 
                                       undefined
  loadFormValues.ansible_inventory_id = updatedStep.parameters.inventory_id || 
                                        updatedStep.ansible_inventory || 
                                        undefined
  loadFormValues.ansible_credential_id = updatedStep.parameters.credential_id || 
                                         updatedStep.ansible_credential || 
                                         undefined
  
  // 清理parameters中的ansible字段，避免重复显示
  const cleanParameters = { ...updatedStep.parameters }
  delete cleanParameters.playbook_id
  delete cleanParameters.inventory_id
  delete cleanParameters.credential_id
  loadFormValues.parameters = JSON.stringify(cleanParameters, null, 2)
}

console.log('Loaded form values:', loadFormValues)
console.log('Expected ansible IDs:', {
  playbook: 5,
  inventory: 4,
  credential: 4
})

// 验证结果
const success = loadFormValues.ansible_playbook_id === 5 &&
                loadFormValues.ansible_inventory_id === 4 &&
                loadFormValues.ansible_credential_id === 4

console.log('\n--- Test Result ---')
console.log('Test passed:', success)
if (!success) {
  console.log('❌ Ansible step save/load test failed!')
} else {
  console.log('✅ Ansible step save/load test passed!')
}
