import { useState, useEffect, useCallback } from 'react'
import { DockerRegistryList } from '../types/docker'
import dockerRegistryService from '../services/dockerRegistryService'

export interface DockerStepDefaults {
  [key: string]: {
    docker_image?: string
    docker_tag?: string
    docker_config?: Record<string, any>
    environment_vars?: Array<{ key: string; value: string }>
    timeout_seconds?: number
  }
}

const defaultStepConfigs: DockerStepDefaults = {
  docker_build: {
    docker_tag: 'latest',
    docker_config: {
      dockerfile_path: 'Dockerfile',
      context_path: '.',
      platform: 'linux/amd64',
      no_cache: false,
      pull: true,
      build_args: []
    },
    timeout_seconds: 1800
  },
  docker_run: {
    docker_tag: 'latest',
    docker_config: {
      detach: true,
      remove: true,
      ports: [],
      volumes: [],
      environment: []
    },
    timeout_seconds: 3600
  },
  docker_push: {
    docker_tag: 'latest',
    docker_config: {
      all_tags: false,
      platform: 'linux/amd64'
    },
    timeout_seconds: 1800
  },
  docker_pull: {
    docker_tag: 'latest',
    docker_config: {
      all_tags: false,
      platform: 'linux/amd64'
    },
    timeout_seconds: 1800
  }
}

export const useDockerStepConfig = () => {
  const [registries, setRegistries] = useState<DockerRegistryList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 获取注册表列表
  const fetchRegistries = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await dockerRegistryService.getRegistries()
      // 处理分页数据格式和直接数组格式
      const registriesArray = Array.isArray(data) ? data : ((data as any).results || [])
      setRegistries(registriesArray)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取注册表列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // 自动加载注册表列表
  useEffect(() => {
    fetchRegistries()
  }, [fetchRegistries])

  // 创建新注册表
  const createRegistry = useCallback(async (registryData: {
    name: string
    url: string
    registry_type: string
    username?: string
    password?: string
    description?: string
    is_default?: boolean
  }) => {
    try {
      const newRegistry = await dockerRegistryService.createRegistry(registryData)
      setRegistries(prev => [...prev, {
        id: newRegistry.id,
        name: newRegistry.name,
        url: newRegistry.url,
        registry_type: newRegistry.registry_type,
        status: newRegistry.status,
        is_default: newRegistry.is_default
      }])
      return newRegistry
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建注册表失败')
      throw err
    }
  }, [])

  // 测试注册表连接
  const testRegistry = useCallback(async (registryId: number) => {
    try {
      return await dockerRegistryService.testRegistry(registryId)
    } catch (err) {
      setError(err instanceof Error ? err.message : '测试注册表连接失败')
      throw err
    }
  }, [])

  // 设置默认注册表
  const setDefaultRegistry = useCallback(async (registryId: number) => {
    try {
      await dockerRegistryService.setDefaultRegistry(registryId)
      setRegistries(prev => prev.map(r => ({
        ...r,
        is_default: r.id === registryId
      })))
    } catch (err) {
      setError(err instanceof Error ? err.message : '设置默认注册表失败')
      throw err
    }
  }, [])

  // 获取步骤类型的默认配置
  const getStepDefaults = useCallback((stepType: string) => {
    return defaultStepConfigs[stepType] || {}
  }, [])

  // 生成步骤的初始表单值
  const getInitialFormValues = useCallback((stepType: string, existingValues?: any) => {
    const defaults = getStepDefaults(stepType)
    return {
      ...defaults,
      ...existingValues
    }
  }, [getStepDefaults])

  // 验证步骤配置
  const validateStepConfig = useCallback((stepType: string, config: any) => {
    const errors: string[] = []

    if (!config.docker_image) {
      errors.push('请输入镜像名称')
    }

    if (stepType === 'docker_push' && !config.docker_registry) {
      errors.push('推送步骤需要选择目标注册表')
    }

    if (stepType === 'docker_build') {
      if (config.docker_config?.dockerfile_path && !config.docker_config.dockerfile_path.trim()) {
        errors.push('Dockerfile 路径不能为空')
      }
      if (config.docker_config?.context_path && !config.docker_config.context_path.trim()) {
        errors.push('构建上下文路径不能为空')
      }
    }

    if (stepType === 'docker_run') {
      if (config.docker_config?.ports) {
        config.docker_config.ports.forEach((port: any, index: number) => {
          if (!port.host || !port.container) {
            errors.push(`端口映射 ${index + 1} 不完整`)
          }
        })
      }
      if (config.docker_config?.volumes) {
        config.docker_config.volumes.forEach((volume: any, index: number) => {
          if (!volume.host || !volume.container) {
            errors.push(`卷挂载 ${index + 1} 不完整`)
          }
        })
      }
    }

    return errors
  }, [])

  // 生成完整的镜像名称
  const generateFullImageName = useCallback((registryId: number | null, imageName: string, tag: string = 'latest') => {
    if (!registryId) {
      return `${imageName}:${tag}`
    }

    const registry = registries.find(r => r.id === registryId)
    if (!registry) {
      return `${imageName}:${tag}`
    }

    return dockerRegistryService.generateFullImageName(registry as any, imageName, tag)
  }, [registries])

  // 获取镜像建议
  const getImageSuggestions = useCallback((registryId: number | null) => {
    const commonImages = [
      'node:18', 'node:16', 'node:alpine',
      'python:3.11', 'python:3.10', 'python:alpine',
      'nginx:latest', 'nginx:alpine',
      'redis:7', 'redis:alpine',
      'mysql:8.0', 'mysql:5.7',
      'postgres:15', 'postgres:alpine',
      'openjdk:17', 'openjdk:11',
      'golang:1.20', 'golang:alpine',
      'ubuntu:22.04', 'ubuntu:20.04',
      'alpine:latest'
    ]

    if (!registryId) {
      return commonImages
    }

    const registry = registries.find(r => r.id === registryId)
    if (!registry || registry.registry_type === 'dockerhub') {
      return commonImages
    }

    // 私有注册表，添加注册表前缀
    const registryHost = registry.url.replace(/^https?:\/\//, '')
    return commonImages.map(img => `${registryHost}/${img}`)
  }, [registries])

  // 初始化时获取注册表列表
  useEffect(() => {
    fetchRegistries()
  }, [fetchRegistries])

  return {
    // 数据
    registries,
    loading,
    error,
    
    // 注册表操作
    fetchRegistries,
    createRegistry,
    testRegistry,
    setDefaultRegistry,
    
    // 步骤配置
    getStepDefaults,
    getInitialFormValues,
    validateStepConfig,
    
    // 工具函数
    generateFullImageName,
    getImageSuggestions,
    
    // 清除错误
    clearError: () => setError(null)
  }
}

export default useDockerStepConfig
