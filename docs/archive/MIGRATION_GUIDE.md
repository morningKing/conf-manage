# 项目运行时数据迁移脚本使用指南

## 功能概述

`migrate_runtime_data.py` 是一个用于将项目的运行时数据从一个项目目录迁移到另一个项目目录的脚本。

**可迁移的数据类型**:
- 📋 **日志文件** (`logs/`) - 脚本执行的日志
- 📁 **执行空间** (`execution_spaces/`) - 脚本执行的工作目录和产生的临时文件
- 📊 **数据库** (`data/database.db`) - SQLite 数据库文件
- 📤 **上传文件** (`data/uploads/`) - 用户上传的文件
- 🔄 **工作流执行空间** (`workflow_execution_spaces/`) - 工作流执行的工作目录

## 安装要求

```bash
# Python 3.6+ 内置库，无需额外依赖
python3 migrate_runtime_data.py --help
```

## 使用方法

### 基本语法

```bash
python migrate_runtime_data.py --source <源项目路径> --target <目标项目路径> [选项]
```

### 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--source` | ✅ | 源项目目录路径（包含运行时数据的项目）|
| `--target` | ✅ | 目标项目目录路径（新项目）|
| `--skip-db` | ❌ | 跳过数据库迁移 |
| `--skip-logs` | ❌ | 跳过日志文件迁移 |
| `--skip-spaces` | ❌ | 跳过执行空间迁移 |
| `--dry-run` | ❌ | 模拟迁移，不实际复制文件 |

## 使用示例

### 1. 完整迁移（所有数据）

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project
```

**迁移内容**:
- ✅ 日志文件
- ✅ 执行空间
- ✅ 上传文件
- ✅ 工作流执行空间
- ✅ 数据库

### 2. 跳过数据库迁移

当目标项目已有新的数据库配置时使用：

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project \
  --skip-db
```

**使用场景**:
- 目标项目是新安装，有新的初始数据库
- 想保留目标项目的现有配置和定时任务

### 3. 只迁移日志和执行空间

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project \
  --skip-db
```

### 4. 模拟迁移（检查会迁移什么）

在真正执行迁移前，先用 `--dry-run` 看看会迁移什么：

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project \
  --dry-run
```

**输出示例**:
```
[模拟] 复制日志: execution_1.log (124.56KB)
[模拟] 复制日志: execution_2.log (89.34KB)
[模拟] 复制执行空间: execution_1 (2.34MB)
[模拟] 复制执行空间: execution_2 (1.56MB)
```

### 5. 只迁移日志

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project \
  --skip-spaces --skip-db
```

### 6. 只迁移执行空间

```bash
python migrate_runtime_data.py \
  --source /home/user/old_project \
  --target /home/user/new_project \
  --skip-logs --skip-db
```

## 工作流程

### 执行步骤

1. **验证路径**
   - 检查源目录是否存在
   - 检查源目录是否是有效的项目（包含 `backend/` 目录）
   - 检查目标目录是否存在
   - 检查目标目录是否是有效的项目

2. **迁移日志文件**
   - 遍历 `源项目/logs/` 目录
   - 将所有 `.log` 文件复制到 `目标项目/logs/`
   - 统计迁移的文件数和总大小

3. **迁移执行空间**
   - 遍历 `源项目/execution_spaces/` 目录
   - 将每个执行空间目录复制到目标项目
   - 保留原始目录结构和文件权限

4. **迁移上传文件**
   - 复制 `源项目/data/uploads/` 目录中的所有文件
   - 保持目录结构不变

5. **迁移工作流执行空间**
   - 复制 `源项目/workflow_execution_spaces/` 目录
   - 保持目录结构不变

6. **迁移数据库**
   - 如果目标项目已有数据库，创建备份（`database.db.backup.YYYYMMDD_HHMMSS`）
   - 复制源项目的 `data/database.db` 到目标项目

7. **生成报告**
   - 生成 `migration_report_YYYYMMDD_HHMMSS.json` 文件
   - 记录迁移统计和任何错误信息

### 输出示例

```
============================================================
开始项目运行时数据迁移
============================================================
源项目: /home/user/old_project
目标项目: /home/user/new_project
============================================================
[2025-12-26 15:30:45] [INFO] 验证目录路径...
[2025-12-26 15:30:45] [SUCCESS] ✓ 目录验证成功
[2025-12-26 15:30:45] [INFO] 开始迁移日志文件...
[2025-12-26 15:30:45] [INFO] 找到 10 个日志文件
[2025-12-26 15:30:45] [INFO]   ✓ 复制日志: execution_1.log (124.56KB)
[2025-12-26 15:30:45] [INFO]   ✓ 复制日志: execution_2.log (89.34KB)
...
[2025-12-26 15:30:50] [SUCCESS] ✓ 日志迁移完成，共迁移 10 个文件
[2025-12-26 15:30:50] [INFO] 开始迁移执行空间...
[2025-12-26 15:30:50] [INFO] 找到 7 个执行空间目录
[2025-12-26 15:30:51] [INFO]   ✓ 复制执行空间: execution_1 (2.34MB)
...
[2025-12-26 15:31:20] [SUCCESS] ✓ 执行空间迁移完成，共迁移 7 个目录
...
============================================================
迁移总结
============================================================
日志文件: 10 个
执行空间: 7 个
上传文件: 15 个
数据库: 已迁移
总数据量: 450.23MB
✓ 迁移完成
============================================================
```

## 迁移报告

迁移完成后，会生成 `migration_report_YYYYMMDD_HHMMSS.json` 文件，包含：

```json
{
  "start_time": "2025-12-26T15:30:45.123456",
  "end_time": "2025-12-26T15:31:20.654321",
  "source": "/home/user/old_project",
  "target": "/home/user/new_project",
  "logs_migrated": 10,
  "execution_spaces_migrated": 7,
  "uploads_migrated": 15,
  "database_migrated": true,
  "total_size": 450230000,
  "total_size_human": "450.23MB",
  "errors": []
}
```

## 常见问题

### Q1: 迁移过程中出错了怎么办？

**A**: 脚本会记录详细的错误信息。检查以下内容：
1. 源和目标目录是否存在且可读写
2. 磁盘空间是否充足（建议空间 > 总数据量的 1.5 倍）
3. 文件权限是否正确

### Q2: 能否只迁移特定的执行空间？

**A**: 目前不支持选择特定的执行空间。如果需要，可以：
1. 先用 `--skip-db` 迁移到目标项目
2. 然后手动删除不需要的执行空间目录

或者修改脚本以支持 `--filter` 参数。

### Q3: 迁移数据库会覆盖目标项目的数据吗？

**A**: 会的。迁移前：
1. 脚本会自动创建备份：`database.db.backup.YYYYMMDD_HHMMSS`
2. 如果不想覆盖，使用 `--skip-db` 参数

### Q4: 执行空间包含什么内容？

**A**: 执行空间包含：
- 上传的文件（复制到执行时）
- 脚本执行期间产生的临时文件
- 脚本输出的文件

### Q5: 能在生产环境中使用吗？

**A**: 可以，但建议：
1. 先用 `--dry-run` 预览迁移内容
2. 在目标项目的备份中进行测试
3. 确认数据完整后再用于生产环境

## 故障排除

### 权限错误

```
ERROR 复制日志失败: execution_1.log - Permission denied
```

**解决**:
```bash
# 检查源目录权限
ls -la /path/to/source/project/logs/

# 如有必要，修改权限
chmod -R 755 /path/to/source/project/logs/
```

### 磁盘空间不足

```
ERROR 复制执行空间失败: execution_1 - No space left on device
```

**解决**:
1. 清理目标磁盘空间
2. 或使用 `--skip-logs` 等参数跳过大文件

### 路径不存在

```
ERROR 源目录不存在: /path/to/source
```

**解决**:
- 确认源项目路径正确
- 确认目录确实存在

## 高级用法

### 仅迁移最近的日志

如果日志过多，可以手动编辑脚本，在 `migrate_logs()` 中添加：

```python
# 只保留最近7天的日志
cutoff_time = datetime.now().timestamp() - (7 * 24 * 3600)
log_files = [f for f in source_logs.glob('*.log') 
             if f.stat().st_mtime > cutoff_time]
```

### 在部署脚本中使用

```bash
#!/bin/bash
# 部署脚本示例

OLD_PROJECT="/var/www/old_project"
NEW_PROJECT="/var/www/new_project"

# 迁移运行时数据
python3 /path/to/migrate_runtime_data.py \
  --source "$OLD_PROJECT" \
  --target "$NEW_PROJECT"

if [ $? -eq 0 ]; then
  echo "数据迁移成功"
  # 继续部署其他步骤
else
  echo "数据迁移失败"
  exit 1
fi
```

## 性能提示

- 大型数据集迁移可能需要几分钟时间
- 进度通过日志实时显示
- 在生产环境中建议在非峰值时段执行迁移

## 安全考虑

- ✅ 迁移前自动备份目标数据库
- ✅ 支持 `--dry-run` 预览迁移
- ✅ 生成详细的迁移报告
- ✅ 所有错误都会被记录

## 支持和反馈

如有问题或建议，请联系开发团队。
