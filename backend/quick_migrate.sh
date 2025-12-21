#!/bin/bash

###############################################################################
# 数据库备份和迁移快速脚本
#
# 功能：
#   1. 备份当前数据库
#   2. 执行数据库迁移
#
# 使用方法：
#   ./quick_migrate.sh [老数据库路径]
#
# 示例：
#   ./quick_migrate.sh                          # 使用默认备份路径
#   ./quick_migrate.sh /path/to/old_db.db       # 指定老数据库路径
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
DB_FILE="$DATA_DIR/database.db"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  数据库迁移工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查数据目录
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}创建数据目录: $DATA_DIR${NC}"
    mkdir -p "$DATA_DIR"
fi

# 步骤1: 备份当前数据库
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="$DATA_DIR/database_backup_$(date +%Y%m%d_%H%M%S).db"
    echo -e "${YELLOW}备份当前数据库...${NC}"
    cp "$DB_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓ 数据库已备份到: $BACKUP_FILE${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  当前数据库不存在，将创建新数据库${NC}"
    echo ""
fi

# 步骤2: 确定老数据库路径
if [ -n "$1" ]; then
    OLD_DB_PATH="$1"
else
    # 使用最新的备份文件
    LATEST_BACKUP=$(ls -t "$DATA_DIR"/database_backup_*.db 2>/dev/null | head -n 1)
    if [ -z "$LATEST_BACKUP" ]; then
        echo -e "${RED}❌ 错误: 未找到老数据库文件${NC}"
        echo -e "${YELLOW}使用方法:${NC}"
        echo -e "  ./quick_migrate.sh /path/to/old_database.db"
        exit 1
    fi
    OLD_DB_PATH="$LATEST_BACKUP"
fi

echo -e "${BLUE}老数据库路径: $OLD_DB_PATH${NC}"
echo -e "${BLUE}新数据库路径: $DB_FILE${NC}"
echo ""

# 检查老数据库是否存在
if [ ! -f "$OLD_DB_PATH" ]; then
    echo -e "${RED}❌ 错误: 老数据库文件不存在: $OLD_DB_PATH${NC}"
    exit 1
fi

# 步骤3: 确认操作
echo -e "${YELLOW}警告: 此操作将使用老数据库覆盖当前数据库${NC}"
read -p "是否继续? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ]; then
    echo -e "${YELLOW}已取消迁移${NC}"
    exit 0
fi

echo ""

# 步骤4: 执行迁移
echo -e "${BLUE}开始执行数据库迁移...${NC}"
echo ""

cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 执行迁移脚本
python migrate_database.py "$OLD_DB_PATH"

MIGRATION_STATUS=$?

echo ""

if [ $MIGRATION_STATUS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ 数据库迁移成功完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}后续步骤:${NC}"
    echo -e "  1. 检查数据完整性"
    echo -e "  2. 启动应用程序测试"
    echo -e "  3. 确认无误后可删除备份文件"
    echo ""
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  ❌ 数据库迁移失败${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}请检查错误信息并重试${NC}"
    echo -e "${YELLOW}如需恢复，可使用备份文件: $BACKUP_FILE${NC}"
    echo ""
    exit 1
fi
