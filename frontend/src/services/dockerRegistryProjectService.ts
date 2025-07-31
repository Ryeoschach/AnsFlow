import { DockerRegistryProject, DockerRegistryProjectFormData } from '../types/docker';

const API_BASE_URL = '/api/v1/docker';

/**
 * Docker注册表项目服务类
 * 提供项目的CRUD操作和管理功能
 */
export class DockerRegistryProjectService {
  /**
   * 获取授权头
   */
  private static getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  /**
   * 获取所有项目
   */
  static async getAllProjects(): Promise<DockerRegistryProject[]> {
    const response = await fetch(`${API_BASE_URL}/registries/projects/`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取项目列表失败');
    }

    const data = await response.json();
    return Array.isArray(data) ? data : data.results || [];
  }

  /**
   * 获取指定注册表的项目
   */
  static async getRegistryProjects(registryId: number): Promise<DockerRegistryProject[]> {
    const response = await fetch(`${API_BASE_URL}/registries/${registryId}/projects/`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取注册表项目失败');
    }

    const data = await response.json();
    return Array.isArray(data) ? data : data.results || [];
  }

  /**
   * 获取单个项目详情
   */
  static async getProject(id: number): Promise<DockerRegistryProject> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/${id}/`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取项目详情失败');
    }

    return response.json();
  }

  /**
   * 创建新项目
   */
  static async createProject(data: DockerRegistryProjectFormData): Promise<DockerRegistryProject> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '创建项目失败');
    }

    return response.json();
  }

  /**
   * 更新项目
   */
  static async updateProject(id: number, data: Partial<DockerRegistryProjectFormData>): Promise<DockerRegistryProject> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/${id}/`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '更新项目失败');
    }

    return response.json();
  }

  /**
   * 删除项目
   */
  static async deleteProject(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/${id}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('删除项目失败');
    }
  }

  /**
   * 根据注册表ID过滤项目
   */
  static async getProjectsByRegistry(registryId: number): Promise<DockerRegistryProject[]> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/?registry_id=${registryId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取项目失败');
    }

    const data = await response.json();
    return data.results || data;
  }

  /**
   * 同步项目信息（从远程注册表同步）
   */
  static async syncProjects(registryId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/registries/${registryId}/sync_projects/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('同步项目失败');
    }
  }

  /**
   * 设置默认项目
   */
  static async setDefaultProject(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/${id}/set_default/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('设置默认项目失败');
    }
  }

  /**
   * 获取项目统计信息
   */
  static async getProjectStats(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/registry-projects/${id}/stats/`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取项目统计失败');
    }

    return response.json();
  }
}

export default DockerRegistryProjectService;
