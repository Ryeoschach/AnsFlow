"""
Django数据库连接服务
用于从FastAPI连接到Django的MySQL数据库获取真实的执行数据
"""
import asyncio
import aiomysql
import structlog
import os
from typing import Dict, List, Optional
from datetime import datetime

logger = structlog.get_logger(__name__)


class DjangoDBService:
    """Django数据库连接服务"""
    
    def __init__(self):
        self.connection_pool = None
        # Django数据库连接配置（MySQL）
        self.db_config = {
            "host": os.getenv("DJANGO_DB_HOST", "localhost"),
            "port": int(os.getenv("DJANGO_DB_PORT", 3306)),
            "user": os.getenv("DJANGO_DB_USER", "ansflow_user"),
            "password": os.getenv("DJANGO_DB_PASSWORD", "ansflow_password_123"),
            "db": os.getenv("DJANGO_DB_NAME", "ansflow_db"),
            "charset": "utf8mb4",
            "autocommit": True
        }
    
    async def init_connection_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = await aiomysql.create_pool(
                **self.db_config,
                minsize=1,
                maxsize=10
            )
            logger.info("Django MySQL database connection pool initialized")
        except Exception as e:
            logger.error("Failed to initialize MySQL database connection pool", error=str(e))
            # 如果无法连接到数据库，使用模拟数据
            self.connection_pool = None
    
    async def close_connection_pool(self):
        """关闭数据库连接池"""
        if self.connection_pool:
            self.connection_pool.close()
            await self.connection_pool.wait_closed()
            logger.info("Django MySQL database connection pool closed")
    
    async def get_execution_with_steps(self, execution_id: int) -> Optional[Dict]:
        """获取执行记录及其步骤信息"""
        if not self.connection_pool:
            logger.warning("No database connection available, using mock data", execution_id=execution_id)
            return await self._get_mock_execution_data(execution_id)
        
        try:
            async with self.connection_pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # 查询执行记录
                    await cursor.execute("""
                        SELECT pe.id, pe.status, pe.created_at, pe.started_at, pe.completed_at,
                               pe.logs as execution_logs, pe.parameters,
                               p.name as pipeline_name, p.description as pipeline_description
                        FROM cicd_integrations_pipelineexecution pe
                        LEFT JOIN pipelines_pipeline p ON pe.pipeline_id = p.id
                        WHERE pe.id = %s
                    """, (execution_id,))
                    
                    execution_row = await cursor.fetchone()
                    if not execution_row:
                        logger.warning("Execution not found in database", execution_id=execution_id)
                        return None
                    
                    # 查询步骤记录（包括并行组信息）
                    await cursor.execute("""
                        SELECT se.id, se.status, se.started_at, se.completed_at,
                               se.logs, se.error_message, se.order,
                               cas.name as atomic_step_name,
                               ps.parallel_group
                        FROM cicd_integrations_stepexecution se
                        LEFT JOIN cicd_integrations_atomicstep cas ON se.atomic_step_id = cas.id
                        LEFT JOIN pipelines_pipelinestep ps ON (cas.id = ps.id AND cas.pipeline_id = ps.pipeline_id)
                        WHERE se.pipeline_execution_id = %s
                        ORDER BY se.order ASC, se.id ASC
                    """, (execution_id,))
                    
                    step_rows = await cursor.fetchall()
                    
                    # 处理步骤数据，按并行组组织
                    steps = []
                    parallel_groups = {}
                    
                    for step_row in step_rows:
                        # 计算执行时间
                        execution_time = None
                        if step_row["started_at"] and step_row["completed_at"]:
                            execution_time = (step_row["completed_at"] - step_row["started_at"]).total_seconds()
                        
                        step_data = {
                            "id": step_row["id"],
                            "name": step_row["atomic_step_name"] or f"步骤 {step_row['id']}",
                            "status": step_row["status"].lower() if step_row["status"] else "pending",
                            "execution_time": execution_time,
                            "output": step_row["logs"] or "",
                            "error_message": step_row["error_message"],
                            "order": step_row["order"],
                            "parallel_group": step_row["parallel_group"]
                        }
                        
                        # 如果有并行组，则按组归类
                        if step_row["parallel_group"]:
                            if step_row["parallel_group"] not in parallel_groups:
                                parallel_groups[step_row["parallel_group"]] = {
                                    "group_id": step_row["parallel_group"],
                                    "name": f"并行组 {len(parallel_groups) + 1}",
                                    "type": "parallel_group",
                                    "status": "pending",
                                    "steps": [],
                                    "order": step_row["order"]  # 使用第一个步骤的order作为组的order
                                }
                            parallel_groups[step_row["parallel_group"]]["steps"].append(step_data)
                        else:
                            # 没有并行组的步骤直接添加
                            steps.append(step_data)
                    
                    # 将并行组添加到步骤列表中，并按order排序
                    for group_id, group_data in parallel_groups.items():
                        # 计算并行组的整体状态
                        group_steps = group_data["steps"]
                        if all(step["status"] == "success" for step in group_steps):
                            group_data["status"] = "success"
                        elif any(step["status"] == "failed" for step in group_steps):
                            group_data["status"] = "failed"
                        elif any(step["status"] == "running" for step in group_steps):
                            group_data["status"] = "running"
                        else:
                            group_data["status"] = "pending"
                        
                        # 计算并行组的总执行时间（最长的步骤时间）
                        max_execution_time = 0
                        for step in group_steps:
                            if step["execution_time"]:
                                max_execution_time = max(max_execution_time, step["execution_time"])
                        group_data["execution_time"] = max_execution_time if max_execution_time > 0 else None
                        
                        steps.append(group_data)
                    
                    # 按order排序所有步骤和组
                    steps.sort(key=lambda x: x.get("order", 0))
                    
                    # 计算总执行时间
                    total_execution_time = 0
                    if execution_row["started_at"] and execution_row["completed_at"]:
                        total_execution_time = (execution_row["completed_at"] - execution_row["started_at"]).total_seconds()
                    elif execution_row["started_at"]:
                        total_execution_time = (datetime.now() - execution_row["started_at"]).total_seconds()
                    
                    return {
                        "id": execution_row["id"],
                        "status": execution_row["status"].lower() if execution_row["status"] else "pending",
                        "pipeline_name": execution_row["pipeline_name"] or f"流水线执行 #{execution_id}",
                        "execution_time": total_execution_time,
                        "steps": steps,
                        "created_at": execution_row["created_at"].isoformat() if execution_row["created_at"] else None,
                        "started_at": execution_row["started_at"].isoformat() if execution_row["started_at"] else None,
                        "completed_at": execution_row["completed_at"].isoformat() if execution_row["completed_at"] else None
                    }
                    
        except Exception as e:
            logger.error("Error fetching execution data from Django MySQL DB", 
                        execution_id=execution_id, error=str(e))
            # 出错时返回静态模拟数据
            return await self._get_mock_execution_data(execution_id)
    
    async def get_execution_logs(self, execution_id: int, last_count: int = 0) -> List[Dict]:
        """获取执行日志（增量获取）"""
        if not self.connection_pool:
            # 如果没有数据库连接，返回空列表（避免模拟日志）
            return []
        
        try:
            async with self.connection_pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # 从执行记录和步骤记录中提取日志信息
                    # 先获取主执行日志
                    await cursor.execute("""
                        SELECT pe.id, pe.logs, pe.status, pe.started_at, pe.completed_at,
                               p.name as pipeline_name
                        FROM cicd_integrations_pipelineexecution pe
                        LEFT JOIN pipelines_pipeline p ON pe.pipeline_id = p.id
                        WHERE pe.id = %s
                    """, (execution_id,))
                    
                    execution_row = await cursor.fetchone()
                    if not execution_row:
                        return []
                    
                    # 获取步骤日志
                    await cursor.execute("""
                        SELECT se.id, se.logs, se.status, se.started_at, se.completed_at,
                               se.order, atos.name as step_name
                        FROM cicd_integrations_stepexecution se
                        LEFT JOIN cicd_integrations_atomicstep atos ON se.atomic_step_id = atos.id
                        WHERE se.pipeline_execution_id = %s
                        ORDER BY se.order ASC, se.id ASC
                    """, (execution_id,))
                    
                    step_rows = await cursor.fetchall()
                    
                    # 构建日志条目
                    logs = []
                    log_id = 1
                    
                    # 添加执行开始日志
                    if execution_row["started_at"]:
                        logs.append({
                            "id": log_id,
                            "timestamp": execution_row["started_at"].isoformat(),
                            "level": "info",
                            "message": f"🚀 开始执行流水线: {execution_row['pipeline_name']}",
                            "step_name": None,
                            "source": "pipeline"
                        })
                        log_id += 1
                    
                    # 添加步骤日志
                    for step_row in step_rows:
                        if step_row["started_at"]:
                            logs.append({
                                "id": log_id,
                                "timestamp": step_row["started_at"].isoformat(),
                                "level": "info",
                                "message": f"⏳ 开始执行步骤: {step_row['step_name'] or ('步骤' + str(step_row['id']))}",
                                "step_name": step_row["step_name"],
                                "source": "step"
                            })
                            log_id += 1
                        
                        # 添加步骤详细日志
                        if step_row["logs"]:
                            log_lines = step_row["logs"].split('\n')
                            for line in log_lines:
                                if line.strip():
                                    logs.append({
                                        "id": log_id,
                                        "timestamp": step_row["started_at"].isoformat() if step_row["started_at"] else datetime.now().isoformat(),
                                        "level": "info",
                                        "message": line,
                                        "step_name": step_row["step_name"],
                                        "source": "step_output"
                                    })
                                    log_id += 1
                        
                        if step_row["completed_at"]:
                            status_emoji = "✅" if step_row["status"] == "success" else "❌" if step_row["status"] == "failed" else "⏹️"
                            logs.append({
                                "id": log_id,
                                "timestamp": step_row["completed_at"].isoformat(),
                                "level": "success" if step_row["status"] == "success" else "error" if step_row["status"] == "failed" else "info",
                                "message": f"{status_emoji} 步骤完成: {step_row['step_name'] or ('步骤' + str(step_row['id']))}",
                                "step_name": step_row["step_name"],
                                "source": "step"
                            })
                            log_id += 1
                    
                    # 添加执行完成日志
                    if execution_row["completed_at"]:
                        status_emoji = "🎉" if execution_row["status"] == "success" else "💥" if execution_row["status"] == "failed" else "⏹️"
                        logs.append({
                            "id": log_id,
                            "timestamp": execution_row["completed_at"].isoformat(),
                            "level": "success" if execution_row["status"] == "success" else "error" if execution_row["status"] == "failed" else "info",
                            "message": f"{status_emoji} 流水线执行完成，状态: {execution_row['status'].upper()}",
                            "step_name": None,
                            "source": "pipeline"
                        })
                    
                    # 返回增量日志（从 last_count 开始）
                    if last_count < len(logs):
                        return logs[last_count:]
                    else:
                        return []
                
        except Exception as e:
            logger.error("Error fetching execution logs from Django DB", 
                        execution_id=execution_id, error=str(e))
            # 出错时返回空列表
            return []
    
    async def _get_mock_execution_data(self, execution_id: int) -> Dict:
        """获取模拟执行数据（当无法连接到真实数据库时使用）"""
        logger.warning("Using mock execution data", execution_id=execution_id)
        
        # 返回静态的模拟数据，不基于时间变化
        return {
            "id": execution_id,
            "status": "completed",  # 固定状态，不会动态变化
            "pipeline_name": f"流水线执行 #{execution_id}",
            "execution_time": 120.5,
            "steps": [
                {
                    "id": 1,
                    "name": "环境检查",
                    "status": "success",
                    "execution_time": 5.2,
                    "output": "✅ 环境检查完成",
                    "error_message": None
                },
                {
                    "id": 2,
                    "name": "代码拉取",
                    "status": "success", 
                    "execution_time": 8.3,
                    "output": "✅ 代码拉取完成",
                    "error_message": None
                },
                {
                    "id": 3,
                    "name": "构建应用",
                    "status": "success",
                    "execution_time": 45.8,
                    "output": "✅ 应用构建完成",
                    "error_message": None
                },
                {
                    "id": 4,
                    "name": "运行测试",
                    "status": "success",
                    "execution_time": 32.1,
                    "output": "✅ 所有测试通过",
                    "error_message": None
                },
                {
                    "id": 5,
                    "name": "部署应用",
                    "status": "success",
                    "execution_time": 29.1,
                    "output": "✅ 部署完成",
                    "error_message": None
                }
            ],
            "created_at": "2025-07-14T10:00:00",
            "started_at": "2025-07-14T10:00:05",
            "finished_at": "2025-07-14T10:02:05"
        }


# 全局数据库服务实例
django_db_service = DjangoDBService()
