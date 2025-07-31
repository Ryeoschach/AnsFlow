import { useState, useEffect, useCallback } from 'react'

// 定义项目接口
export interface DockerRegistryProject {
  id: number
  name: string
  description?: string
  registry: number  // 匹配后端序列化器的字段名
  registry_name?: string
  image_count: number
  last_updated: string
  visibility: 'public' | 'private'
  tags: string[]
  is_default: boolean
  config: Record<string, any>
  created_by: number
  created_at: string
  updated_at: string
}

// 定义Hook返回类型
export interface UseDockerRegistryProjectsReturn {
  projects: DockerRegistryProject[]
  loading: boolean
  error: string | null
  getRegistryProjects: (registryId: number) => DockerRegistryProject[]
  fetchProjects: () => Promise<void>
  refreshProjects: (registryId: number) => Promise<void>
}

/**
 * Docker注册表项目管理Hook
 * 提供获取和管理Docker注册表中项目的功能
 */
export const useDockerRegistryProjects = (): UseDockerRegistryProjectsReturn => {
  const [projects, setProjects] = useState<DockerRegistryProject[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 获取所有注册表的项目
  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // 首先获取所有注册表
      const registriesResponse = await fetch('/api/v1/docker/registries/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      })

      if (!registriesResponse.ok) {
        throw new Error(`获取注册表列表失败: ${registriesResponse.statusText}`)
      }

      const registriesData = await registriesResponse.json()
      const registries = Array.isArray(registriesData) ? registriesData : registriesData.results || []
      
      // 为每个注册表获取项目列表
      const allProjects: DockerRegistryProject[] = []
      
      for (const registry of registries) {
        try {
          const projectsResponse = await fetch(`/api/v1/docker/registries/${registry.id}/projects/`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
          })

          if (projectsResponse.ok) {
            const projectsData = await projectsResponse.json()
            const projects = Array.isArray(projectsData) ? projectsData : projectsData.results || []
            
            // 为每个项目添加数字ID以确保兼容性
            const processedProjects = projects.map((project: any) => ({
              ...project,
              id: parseInt(project.id, 10), // 确保ID是数字
              registry: registry.id
            }))
            
            allProjects.push(...processedProjects)
          }
        } catch (error) {
          console.warn(`获取注册表 ${registry.id} 的项目失败:`, error)
        }
      }
      
      setProjects(allProjects)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取项目列表失败'
      setError(errorMessage)
      console.error('获取Docker注册表项目失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 根据注册表ID获取项目
  const getRegistryProjects = useCallback((registryId: number): DockerRegistryProject[] => {
    return projects.filter(project => project.registry === registryId)
  }, [projects])

  // 刷新特定注册表的项目
  const refreshProjects = useCallback(async (registryId: number) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/v1/docker/registries/${registryId}/projects/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      })

      if (!response.ok) {
        throw new Error(`刷新注册表项目失败: ${response.statusText}`)
      }

      const data = await response.json()
      
      // 更新对应注册表的项目
      setProjects(prevProjects => {
        const otherProjects = prevProjects.filter(p => p.registry !== registryId)
        return [...otherProjects, ...data]
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新项目失败'
      setError(errorMessage)
      console.error('刷新Docker注册表项目失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 组件挂载时自动获取项目列表
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    loading,
    error,
    getRegistryProjects,
    fetchProjects,
    refreshProjects
  }
}

export default useDockerRegistryProjects
