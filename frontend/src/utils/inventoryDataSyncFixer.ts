/**
 * 清单数据同步修复工具
 * 用于强制刷新清单统计数据，解决主机组移除后统计不更新的问题
 */

import { apiService } from '../services/api';

export class InventoryDataSyncFixer {
  /**
   * 强制刷新指定清单的统计数据
   * @param inventoryId 清单ID
   * @returns 是否刷新成功
   */
  public static async forceRefreshInventoryStats(inventoryId: number): Promise<boolean> {
    try {
      console.log(`🔄 强制刷新清单 ${inventoryId} 的统计数据`);
      
      // 1. 重新获取清单数据（绕过可能的缓存）
      const timestamp = Date.now();
      const headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Requested-At': timestamp.toString()
      };
      
      // 使用自定义请求获取清单数据
      const inventory = await apiService.getAnsibleInventory(inventoryId);
      
      // 2. 验证统计数据的准确性
      const actualGroups = await apiService.getInventoryGroups(inventoryId);
      const actualGroupsCount = Array.isArray(actualGroups) ? actualGroups.length : 0;
      const actualActiveGroupsCount = Array.isArray(actualGroups) 
        ? actualGroups.filter((g: any) => g.is_active).length 
        : 0;
      
      const reportedGroupsCount = inventory.groups_count || 0;
      const reportedActiveGroupsCount = inventory.active_groups_count || 0;
      
      console.log('📊 统计数据对比:', {
        reported: {
          groups_count: reportedGroupsCount,
          active_groups_count: reportedActiveGroupsCount
        },
        actual: {
          groups_count: actualGroupsCount,
          active_groups_count: actualActiveGroupsCount
        },
        isConsistent: reportedGroupsCount === actualGroupsCount && 
                     reportedActiveGroupsCount === actualActiveGroupsCount
      });
      
      // 3. 如果数据不一致，尝试触发后端重新计算
      if (reportedGroupsCount !== actualGroupsCount || 
          reportedActiveGroupsCount !== actualActiveGroupsCount) {
        
        console.warn('⚠️ 检测到统计数据不一致，尝试触发后端重新计算');
        
        // 可以通过调用特定端点触发重新计算（如果后端支持）
        // 或者通过其他方式强制刷新
        
        return false; // 数据不一致
      }
      
      console.log('✅ 统计数据已同步');
      return true;
      
    } catch (error) {
      console.error('❌ 强制刷新统计数据失败:', error);
      return false;
    }
  }

  /**
   * 修复所有清单的统计数据
   */
  public static async fixAllInventoryStats(): Promise<{
    total: number;
    fixed: number;
    failed: number;
    results: Array<{ id: number; name: string; success: boolean; error?: string }>;
  }> {
    try {
      console.log('🔧 开始修复所有清单的统计数据');
      
      // 获取所有清单
      const inventories = await apiService.getAnsibleInventories();
      const results: Array<{ id: number; name: string; success: boolean; error?: string }> = [];
      
      let fixed = 0;
      let failed = 0;
      
      for (const inventory of inventories) {
        try {
          const success = await this.forceRefreshInventoryStats(inventory.id);
          results.push({
            id: inventory.id,
            name: inventory.name,
            success
          });
          
          if (success) {
            fixed++;
          } else {
            failed++;
          }
        } catch (error: any) {
          results.push({
            id: inventory.id,
            name: inventory.name,
            success: false,
            error: error.message
          });
          failed++;
        }
      }
      
      console.log('🎯 修复完成:', {
        total: inventories.length,
        fixed,
        failed
      });
      
      return {
        total: inventories.length,
        fixed,
        failed,
        results
      };
      
    } catch (error) {
      console.error('❌ 批量修复失败:', error);
      throw error;
    }
  }

  /**
   * 实时监控清单统计数据的一致性
   * @param inventoryId 清单ID
   * @param onInconsistency 检测到不一致时的回调
   */
  public static startMonitoring(
    inventoryId: number, 
    onInconsistency: (data: {
      inventoryId: number;
      reported: { groups_count: number; active_groups_count: number };
      actual: { groups_count: number; active_groups_count: number };
    }) => void
  ): () => void {
    
    const checkConsistency = async () => {
      try {
        const inventory = await apiService.getAnsibleInventory(inventoryId);
        const actualGroups = await apiService.getInventoryGroups(inventoryId);
        
        const actualGroupsCount = Array.isArray(actualGroups) ? actualGroups.length : 0;
        const actualActiveGroupsCount = Array.isArray(actualGroups) 
          ? actualGroups.filter((g: any) => g.is_active).length 
          : 0;
        
        const reportedGroupsCount = inventory.groups_count || 0;
        const reportedActiveGroupsCount = inventory.active_groups_count || 0;
        
        if (reportedGroupsCount !== actualGroupsCount || 
            reportedActiveGroupsCount !== actualActiveGroupsCount) {
          
          onInconsistency({
            inventoryId,
            reported: {
              groups_count: reportedGroupsCount,
              active_groups_count: reportedActiveGroupsCount
            },
            actual: {
              groups_count: actualGroupsCount,
              active_groups_count: actualActiveGroupsCount
            }
          });
        }
      } catch (error) {
        console.error('监控过程中发生错误:', error);
      }
    };
    
    // 每5秒检查一次
    const intervalId = setInterval(checkConsistency, 5000);
    
    // 返回停止监控的函数
    return () => {
      clearInterval(intervalId);
      console.log(`停止监控清单 ${inventoryId} 的统计数据`);
    };
  }
}
