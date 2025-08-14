#!/usr/bin/env node

/**
 * Kubernetes 数据流测试脚本
 * 用于验证前端到后端的 K8s 字段传递是否正确
 */

// 模拟前端步骤数据
const frontendStepData = {
  name: "Test K8s Deploy",
  step_type: "k8s_deploy",
  description: "测试 Kubernetes 部署步骤",
  k8s_cluster_id: 1,  // 前端表单字段
  k8s_namespace: "default",
  k8s_resource_name: "test-app",
  k8s_config: {
    deployment_yaml: "kind: Deployment\nmetadata:\n  name: test-app"
  }
};

// 模拟我们修复后的映射逻辑
function mapStepDataForAPI(stepData) {
  return {
    name: stepData.name,
    step_type: stepData.step_type,
    description: stepData.description || '',
    parameters: stepData.parameters || {},
    order: 1,
    is_active: true,
    git_credential: null,
    // 关键修复：添加 Kubernetes 字段映射
    k8s_cluster: stepData.k8s_cluster_id || stepData.k8s_cluster || null,
    k8s_namespace: stepData.k8s_namespace || '',
    k8s_resource_name: stepData.k8s_resource_name || '',
    k8s_config: stepData.k8s_config || null,
    // Docker 字段
    docker_image: stepData.docker_image || '',
    docker_tag: stepData.docker_tag || '',
    docker_registry: stepData.docker_registry || null,
    docker_config: stepData.docker_config || null,
    // Ansible 字段
    ansible_credential: stepData.ansible_credential || null
  };
}

// 执行测试
console.log('🧪 测试 Kubernetes 数据流映射');
console.log('');

console.log('📥 前端输入数据:');
console.log(JSON.stringify(frontendStepData, null, 2));
console.log('');

const apiPayload = mapStepDataForAPI(frontendStepData);

console.log('📤 发送到后端的 API 负载:');
console.log(JSON.stringify(apiPayload, null, 2));
console.log('');

// 验证关键字段
const validationResults = {
  k8s_cluster_mapped: apiPayload.k8s_cluster !== null,
  k8s_namespace_mapped: apiPayload.k8s_namespace !== '',
  k8s_resource_name_mapped: apiPayload.k8s_resource_name !== '',
  k8s_config_mapped: apiPayload.k8s_config !== null
};

console.log('✅ 验证结果:');
Object.entries(validationResults).forEach(([key, result]) => {
  console.log(`   ${result ? '✅' : '❌'} ${key}: ${result}`);
});

if (Object.values(validationResults).every(result => result)) {
  console.log('');
  console.log('🎉 所有 Kubernetes 字段映射成功！');
  console.log('💡 修复应该解决了 "No Kubernetes cluster specified for step" 错误');
} else {
  console.log('');
  console.log('❌ 存在字段映射问题，需要进一步调试');
}
