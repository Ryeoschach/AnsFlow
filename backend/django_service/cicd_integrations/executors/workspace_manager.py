"""
流水线工作目录管理器
为每个流水线执行创建独立的工作目录
"""
import os
import tempfile
import shutil
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PipelineWorkspaceManager:
    """流水线工作目录管理器"""
    
    def __init__(self):
        self.base_dir = "/tmp"
        self.workspaces: Dict[str, str] = {}  # execution_id -> workspace_path
        # 默认保留工作目录，便于调试和查看执行结果
        self.preserve_workspaces = True
    
    def create_workspace(self, pipeline_name: str, execution_id: int) -> str:
        """
        为流水线执行创建工作目录
        
        Args:
            pipeline_name: 流水线名称
            execution_id: 流水线执行编号
            
        Returns:
            工作目录路径
        """
        try:
            # 清理流水线名称，确保它可以作为文件夹名
            safe_pipeline_name = self._sanitize_name(pipeline_name)
            
            # 创建目录名：/tmp/流水线名称_执行编号
            workspace_name = f"{safe_pipeline_name}_{execution_id}"
            workspace_path = os.path.join(self.base_dir, workspace_name)
            
            # 如果目录已存在，检查是否为空
            if os.path.exists(workspace_path):
                # 检查目录是否为空
                if os.listdir(workspace_path):
                    logger.info(f"Workspace already exists and has content, reusing: {workspace_path}")
                else:
                    logger.info(f"Workspace already exists but is empty, reusing: {workspace_path}")
            else:
                # 创建工作目录
                os.makedirs(workspace_path, exist_ok=True)
                logger.info(f"Created new workspace: {workspace_path}")
            
            # 记录工作目录
            workspace_key = f"{execution_id}"
            self.workspaces[workspace_key] = workspace_path
            
            logger.info(f"Created workspace for pipeline '{pipeline_name}' execution {execution_id}: {workspace_path}")
            return workspace_path
            
        except Exception as e:
            logger.error(f"Failed to create workspace for pipeline '{pipeline_name}' execution {execution_id}: {e}")
            raise
    
    def get_workspace(self, execution_id: int) -> Optional[str]:
        """
        获取流水线执行的工作目录
        
        Args:
            execution_id: 流水线执行编号
            
        Returns:
            工作目录路径，如果不存在返回None
        """
        workspace_key = f"{execution_id}"
        return self.workspaces.get(workspace_key)
    
    def cleanup_workspace(self, execution_id: int, force_cleanup: bool = False) -> bool:
        """
        清理流水线执行的工作目录
        
        Args:
            execution_id: 流水线执行编号
            force_cleanup: 是否强制清理，忽略全局保留设置
            
        Returns:
            是否清理成功
        """
        try:
            workspace_key = f"{execution_id}"
            workspace_path = self.workspaces.get(workspace_key)
            
            # 检查是否应该保留工作目录
            if self.preserve_workspaces and not force_cleanup:
                if workspace_path:
                    logger.info(f"工作目录保留模式：跳过清理 {workspace_path} (execution_id: {execution_id})")
                    logger.info(f"工作目录位置: {workspace_path}")
                    logger.info(f"如需强制清理，请调用 workspace_manager.cleanup_workspace({execution_id}, force_cleanup=True)")
                return True
            
            if workspace_path and os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
                logger.info(f"Cleaned up workspace for execution {execution_id}: {workspace_path}")
            
            # 从记录中移除
            if workspace_key in self.workspaces:
                del self.workspaces[workspace_key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup workspace for execution {execution_id}: {e}")
            return False
    
    def force_cleanup_workspace(self, execution_id: int) -> bool:
        """强制清理指定的工作目录"""
        return self.cleanup_workspace(execution_id, force_cleanup=True)
    
    def set_preserve_workspaces(self, preserve: bool):
        """
        设置是否保留工作目录
        
        Args:
            preserve: True表示保留工作目录，False表示自动清理
        """
        self.preserve_workspaces = preserve
        logger.info(f"工作目录保留模式设置为: {preserve}")
    
    def list_preserved_workspaces(self) -> Dict[str, str]:
        """
        列出所有保留的工作目录
        
        Returns:
            Dict[execution_id, workspace_path]
        """
        preserved = {}
        for execution_id, workspace_path in self.workspaces.items():
            if os.path.exists(workspace_path):
                preserved[execution_id] = workspace_path
        return preserved
    
    def ensure_workspace_exists(self, execution_id: int) -> bool:
        """
        确保工作目录存在
        
        Args:
            execution_id: 流水线执行编号
            
        Returns:
            工作目录是否存在
        """
        workspace_path = self.get_workspace(execution_id)
        if workspace_path and os.path.exists(workspace_path):
            return True
        return False
    
    def _sanitize_name(self, name: str) -> str:
        """
        清理名称，确保可以作为文件夹名
        
        Args:
            name: 原始名称
            
        Returns:
            清理后的名称
        """
        import re
        
        # 替换非法字符为下划线
        sanitized = re.sub(r'[<>:"/\\|?*\s]', '_', name)
        
        # 移除多余的下划线
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 移除首尾下划线
        sanitized = sanitized.strip('_')
        
        # 限制长度
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        # 如果为空，使用默认名称
        if not sanitized:
            sanitized = "pipeline"
        
        return sanitized
    
    def list_workspaces(self) -> Dict[str, str]:
        """
        列出所有工作目录
        
        Returns:
            执行ID到工作目录路径的映射
        """
        return self.workspaces.copy()
    
    def cleanup_all_workspaces(self) -> int:
        """
        清理所有工作目录
        
        Returns:
            清理的目录数量
        """
        cleaned_count = 0
        
        for execution_id in list(self.workspaces.keys()):
            try:
                execution_id_int = int(execution_id)
                if self.cleanup_workspace(execution_id_int):
                    cleaned_count += 1
            except ValueError:
                continue
        
        return cleaned_count

# 全局工作目录管理器实例
workspace_manager = PipelineWorkspaceManager()
