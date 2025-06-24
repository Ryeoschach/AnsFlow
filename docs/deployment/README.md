# 🚀 AnsFlow 部署指南

## 📋 目录
- [部署方式概览](#部署方式概览)
- [Docker 部署](#docker-部署)
- [Kubernetes 部署](#kubernetes-部署)
- [生产环境配置](#生产环境配置)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)

## 🎯 部署方式概览

AnsFlow 支持多种部署方式：

| 部署方式 | 适用场景 | 复杂度 | 推荐度 |
|----------|----------|--------|--------|
| Docker Compose | 开发环境、小型团队 | ⭐ | ⭐⭐⭐⭐⭐ |
| Kubernetes | 生产环境、大规模部署 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 云服务 | 快速上线、托管服务 | ⭐⭐ | ⭐⭐⭐⭐ |
| 手动部署 | 特殊需求、完全控制 | ⭐⭐⭐⭐ | ⭐⭐ |

## 🐳 Docker 部署

### 开发环境部署

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ansflow.git
cd ansflow

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件中的配置

# 3. 启动服务
docker-compose up -d

# 4. 初始化数据库
make db-init

# 5. 创建超级用户
make superuser
```

### 生产环境部署

#### 1. 生产环境配置文件

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: ansflow_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
      - media_files:/var/www/media
    depends_on:
      - django_service
      - frontend
    networks:
      - ansflow_network

  # Django 生产服务
  django_service:
    build:
      context: ./backend/django_service
      dockerfile: Dockerfile.prod
    container_name: ansflow_django_prod
    restart: unless-stopped
    environment:
      - DEBUG=False
      - DATABASE_URL=mysql://ansflow_user:${DB_PASSWORD}@mysql:3306/ansflow_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${DJANGO_SECRET_KEY}
    volumes:
      - static_files:/app/static
      - media_files:/app/media
    depends_on:
      - mysql
      - redis
    networks:
      - ansflow_network
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

  # React 生产构建
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: ansflow_frontend_prod
    restart: unless-stopped
    volumes:
      - frontend_build:/app/build
    networks:
      - ansflow_network

  # 其他服务配置...

volumes:
  static_files:
  frontend_build:
  # 其他卷...
```

#### 2. 生产环境启动

```bash
# 1. 设置生产环境变量
cp .env.example .env.prod
# 编辑生产环境配置

# 2. 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 3. 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 4. 收集静态文件
docker-compose -f docker-compose.prod.yml exec django_service python manage.py collectstatic --noinput

# 5. 数据库迁移
docker-compose -f docker-compose.prod.yml exec django_service python manage.py migrate
```

### Nginx 配置

创建 `deployment/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream django {
        server django_service:8000;
    }
    
    upstream fastapi {
        server fastapi_service:8001;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # 静态文件
        location /static/ {
            alias /var/www/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /var/www/media/;
            expires 7d;
        }

        # Django API
        location /api/ {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # FastAPI 接口
        location /fastapi/ {
            proxy_pass http://fastapi/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket 支持
        location /ws/ {
            proxy_pass http://fastapi;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # 前端应用
        location / {
            try_files $uri $uri/ /index.html;
            root /var/www/frontend;
            expires 1h;
        }
    }
}
```

## ☸️ Kubernetes 部署

### 1. 命名空间

```yaml
# deployment/kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ansflow
```

### 2. ConfigMap 配置

```yaml
# deployment/kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ansflow-config
  namespace: ansflow
data:
  DJANGO_DEBUG: "False"
  DB_HOST: "mysql-service"
  REDIS_HOST: "redis-service"
  RABBITMQ_HOST: "rabbitmq-service"
```

### 3. Secret 配置

```yaml
# deployment/kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ansflow-secrets
  namespace: ansflow
type: Opaque
stringData:
  DJANGO_SECRET_KEY: "your-super-secret-key"
  DB_PASSWORD: "your-db-password"
  JWT_SECRET_KEY: "your-jwt-secret"
```

### 4. MySQL 部署

```yaml
# deployment/kubernetes/mysql.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  namespace: ansflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "root_password"
        - name: MYSQL_DATABASE
          value: "ansflow_db"
        - name: MYSQL_USER
          value: "ansflow_user"
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ansflow-secrets
              key: DB_PASSWORD
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        persistentVolumeClaim:
          claimName: mysql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: ansflow
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: ansflow
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 5. Django 服务部署

```yaml
# deployment/kubernetes/django.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-service
  namespace: ansflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: django-service
  template:
    metadata:
      labels:
        app: django-service
    spec:
      containers:
      - name: django
        image: ansflow/django:latest
        env:
        - name: DEBUG
          valueFrom:
            configMapKeyRef:
              name: ansflow-config
              key: DJANGO_DEBUG
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ansflow-secrets
              key: DJANGO_SECRET_KEY
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: django-service
  namespace: ansflow
spec:
  selector:
    app: django-service
  ports:
  - port: 8000
    targetPort: 8000
```

### 6. Ingress 配置

```yaml
# deployment/kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ansflow-ingress
  namespace: ansflow
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - ansflow.yourdomain.com
    secretName: ansflow-tls
  rules:
  - host: ansflow.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: django-service
            port:
              number: 8000
      - path: /fastapi
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 8001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### 部署到 Kubernetes

```bash
# 1. 应用所有配置
kubectl apply -f deployment/kubernetes/

# 2. 等待 Pod 就绪
kubectl get pods -n ansflow -w

# 3. 检查服务状态
kubectl get services -n ansflow

# 4. 查看日志
kubectl logs -n ansflow deployment/django-service

# 5. 执行数据库迁移
kubectl exec -n ansflow deployment/django-service -- python manage.py migrate
```

## ⚙️ 生产环境配置

### 环境变量配置

生产环境需要配置以下关键环境变量：

```bash
# Django 配置
DJANGO_SECRET_KEY=your-super-secret-key-minimum-50-characters-long
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库配置
DATABASE_URL=mysql://user:password@host:port/database

# Redis 配置
REDIS_URL=redis://host:port/0

# 安全配置
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True

# 邮件配置
EMAIL_HOST=smtp.yourmailprovider.com
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 性能优化

#### 1. Django 优化

```python
# settings/production.py

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 会话配置
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# 数据库连接池
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'sql_mode': 'traditional',
            'charset': 'utf8mb4',
            'init_command': 'SET default_storage_engine=INNODB',
        },
        'CONN_MAX_AGE': 60,
    }
}
```

#### 2. Gunicorn 配置

```python
# deployment/gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
preload_app = True
```

#### 3. FastAPI 优化

```python
# backend/fastapi_service/main.py
import uvicorn
from fastapi import FastAPI

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
```

## 📊 监控和日志

### 1. Prometheus 监控

配置 Prometheus 采集指标：

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django-service'
    static_configs:
      - targets: ['django-service:8000']
    metrics_path: '/metrics'
    
  - job_name: 'fastapi-service'
    static_configs:
      - targets: ['fastapi-service:8001']
    metrics_path: '/metrics'
```

### 2. Grafana 仪表盘

导入预配置的仪表盘：

```json
{
  "dashboard": {
    "title": "AnsFlow Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### 3. 日志聚合

使用 ELK Stack 进行日志聚合：

```yaml
# deployment/logging/elasticsearch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
spec:
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
        env:
        - name: discovery.type
          value: single-node
        - name: ES_JAVA_OPTS
          value: "-Xms512m -Xmx512m"
```

## 💾 备份和恢复

### 数据库备份

```bash
# 创建备份脚本
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 备份 MySQL
docker-compose exec mysql mysqldump -u ansflow_user -p ansflow_db > \
  ${BACKUP_DIR}/mysql_backup_${TIMESTAMP}.sql

# 备份 Redis
docker-compose exec redis redis-cli SAVE
docker cp ansflow_redis:/data/dump.rdb ${BACKUP_DIR}/redis_backup_${TIMESTAMP}.rdb

# 上传到云存储
aws s3 cp ${BACKUP_DIR}/ s3://your-backup-bucket/ --recursive
```

### 自动备份

```yaml
# deployment/kubernetes/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: ansflow
spec:
  schedule: "0 2 * * *"  # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: ansflow/backup:latest
            command:
            - /bin/bash
            - -c
            - |
              mysqldump -h mysql-service -u ansflow_user -p$DB_PASSWORD ansflow_db > /backup/mysql_$(date +%Y%m%d).sql
              aws s3 cp /backup/ s3://your-backup-bucket/ --recursive
            env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: ansflow-secrets
                  key: DB_PASSWORD
          restartPolicy: OnFailure
```

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看容器日志
docker-compose logs django_service

# 检查容器状态
docker-compose ps

# 重启服务
docker-compose restart django_service
```

#### 2. 数据库连接问题

```bash
# 检查数据库状态
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"

# 检查网络连接
docker-compose exec django_service ping mysql

# 重置数据库连接
docker-compose restart mysql
docker-compose restart django_service
```

#### 3. 性能问题

```bash
# 查看资源使用
docker stats

# 查看慢查询
docker-compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# 检查 Redis 状态
docker-compose exec redis redis-cli INFO
```

### 健康检查

```bash
# 服务健康检查脚本
#!/bin/bash

echo "检查 AnsFlow 服务状态..."

# 检查 Django 服务
if curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "✅ Django 服务正常"
else
    echo "❌ Django 服务异常"
fi

# 检查 FastAPI 服务
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ FastAPI 服务正常"
else
    echo "❌ FastAPI 服务异常"
fi

# 检查前端服务
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi
```

---

📚 **相关文档**:
- [开发指南](../development/README.md)
- [API 文档](../api/README.md)
- [项目架构](../../项目说明/技术架构分析报告.md)
