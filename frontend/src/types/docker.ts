/**
 * Docker集成前端类型定义
 */

// 基础接口
export interface BaseModel {
  id: number;
  created_at: string;
  updated_at: string;
}

// 端口映射
export interface PortMapping {
  host: string;
  container: string;
  protocol?: 'tcp' | 'udp';
}

// 数据卷映射
export interface VolumeMapping {
  host: string;
  container: string;
  mode?: 'ro' | 'rw';
}

// Docker仓库类型
export type DockerRegistryType = 'dockerhub' | 'private' | 'harbor' | 'ecr' | 'gcr' | 'acr';

// Docker仓库状态
export type DockerRegistryStatus = 'active' | 'inactive' | 'error';

// Docker仓库接口
export interface DockerRegistry extends BaseModel {
  name: string;
  url: string;
  registry_type: DockerRegistryType;
  username: string;
  project_name: string;
  description: string;
  status: DockerRegistryStatus;
  last_check?: string;
  check_message: string;
  is_default: boolean;
  created_by: number;
}

// Docker仓库列表接口
export interface DockerRegistryList {
  id: number;
  name: string;
  url: string;
  registry_type: DockerRegistryType;
  project_name: string;
  status: DockerRegistryStatus;
  is_default: boolean;
}

// Docker镜像构建状态
export type DockerImageBuildStatus = 'pending' | 'building' | 'success' | 'failed' | 'cancelled';

// Docker镜像版本接口
export interface DockerImageVersion extends BaseModel {
  id: number;
  version: string;
  dockerfile_content: string;
  build_context: string;
  build_args: Record<string, any>;
  checksum: string;
  changelog: string;
  docker_image_id: string;
  image_size?: number;
  is_release: boolean;
  created_by: number;
}

// Docker镜像接口
export interface DockerImage extends BaseModel {
  name: string;
  tag: string;
  registry: number;
  registry_name: string;
  full_name: string;
  dockerfile_content: string;
  build_context: string;
  build_args: Record<string, any>;
  image_size?: number;
  image_id: string;
  image_digest: string;
  build_status: DockerImageBuildStatus;
  build_logs: string;
  build_started_at?: string;
  build_completed_at?: string;
  build_duration?: number;
  is_pushed: boolean;
  pushed_at?: string;
  description: string;
  labels: Record<string, string>;
  is_template: boolean;
  created_by: number;
  versions: DockerImageVersion[];
}

// Docker镜像列表接口
export interface DockerImageList {
  id: number;
  name: string;
  tag: string;
  registry_name: string;
  build_status: DockerImageBuildStatus;
  image_size?: number;
  is_template: boolean;
  created_at: string;
}

// Docker容器状态
export type DockerContainerStatus = 'created' | 'running' | 'paused' | 'restarting' | 'removing' | 'stopped' | 'exited' | 'dead';

// Docker容器接口
export interface DockerContainer extends BaseModel {
  name: string;
  image: number;
  image_name: string;
  image_tag: string;
  container_id: string;
  command: string;
  working_dir: string;
  environment_vars: Record<string, string>;
  port_mappings: PortMapping[];
  volumes: VolumeMapping[];
  network_mode: string;
  memory_limit: string;
  cpu_limit: string;
  status: DockerContainerStatus;
  exit_code?: number;
  started_at?: string;
  finished_at?: string;
  description: string;
  labels: Record<string, string>;
  auto_remove: boolean;
  restart_policy: string;
  created_by: number;
  stats: DockerContainerStats[];
}

// Docker容器列表接口
export interface DockerContainerList {
  id: number;
  name: string;
  image_name: string;
  status: DockerContainerStatus;
  started_at?: string;
  created_at: string;
}

// Docker容器统计接口
export interface DockerContainerStats {
  id: number;
  cpu_usage_percent: number;
  cpu_system_usage: number;
  cpu_total_usage: number;
  memory_usage: number;
  memory_limit: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  block_read_bytes: number;
  block_write_bytes: number;
  pids: number;
  recorded_at: string;
}

// Docker Compose状态
export type DockerComposeStatus = 'created' | 'running' | 'stopped' | 'paused' | 'error';

// Docker Compose接口
export interface DockerCompose extends BaseModel {
  name: string;
  compose_content: string;
  working_directory: string;
  environment_file: string;
  status: DockerComposeStatus;
  services: string[];
  networks: string[];
  volumes: string[];
  description: string;
  labels: Record<string, string>;
  created_by: number;
}

// Docker Compose列表接口
export interface DockerComposeList {
  id: number;
  name: string;
  status: DockerComposeStatus;
  created_at: string;
}

// API响应接口
export interface DockerApiResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// Docker操作响应接口
export interface DockerActionResponse {
  status: 'success' | 'error';
  message: string;
  task_id?: string;
  data?: any;
}

// Dockerfile模板类型
export type DockerfileTemplateType = 'node' | 'python' | 'nginx' | 'java' | 'go';

// Dockerfile模板接口
export interface DockerfileTemplate {
  template: string;
}

// Docker Compose模板类型
export type DockerComposeTemplateType = 'web-app' | 'microservice' | 'database';

// Docker Compose模板接口
export interface DockerComposeTemplate {
  template: string;
}

// Docker构建参数接口
export interface DockerBuildArgs {
  [key: string]: string;
}

// Docker环境变量接口
export interface DockerEnvironmentVars {
  [key: string]: string;
}

// Docker镜像构建请求接口
export interface DockerImageBuildRequest {
  dockerfile_content?: string;
  build_args?: DockerBuildArgs;
  force_rebuild?: boolean;
}

// Docker镜像推送请求接口
export interface DockerImagePushRequest {
  tag?: string;
  registry_id?: number;
}

// Docker容器操作请求接口
export interface DockerContainerActionRequest {
  force?: boolean;
  timeout?: number;
}

// Docker容器日志请求接口
export interface DockerContainerLogsRequest {
  tail?: string;
  since?: string;
  follow?: boolean;
}

// Docker容器日志响应接口
export interface DockerContainerLogsResponse {
  logs: string;
  container_id: string;
}

// Docker Compose操作请求接口
export interface DockerComposeActionRequest {
  services?: string[];
  force?: boolean;
}

// Docker镜像版本创建请求接口
export interface DockerImageVersionCreateRequest {
  version: string;
  dockerfile_content: string;
  build_context: string;
  build_args?: DockerBuildArgs;
  changelog?: string;
  is_release?: boolean;
}

// Docker仓库测试连接响应接口
export interface DockerRegistryTestResponse {
  status: 'success' | 'error';
  message: string;
  latency?: number;
}

// Docker资源使用统计接口
export interface DockerResourceStats {
  total_images: number;
  total_containers: number;
  running_containers: number;
  total_registries: number;
  total_compose_projects: number;
  disk_usage: {
    images: number;
    containers: number;
    volumes: number;
    build_cache: number;
  };
}

// 表单数据接口
export interface DockerRegistryFormData {
  name: string;
  url: string;
  registry_type: DockerRegistryType;
  username?: string;
  password?: string;
  description?: string;
  is_default?: boolean;
}

export interface DockerImageFormData {
  name: string;
  tag: string;
  registry: number;
  dockerfile_content: string;
  build_context?: string;
  build_args?: DockerBuildArgs;
  description?: string;
  is_template?: boolean;
}

export interface DockerContainerFormData {
  name: string;
  image: number;
  command?: string;
  working_dir?: string;
  environment_vars?: DockerEnvironmentVars;
  port_mappings?: PortMapping[];
  volumes?: VolumeMapping[];
  network_mode?: string;
  memory_limit?: string;
  cpu_limit?: string;
  description?: string;
  restart_policy?: string;
  auto_remove?: boolean;
}

export interface DockerComposeFormData {
  name: string;
  compose_content: string;
  working_directory?: string;
  environment_file?: string;
  description?: string;
}
