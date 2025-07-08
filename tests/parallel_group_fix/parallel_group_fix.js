/**
 * 并行组管理修复补丁
 * 解决步骤与并行组关联的数据同步问题
 */

// 1. 修复ParallelGroupManager组件中的数据获取逻辑
const ParallelGroupManagerFixes = {
  
  // 增强的getStepsForGroup方法
  getStepsForGroup: (groupId, availableSteps, parallelGroups) => {
    console.log('🔍 获取并行组步骤:', groupId, '可用步骤:', availableSteps?.length || 0)
    
    if (!Array.isArray(availableSteps) || availableSteps.length === 0) {
      console.warn('⚠️ availableSteps 不是数组或为空')
      return []
    }
    
    // 方法1: 从步骤的parallel_group字段获取（主要数据源）
    const stepsFromField = availableSteps
      .filter(step => step.parallel_group === groupId)
      .map(step => step.id)
    
    console.log('📋 从步骤字段获取:', stepsFromField)
    
    // 方法2: 从并行组的steps数组获取（备选数据源）
    let stepsFromGroup = []
    if (Array.isArray(parallelGroups)) {
      const group = parallelGroups.find(g => g.id === groupId)
      if (group && Array.isArray(group.steps)) {
        stepsFromGroup = group.steps
      }
    }
    
    console.log('📋 从并行组配置获取:', stepsFromGroup)
    
    // 优先使用步骤字段的数据，如果为空则使用并行组配置的数据
    const result = stepsFromField.length > 0 ? stepsFromField : stepsFromGroup
    
    console.log('✅ 最终结果:', result)
    return result
  },
  
  // 数据同步验证方法
  validateDataSync: (parallelGroups, availableSteps) => {
    console.log('🔍 验证数据同步状态...')
    
    const issues = []
    
    if (!Array.isArray(parallelGroups) || !Array.isArray(availableSteps)) {
      issues.push('数据格式错误: parallelGroups或availableSteps不是数组')
      return issues
    }
    
    // 检查每个并行组的步骤配置
    parallelGroups.forEach(group => {
      const groupId = group.id
      const groupSteps = group.steps || []
      
      // 检查组中配置的步骤是否实际存在
      groupSteps.forEach(stepId => {
        const step = availableSteps.find(s => s.id === stepId)
        if (!step) {
          issues.push(`并行组 ${groupId} 中的步骤 ${stepId} 不存在`)
        } else if (step.parallel_group !== groupId) {
          issues.push(`步骤 ${stepId} 的parallel_group字段(${step.parallel_group})与所属组(${groupId})不匹配`)
        }
      })
    })
    
    // 检查有parallel_group字段的步骤是否都在对应的并行组中
    availableSteps.forEach(step => {
      if (step.parallel_group) {
        const group = parallelGroups.find(g => g.id === step.parallel_group)
        if (!group) {
          issues.push(`步骤 ${step.id} 引用的并行组 ${step.parallel_group} 不存在`)
        } else if (!group.steps || !group.steps.includes(step.id)) {
          issues.push(`步骤 ${step.id} 未在其所属并行组 ${step.parallel_group} 的steps数组中`)
        }
      }
    })
    
    if (issues.length > 0) {
      console.warn('⚠️ 发现数据同步问题:', issues)
    } else {
      console.log('✅ 数据同步验证通过')
    }
    
    return issues
  }
}

// 2. 修复PipelineEditor中的保存逻辑
const PipelineEditorFixes = {
  
  // 增强的并行组保存方法
  handleParallelGroupSave: async (groups, pipeline, steps, setSteps, setParallelGroups, apiService, pipelineForm, message) => {
    console.log('🔄 开始保存并行组:', groups.length, '个组')
    
    try {
      if (!pipeline) {
        message.error('请先选择流水线')
        return false
      }
      
      // 1. 数据验证
      const issues = ParallelGroupManagerFixes.validateDataSync(groups, steps)
      if (issues.length > 0) {
        console.warn('⚠️ 保存前发现数据问题:', issues)
        // 继续保存，但记录警告
      }
      
      // 2. 准备要保存的数据
      const safeGroups = Array.isArray(groups) ? groups : []
      
      // 3. 保存并行组到后端
      console.log('💾 保存并行组到后端...')
      const savePromises = safeGroups.map(async (group) => {
        const groupWithPipeline = {
          ...group,
          pipeline: pipeline.id
        }
        
        console.log('💾 处理并行组:', group.id, group.name)
        
        try {
          // 检查是否为新组（ID以timestamp开头）
          if (group.id.startsWith('parallel_')) {
            console.log('🆕 创建新并行组:', group.id)
            return await apiService.createParallelGroup(groupWithPipeline)
          } else {
            console.log('📝 更新现有并行组:', group.id)
            return await apiService.updateParallelGroup(group.id, groupWithPipeline)
          }
        } catch (error) {
          console.error('❌ 保存并行组失败:', group.id, error)
          throw error
        }
      })
      
      // 4. 等待并行组保存完成
      const savedGroups = await Promise.all(savePromises)
      console.log('✅ 并行组保存完成:', savedGroups.length, '个')
      
      // 5. 同步步骤的parallel_group字段
      console.log('🔗 同步步骤的并行组关联...')
      const updatedSteps = steps.map(step => {
        // 查找步骤属于哪个并行组
        const belongsToGroup = safeGroups.find(group => 
          group.steps && group.steps.includes(step.id)
        )
        
        return {
          ...step,
          parallel_group: belongsToGroup ? belongsToGroup.id : undefined
        }
      })
      
      // 6. 保存更新后的步骤到后端
      console.log('💾 保存步骤的并行组关联...')
      try {
        const pipelineInfo = await pipelineForm.validateFields().catch(() => ({
          name: pipeline.name,
          description: pipeline.description
        }))
        
        const updateData = {
          ...pipelineInfo,
          steps: updatedSteps
        }
        
        await apiService.updatePipeline(pipeline.id, updateData)
        console.log('✅ 流水线步骤更新完成')
        
        // 7. 更新前端状态
        setSteps(updatedSteps)
        setParallelGroups(savedGroups)
        
        message.success('并行组配置已保存')
        return true
        
      } catch (error) {
        console.error('❌ 保存步骤关联失败:', error)
        message.error('保存步骤关联失败: ' + error.message)
        return false
      }
      
    } catch (error) {
      console.error('❌ 保存并行组失败:', error)
      message.error('保存并行组失败: ' + error.message)
      return false
    }
  },
  
  // 数据刷新方法
  refreshParallelGroupData: async (pipeline, apiService, setParallelGroups, setSteps) => {
    if (!pipeline) return
    
    try {
      console.log('🔄 刷新并行组数据...')
      
      // 重新获取流水线详情
      const pipelineDetail = await apiService.getPipeline(pipeline.id)
      const freshSteps = pipelineDetail.steps || []
      
      // 重新获取并行组数据
      const freshGroups = await apiService.getParallelGroups(pipeline.id)
      
      console.log('✅ 数据刷新完成:', freshSteps.length, '个步骤,', freshGroups.length, '个并行组')
      
      // 更新状态
      setSteps(freshSteps)
      setParallelGroups(freshGroups)
      
      // 验证数据一致性
      const issues = ParallelGroupManagerFixes.validateDataSync(freshGroups, freshSteps)
      if (issues.length > 0) {
        console.warn('⚠️ 刷新后仍存在数据问题:', issues)
      }
      
    } catch (error) {
      console.error('❌ 刷新数据失败:', error)
    }
  }
}

// 3. API服务修复
const ApiServiceFixes = {
  
  // 增强的getParallelGroups方法
  getParallelGroups: async (api, pipelineId) => {
    const url = pipelineId ? `/pipelines/parallel-groups/?pipeline=${pipelineId}` : '/pipelines/parallel-groups/'
    console.log('🔄 API调用: 获取并行组', url)
    
    try {
      const response = await api.get(url)
      console.log('✅ API响应: 获取并行组', response.data)
      
      // 处理不同的响应格式
      let groups = []
      
      if (response.data && Array.isArray(response.data.results)) {
        // Django REST Framework分页响应
        groups = response.data.results
        console.log('📊 使用分页格式，共', groups.length, '个并行组')
      } else if (Array.isArray(response.data)) {
        // 直接数组响应
        groups = response.data
        console.log('📊 使用数组格式，共', groups.length, '个并行组')
      } else {
        console.warn('⚠️ 意外的并行组数据格式:', response.data)
        groups = []
      }
      
      // 数据验证
      const validGroups = groups.filter(group => {
        const isValid = group && typeof group.id === 'string' && typeof group.name === 'string'
        if (!isValid) {
          console.warn('⚠️ 无效的并行组数据:', group)
        }
        return isValid
      })
      
      console.log('✅ 返回', validGroups.length, '个有效并行组')
      return validGroups
      
    } catch (error) {
      console.error('❌ 获取并行组失败:', error)
      throw error
    }
  }
}

// 4. 使用指南
const UsageGuide = {
  
  // 在ParallelGroupManager组件中使用
  useInParallelGroupManager: () => {
    console.log(`
    // 在ParallelGroupManager组件中替换getStepsForGroup方法:
    const getStepsForGroup = (groupId) => {
      return ParallelGroupManagerFixes.getStepsForGroup(groupId, safeAvailableSteps, safeParallelGroups)
    }
    
    // 在组件挂载时验证数据:
    useEffect(() => {
      const issues = ParallelGroupManagerFixes.validateDataSync(safeParallelGroups, safeAvailableSteps)
      if (issues.length > 0) {
        console.warn('并行组数据同步问题:', issues)
      }
    }, [safeParallelGroups, safeAvailableSteps])
    `)
  },
  
  // 在PipelineEditor组件中使用
  useInPipelineEditor: () => {
    console.log(`
    // 在PipelineEditor组件中替换handleParallelGroupSave方法:
    const handleParallelGroupSave = async (groups) => {
      return await PipelineEditorFixes.handleParallelGroupSave(
        groups, pipeline, steps, setSteps, setParallelGroups, 
        apiService, pipelineForm, message
      )
    }
    
    // 添加数据刷新方法:
    const refreshData = async () => {
      await PipelineEditorFixes.refreshParallelGroupData(
        pipeline, apiService, setParallelGroups, setSteps
      )
    }
    `)
  }
}

// 导出修复方法
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    ParallelGroupManagerFixes,
    PipelineEditorFixes,
    ApiServiceFixes,
    UsageGuide
  }
}

console.log('🔧 并行组管理修复补丁已加载')
console.log('📖 使用 UsageGuide 查看具体的使用方法')
