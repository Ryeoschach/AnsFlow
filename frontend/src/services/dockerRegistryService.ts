import { DockerRegistry, DockerRegistryList } from '../types/docker'

export interface CreateDockerRegistryRequest {
  name: string
  url: string
  registry_type: string
  username?: string
  password?: string
  description?: string
  is_default?: boolean
}

export interface UpdateDockerRegistryRequest {
  name?: string
  url?: string
  registry_type?: string
  username?: string
  password?: string
  description?: string
  is_default?: boolean
}

class DockerRegistryService {
  private baseUrl: string

  constructor() {
    this.baseUrl = '/api/v1/docker/registries'
  }

  /**
   * 获取所有注册表列表
   */
  async getRegistries(): Promise<DockerRegistryList[]> {
    const response = await fetch(this.baseUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`获取注册表列表失败: ${response.statusText}`)
    }

    const data = await response.json()
    // 后端返回分页格式，提取results数组
    return data.results || data
  }

  /**
   * 获取注册表详情
   */
  async getRegistry(id: number): Promise<DockerRegistry> {
    const response = await fetch(`${this.baseUrl}/${id}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`获取注册表详情失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 创建新注册表
   */
  async createRegistry(data: CreateDockerRegistryRequest): Promise<DockerRegistry> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      throw new Error(`创建注册表失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 更新注册表
   */
  async updateRegistry(id: number, data: UpdateDockerRegistryRequest): Promise<DockerRegistry> {
    const response = await fetch(`${this.baseUrl}/${id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      throw new Error(`更新注册表失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 删除注册表
   */
  async deleteRegistry(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`删除注册表失败: ${response.statusText}`)
    }
  }

  /**
   * 测试注册表连接
   */
  async testRegistry(id: number): Promise<{ success: boolean; message: string }> {
    console.log('dockerRegistryService.testRegistry 开始调用，ID:', id)
    
    const response = await fetch(`${this.baseUrl}/${id}/test_connection/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    console.log('HTTP 响应状态:', response.status, response.statusText)
    console.log('HTTP 响应 OK:', response.ok)

    if (!response.ok) {
      console.log('HTTP 响应不正常，尝试解析错误')
      // 尝试解析错误响应
      try {
        const errorData = await response.json()
        console.log('解析的错误数据:', errorData)
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
      } catch (parseError) {
        console.log('解析错误失败:', parseError)
        throw new Error(`测试注册表连接失败: HTTP ${response.status}`)
      }
    }

    const result = await response.json()
    console.log('成功解析的响应数据:', result)
    return result
  }

  /**
   * 设置默认注册表
   */
  async setDefaultRegistry(id: number): Promise<DockerRegistry> {
    const response = await fetch(`${this.baseUrl}/${id}/set_default/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`设置默认注册表失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 获取注册表下的镜像列表
   */
  async getRegistryImages(registryId: number, page = 1, pageSize = 20): Promise<{
    results: Array<{
      name: string
      tags: string[]
      size: number
      created_at: string
    }>
    count: number
    next: string | null
    previous: string | null
  }> {
    const response = await fetch(`${this.baseUrl}/${registryId}/images/?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`获取镜像列表失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 搜索注册表中的镜像
   */
  async searchImages(registryId: number, query: string): Promise<Array<{
    name: string
    description: string
    stars: number
    official: boolean
  }>> {
    const response = await fetch(`${this.baseUrl}/${registryId}/search/?q=${encodeURIComponent(query)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`搜索镜像失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 获取注册表的使用统计
   */
  async getRegistryStats(id: number): Promise<{
    total_images: number
    total_pulls: number
    total_pushes: number
    storage_usage: number
    last_activity: string
  }> {
    const response = await fetch(`${this.baseUrl}/${id}/stats/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`获取注册表统计失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 同步注册表信息
   */
  async syncRegistry(id: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/${id}/sync/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      throw new Error(`同步注册表失败: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 获取默认注册表
   */
  async getDefaultRegistry(): Promise<DockerRegistryList | null> {
    try {
      const registries = await this.getRegistries()
      return registries.find(r => r.is_default) || null
    } catch (error) {
      console.error('获取默认注册表失败:', error)
      return null
    }
  }

  /**
   * 验证注册表URL格式
   */
  validateRegistryUrl(url: string): boolean {
    try {
      const urlObj = new URL(url)
      return ['http:', 'https:'].includes(urlObj.protocol)
    } catch {
      return false
    }
  }

  /**
   * 生成镜像全名（包含注册表前缀）
   */
  generateFullImageName(registry: DockerRegistry, imageName: string, tag: string = 'latest'): string {
    if (registry.registry_type === 'dockerhub') {
      return `${imageName}:${tag}`
    }
    
    const registryHost = registry.url.replace(/^https?:\/\//, '')
    return `${registryHost}/${imageName}:${tag}`
  }

  /**
   * 解析镜像名称
   */
  parseImageName(fullImageName: string): {
    registry?: string
    name: string
    tag: string
  } {
    const parts = fullImageName.split('/')
    let registry: string | undefined
    let name: string
    let tag = 'latest'

    if (parts.length > 1 && parts[0].includes('.')) {
      // 包含注册表地址
      registry = parts[0]
      name = parts.slice(1).join('/')
    } else {
      // Docker Hub 镜像
      name = parts.join('/')
    }

    // 提取标签
    if (name.includes(':')) {
      const [imageName, imageTag] = name.split(':')
      name = imageName
      tag = imageTag
    }

    return { registry, name, tag }
  }
}

export const dockerRegistryService = new DockerRegistryService()
export default dockerRegistryService
