
// 前端镜像标签提取功能测试脚本
// 在浏览器控制台中运行此脚本来测试功能

function testImageTagExtraction() {
    console.log('🧪 测试镜像标签提取功能');
    
    const testCases = [
        { input: 'nginx:alpine', expectedImage: 'nginx', expectedTag: 'alpine' },
        { input: 'ubuntu:20.04', expectedImage: 'ubuntu', expectedTag: '20.04' },
        { input: 'registry.example.com/myapp:v1.2.3', expectedImage: 'registry.example.com/myapp', expectedTag: 'v1.2.3' },
        { input: 'redis', expectedImage: 'redis', expectedTag: 'latest' },
        { input: 'hello-world:latest', expectedImage: 'hello-world', expectedTag: 'latest' }
    ];
    
    testCases.forEach((testCase, index) => {
        console.log(`📝 测试用例 ${index + 1}: ${testCase.input}`);
        
        // 模拟前端逻辑
        let actualImage, actualTag;
        
        if (testCase.input.includes(':')) {
            const parts = testCase.input.split(':');
            if (parts.length === 2) {
                [actualImage, actualTag] = parts;
            } else {
                actualImage = testCase.input;
                actualTag = 'latest';
            }
        } else {
            actualImage = testCase.input;
            actualTag = 'latest';
        }
        
        const imageMatch = actualImage === testCase.expectedImage;
        const tagMatch = actualTag === testCase.expectedTag;
        
        if (imageMatch && tagMatch) {
            console.log(`  ✅ 提取正确 - 镜像: ${actualImage}, 标签: ${actualTag}`);
        } else {
            console.log(`  ❌ 提取错误 - 期望镜像: ${testCase.expectedImage}, 实际镜像: ${actualImage}`);
            console.log(`               期望标签: ${testCase.expectedTag}, 实际标签: ${actualTag}`);
        }
    });
}

// 运行测试
testImageTagExtraction();

// 手动测试说明
console.log(`
📋 手动测试步骤:
1. 打开 AnsFlow 流水线编辑页面
2. 添加一个 Docker Pull 步骤
3. 在镜像名称字段输入 'nginx:alpine'
4. 检查标签字段是否自动填充为 'alpine'
5. 检查镜像名称字段是否变为 'nginx'
6. 保存步骤并查看参数是否正确存储
`);
    