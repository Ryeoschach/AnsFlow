-- AnsFlow 统一日志系统数据库迁移脚本
-- 创建统一日志表和同步位置表

-- 创建统一日志表（如果不存在）
CREATE TABLE IF NOT EXISTS `unified_logs` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `log_id` varchar(255) NOT NULL COMMENT '唯一日志ID',
    `timestamp` datetime(3) NOT NULL COMMENT '日志时间戳',
    `level` varchar(20) NOT NULL COMMENT '日志级别',
    `service` varchar(50) NOT NULL COMMENT '服务名称',
    `component` varchar(100) DEFAULT NULL COMMENT '组件名称',
    `module` varchar(100) DEFAULT NULL COMMENT '模块名称',
    `message` text NOT NULL COMMENT '日志消息',
    `execution_id` int(11) DEFAULT NULL COMMENT '执行ID',
    `trace_id` varchar(100) DEFAULT NULL COMMENT '追踪ID',
    `extra_data` json DEFAULT NULL COMMENT '额外数据',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_log_id` (`log_id`),
    KEY `idx_timestamp` (`timestamp`),
    KEY `idx_service` (`service`),
    KEY `idx_level` (`level`),
    KEY `idx_execution_id` (`execution_id`),
    KEY `idx_trace_id` (`trace_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一日志表';

-- 创建日志同步位置表
CREATE TABLE IF NOT EXISTS `log_sync_position` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `service_name` varchar(100) NOT NULL COMMENT '服务名称',
    `redis_stream_id` varchar(255) NOT NULL COMMENT 'Redis Stream消息ID',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_service_name` (`service_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日志同步位置表';

-- 插入一些测试数据到统一日志表（如果为空）
INSERT IGNORE INTO `unified_logs` (`log_id`, `timestamp`, `level`, `service`, `component`, `module`, `message`, `execution_id`) VALUES
('django-test-1', NOW(), 'INFO', 'django_service', 'auth', 'authentication', '用户登录成功', 1001),
('django-test-2', NOW(), 'ERROR', 'django_service', 'pipeline', 'executor', '管道执行失败', 1002),
('django-test-3', NOW(), 'WARNING', 'django_service', 'project', 'manager', '项目配置警告', 1003),
('system-test-1', NOW(), 'INFO', 'system', 'monitor', 'health', '系统健康检查正常', NULL),
('system-test-2', NOW(), 'DEBUG', 'system', 'scheduler', 'cron', '定时任务执行', NULL),
('fastapi-test-1', NOW(), 'INFO', 'fastapi', 'webhook', 'handler', 'Webhook处理完成', 2001),
('fastapi-test-2', NOW(), 'ERROR', 'fastapi', 'api', 'endpoint', 'API请求失败', 2002),
('fastapi-test-3', NOW(), 'INFO', 'fastapi', 'websocket', 'connection', 'WebSocket连接建立', NULL);

-- 创建视图用于快速查询最近日志
CREATE OR REPLACE VIEW `recent_logs` AS
SELECT 
    log_id,
    timestamp,
    level,
    service,
    component,
    module,
    LEFT(message, 100) as message_preview,
    execution_id,
    trace_id
FROM unified_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;

-- 显示表结构和数据统计
SELECT 'unified_logs表结构' as info;
DESCRIBE unified_logs;

SELECT 'log_sync_position表结构' as info;
DESCRIBE log_sync_position;

SELECT 'unified_logs数据统计' as info;
SELECT 
    COUNT(*) as total_logs,
    COUNT(DISTINCT service) as unique_services,
    MIN(timestamp) as earliest_log,
    MAX(timestamp) as latest_log
FROM unified_logs;

SELECT '按服务分组统计' as info;
SELECT 
    service,
    COUNT(*) as log_count,
    COUNT(DISTINCT level) as unique_levels
FROM unified_logs 
GROUP BY service 
ORDER BY log_count DESC;
