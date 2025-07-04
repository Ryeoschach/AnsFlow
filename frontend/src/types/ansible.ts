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
