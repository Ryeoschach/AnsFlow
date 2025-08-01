import { authenticatedApiService } from './authenticatedApiService';

/**
 * Ansible相关API服务
 * 专门处理Ansible主机清单和主机组管理
 */
export class AnsibleApiService {
  /**
   * 从主机清单中移除主机组
   */
  public async removeGroupsFromInventory(
    inventoryId: number, 
    groupIds: number[]
  ): Promise<{ 
    message: string; 
    removed_count: number;
    current_stats?: {
      groups_count: number;
      active_groups_count: number;
    };
  }> {
    try {
      console.log('准备移除主机组:', {
        inventoryId,
        groupIds,
        count: groupIds.length
      });

      // 验证参数
      if (!inventoryId || inventoryId <= 0) {
        throw new Error('无效的主机清单ID');
      }

      if (!groupIds || groupIds.length === 0) {
        throw new Error('没有选择要移除的主机组');
      }

      // 执行API请求
      const result = await authenticatedApiService.post(
        `/ansible/inventories/${inventoryId}/remove_groups/`,
        { group_ids: groupIds }
      );

      console.log('主机组移除成功:', result);
      return result;

    } catch (error: any) {
      console.error('移除主机组失败:', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status,
        inventoryId,
        groupIds
      });

      // 根据错误类型提供友好的错误信息
      if (error.response?.status === 401) {
        throw new Error('认证失败，请重新登录');
      } else if (error.response?.status === 403) {
        throw new Error('权限不足，无法移除主机组');
      } else if (error.response?.status === 404) {
        throw new Error('主机清单或主机组不存在');
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.response?.data?.message) {
        throw new Error(error.response.data.message);
      } else {
        throw new Error(`移除主机组失败: ${error.message}`);
      }
    }
  }

  /**
   * 向主机清单添加主机组
   */
  public async addGroupsToInventory(
    inventoryId: number, 
    groupIds: number[]
  ): Promise<{ 
    message: string; 
    added_count: number;
    current_stats?: {
      groups_count: number;
      active_groups_count: number;
    };
  }> {
    try {
      console.log('准备添加主机组:', {
        inventoryId,
        groupIds,
        count: groupIds.length
      });

      const result = await authenticatedApiService.post(
        `/ansible/inventories/${inventoryId}/add_groups/`,
        { group_ids: groupIds }
      );

      console.log('主机组添加成功:', result);
      return result;

    } catch (error: any) {
      console.error('添加主机组失败:', error);
      
      if (error.response?.status === 401) {
        throw new Error('认证失败，请重新登录');
      } else if (error.response?.status === 403) {
        throw new Error('权限不足，无法添加主机组');
      } else {
        throw new Error(`添加主机组失败: ${error.message}`);
      }
    }
  }

  /**
   * 获取主机清单详情
   */
  public async getInventoryDetail(inventoryId: number): Promise<any> {
    try {
      return await authenticatedApiService.get(`/ansible/inventories/${inventoryId}/`);
    } catch (error: any) {
      console.error('获取主机清单详情失败:', error);
      throw error;
    }
  }

  /**
   * 获取主机清单中的主机组
   */
  public async getInventoryGroups(inventoryId: number): Promise<any[]> {
    try {
      const result = await authenticatedApiService.get(`/ansible/inventories/${inventoryId}/groups/`);
      return result.results || result;
    } catch (error: any) {
      console.error('获取主机清单主机组失败:', error);
      throw error;
    }
  }

  /**
   * 获取所有可用的主机组
   */
  public async getAvailableGroups(): Promise<any[]> {
    try {
      const result = await authenticatedApiService.get('/ansible/host_groups/');
      return result.results || result;
    } catch (error: any) {
      console.error('获取可用主机组失败:', error);
      throw error;
    }
  }

  /**
   * 测试主机组移除功能
   */
  public async testRemoveGroups(inventoryId: number, groupIds: number[]): Promise<void> {
    console.log('🧪 开始测试主机组移除功能');
    
    try {
      // 1. 获取认证状态
      const authInfo = authenticatedApiService.getAuthDebugInfo();
      console.log('认证状态:', authInfo);

      // 2. 验证API端点是否可访问
      const inventoryDetail = await this.getInventoryDetail(inventoryId);
      console.log('主机清单详情:', inventoryDetail);

      // 3. 执行移除操作
      const result = await this.removeGroupsFromInventory(inventoryId, groupIds);
      console.log('✅ 移除测试成功:', result);

    } catch (error) {
      console.error('❌ 移除测试失败:', error);
      throw error;
    }
  }
}

// 导出单例实例
export const ansibleApiService = new AnsibleApiService();
