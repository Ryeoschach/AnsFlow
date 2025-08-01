/**
 * 简化版清单主机组API调试工具
 * 专门用于快速诊断API调用问题
 */

import React, { useState } from 'react';
import { Card, Button, Typography, Space, Input, message } from 'antd';

const { Title, Text, Paragraph } = Typography;

export const SimpleDebugTool: React.FC = () => {
  const [inventoryId, setInventoryId] = useState<number>(1);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<string>('');

  const testAPI = async () => {
    setTesting(true);
    setResult('测试中...');
    
    try {
      // 获取token
      const token = localStorage.getItem('authToken');
      console.log('🔍 Token状态:', token ? '已存在' : '缺失');
      
      if (!token) {
        setResult('❌ 错误: 未找到认证Token');
        return;
      }

      // 直接调用API
      const response = await fetch(`/api/ansible/inventories/${inventoryId}/groups/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📡 API响应状态:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API错误响应:', errorText);
        setResult(`❌ API调用失败: ${response.status} - ${response.statusText}\n详情: ${errorText}`);
        return;
      }

      const data = await response.json();
      console.log('✅ API响应数据:', data);
      
      let analysisResult = `✅ API调用成功!\n\n`;
      analysisResult += `清单ID: ${inventoryId}\n`;
      analysisResult += `数据类型: ${Array.isArray(data) ? '数组' : typeof data}\n`;
      
      if (Array.isArray(data)) {
        analysisResult += `主机组数量: ${data.length}\n\n`;
        
        if (data.length > 0) {
          const firstGroup = data[0];
          analysisResult += `数据结构分析:\n`;
          analysisResult += `- 包含group_id字段: ${firstGroup.hasOwnProperty('group_id') ? '是' : '否'}\n`;
          analysisResult += `- 包含group字段: ${firstGroup.hasOwnProperty('group') ? '是' : '否'}\n`;
          analysisResult += `- 包含group_name字段: ${firstGroup.hasOwnProperty('group_name') ? '是' : '否'}\n`;
          analysisResult += `- 包含is_active字段: ${firstGroup.hasOwnProperty('is_active') ? '是' : '否'}\n`;
          analysisResult += `- 所有字段: ${Object.keys(firstGroup).join(', ')}\n\n`;
          
          analysisResult += `示例数据:\n${JSON.stringify(firstGroup, null, 2)}`;
        }
      } else {
        analysisResult += `响应数据:\n${JSON.stringify(data, null, 2)}`;
      }
      
      setResult(analysisResult);
      message.success('API测试成功!');
      
    } catch (error: any) {
      console.error('❌ 测试异常:', error);
      setResult(`❌ 测试异常: ${error.message}`);
      message.error('API测试失败!');
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card title="简化版API调试工具" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <Text>清单ID:</Text>
          <Input 
            type="number" 
            value={inventoryId} 
            onChange={(e) => setInventoryId(Number(e.target.value))}
            style={{ width: '100px' }}
          />
          <Button
            type="primary"
            onClick={testAPI}
            loading={testing}
          >
            测试API
          </Button>
        </Space>

        {result && (
          <Card size="small" title="测试结果">
            <Paragraph>
              <pre style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: '12px', 
                background: '#f5f5f5', 
                padding: '8px',
                borderRadius: '4px',
                maxHeight: '400px',
                overflow: 'auto'
              }}>
                {result}
              </pre>
            </Paragraph>
          </Card>
        )}
      </Space>
    </Card>
  );
};
