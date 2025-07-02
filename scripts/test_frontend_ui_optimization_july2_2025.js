#!/usr/bin/env node

/**
 * 前端UI优化验证测试脚本
 * 日期: 2025年7月2日
 * 功能: 验证Select组件样式统一和表格操作列优化效果
 */

const fs = require('fs');
const path = require('path');

// 测试配置
const TEST_CONFIG = {
  projectRoot: '/Users/creed/workspace/sourceCode/AnsFlow',
  frontendRoot: '/Users/creed/workspace/sourceCode/AnsFlow/frontend',
  testFiles: {
    pipelineEditor: '/Users/creed/workspace/sourceCode/AnsFlow/frontend/src/components/pipeline/PipelineEditor.tsx',
    pipelinesPage: '/Users/creed/workspace/sourceCode/AnsFlow/frontend/src/pages/Pipelines.tsx'
  }
};

console.log('🚀 前端UI优化验证测试开始');
console.log('=' .repeat(60));

/**
 * 测试1: 验证Select组件样式CSS注入
 */
function testSelectStylesInjection() {
  console.log('\n📋 测试1: Select组件样式CSS注入验证');
  
  const requiredStyles = [
    '.ant-select-selection-item > div > div:nth-child(2)',
    'display: none !important',
    '.ant-select-selection-item',
    'line-height: 30px !important',
    'overflow: hidden !important'
  ];
  
  const files = [TEST_CONFIG.testFiles.pipelineEditor, TEST_CONFIG.testFiles.pipelinesPage];
  let allTestsPassed = true;
  
  files.forEach((filePath, index) => {
    console.log(`\n  检查文件${index + 1}: ${path.basename(filePath)}`);
    
    if (!fs.existsSync(filePath)) {
      console.log(`  ❌ 文件不存在: ${filePath}`);
      allTestsPassed = false;
      return;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    requiredStyles.forEach(style => {
      if (content.includes(style)) {
        console.log(`  ✅ 找到必需样式: ${style}`);
      } else {
        console.log(`  ❌ 缺少必需样式: ${style}`);
        allTestsPassed = false;
      }
    });
  });
  
  return allTestsPassed;
}

/**
 * 测试2: 验证optionLabelProp配置
 */
function testOptionLabelPropConfig() {
  console.log('\n📋 测试2: optionLabelProp="label" 配置验证');
  
  const files = [TEST_CONFIG.testFiles.pipelineEditor, TEST_CONFIG.testFiles.pipelinesPage];
  let allTestsPassed = true;
  
  files.forEach((filePath, index) => {
    console.log(`\n  检查文件${index + 1}: ${path.basename(filePath)}`);
    
    if (!fs.existsSync(filePath)) {
      console.log(`  ❌ 文件不存在: ${filePath}`);
      allTestsPassed = false;
      return;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 检查optionLabelProp="label"配置
    const optionLabelPropCount = (content.match(/optionLabelProp="label"/g) || []).length;
    
    if (optionLabelPropCount > 0) {
      console.log(`  ✅ 找到${optionLabelPropCount}个optionLabelProp="label"配置`);
      
      // 针对Pipelines.tsx，应该有2个Select组件使用此配置
      if (filePath.includes('Pipelines.tsx') && optionLabelPropCount >= 2) {
        console.log(`  ✅ Pipelines.tsx包含至少2个Select配置（执行模式+执行工具）`);
      } else if (filePath.includes('PipelineEditor.tsx') && optionLabelPropCount >= 1) {
        console.log(`  ✅ PipelineEditor.tsx包含Select配置`);
      }
    } else {
      console.log(`  ❌ 未找到optionLabelProp="label"配置`);
      allTestsPassed = false;
    }
  });
  
  return allTestsPassed;
}

/**
 * 测试3: 验证表格操作列优化
 */
function testTableActionsOptimization() {
  console.log('\n📋 测试3: 表格操作列优化验证');
  
  const filePath = TEST_CONFIG.testFiles.pipelinesPage;
  let allTestsPassed = true;
  
  if (!fs.existsSync(filePath)) {
    console.log(`  ❌ 文件不存在: ${filePath}`);
    return false;
  }
  
  const content = fs.readFileSync(filePath, 'utf8');
  
  // 检查图标按钮配置
  const iconButtonTests = [
    { pattern: 'icon={<EditOutlined />}', description: '编辑图标按钮' },
    { pattern: 'icon={<SettingOutlined />}', description: '配置图标按钮' },
    { pattern: 'Tooltip title="编辑流水线"', description: '编辑按钮Tooltip' },
    { pattern: 'Tooltip title="拖拽式配置"', description: '配置按钮Tooltip' }
  ];
  
  iconButtonTests.forEach(test => {
    if (content.includes(test.pattern)) {
      console.log(`  ✅ ${test.description}: ${test.pattern}`);
    } else {
      console.log(`  ❌ 缺少${test.description}: ${test.pattern}`);
      allTestsPassed = false;
    }
  });
  
  // 检查下拉菜单配置
  if (content.includes('menu={{') && content.includes('trigger={[\'click\']}')) {
    console.log(`  ✅ 下拉菜单配置正确`);
  } else {
    console.log(`  ❌ 下拉菜单配置缺失`);
    allTestsPassed = false;
  }
  
  // 检查是否移除了固定宽度配置
  const fixedWidthPatterns = ['width:', 'fixed:', 'scroll:'];
  let foundFixedWidth = false;
  
  fixedWidthPatterns.forEach(pattern => {
    if (content.includes(pattern) && content.includes('columns:')) {
      // 进一步检查是否在columns配置中
      const lines = content.split('\n');
      let inColumnsConfig = false;
      
      lines.forEach(line => {
        if (line.includes('const columns')) inColumnsConfig = true;
        if (inColumnsConfig && line.includes(pattern) && !line.includes('//')) {
          foundFixedWidth = true;
        }
        if (line.includes(']') && inColumnsConfig) inColumnsConfig = false;
      });
    }
  });
  
  if (!foundFixedWidth) {
    console.log(`  ✅ 已移除表格固定宽度配置`);
  } else {
    console.log(`  ❌ 仍存在表格固定宽度配置`);
    allTestsPassed = false;
  }
  
  return allTestsPassed;
}

/**
 * 测试4: 验证样式注入唯一性
 */
function testStyleInjectionUniqueness() {
  console.log('\n📋 测试4: 样式注入唯一性验证');
  
  const files = [TEST_CONFIG.testFiles.pipelineEditor, TEST_CONFIG.testFiles.pipelinesPage];
  let allTestsPassed = true;
  
  const expectedIds = {
    [TEST_CONFIG.testFiles.pipelineEditor]: 'pipeline-editor-styles',
    [TEST_CONFIG.testFiles.pipelinesPage]: 'pipelines-page-styles'
  };
  
  files.forEach((filePath, index) => {
    console.log(`\n  检查文件${index + 1}: ${path.basename(filePath)}`);
    
    if (!fs.existsSync(filePath)) {
      console.log(`  ❌ 文件不存在: ${filePath}`);
      allTestsPassed = false;
      return;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    const expectedId = expectedIds[filePath];
    
    if (content.includes(`getElementById('${expectedId}')`)) {
      console.log(`  ✅ 样式注入ID正确: ${expectedId}`);
    } else {
      console.log(`  ❌ 样式注入ID缺失或错误: ${expectedId}`);
      allTestsPassed = false;
    }
    
    if (content.includes(`style.id = '${expectedId}'`)) {
      console.log(`  ✅ 样式ID设置正确: ${expectedId}`);
    } else {
      console.log(`  ❌ 样式ID设置缺失: ${expectedId}`);
      allTestsPassed = false;
    }
  });
  
  return allTestsPassed;
}

/**
 * 测试5: 验证构建配置
 */
function testBuildConfiguration() {
  console.log('\n📋 测试5: 构建配置验证');
  
  const packageJsonPath = path.join(TEST_CONFIG.frontendRoot, 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    console.log(`  ❌ package.json不存在: ${packageJsonPath}`);
    return false;
  }
  
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    // 检查必需的依赖
    const requiredDeps = ['react', 'antd', '@ant-design/icons'];
    let allDepsFound = true;
    
    requiredDeps.forEach(dep => {
      if (packageJson.dependencies && packageJson.dependencies[dep]) {
        console.log(`  ✅ 依赖存在: ${dep}@${packageJson.dependencies[dep]}`);
      } else {
        console.log(`  ❌ 缺少依赖: ${dep}`);
        allDepsFound = false;
      }
    });
    
    // 检查构建脚本
    if (packageJson.scripts && packageJson.scripts.build) {
      console.log(`  ✅ 构建脚本存在: ${packageJson.scripts.build}`);
    } else {
      console.log(`  ❌ 构建脚本缺失`);
      allDepsFound = false;
    }
    
    return allDepsFound;
  } catch (error) {
    console.log(`  ❌ 解析package.json失败: ${error.message}`);
    return false;
  }
}

/**
 * 主测试执行器
 */
function runAllTests() {
  const tests = [
    { name: 'Select组件样式CSS注入', fn: testSelectStylesInjection },
    { name: 'optionLabelProp配置', fn: testOptionLabelPropConfig },
    { name: '表格操作列优化', fn: testTableActionsOptimization },
    { name: '样式注入唯一性', fn: testStyleInjectionUniqueness },
    { name: '构建配置', fn: testBuildConfiguration }
  ];
  
  let passedTests = 0;
  const totalTests = tests.length;
  
  tests.forEach((test, index) => {
    try {
      const result = test.fn();
      if (result) {
        passedTests++;
        console.log(`\n✅ 测试${index + 1}通过: ${test.name}`);
      } else {
        console.log(`\n❌ 测试${index + 1}失败: ${test.name}`);
      }
    } catch (error) {
      console.log(`\n💥 测试${index + 1}异常: ${test.name} - ${error.message}`);
    }
  });
  
  // 总结
  console.log('\n' + '=' .repeat(60));
  console.log('📊 测试结果总结');
  console.log('=' .repeat(60));
  console.log(`总测试数: ${totalTests}`);
  console.log(`通过测试: ${passedTests}`);
  console.log(`失败测试: ${totalTests - passedTests}`);
  console.log(`成功率: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
  
  if (passedTests === totalTests) {
    console.log('\n🎉 所有测试通过！前端UI优化修复验证成功！');
    console.log('\n📝 下一步操作:');
    console.log('   1. 重启前端开发服务器: npm run dev');
    console.log('   2. 验证页面效果:');
    console.log('      - http://localhost:3000/pipelines (流水线列表 → 编辑)');
    console.log('      - http://localhost:3000/pipelines (流水线列表 → 配置)');
    console.log('   3. 测试Select组件选中后只显示主标题');
    console.log('   4. 验证操作列图标按钮和下拉菜单功能');
  } else {
    console.log('\n⚠️  部分测试失败，请检查上述错误信息并修复');
  }
  
  return passedTests === totalTests;
}

// 开始执行测试
runAllTests();
