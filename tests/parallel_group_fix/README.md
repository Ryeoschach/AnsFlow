# 并行组管理功能测试脚本

## 测试脚本说明

本目录包含了AnsFlow并行组管理功能修复过程中的所有测试脚本。

## 测试脚本列表

### 后端测试
- `test_parallel_group_fix.py` - 并行组修复功能测试
- `test_parallel_group_operations.py` - 并行组操作测试
- `test_pipeline_save_parallel_groups.py` - 流水线保存并行组测试
- `check_parallel_group_issues.py` - 并行组问题检查脚本

### 前端测试
- `test_parallel_group_frontend.html` - 并行组前端测试页面
- `test_parallel_group_serializer.py` - 并行组序列化器测试

### 修复脚本
- `fix_parallel_group_frontend.js` - 并行组前端修复脚本
- `parallel_group_fix.js` - 并行组修复JS脚本

## 运行方法

### 后端测试
```bash
cd backend/django_service
python test_parallel_group_fix.py
python test_parallel_group_operations.py
python test_pipeline_save_parallel_groups.py
python check_parallel_group_issues.py
```

### 前端测试
在浏览器中打开 `test_parallel_group_frontend.html`

## 测试结果

✅ 所有测试均已通过验证
✅ 并行组与步骤关联正常
✅ 数据持久化功能正常
✅ 前后端数据一致性验证通过
