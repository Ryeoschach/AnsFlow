// Ansible集成相关类型定义

export interface AnsibleInventory {
  id: number;
  name: string;
  description: string;
  content: string;
  format_type: 'ini' | 'yaml';
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
  hosts_count?: number;
  active_hosts_count?: number;
  groups_count?: number;
  active_groups_count?: number;
}

export interface AnsiblePlaybook {
  id: number;
  name: string;
  description: string;
  content: string;
  version: string;
  is_template: boolean;
  category: string;
  category_display: string;
  parameters: Record<string, any>;
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface AnsibleCredential {
  id: number;
  name: string;
  credential_type: 'ssh_key' | 'password' | 'vault';
  credential_type_display: string;
  username: string;
  has_password: boolean;
  has_ssh_key: boolean;
  has_vault_password: boolean;
  created_by: number;
  created_by_username: string;
  created_at: string;
}

export interface AnsibleExecution {
  id: number;
  playbook: AnsiblePlaybook;
  inventory: AnsibleInventory;
  credential: AnsibleCredential;
  parameters: Record<string, any>;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  status_display: string;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
  stdout: string;
  stderr: string;
  return_code: number | null;
  created_by: number;
  created_by_username: string;
  created_at: string;
}

export interface AnsibleExecutionList {
  id: number;
  playbook_name: string;
  inventory_name: string;
  credential_name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  status_display: string;
  duration: number | null;
  started_at: string | null;
  completed_at: string | null;
  return_code: number | null;
  created_by_username: string;
  created_at: string;
}

export interface AnsibleStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  running_executions: number;
  pending_executions: number;
  success_rate: number;
  total_playbooks: number;
  total_inventories: number;
  total_credentials: number;
}

export interface ExecutePlaybookRequest {
  inventory_id: number;
  credential_id: number;
  parameters?: Record<string, any>;
}

export interface ExecutePlaybookResponse {
  message: string;
  execution_id: number;
  task_id: string;
}

export interface ExecutionLogsResponse {
  execution_id: number;
  status: string;
  stdout: string;
  stderr: string;
  return_code: number | null;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  details?: string;
}

export interface AnsibleHost {
  id: number;
  hostname: string;
  ip_address: string;
  port: number;
  username: string;
  connection_type: string;
  become_method: string;
  credential?: number | null;  // 关联的认证凭据ID
  temp_password?: string;      // 临时密码
  temp_ssh_key?: string;       // 临时SSH密钥
  status: 'active' | 'inactive' | 'failed' | 'unknown';
  status_display: string;
  last_check: string | null;
  check_message: string;
  os_family: string;
  os_distribution: string;
  os_version: string;
  ansible_facts: Record<string, any>;
  tags: Record<string, any>;
  groups: AnsibleHostGroup[];
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface AnsibleHostGroup {
  id: number;
  name: string;
  description: string;
  parent: number | null;
  parent_name?: string;
  variables: Record<string, any>;
  children?: AnsibleHostGroup[];
  hosts_count: number;
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface AnsibleHostGroupMembership {
  id: number;
  host: AnsibleHost;
  group: AnsibleHostGroup;
  variables: Record<string, any>;
  created_at: string;
}

export interface AnsibleInventoryVersion {
  id: number;
  inventory: number;
  version: string;
  content: string;
  checksum: string;
  changelog: string;
  created_by: number;
  created_by_username: string;
  created_at: string;
}

export interface AnsiblePlaybookVersion {
  id: number;
  playbook: number;
  version: string;
  content: string;
  checksum: string;
  changelog: string;
  is_release: boolean;
  created_by: number;
  created_by_username: string;
  created_at: string;
}

export interface FileUploadRequest {
  file: File;
  name: string;
  description?: string;
}

export interface FileUploadResponse {
  id: number;
  name: string;
  message: string;
}

export interface HostConnectivityResult {
  host_id: number;
  hostname: string;
  success: boolean;
  status: string;
  message: string;
}

export interface HostFactsResult {
  success: boolean;
  facts?: Record<string, any>;
  message: string;
}

export interface ConnectionTestRequest {
  ip_address: string;
  username: string;
  port?: number;
  connection_type?: string;
  password?: string;
  ssh_private_key?: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  details?: {
    return_code: number;
    stdout: string;
    stderr: string;
    command: string;
  };
}

export interface BatchHostOperation {
  action: 'check_connectivity' | 'gather_facts' | 'add_to_group' | 'remove_from_group';
  host_ids: number[];
  group_id?: number;
}

export interface InventoryGroup {
  id: number;
  inventory: number;
  group: number;          // 兼容性字段
  group_id: number;       // 后端实际返回的字段
  group_name: string;
  group_description: string;
  inventory_name: string;
  group_variables: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  hosts_count?: number;
}

export interface InventoryGroupBatch {
  inventory_id: number;
  group_ids: number[];
  inventory_names?: string[];
  group_variables?: Record<string, any>[];
  is_active?: boolean;
}
