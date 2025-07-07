// 备选方案：如果自动保存有问题，可以使用这个简化版本
// 这个版本只更新本地状态，需要用户手动点击"保存流水线"

const handleStepSubmit_SimpleVersion = async () => {
  try {
    const values = await form.validateFields()
    
    let parameters = {}
    if (values.parameters) {
      try {
        parameters = JSON.parse(values.parameters)
      } catch (e) {
        message.error('参数格式错误，请输入有效的JSON')
        return
      }
    }

    // 处理ansible步骤的特殊字段
    if (values.step_type === 'ansible') {
      parameters = {
        ...parameters,
        playbook_id: values.ansible_playbook_id,
        inventory_id: values.ansible_inventory_id,
        credential_id: values.ansible_credential_id
      }
    }

    const stepData = {
      ...values,
      parameters,
      ansible_playbook: values.step_type === 'ansible' ? values.ansible_playbook_id : undefined,
      ansible_inventory: values.step_type === 'ansible' ? values.ansible_inventory_id : undefined,
      ansible_credential: values.step_type === 'ansible' ? values.ansible_credential_id : undefined
    }

    // 只更新本地状态，不自动保存
    if (editingStep) {
      const updatedSteps = steps.map(step => 
        step.id === editingStep.id 
          ? { 
              ...step, 
              ...stepData,
              git_credential: values.git_credential_id || null
            }
          : step
      )
      setSteps(updatedSteps)
      message.success('步骤更新成功（请点击"保存流水线"按钮保存到数据库）')
    } else {
      const newStep = {
        id: Date.now(),
        ...stepData,
        pipeline: pipeline?.id || 0,
        is_active: true,
        created_at: new Date().toISOString(),
        git_credential: values.git_credential_id || null
      }
      setSteps([...steps, newStep])
      message.success('步骤添加成功（请点击"保存流水线"按钮保存到数据库）')
    }

    setStepFormVisible(false)
  } catch (error) {
    console.error('Failed to save step:', error)
    message.error('步骤操作失败')
  }
}
