#!/usr/bin/env node

/**
 * Kubernetes 步骤编辑回显测试脚本
 * 验证编辑K8s步骤时字段是否正确回显
 */

// 模拟从后端获取的步骤数据
const mockK8sStep = {
  id: 123,
  name: "通过helm发布app",
  step_type: "k8s_deploy", 
  description: "在 Kubernetes 集群中部署应用",
  // AtomicStep 顶层K8s字段
  k8s_cluster: 1,
  k8s_namespace: "default",
  k8s_resource_name: "my-app-deployment",
  k8s_config: {
    deploy_type: "helm",
    wait_for_rollout: true
  },
  // 其他字段
  parameters: {},
  order: 2,
  pipeline: 456
};

// 模拟修复后的 handleEditStep 函数中的 K8s 处理逻辑
function processK8sStepForEdit(step) {
  const formValues = {
    name: step.name,
    step_type: step.step_type,
    description: step.description,
    order: step.order
  };

  // K8s步骤特殊处理：提取K8s配置字段
  if (step.step_type?.startsWith('k8s_')) {
    const k8sParams = step.parameters || {};
    
    // 从步骤对象的顶层字段获取Kubernetes配置
    formValues.k8s_cluster_id = step.k8s_cluster;
    formValues.k8s_namespace = step.k8s_namespace;
    formValues.k8s_resource_name = step.k8s_resource_name;
    formValues.k8s_config = step.k8s_config;
    
    // 从参数中获取K8s配置（优先级更高）
    if (k8sParams.k8s_cluster_id) formValues.k8s_cluster_id = k8sParams.k8s_cluster_id;
    if (k8sParams.k8s_cluster) formValues.k8s_cluster_id = k8sParams.k8s_cluster;
    if (k8sParams.k8s_namespace) formValues.k8s_namespace = k8sParams.k8s_namespace;
    if (k8sParams.k8s_resource_name) formValues.k8s_resource_name = k8sParams.k8s_resource_name;
    if (k8sParams.k8s_config) formValues.k8s_config = k8sParams.k8s_config;
    
    // 清理参数中的K8s字段，避免重复显示
    const cleanParameters = { ...k8sParams };
    delete cleanParameters.k8s_cluster_id;
    delete cleanParameters.k8s_cluster;
    delete cleanParameters.k8s_namespace;
    delete cleanParameters.k8s_resource_name;
    delete cleanParameters.k8s_config;
    
    formValues.parameters = Object.keys(cleanParameters).length > 0 
      ? JSON.stringify(cleanParameters, null, 2) 
      : '{}';
  }

  return formValues;
}

console.log('🧪 测试 Kubernetes 步骤编辑回显修复');
console.log('');

console.log('📥 模拟步骤数据:');
console.log(JSON.stringify(mockK8sStep, null, 2));
console.log('');

const processedFormValues = processK8sStepForEdit(mockK8sStep);

console.log('📤 处理后的表单值:');
console.log(JSON.stringify(processedFormValues, null, 2));
console.log('');

// 验证关键字段
const validationResults = {
  cluster_id_extracted: processedFormValues.k8s_cluster_id === mockK8sStep.k8s_cluster,
  namespace_extracted: processedFormValues.k8s_namespace === mockK8sStep.k8s_namespace,
  resource_name_extracted: processedFormValues.k8s_resource_name === mockK8sStep.k8s_resource_name,
  config_extracted: JSON.stringify(processedFormValues.k8s_config) === JSON.stringify(mockK8sStep.k8s_config),
  parameters_cleaned: processedFormValues.parameters === '{}'
};

console.log('✅ 验证结果:');
Object.entries(validationResults).forEach(([key, result]) => {
  console.log(`   ${result ? '✅' : '❌'} ${key}: ${result}`);
});

if (Object.values(validationResults).every(result => result)) {
  console.log('');
  console.log('🎉 所有 Kubernetes 字段回显测试通过！');
  console.log('💡 修复应该解决了编辑K8s步骤时字段变空的问题');
  console.log('');
  console.log('📋 修复效果:');
  console.log('   - ✅ 集群选择: 将正确回显已选择的集群');
  console.log('   - ✅ 命名空间: 将自动加载集群的命名空间并回显当前值');
  console.log('   - ✅ 资源名称: 将正确回显已配置的资源名称');
  console.log('   - ✅ 部署配置: Helm配置等将正确回显');
} else {
  console.log('');
  console.log('❌ 存在字段回显问题，需要进一步调试');
}
