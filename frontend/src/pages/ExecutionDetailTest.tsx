import React, { useEffect, useState } from 'react'
import { Card, Button, Typography } from 'antd'

const { Text, Paragraph } = Typography

const ExecutionDetailTest: React.FC = () => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      // 设置token
      const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMzQ1NzE3LCJpYXQiOjE3NTEzNDIxMTcsImp0aSI6ImUzMGQzYWIwOTEzNTRjNjJiOWU3ZTdiOTM4NzVlMWJhIiwidXNlcl9pZCI6MX0.FJHQB0srOuzc5unDjj_8OcaJ86jNBLNt3pzXqHJ-4k8'
      localStorage.setItem('authToken', testToken)
      
      const response = await fetch('/api/v1/cicd/executions/15/', {
        headers: {
          'Authorization': `Bearer ${testToken}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div style={{ padding: '24px' }}>
      <Card title="执行详情测试" extra={
        <Button onClick={fetchData} loading={loading}>
          重新获取
        </Button>
      }>
        {error && (
          <div style={{ color: 'red', marginBottom: 16 }}>
            错误: {error}
          </div>
        )}
        
        {loading && <div>加载中...</div>}
        
        {data && (
          <div>
            <p><strong>执行ID:</strong> {data.id}</p>
            <p><strong>流水线名称:</strong> {data.pipeline_name}</p>
            <p><strong>状态:</strong> {data.status}</p>
            <p><strong>步骤执行数量:</strong> {data.step_executions?.length || 0}</p>
            
            {data.step_executions && data.step_executions.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>步骤执行详情:</h4>
                {data.step_executions.map((step: any, index: number) => (
                  <Card key={step.id} size="small" style={{ marginBottom: 8 }}>
                    <p><strong>步骤 {index + 1}:</strong> {step.atomic_step_name}</p>
                    <p><strong>状态:</strong> {step.status}</p>
                    <p><strong>日志:</strong> {step.logs ? step.logs.substring(0, 100) + '...' : '无日志'}</p>
                  </Card>
                ))}
              </div>
            )}
            
            <details style={{ marginTop: 16 }}>
              <summary>完整数据</summary>
              <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '8px', overflow: 'auto' }}>
                {JSON.stringify(data, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </Card>
    </div>
  )
}

export default ExecutionDetailTest
