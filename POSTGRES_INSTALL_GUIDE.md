# PostgreSQL 安装和迁移指南

## 当前状态检查

✅ **已具备条件:**
- psycopg2 Python包已安装（可以连接PostgreSQL）
- Docker已安装（但Docker Desktop未运行）
- 迁移脚本已修复

❌ **缺少条件:**
- PostgreSQL服务未运行
- 端口5432未监听
- confmanage数据库不存在

## 安装PostgreSQL的选项

### 选项1: 使用Docker（推荐，最快）

**步骤1: 启动Docker Desktop**
```bash
# 在Windows中启动Docker Desktop应用
# 或从命令行启动（如果可用）
```

**步骤2: 运行PostgreSQL容器**
```bash
docker run --name postgres-confmanage \
  -e POSTGRES_PASSWORD=jay123 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=confmanage \
  -p 5432:5432 \
  -d postgres:15-alpine
```

**步骤3: 等待PostgreSQL启动**
```bash
# 等待10秒
sleep 10

# 检查容器状态
docker ps | grep postgres-confmanage

# 检查PostgreSQL就绪
docker exec postgres-confmanage pg_isready -U postgres
```

**步骤4: 执行迁移**
```bash
# 设置环境变量
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=jay123
export DB_NAME=confmanage

# 执行迁移脚本
python backend/migrate_to_postgres_fixed.py
```

### 选项2: 安装PostgreSQL Windows版本

**步骤1: 下载PostgreSQL**
- 访问: https://www.postgresql.org/download/windows/
- 下载PostgreSQL 15或16版本
- 运行安装程序

**步骤2: 安装时配置**
- 设置超级用户密码为: `jay123`
- 端口: `5432`
- 安装pgAdmin 4（可选）

**步骤3: 启动PostgreSQL服务**
```bash
# PostgreSQL服务会自动启动
# 或手动启动：
net start postgresql-x64-15
```

**步骤4: 创建数据库**
```bash
# 使用psql或pgAdmin创建数据库
psql -U postgres -c "CREATE DATABASE confmanage;"
```

**步骤5: 执行迁移**
```bash
# 设置环境变量并执行迁移
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=jay123
export DB_NAME=confmanage

python backend/migrate_to_postgres_fixed.py
```

### 选项3: 使用云数据库服务（适合远程部署）

**支持的云服务:**
- AWS RDS for PostgreSQL
- Azure Database for PostgreSQL
- Google Cloud SQL for PostgreSQL
- 阿里云RDS PostgreSQL
- 腾讯云PostgreSQL

**步骤:**
1. 在云平台创建PostgreSQL实例
2. 配置连接信息：
   - DB_HOST: 云实例地址
   - DB_PORT: 通常5432
   - DB_USER: 设置的用户名
   - DB_PASSWORD: jay123或云实例密码
   - DB_NAME: confmanage
3. 执行迁移脚本

## 快速执行命令（假设使用Docker）

### 一键安装和迁移脚本

创建并运行以下脚本：

```bash
#!/bin/bash
# install_and_migrate.sh

echo "=== PostgreSQL安装和迁移 ==="

# 1. 检查Docker Desktop是否运行
echo "检查Docker Desktop状态..."
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker Desktop未运行"
    echo "请先启动Docker Desktop应用"
    exit 1
fi

# 2. 启动PostgreSQL容器
echo "启动PostgreSQL容器..."
docker run --name postgres-confmanage \
  -e POSTGRES_PASSWORD=jay123 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=confmanage \
  -p 5432:5432 \
  -d postgres:15-alpine

# 3. 等待启动
echo "等待PostgreSQL启动..."
sleep 10

# 4. 检查状态
echo "检查PostgreSQL状态..."
docker exec postgres-confmanage pg_isready -U postgres

if [ $? -ne 0 ]; then
    echo "错误: PostgreSQL未就绪"
    exit 1
fi

echo "✓ PostgreSQL已就绪"

# 5. 设置环境变量
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=jay123
export DB_NAME=confmanage

# 6. 执行迁移
echo "执行数据库迁移..."
python backend/migrate_to_postgres_fixed.py

echo "=== 完成 ==="
```

## 验证迁移结果

### 连接PostgreSQL测试

```bash
# 使用psql（如果已安装）
psql -U postgres -h localhost -d confmanage -c "\dt"

# 或使用Python
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='jay123',
    database='confmanage'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM folders')
print('Folders count:', cur.fetchone()[0])
conn.close()
"
```

### 检查迁移数据

```sql
-- 检查各表数据量
SELECT
    'folders' as table_name, COUNT(*) as count FROM folders
UNION ALL SELECT 'scripts', COUNT(*) FROM scripts
UNION ALL SELECT 'executions', COUNT(*) FROM executions
UNION ALL SELECT 'workflows', COUNT(*) FROM workflows;

-- 检查外键关系
SELECT s.id, s.name, f.name as folder_name
FROM scripts s
LEFT JOIN folders f ON s.folder_id = f.id
LIMIT 5;
```

## 常见问题处理

### 问题1: Docker Desktop未启动

**解决方案:**
- 打开Windows开始菜单
- 搜索"Docker Desktop"
- 点击启动
- 等待Docker图标变为绿色（表示就绪）

### 问题2: 端口5432被占用

**检查端口占用:**
```bash
netstat -ano | findstr :5432
```

**解决方案:**
- 如果其他PostgreSQL占用，停止该服务
- 或使用其他端口（如5433），并更新DB_PORT配置

### 问题3: 迁移脚本失败

**检查日志:**
```bash
python backend/migrate_to_postgres_fixed.py --skip-verify
# 查看详细错误信息
```

**常见错误:**
1. 连接失败 → 检查PostgreSQL是否运行
2. 权限错误 → 检查密码是否正确
3. 数据库不存在 → 手动创建数据库

### 问题4: 先修复SQLite内部迁移

**如果SQLite还有category→folder未完成迁移:**
```bash
# 先修复SQLite内部迁移
python backend/migrations/migrate_categories_to_folders.py migrate

# 验证SQLite状态
python test_db_migration.py

# 再迁移到PostgreSQL
python backend/migrate_to_postgres_fixed.py
```

## 推荐执行流程

### 最快方案（使用Docker）

```bash
# 1. 启动Docker Desktop（手动）
# 2. 执行以下命令
docker run --name postgres-confmanage -e POSTGRES_PASSWORD=jay123 -e POSTGRES_USER=postgres -e POSTGRES_DB=confmanage -p 5432:5432 -d postgres:15-alpine
sleep 10
export DB_TYPE=postgres DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=jay123 DB_NAME=confmanage
python backend/migrate_to_postgres_fixed.py
```

### 生产环境方案（安装PostgreSQL）

```bash
# 1. 下载并安装PostgreSQL Windows版本
# 2. 配置密码为jay123
# 3. 启动服务
# 4. 执行迁移
export DB_TYPE=postgres DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=jay123 DB_NAME=confmanage
python backend/migrate_to_postgres_fixed.py
```

## 环境变量配置

**临时设置（当前会话）:**
```bash
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=jay123
export DB_NAME=confmanage
```

**永久设置（添加到.bashrc或config）:**
```bash
# 编辑 backend/config.py
DB_TYPE = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'postgres'
DB_PASSWORD = 'jay123'
DB_NAME = 'confmanage'
```

## 下一步

请选择一个安装方式：
1. **Docker** - 最快，适合开发测试
2. **Windows安装** - 稳定，适合生产环境
3. **云数据库** - 适合远程部署

然后执行对应的迁移脚本。