// 前端并行组管理修复脚本
// 修复PipelineEditor.tsx中的并行组数据同步问题

// 1. 修复handleParallelGroupSave函数
const handleParallelGroupSave = async (groups: ParallelGroup[]) => {
  try {
    if (!pipeline) {
      message.error('请先选择流水线')
      return
    }

    console.log('🔄 开始保存并行组:', groups.length, '个组')
    console.log('📊 当前并行组状态:', groups)

    // 确保 parallelGroups 是数组
    const safeParallelGroups = Array.isArray(parallelGroups) ? parallelGroups : []
    
    // 第一步：保存并行组到后端
    const savePromises = groups.map(async (group) => {
      const groupWithPipeline = {
        ...group,
        pipeline: pipeline.id
      }

      console.log('💾 处理并行组:', group.id, group.name, '包含步骤:', group.steps)

      if (safeParallelGroups.find(existing => existing.id === group.id)) {
        console.log('📝 更新现有并行组:', group.id)
        return await apiService.updateParallelGroup(group.id, groupWithPipeline)
      } else {
        console.log('🆕 创建新并行组:', group.id)
        return await apiService.createParallelGroup(groupWithPipeline)
      }
    })

    // 删除本地已删除但后端仍存在的组
    const deletedGroups = safeParallelGroups.filter(
      existing => !groups.find(group => group.id === existing.id)
    )
    console.log('🗑️ 需要删除的并行组:', deletedGroups.length, '个')
    
    const deletePromises = deletedGroups.map(group => {
      console.log('🗑️ 删除并行组:', group.id)
      return apiService.deleteParallelGroup(group.id)
    })

    // 等待所有并行组操作完成
    console.log('⏳ 等待所有并行组API操作完成...')
    await Promise.all([...savePromises, ...deletePromises])

    // 第二步：同步更新步骤的并行组关联
    console.log('🔗 开始同步步骤的并行组关联...')
    
    // 创建步骤的并行组关联映射
    const stepGroupMapping = new Map<number, string>()
    
    groups.forEach(group => {
      if (group.steps && group.steps.length > 0) {
        group.steps.forEach(stepId => {
          stepGroupMapping.set(stepId, group.id)
          console.log(`🔗 映射步骤 ${stepId} → 并行组 ${group.id}`)
        })
      }
    })

    // 更新步骤数组
    const updatedSteps = steps.map(step => {
      const newParallelGroup = stepGroupMapping.get(step.id)
      if (newParallelGroup) {
        console.log(`🔗 更新步骤 ${step.id} (${step.name}) 的并行组: ${step.parallel_group} → ${newParallelGroup}`)
        return {
          ...step,
          parallel_group: newParallelGroup
        }
      } else if (step.parallel_group) {
        console.log(`🔗 清除步骤 ${step.id} (${step.name}) 的并行组: ${step.parallel_group} → undefined`)
        return {
          ...step,
          parallel_group: undefined
        }
      }
      return step
    })

    // 第三步：批量更新步骤到后端
    console.log('💾 批量更新步骤的并行组关联到后端...')
    
    // 获取流水线信息
    const pipelineInfo = await pipelineForm.validateFields().catch(() => ({
      name: pipeline.name,
      description: pipeline.description,
      tool_integration: pipeline.tool_integration || {}
    }))

    // 构建更新数据
    const updateData = {
      ...pipelineInfo,
      steps: updatedSteps.map(step => ({
        id: step.id,
        name: step.name,
        step_type: step.step_type,
        description: step.description,
        order: step.order,
        parameters: getStepParameters(step),
        parallel_group: step.parallel_group,
        git_credential_id: step.git_credential_id,
        // 保留其他字段
        dependencies: step.dependencies,
        conditions: step.conditions,
        approval_required: step.approval_required,
        approval_users: step.approval_users,
        retry_policy: step.retry_policy,
        notification_config: step.notification_config,
        // Ansible字段
        ansible_playbook: step.ansible_playbook,
        ansible_inventory: step.ansible_inventory,
        ansible_credential: step.ansible_credential,
        ansible_parameters: step.ansible_parameters
      }))
    }

    console.log('💾 保存完整的流水线数据...')
    await apiService.updatePipeline(pipeline.id, updateData)

    // 第四步：更新本地状态
    console.log('🔄 更新本地组件状态...')
    setSteps(updatedSteps)
    setParallelGroups(groups)

    console.log('🎉 并行组保存完成!')
    message.success('并行组配置已保存并同步')

  } catch (error) {
    console.error('❌ 保存并行组失败:', error)
    message.error('保存并行组失败，请检查网络连接或联系管理员')
  }
}

// 2. 修复并行组数据获取逻辑
const loadParallelGroups = async (pipelineId: number) => {
  try {
    console.log('🔄 加载并行组数据:', pipelineId)
    
    const parallelGroupsData = await apiService.getParallelGroups(pipelineId)
    console.log('✅ 并行组数据加载成功:', parallelGroupsData.length, '个组')
    
    // 确保数据格式正确
    const validGroups = parallelGroupsData.filter(group => 
      group && typeof group === 'object' && group.id && group.name
    )
    
    if (validGroups.length !== parallelGroupsData.length) {
      console.warn('⚠️ 过滤掉了无效的并行组数据')
    }
    
    setParallelGroups(validGroups)
    console.log('📊 已更新并行组状态:', validGroups.length, '个有效组')
    
  } catch (error) {
    console.error('❌ 加载并行组失败:', error)
    setParallelGroups([])
    message.error('加载并行组失败')
  }
}

// 3. 修复并行组管理组件的步骤获取逻辑
const getStepsForGroup = (groupId: string) => {
  if (!Array.isArray(safeAvailableSteps) || safeAvailableSteps.length === 0) {
    console.warn('⚠️ 没有可用的步骤数据')
    return []
  }
  
  const groupSteps = safeAvailableSteps
    .filter(step => step.parallel_group === groupId)
    .map(step => step.id)
  
  console.log(`🔍 并行组 ${groupId} 包含步骤:`, groupSteps)
  return groupSteps
}

// 4. 修复并行组管理组件的数据同步
const syncGroupStepsData = (groups: ParallelGroup[]) => {
  console.log('🔄 同步并行组步骤数据...')
  
  const syncedGroups = groups.map(group => {
    const dynamicSteps = getStepsForGroup(group.id)
    const hasStepsConfig = group.steps && group.steps.length > 0
    
    // 如果动态获取的步骤与配置的步骤不一致，使用动态获取的
    if (dynamicSteps.length > 0 && (!hasStepsConfig || 
        !arraysEqual(dynamicSteps.sort(), group.steps.sort()))) {
      console.log(`🔄 更新并行组 ${group.id} 的步骤配置:`, group.steps, '→', dynamicSteps)
      return {
        ...group,
        steps: dynamicSteps
      }
    }
    
    return group
  })
  
  return syncedGroups
}

// 辅助函数：比较数组是否相等
const arraysEqual = (a: number[], b: number[]) => {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false
  }
  return true
}

// 5. 修复前端API服务的响应处理
const getParallelGroupsFixed = async (pipelineId?: number): Promise<any[]> => {
  const url = pipelineId ? `/pipelines/parallel-groups/?pipeline=${pipelineId}` : '/pipelines/parallel-groups/'
  console.log('🔄 API调用: 获取并行组', url)
  
  try {
    const response = await this.api.get(url)
    console.log('✅ API响应: 获取并行组', response.data)
    
    // 处理不同的响应格式
    let groups: any[] = []
    
    if (response.data && Array.isArray(response.data.results)) {
      // Django REST Framework 分页格式
      groups = response.data.results
      console.log('📊 使用分页格式，共', groups.length, '个并行组')
    } else if (Array.isArray(response.data)) {
      // 直接数组格式
      groups = response.data
      console.log('📊 使用数组格式，共', groups.length, '个并行组')
    } else {
      console.warn('⚠️ 未识别的并行组数据格式:', response.data)
      return []
    }
    
    // 数据验证
    const validGroups = groups.filter(group => {
      if (!group || typeof group !== 'object') {
        console.warn('⚠️ 无效的并行组数据:', group)
        return false
      }
      
      if (!group.id || !group.name) {
        console.warn('⚠️ 并行组缺少必要字段:', group)
        return false
      }
      
      return true
    })
    
    if (validGroups.length !== groups.length) {
      console.warn('⚠️ 过滤掉了', groups.length - validGroups.length, '个无效并行组')
    }
    
    return validGroups
    
  } catch (error) {
    console.error('❌ 获取并行组失败:', error)
    throw error
  }
}

console.log('🚀 并行组管理修复脚本已加载')

// 使用说明：
// 1. 将上述函数替换到对应的组件中
// 2. 在PipelineEditor.tsx中替换handleParallelGroupSave函数
// 3. 在apiService.ts中替换getParallelGroups函数
// 4. 在ParallelGroupManager.tsx中添加数据同步逻辑
// 5. 重新构建并测试前端应用
