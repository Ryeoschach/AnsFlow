#!/bin/bash
# RabbitMQ 初始化脚本

# 等待 RabbitMQ 启动
sleep 10

# 创建虚拟主机
rabbitmqctl add_vhost ansflow_vhost

# 设置用户权限
rabbitmqctl set_permissions -p ansflow_vhost ansflow ".*" ".*" ".*"

# 创建队列
rabbitmqctl eval 'rabbit_amqqueue:declare({resource, <<"ansflow_vhost">>, queue, <<"high_priority">>}, true, false, [], none).'
rabbitmqctl eval 'rabbit_amqqueue:declare({resource, <<"ansflow_vhost">>, queue, <<"medium_priority">>}, true, false, [], none).'
rabbitmqctl eval 'rabbit_amqqueue:declare({resource, <<"ansflow_vhost">>, queue, <<"low_priority">>}, true, false, [], none).'

echo "RabbitMQ 初始化完成"
