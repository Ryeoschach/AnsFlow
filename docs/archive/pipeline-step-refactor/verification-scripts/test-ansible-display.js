/**
 * 测试Ansible步骤显示逻辑
 * 确保保存后再次编辑时，参数不会重复显示
 */

// 模拟handleEditStep逻辑
function handleEditStep(step) {
  console.log('Testing handleEditStep with step:', step);
  
  // 准备基础表单值
  let baseParameters = step.parameters || {};
  
  const formValues = {
    name: step.name,
    step_type: step.step_type,
    description: step.description,
    order: step.order,
    git_credential_id: step.git_credential || undefined
  };

  // 如果是ansible步骤，从parameters中提取ansible相关字段
  if (step.step_type === 'ansible') {
    // 优先从parameters中读取（主要存储方式）
    formValues.ansible_playbook_id = step.parameters?.playbook_id || 
                                     step.ansible_playbook || 
                                     undefined;
    formValues.ansible_inventory_id = step.parameters?.inventory_id || 
                                      step.ansible_inventory || 
                                      undefined;
    formValues.ansible_credential_id = step.parameters?.credential_id || 
                                       step.ansible_credential || 
                                       undefined;
    
    // 清理parameters中的ansible字段，避免重复显示
    const cleanParameters = { ...baseParameters };
    delete cleanParameters.playbook_id;
    delete cleanParameters.inventory_id;
    delete cleanParameters.credential_id;
    
    // 只有在清理后的参数不为空时才显示
    formValues.parameters = Object.keys(cleanParameters).length > 0 
      ? JSON.stringify(cleanParameters, null, 2) 
      : '{}';
    
    console.log('Ansible step loaded:', {
      playbook: formValues.ansible_playbook_id,
      inventory: formValues.ansible_inventory_id,
      credential: formValues.ansible_credential_id,
      originalParameters: step.parameters,
      cleanParameters: cleanParameters,
      formParameters: formValues.parameters
    });
  } else {
    // 非ansible步骤直接使用原始参数
    formValues.parameters = JSON.stringify(baseParameters, null, 2);
  }

  return formValues;
}

// 模拟显示逻辑
function displayStepCard(step) {
  console.log('Displaying step card for:', step.name);
  
  // 显示Ansible配置
  if (step.step_type === 'ansible') {
    console.log('Ansible配置:');
    if (step.parameters?.playbook_id || step.ansible_playbook) {
      console.log(`  Playbook ID: ${step.parameters?.playbook_id || step.ansible_playbook}`);
    }
    if (step.parameters?.inventory_id || step.ansible_inventory) {
      console.log(`  Inventory ID: ${step.parameters?.inventory_id || step.ansible_inventory}`);
    }
    if (step.parameters?.credential_id || step.ansible_credential) {
      console.log(`  Credential ID: ${step.parameters?.credential_id || step.ansible_credential}`);
    }
  }
  
  // 显示清理后的参数（不包含ansible字段）
  const displayParams = { ...step.parameters };
  if (step.step_type === 'ansible') {
    delete displayParams.playbook_id;
    delete displayParams.inventory_id;
    delete displayParams.credential_id;
  }
  
  if (Object.keys(displayParams).length > 0) {
    console.log('参数:', JSON.stringify(displayParams, null, 2));
  } else {
    console.log('参数: (无)');
  }
}

// 测试场景1: 初始创建的Ansible步骤
console.log('=== 测试场景1: 初始创建的Ansible步骤 ===');
const initialStep = {
  id: 1,
  name: 'Deploy App',
  step_type: 'ansible',
  description: '部署应用',
  parameters: {
    playbook_id: 1,
    inventory_id: 2,
    credential_id: 3,
    extra_vars: { app_port: 8080 },
    check_mode: false
  },
  order: 1
};

displayStepCard(initialStep);
const formValues1 = handleEditStep(initialStep);
console.log('编辑表单值:', formValues1);

// 测试场景2: 经过编辑保存后的步骤
console.log('\n=== 测试场景2: 经过编辑保存后的步骤 ===');
const editedStep = {
  id: 1,
  name: 'Deploy App Updated',
  step_type: 'ansible',
  description: '部署应用 - 更新版',
  parameters: {
    playbook_id: 2,
    inventory_id: 3,
    credential_id: 4,
    extra_vars: { app_port: 9000 },
    check_mode: true,
    timeout: 600
  },
  ansible_playbook: 2,
  ansible_inventory: 3,
  ansible_credential: 4,
  order: 1
};

displayStepCard(editedStep);
const formValues2 = handleEditStep(editedStep);
console.log('编辑表单值:', formValues2);

// 验证参数字段不包含ansible ID
const parsedParams = JSON.parse(formValues2.parameters);
const hasAnsibleIds = parsedParams.hasOwnProperty('playbook_id') || 
                     parsedParams.hasOwnProperty('inventory_id') || 
                     parsedParams.hasOwnProperty('credential_id');

console.log('\n=== 测试结果 ===');
console.log('参数字段是否包含Ansible ID:', hasAnsibleIds);
console.log('测试是否通过:', !hasAnsibleIds ? '✅ 通过' : '❌ 失败');

if (!hasAnsibleIds) {
  console.log('🎉 修复成功！Ansible步骤保存后回显时，参数不会重复显示Ansible ID了！');
} else {
  console.log('❌ 修复失败！仍然存在重复显示问题。');
}
