"""
依赖关系解析器
负责分析步骤间的依赖关系，生成执行计划，支持并行执行
"""
import asyncio
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class StepNode:
    """步骤节点"""
    step_id: int
    step_name: str
    step_type: str
    dependencies: List[int]
    conditions: Dict[str, any]
    parallel_group: Optional[str] = None
    priority: int = 0

class DependencyResolver:
    """依赖关系解析器"""
    
    def __init__(self):
        self.steps: Dict[int, StepNode] = {}
        self.dependency_graph: Dict[int, List[int]] = defaultdict(list)
        self.reverse_graph: Dict[int, List[int]] = defaultdict(list)
    
    def add_step(self, step_node: StepNode) -> None:
        """添加步骤节点"""
        self.steps[step_node.step_id] = step_node
        
        # 构建依赖图
        for dep_id in step_node.dependencies:
            self.dependency_graph[dep_id].append(step_node.step_id)
            self.reverse_graph[step_node.step_id].append(dep_id)
    
    def validate_dependencies(self) -> List[str]:
        """验证依赖关系，检查循环依赖"""
        errors = []
        
        # 检查步骤是否存在
        for step_id, step_node in self.steps.items():
            for dep_id in step_node.dependencies:
                if dep_id not in self.steps:
                    errors.append(f"步骤 {step_node.step_name} 依赖的步骤 ID {dep_id} 不存在")
        
        # 检查循环依赖
        if self._has_cycle():
            errors.append("检测到循环依赖关系")
        
        return errors
    
    def _has_cycle(self) -> bool:
        """检查是否存在循环依赖（使用DFS）"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step_id in self.steps:
            if step_id not in visited:
                if dfs(step_id):
                    return True
        
        return False
    
    def get_execution_plan(self) -> List[List[int]]:
        """
        生成执行计划，返回批次列表
        每个批次内的步骤可以并行执行
        """
        # 拓扑排序生成执行层级
        in_degree = defaultdict(int)
        
        # 计算每个节点的入度
        for step_id in self.steps:
            in_degree[step_id] = len(self.reverse_graph.get(step_id, []))
        
        # 执行计划：每个子列表代表一个可以并行执行的批次
        execution_plan = []
        queue = deque()
        
        # 找到入度为0的节点（没有依赖的步骤）
        for step_id, degree in in_degree.items():
            if degree == 0:
                queue.append(step_id)
        
        while queue:
            # 当前批次
            current_batch = []
            next_queue = deque()
            
            # 处理当前层级的所有节点
            while queue:
                step_id = queue.popleft()
                current_batch.append(step_id)
                
                # 更新依赖此步骤的节点
                for dependent_id in self.dependency_graph.get(step_id, []):
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        next_queue.append(dependent_id)
            
            if current_batch:
                # 按优先级和并行组排序当前批次
                current_batch.sort(key=lambda x: (
                    self.steps[x].priority,
                    self.steps[x].step_name
                ))
                execution_plan.append(current_batch)
            
            queue = next_queue
        
        return execution_plan
    
    def get_parallel_groups(self, step_ids: List[int]) -> Dict[str, List[int]]:
        """
        将步骤按并行组分组
        返回 {group_name: [step_ids]} 的映射
        """
        groups = defaultdict(list)
        ungrouped = []
        
        for step_id in step_ids:
            step = self.steps[step_id]
            if step.parallel_group:
                groups[step.parallel_group].append(step_id)
            else:
                ungrouped.append(step_id)
        
        # 未分组的步骤每个都是独立的组
        for i, step_id in enumerate(ungrouped):
            groups[f"_ungrouped_{i}"].append(step_id)
        
        return dict(groups)
    
    def can_execute_step(self, step_id: int, completed_steps: Set[int]) -> bool:
        """检查步骤是否可以执行（所有依赖都已完成）"""
        step = self.steps.get(step_id)
        if not step:
            return False
        
        # 检查所有依赖是否已完成
        for dep_id in step.dependencies:
            if dep_id not in completed_steps:
                return False
        
        return True
    
    def get_ready_steps(self, completed_steps: Set[int], running_steps: Set[int]) -> List[int]:
        """获取可以开始执行的步骤"""
        ready_steps = []
        
        for step_id, step in self.steps.items():
            # 跳过已完成或正在运行的步骤
            if step_id in completed_steps or step_id in running_steps:
                continue
            
            # 检查是否可以执行
            if self.can_execute_step(step_id, completed_steps):
                ready_steps.append(step_id)
        
        # 按优先级排序
        ready_steps.sort(key=lambda x: (
            self.steps[x].priority,
            self.steps[x].step_name
        ))
        
        return ready_steps
    
    def get_step_dependencies(self, step_id: int) -> List[int]:
        """获取步骤的直接依赖"""
        step = self.steps.get(step_id)
        return step.dependencies if step else []
    
    def get_step_dependents(self, step_id: int) -> List[int]:
        """获取依赖此步骤的其他步骤"""
        return self.dependency_graph.get(step_id, [])
    
    def get_critical_path(self) -> List[int]:
        """
        计算关键路径（最长路径）
        用于估算流水线最短完成时间
        """
        # 拓扑排序的同时计算最长路径
        in_degree = defaultdict(int)
        distance = defaultdict(int)
        
        for step_id in self.steps:
            in_degree[step_id] = len(self.reverse_graph.get(step_id, []))
        
        queue = deque()
        for step_id, degree in in_degree.items():
            if degree == 0:
                queue.append(step_id)
                distance[step_id] = 1
        
        topo_order = []
        
        while queue:
            step_id = queue.popleft()
            topo_order.append(step_id)
            
            for dependent_id in self.dependency_graph.get(step_id, []):
                distance[dependent_id] = max(
                    distance[dependent_id],
                    distance[step_id] + 1
                )
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # 找到距离最大的节点，反向追踪路径
        max_distance = max(distance.values()) if distance else 0
        end_nodes = [k for k, v in distance.items() if v == max_distance]
        
        if not end_nodes:
            return []
        
        # 从其中一个终点反向追踪关键路径
        path = []
        current = end_nodes[0]
        
        while current is not None:
            path.append(current)
            # 找到能到达当前节点的最长路径的前驱
            next_node = None
            max_prev_distance = -1
            
            for prev_id in self.reverse_graph.get(current, []):
                if distance[prev_id] > max_prev_distance:
                    max_prev_distance = distance[prev_id]
                    next_node = prev_id
            
            current = next_node
        
        path.reverse()
        return path
    
    def estimate_execution_time(self, step_durations: Dict[int, int]) -> int:
        """
        估算流水线执行时间
        step_durations: {step_id: duration_seconds}
        """
        execution_plan = self.get_execution_plan()
        total_time = 0
        
        for batch in execution_plan:
            # 每个批次的时间是其中最长步骤的时间
            batch_time = max(
                step_durations.get(step_id, 0) 
                for step_id in batch
            ) if batch else 0
            total_time += batch_time
        
        return total_time
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典，便于序列化"""
        return {
            'steps': {
                step_id: {
                    'step_name': step.step_name,
                    'step_type': step.step_type,
                    'dependencies': step.dependencies,
                    'conditions': step.conditions,
                    'parallel_group': step.parallel_group,
                    'priority': step.priority
                }
                for step_id, step in self.steps.items()
            },
            'execution_plan': self.get_execution_plan(),
            'critical_path': self.get_critical_path()
        }
