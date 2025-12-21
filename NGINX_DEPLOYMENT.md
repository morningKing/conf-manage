# Nginx 生产环境部署指南

本文档提供脚本管理系统使用 Nginx 反向代理的完整部署方案。

## 目录

- [系统架构](#系统架构)
- [前置要求](#前置要求)
- [Nginx 配置](#nginx-配置)
- [后端服务配置](#后端服务配置)
- [部署步骤](#部署步骤)
- [常见问题](#常见问题)
- [性能优化](#性能优化)

---

## 系统架构

```
┌─────────────┐
│   用户浏览器   │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────────────────────────┐
│            Nginx (端口 80/443)        │
│  ┌────────────────┬─────────────┐   │
│  │  静态文件服务   │  API 反向代理 │   │
│  │  (前端 dist)   │  (/api/*)    │   │
│  └────────────────┴──────┬──────┘   │
└──────────────────────────┼──────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Flask 后端     │
                  │  (端口 5000)    │
                  └────────────────┘
```

**优势：**
- ✅ 生产级性能和稳定性
- ✅ 支持 HTTPS 加密
- ✅ 自动处理静态资源缓存
- ✅ 支持 SSE 实时日志流
- ✅ 支持大文件上传
- ✅ 负载均衡和故障转移

---

## 前置要求

### 系统要求

- **操作系统**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **Nginx**: 1.18+
- **Python**: 3.9+
- **Node.js**: 16+ (仅构建时需要)
- **内存**: 最低 1GB，推荐 2GB+
- **磁盘**: 最低 5GB 可用空间

### 软件安装

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx python3 python3-pip python3-venv
```

**CentOS/RHEL:**
```bash
sudo yum install epel-release
sudo yum install nginx python3 python3-pip
```

---

## Nginx 配置

### 基础 HTTP 配置

创建配置文件 `/etc/nginx/sites-available/script-manager` (Ubuntu) 或 `/etc/nginx/conf.d/script-manager.conf` (CentOS):

```nginx
# 脚本管理系统 Nginx 配置
# 适用于生产环境部署

# 上游后端服务器配置
upstream backend_server {
    server 127.0.0.1:5000;
    # 如果后端在其他服务器，修改为: server 192.168.1.100:5000;
    keepalive 32;
}

# HTTP 服务器配置
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;  # 修改为您的域名或服务器IP

    # 如果使用IP访问，可以使用:
    # server_name 192.168.1.100;
    # 或者使用默认服务器:
    # server_name _;

    # 字符集
    charset utf-8;

    # 访问日志和错误日志
    access_log /var/log/nginx/script-manager-access.log;
    error_log /var/log/nginx/script-manager-error.log;

    # 客户端上传文件大小限制（支持大文件上传）
    client_max_body_size 100M;
    client_body_buffer_size 128k;

    # 前端静态文件根目录
    root /path/to/conf-manage/frontend/dist;  # 修改为实际路径
    index index.html;

    # 启用 gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # API 反向代理
    location /api/ {
        # 代理到后端 Flask 服务
        proxy_pass http://backend_server;

        # 代理头部设置
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式传输支持（关键配置）
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        # 禁用缓冲以支持实时日志流
        chunked_transfer_encoding on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 300s;
    }

    # 静态资源缓存策略
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # SPA 路由支持（所有非文件请求返回 index.html）
    location / {
        try_files $uri $uri/ /index.html;

        # 禁用 index.html 缓存
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### HTTPS 配置（推荐生产环境）

创建或修改配置文件，添加 SSL 支持：

```nginx
# HTTPS 服务器配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 其他配置与 HTTP 相同
    charset utf-8;
    access_log /var/log/nginx/script-manager-ssl-access.log;
    error_log /var/log/nginx/script-manager-ssl-error.log;
    client_max_body_size 100M;

    root /path/to/conf-manage/frontend/dist;
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    location /api/ {
        proxy_pass http://backend_server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        chunked_transfer_encoding on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 300s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # HTTPS 专属安全头部
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}

# HTTP 到 HTTPS 重定向
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 免费 SSL 证书（Let's Encrypt）

使用 Certbot 自动获取和配置 SSL 证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
sudo yum install certbot python3-certbot-nginx  # CentOS

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d your-domain.com

# 自动续期（添加到 crontab）
sudo certbot renew --dry-run
```

---

## 后端服务配置

### Systemd 服务管理（推荐）

创建 systemd 服务文件 `/etc/systemd/system/script-manager-backend.service`:

```ini
[Unit]
Description=Script Manager Backend Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/conf-manage
Environment="PATH=/path/to/conf-manage/venv/bin"
Environment="PYTHONPATH=/path/to/conf-manage/backend"
ExecStart=/path/to/conf-manage/venv/bin/python3 /path/to/conf-manage/backend/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全增强
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

**管理服务：**

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start script-manager-backend

# 设置开机自启
sudo systemctl enable script-manager-backend

# 查看状态
sudo systemctl status script-manager-backend

# 查看日志
sudo journalctl -u script-manager-backend -f

# 重启服务
sudo systemctl restart script-manager-backend

# 停止服务
sudo systemctl stop script-manager-backend
```

### 使用 Gunicorn（生产级 WSGI 服务器）

安装 Gunicorn:

```bash
cd /path/to/conf-manage
source venv/bin/activate
pip install gunicorn
```

修改 systemd 服务文件，使用 Gunicorn:

```ini
[Service]
ExecStart=/path/to/conf-manage/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    --access-logfile /var/log/script-manager/access.log \
    --error-logfile /var/log/script-manager/error.log \
    app:app
```

创建日志目录：

```bash
sudo mkdir -p /var/log/script-manager
sudo chown www-data:www-data /var/log/script-manager
```

---

## 部署步骤

### 1. 准备项目文件

```bash
# 克隆或上传项目到服务器
cd /opt
sudo git clone https://github.com/your-repo/conf-manage.git
cd conf-manage

# 或者从本地上传
scp -r /path/to/conf-manage user@server:/opt/
```

### 2. 构建前端

```bash
cd /opt/conf-manage/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建完成后，dist 目录包含所有静态文件
ls -la dist/
```

### 3. 配置后端

```bash
cd /opt/conf-manage

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
cd backend
python3 -c "from app import db; db.create_all()"
```

### 4. 配置 Nginx

```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/script-manager

# 粘贴上面的 Nginx 配置，并修改以下内容：
# - server_name: 改为您的域名或IP
# - root: 改为 /opt/conf-manage/frontend/dist
# - upstream backend_server: 确保指向正确的后端地址

# 创建软链接 (Ubuntu/Debian)
sudo ln -s /etc/nginx/sites-available/script-manager /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 如果测试通过，输出：
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 5. 配置后端服务

```bash
# 创建 systemd 服务文件
sudo nano /etc/systemd/system/script-manager-backend.service

# 粘贴上面的 systemd 配置，修改路径为实际路径

# 修改权限
sudo chown -R www-data:www-data /opt/conf-manage
sudo chmod -R 755 /opt/conf-manage

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start script-manager-backend
sudo systemctl enable script-manager-backend

# 检查状态
sudo systemctl status script-manager-backend
```

### 6. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

### 7. 启动 Nginx

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

### 8. 验证部署

```bash
# 测试后端健康检查
curl http://localhost:5000/health

# 测试 Nginx
curl http://localhost

# 从外部访问
# 浏览器打开: http://your-server-ip
```

---

## 常见问题

### 1. 502 Bad Gateway

**原因**: 后端服务未运行或连接失败

**排查步骤**:
```bash
# 检查后端服务状态
sudo systemctl status script-manager-backend

# 检查后端是否监听 5000 端口
sudo netstat -tlnp | grep 5000

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/script-manager-error.log

# 查看后端日志
sudo journalctl -u script-manager-backend -f
```

**解决方案**:
```bash
# 重启后端服务
sudo systemctl restart script-manager-backend

# 如果端口被占用，杀掉进程
sudo lsof -ti:5000 | xargs kill -9
```

### 2. 404 Not Found（刷新页面后）

**原因**: SPA 路由配置问题

**解决方案**: 确保 Nginx 配置包含：
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 3. SSE 流式日志不工作

**原因**: Nginx 缓冲配置

**解决方案**: 确保 API location 配置包含：
```nginx
proxy_buffering off;
proxy_cache off;
chunked_transfer_encoding on;
```

### 4. 文件上传失败（413 Request Entity Too Large）

**原因**: 文件大小超过限制

**解决方案**: 修改 Nginx 配置：
```nginx
client_max_body_size 100M;  # 根据需要调整大小
```

然后重启 Nginx:
```bash
sudo systemctl restart nginx
```

### 5. 权限错误

**原因**: Nginx 用户没有权限访问文件

**解决方案**:
```bash
# 修改所有者
sudo chown -R www-data:www-data /opt/conf-manage

# 修改权限
sudo chmod -R 755 /opt/conf-manage/frontend/dist
sudo chmod -R 755 /opt/conf-manage/backend
```

### 6. CORS 错误

**原因**: 跨域配置问题

**解决方案**: 后端 Flask 应用已配置 CORS，确保前端使用相对路径 `/api`

### 7. SSL 证书问题

**查看证书信息**:
```bash
sudo certbot certificates
```

**手动续期**:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 性能优化

### 1. Nginx 性能调优

编辑 `/etc/nginx/nginx.conf`:

```nginx
# 工作进程数（通常设置为 CPU 核心数）
worker_processes auto;

# 每个进程的最大连接数
events {
    worker_connections 2048;
    use epoll;
}

http {
    # 启用 sendfile
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # 保持连接超时
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # 启用 gzip 压缩
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript;

    # 客户端缓冲区大小
    client_body_buffer_size 128k;
    client_max_body_size 100M;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;

    # 其他配置...
}
```

### 2. 后端性能调优

**使用 Gunicorn 多进程**:

```bash
# 工作进程数 = (2 × CPU核心数) + 1
gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
```

**启用日志轮转**:

创建 `/etc/logrotate.d/script-manager`:
```
/var/log/script-manager/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload script-manager-backend > /dev/null 2>&1 || true
    endscript
}
```

### 3. 数据库优化

**SQLite 优化** (backend/config.py):
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/database.db?check_same_thread=False'
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}
```

**定期清理执行历史**:
```bash
# 添加到 crontab
0 2 * * * /opt/conf-manage/venv/bin/python3 /opt/conf-manage/backend/cleanup_old_executions.py
```

### 4. 监控和日志

**安装监控工具**:
```bash
# Nginx 状态监控
sudo apt install nginx-extras  # 启用 stub_status

# 系统监控
sudo apt install htop iotop
```

**Nginx 状态页面配置**:
```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

**查看实时日志**:
```bash
# Nginx 访问日志
sudo tail -f /var/log/nginx/script-manager-access.log

# 后端服务日志
sudo journalctl -u script-manager-backend -f

# 系统资源使用
htop
```

---

## 安全建议

### 1. 限制访问 IP

```nginx
# 只允许特定 IP 访问
location / {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
}
```

### 2. 启用基础认证

```bash
# 安装工具
sudo apt install apache2-utils

# 创建密码文件
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 在 Nginx 配置中添加
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### 3. 禁用不必要的 HTTP 方法

```nginx
# 只允许 GET, POST, PUT, DELETE
if ($request_method !~ ^(GET|POST|PUT|DELETE)$ ) {
    return 405;
}
```

### 4. 防止 DDoS 攻击

```nginx
# 限制请求速率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

### 5. 定期更新

```bash
# 更新系统和软件包
sudo apt update && sudo apt upgrade

# 更新 SSL 证书
sudo certbot renew
```

---

## 备份策略

### 1. 备份数据库

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backup/script-manager"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/conf-manage/backend/data/database.db \
   $BACKUP_DIR/database_$DATE.db

# 保留最近 7 天的备份
find $BACKUP_DIR -name "database_*.db" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/database_$DATE.db"
```

添加到 crontab:
```bash
0 3 * * * /opt/scripts/backup-database.sh
```

### 2. 备份上传文件

```bash
#!/bin/bash
# backup-uploads.sh

BACKUP_DIR="/backup/script-manager"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz \
    /opt/conf-manage/backend/data/uploads

# 保留最近 30 天的备份
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete
```

---

## 总结

完成以上配置后，您的脚本管理系统将以生产级别运行：

- ✅ Nginx 提供高性能静态文件服务和 API 反向代理
- ✅ Systemd 管理后端服务，自动重启和日志记录
- ✅ SSL/TLS 加密保护数据传输安全
- ✅ 防火墙保护服务器安全
- ✅ 日志轮转防止磁盘空间耗尽
- ✅ 定期备份数据防止丢失

如遇问题，请查看日志文件或提交 Issue。
