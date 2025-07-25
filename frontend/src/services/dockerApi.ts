import axios from 'axios';

// API基础URL配置
const API_BASE_URL = '/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken'); // 修复：使用正确的token键名
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，重定向到登录页
      localStorage.removeItem('authToken'); // 修复：使用正确的token键名
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Docker注册表相关API
export const dockerRegistryAPI = {
  // 获取所有注册表
  getRegistries: () =>
    apiClient.get('/v1/docker/registries/'),

  // 创建注册表
  createRegistry: (data: any) =>
    apiClient.post('/v1/docker/registries/', data),

  // 更新注册表
  updateRegistry: (id: number, data: any) =>
    apiClient.put(`/v1/docker/registries/${id}/`, data),

  // 删除注册表
  deleteRegistry: (id: number) =>
    apiClient.delete(`/v1/docker/registries/${id}/`),

  // 测试注册表连接
  testRegistry: (id: number) =>
    apiClient.post(`/v1/docker/registries/${id}/test-connection/`),

  // 设置默认注册表
  setDefaultRegistry: (id: number) =>
    apiClient.post(`/v1/docker/registries/${id}/set-default/`),

  // 获取注册表的项目列表
  getRegistryProjects: (registryId: number) =>
    apiClient.get(`/v1/docker/registry-projects/?registry=${registryId}`),

  // 获取所有项目
  getProjects: () =>
    apiClient.get('/v1/docker/registry-projects/'),

  // 创建项目
  createProject: (data: any) =>
    apiClient.post('/v1/docker/registry-projects/', data),

  // 更新项目
  updateProject: (id: number, data: any) =>
    apiClient.put(`/v1/docker/registry-projects/${id}/`, data),

  // 删除项目
  deleteProject: (id: number) =>
    apiClient.delete(`/v1/docker/registry-projects/${id}/`),

  // 设置默认项目
  setDefaultProject: (id: number) =>
    apiClient.post(`/v1/docker/registry-projects/${id}/set-default/`),
};

// Docker镜像相关API
export const dockerImageAPI = {
  // 获取镜像列表
  getImages: (params?: any) =>
    apiClient.get('/v1/docker/images/', { params }),

  // 构建镜像
  buildImage: (data: any) =>
    apiClient.post('/v1/docker/images/build/', data),

  // 推送镜像
  pushImage: (id: number, data: any) =>
    apiClient.post(`/v1/docker/images/${id}/push/`, data),

  // 拉取镜像
  pullImage: (data: any) =>
    apiClient.post('/v1/docker/images/pull/', data),

  // 获取镜像构建日志
  getBuildLogs: (id: number) =>
    apiClient.get(`/v1/docker/images/${id}/logs/`),

  // 获取镜像建议
  getImageSuggestions: (query: string) =>
    apiClient.get(`/v1/docker/images/suggestions/?q=${query}`),
};

// Docker容器相关API
export const dockerContainerAPI = {
  // 获取容器列表
  getContainers: (params?: any) =>
    apiClient.get('/v1/docker/containers/', { params }),

  // 创建并运行容器
  runContainer: (data: any) =>
    apiClient.post('/v1/docker/containers/run/', data),

  // 停止容器
  stopContainer: (id: number) =>
    apiClient.post(`/v1/docker/containers/${id}/stop/`),

  // 启动容器
  startContainer: (id: number) =>
    apiClient.post(`/v1/docker/containers/${id}/start/`),

  // 重启容器
  restartContainer: (id: number) =>
    apiClient.post(`/v1/docker/containers/${id}/restart/`),

  // 删除容器
  removeContainer: (id: number) =>
    apiClient.delete(`/v1/docker/containers/${id}/`),

  // 获取容器日志
  getContainerLogs: (id: number, params?: any) =>
    apiClient.get(`/v1/docker/containers/${id}/logs/`, { params }),

  // 获取容器统计信息
  getContainerStats: (id: number) =>
    apiClient.get(`/v1/docker/containers/${id}/stats/`),
};

// 通用类型定义
export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DockerRegistry {
  id: number;
  name: string;
  url: string;
  registry_type: string;
  username: string;
  description: string;
  status: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  available_projects?: DockerRegistryProject[];
}

export interface DockerRegistryProject {
  id: number;
  name: string;
  description?: string;
  is_default: boolean;
  registry: number;
  registry_name?: string;
  created_at: string;
  updated_at: string;
}

export interface DockerImage {
  id: number;
  name: string;
  tag: string;
  registry: number;
  registry_name: string;
  build_status: string;
  image_size?: number;
  created_at: string;
  updated_at: string;
}

export interface DockerContainer {
  id: number;
  name: string;
  image: number;
  image_name: string;
  status: string;
  created_at: string;
  started_at?: string;
}

export default apiClient;
