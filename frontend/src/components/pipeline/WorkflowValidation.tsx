import React, { useEffect, useState, useMemo } from 'react';
import { Alert, Card, List, Tag, Collapse, Space, Button, Tooltip } from 'antd';
import { ExclamationCircleOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { PipelineStep, ValidationResult, ValidationIssue } from '../../types';

const { Panel } = Collapse;

interface WorkflowValidationProps {
  steps: PipelineStep[];
  onValidationComplete?: (result: ValidationResult) => void;
  autoValidate?: boolean;
}

const WorkflowValidation: React.FC<WorkflowValidationProps> = ({
  steps,
  onValidationComplete,
  autoValidate = true
}) => {
  const [validationResult, setValidationResult] = useState<ValidationResult>({
    isValid: true,
    issues: [],
    suggestions: []
  });

  // 验证逻辑
  const validateWorkflow = useMemo(() => {
    const issues: ValidationIssue[] = [];

    // 1. 检查步骤基本配置
    steps.forEach((step, index) => {
      if (!step.name || step.name.trim() === '') {
        issues.push({
          type: 'error',
          message: `步骤 ${index + 1} 缺少名称`,
          stepId: step.id,
          field: 'name'
        });
      }

      if (!step.command || step.command.trim() === '') {
        issues.push({
          type: 'error',
          message: `步骤 "${step.name || index + 1}" 缺少命令`,
          stepId: step.id,
          field: 'command'
        });
      }

      // 检查超时设置
      if (step.timeout && step.timeout <= 0) {
        issues.push({
          type: 'warning',
          message: `步骤 "${step.name}" 的超时时间应该大于0`,
          stepId: step.id,
          field: 'timeout'
        });
      }
    });

    // 2. 检查依赖关系
    steps.forEach(step => {
      if (step.dependencies) {
        step.dependencies.forEach(depId => {
          const depExists = steps.some(s => s.id === depId);
          if (!depExists) {
            issues.push({
              type: 'error',
              message: `步骤 "${step.name}" 依赖的步骤 "${depId}" 不存在`,
              stepId: step.id,
              field: 'dependencies'
            });
          }
        });
      }
    });

    // 3. 检查循环依赖
    const hasCyclicDependency = (stepId: number, visited: Set<number>, path: Set<number>): boolean => {
      if (path.has(stepId)) return true;
      if (visited.has(stepId)) return false;

      visited.add(stepId);
      path.add(stepId);

      const step = steps.find(s => s.id === stepId);
      if (step?.dependencies) {
        for (const depId of step.dependencies) {
          if (hasCyclicDependency(depId, visited, path)) {
            return true;
          }
        }
      }

      path.delete(stepId);
      return false;
    };

    const visited = new Set<number>();
    for (const step of steps) {
      if (!visited.has(step.id)) {
        if (hasCyclicDependency(step.id, visited, new Set())) {
          issues.push({
            type: 'error',
            message: `检测到循环依赖，涉及步骤 "${step.name}"`,
            stepId: step.id,
            field: 'dependencies'
          });
        }
      }
    }

    // 4. 检查并行组配置
    const parallelGroups = new Map<string, PipelineStep[]>();
    steps.forEach(step => {
      if (step.parallelGroup) {
        if (!parallelGroups.has(step.parallelGroup)) {
          parallelGroups.set(step.parallelGroup, []);
        }
        parallelGroups.get(step.parallelGroup)!.push(step);
      }
    });

    parallelGroups.forEach((groupSteps, groupId) => {
      if (groupSteps.length < 2) {
        issues.push({
          type: 'warning',
          message: `并行组 "${groupId}" 只有一个步骤，建议移除并行组配置`,
          stepId: groupSteps[0].id,
          field: 'parallelGroup'
        });
      }
    });

    // 5. 性能建议
    const suggestions: string[] = [];
    
    if (steps.length > 10) {
      suggestions.push('工作流步骤较多，建议考虑拆分为子工作流');
    }

    const stepsWithoutTimeout = steps.filter(s => !s.timeout);
    if (stepsWithoutTimeout.length > 0) {
      suggestions.push(`有 ${stepsWithoutTimeout.length} 个步骤未设置超时时间，建议添加超时配置`);
    }

    const hasParallelSteps = steps.some(s => s.parallelGroup);
    if (!hasParallelSteps && steps.length > 3) {
      suggestions.push('考虑使用并行执行来提高工作流性能');
    }

    return {
      isValid: issues.filter(i => i.type === 'error').length === 0,
      issues,
      suggestions
    };
  }, [steps]);

  useEffect(() => {
    if (autoValidate) {
      setValidationResult(validateWorkflow);
      onValidationComplete?.(validateWorkflow);
    }
  }, [validateWorkflow, autoValidate, onValidationComplete]);

  const handleManualValidate = () => {
    const result = validateWorkflow;
    setValidationResult(result);
    onValidationComplete?.(result);
  };

  const getIssueIcon = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getIssueColor = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'success';
    }
  };

  const errorCount = validationResult.issues.filter(i => i.type === 'error').length;
  const warningCount = validationResult.issues.filter(i => i.type === 'warning').length;

  return (
    <Card 
      title="工作流验证" 
      size="small"
      extra={
        !autoValidate && (
          <Button size="small" onClick={handleManualValidate}>
            重新验证
          </Button>
        )
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 总体状态 */}
        <Alert
          message={
            validationResult.isValid 
              ? `验证通过 (${steps.length} 个步骤)` 
              : `发现 ${errorCount} 个错误, ${warningCount} 个警告`
          }
          type={validationResult.isValid ? 'success' : 'error'}
          showIcon
        />

        {/* 问题列表 */}
        {validationResult.issues.length > 0 && (
          <Collapse size="small">
            <Panel 
              header={`问题详情 (${validationResult.issues.length})`} 
              key="issues"
            >
              <List
                size="small"
                dataSource={validationResult.issues}
                renderItem={(issue) => (
                  <List.Item>
                    <Space>
                      {getIssueIcon(issue.type)}
                      <span>{issue.message}</span>
                      <Tag color={getIssueColor(issue.type)}>
                        {issue.type === 'error' ? '错误' : '警告'}
                      </Tag>
                      {issue.field && (
                        <Tag color="default">{issue.field}</Tag>
                      )}
                    </Space>
                  </List.Item>
                )}
              />
            </Panel>
          </Collapse>
        )}

        {/* 优化建议 */}
        {validationResult.suggestions.length > 0 && (
          <Collapse size="small">
            <Panel 
              header={`优化建议 (${validationResult.suggestions.length})`} 
              key="suggestions"
            >
              <List
                size="small"
                dataSource={validationResult.suggestions}
                renderItem={(suggestion) => (
                  <List.Item>
                    <Space>
                      <CheckCircleOutlined style={{ color: '#1890ff' }} />
                      <span>{suggestion}</span>
                    </Space>
                  </List.Item>
                )}
              />
            </Panel>
          </Collapse>
        )}

        {/* 验证统计 */}
        <div style={{ fontSize: '12px', color: '#666' }}>
          <Space split={<span>|</span>}>
            <span>总步骤: {steps.length}</span>
            <span>错误: {errorCount}</span>
            <span>警告: {warningCount}</span>
            <span>并行组: {new Set(steps.filter(s => s.parallelGroup).map(s => s.parallelGroup)).size}</span>
          </Space>
        </div>
      </Space>
    </Card>
  );
};

export default WorkflowValidation;
