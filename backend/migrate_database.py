"""
数据库迁移脚本

功能：将老数据库的数据迁移到新数据库

使用方法：
    python migrate_database.py [老数据库路径]

示例：
    python migrate_database.py ../data/database_old.db

如果不指定路径，默认会查找 ../data/database_backup.db
"""
import sys
import os
import sqlite3
from datetime import datetime
import shutil

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.script import Script, ScriptVersion
from models.execution import Execution
from models.schedule import Schedule
from models.environment import Environment
from models.category import Category, Tag, script_tags
from models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowNodeExecution
from models.workflow_template import WorkflowTemplate
from models.global_variable import GlobalVariable
from models.ai_config import AIConfig


class DatabaseMigration:
    """数据库迁移工具"""

    def __init__(self, old_db_path, app):
        self.old_db_path = old_db_path
        self.app = app
        self.old_conn = None
        self.stats = {
            'categories': 0,
            'tags': 0,
            'environments': 0,
            'scripts': 0,
            'script_versions': 0,
            'executions': 0,
            'schedules': 0,
            'workflows': 0,
            'workflow_nodes': 0,
            'workflow_edges': 0,
            'workflow_executions': 0,
            'workflow_node_executions': 0,
            'workflow_templates': 0,
            'global_variables': 0,
            'ai_configs': 0,
            'script_tags': 0,
        }

    def connect_old_db(self):
        """连接到老数据库"""
        if not os.path.exists(self.old_db_path):
            raise FileNotFoundError(f"老数据库文件不存在: {self.old_db_path}")

        print(f"连接到老数据库: {self.old_db_path}")
        self.old_conn = sqlite3.connect(self.old_db_path)
        self.old_conn.row_factory = sqlite3.Row

    def table_exists(self, table_name):
        """检查表是否存在"""
        cursor = self.old_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def get_columns(self, table_name):
        """获取表的列名"""
        cursor = self.old_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    def migrate_categories(self):
        """迁移分类数据"""
        if not self.table_exists('category'):
            print("⚠️  category 表不存在，跳过")
            return

        print("开始迁移 categories...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM category")

        for row in cursor.fetchall():
            category = Category(
                id=row['id'],
                name=row['name'],
                description=row['description'] if 'description' in row.keys() else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            db.session.add(category)
            self.stats['categories'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['categories']} 个分类")

    def migrate_tags(self):
        """迁移标签数据"""
        if not self.table_exists('tag'):
            print("⚠️  tag 表不存在，跳过")
            return

        print("开始迁移 tags...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM tag")

        for row in cursor.fetchall():
            tag = Tag(
                id=row['id'],
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            db.session.add(tag)
            self.stats['tags'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['tags']} 个标签")

    def migrate_environments(self):
        """迁移环境变量数据"""
        if not self.table_exists('environment'):
            print("⚠️  environment 表不存在，跳过")
            return

        print("开始迁移 environments...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM environment")

        for row in cursor.fetchall():
            env = Environment(
                id=row['id'],
                name=row['name'],
                value=row['value'],
                description=row['description'] if 'description' in row.keys() else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            db.session.add(env)
            self.stats['environments'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['environments']} 个环境变量")

    def migrate_scripts(self):
        """迁移脚本数据"""
        if not self.table_exists('script'):
            print("⚠️  script 表不存在，跳过")
            return

        print("开始迁移 scripts...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM script")

        columns = self.get_columns('script')

        for row in cursor.fetchall():
            script = Script(
                id=row['id'],
                name=row['name'],
                description=row['description'] if 'description' in columns else None,
                category_id=row['category_id'] if 'category_id' in columns else None,
                script_type=row['script_type'] if 'script_type' in columns else 'python',
                content=row['content'],
                params_schema=row['params_schema'] if 'params_schema' in columns else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow(),
                version=row['version'] if 'version' in columns else 1,
            )
            db.session.add(script)
            self.stats['scripts'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['scripts']} 个脚本")

    def migrate_script_versions(self):
        """迁移脚本版本数据"""
        if not self.table_exists('script_version'):
            print("⚠️  script_version 表不存在，跳过")
            return

        print("开始迁移 script_versions...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM script_version")

        columns = self.get_columns('script_version')

        for row in cursor.fetchall():
            version = ScriptVersion(
                id=row['id'],
                script_id=row['script_id'],
                version=row['version'],
                content=row['content'],
                description=row['description'] if 'description' in columns else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            )
            db.session.add(version)
            self.stats['script_versions'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['script_versions']} 个脚本版本")

    def migrate_script_tags(self):
        """迁移脚本-标签关联数据"""
        if not self.table_exists('script_tags'):
            print("⚠️  script_tags 表不存在，跳过")
            return

        print("开始迁移 script_tags...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM script_tags")

        for row in cursor.fetchall():
            db.session.execute(
                script_tags.insert().values(
                    script_id=row['script_id'],
                    tag_id=row['tag_id']
                )
            )
            self.stats['script_tags'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['script_tags']} 个脚本-标签关联")

    def migrate_executions(self):
        """迁移执行记录数据"""
        if not self.table_exists('execution'):
            print("⚠️  execution 表不存在，跳过")
            return

        print("开始迁移 executions...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM execution")

        columns = self.get_columns('execution')

        for row in cursor.fetchall():
            execution = Execution(
                id=row['id'],
                script_id=row['script_id'],
                status=row['status'],
                output=row['output'] if 'output' in columns else None,
                error=row['error'] if 'error' in columns else None,
                params=row['params'] if 'params' in columns else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                started_at=datetime.fromisoformat(row['started_at']) if 'started_at' in columns and row['started_at'] else None,
                finished_at=datetime.fromisoformat(row['finished_at']) if 'finished_at' in columns and row['finished_at'] else None,
                progress=row['progress'] if 'progress' in columns else 0,
                stage=row['stage'] if 'stage' in columns else 'pending',
            )
            db.session.add(execution)
            self.stats['executions'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['executions']} 条执行记录")

    def migrate_schedules(self):
        """迁移定时任务数据"""
        if not self.table_exists('schedule'):
            print("⚠️  schedule 表不存在，跳过")
            return

        print("开始迁移 schedules...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM schedule")

        columns = self.get_columns('schedule')

        for row in cursor.fetchall():
            schedule = Schedule(
                id=row['id'],
                script_id=row['script_id'],
                name=row['name'] if 'name' in columns else f"定时任务_{row['id']}",
                cron_expression=row['cron_expression'],
                enabled=bool(row['enabled']) if 'enabled' in columns else True,
                params=row['params'] if 'params' in columns else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if 'updated_at' in columns and row['updated_at'] else datetime.utcnow(),
                last_run_at=datetime.fromisoformat(row['last_run_at']) if 'last_run_at' in columns and row['last_run_at'] else None,
            )
            db.session.add(schedule)
            self.stats['schedules'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['schedules']} 个定时任务")

    def migrate_workflows(self):
        """迁移工作流数据"""
        if not self.table_exists('workflow'):
            print("⚠️  workflow 表不存在，跳过")
            return

        print("开始迁移 workflows...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow")

        columns = self.get_columns('workflow')

        for row in cursor.fetchall():
            workflow = Workflow(
                id=row['id'],
                name=row['name'],
                description=row['description'] if 'description' in columns else None,
                config=row['config'] if 'config' in columns else '{}',
                enabled=bool(row['enabled']) if 'enabled' in columns else True,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if 'updated_at' in columns and row['updated_at'] else datetime.utcnow(),
            )
            db.session.add(workflow)
            self.stats['workflows'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflows']} 个工作流")

    def migrate_workflow_nodes(self):
        """迁移工作流节点数据"""
        if not self.table_exists('workflow_node'):
            print("⚠️  workflow_node 表不存在，跳过")
            return

        print("开始迁移 workflow_nodes...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow_node")

        columns = self.get_columns('workflow_node')

        for row in cursor.fetchall():
            node = WorkflowNode(
                id=row['id'],
                workflow_id=row['workflow_id'],
                node_id=row['node_id'],
                node_type=row['node_type'],
                script_id=row['script_id'] if 'script_id' in columns else None,
                config=row['config'] if 'config' in columns else '{}',
                position_x=row['position_x'] if 'position_x' in columns else 0,
                position_y=row['position_y'] if 'position_y' in columns else 0,
            )
            db.session.add(node)
            self.stats['workflow_nodes'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflow_nodes']} 个工作流节点")

    def migrate_workflow_edges(self):
        """迁移工作流边数据"""
        if not self.table_exists('workflow_edge'):
            print("⚠️  workflow_edge 表不存在，跳过")
            return

        print("开始迁移 workflow_edges...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow_edge")

        columns = self.get_columns('workflow_edge')

        for row in cursor.fetchall():
            edge = WorkflowEdge(
                id=row['id'],
                workflow_id=row['workflow_id'],
                edge_id=row['edge_id'],
                source_node_id=row['source_node_id'],
                target_node_id=row['target_node_id'],
                condition=row['condition'] if 'condition' in columns else None,
            )
            db.session.add(edge)
            self.stats['workflow_edges'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflow_edges']} 个工作流边")

    def migrate_workflow_executions(self):
        """迁移工作流执行记录"""
        if not self.table_exists('workflow_execution'):
            print("⚠️  workflow_execution 表不存在，跳过")
            return

        print("开始迁移 workflow_executions...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow_execution")

        columns = self.get_columns('workflow_execution')

        for row in cursor.fetchall():
            execution = WorkflowExecution(
                id=row['id'],
                workflow_id=row['workflow_id'],
                status=row['status'],
                params=row['params'] if 'params' in columns else None,
                error=row['error'] if 'error' in columns else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                start_time=datetime.fromisoformat(row['start_time']) if 'start_time' in columns and row['start_time'] else None,
                end_time=datetime.fromisoformat(row['end_time']) if 'end_time' in columns and row['end_time'] else None,
            )
            db.session.add(execution)
            self.stats['workflow_executions'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflow_executions']} 条工作流执行记录")

    def migrate_workflow_node_executions(self):
        """迁移工作流节点执行记录"""
        if not self.table_exists('workflow_node_execution'):
            print("⚠️  workflow_node_execution 表不存在，跳过")
            return

        print("开始迁移 workflow_node_executions...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow_node_execution")

        columns = self.get_columns('workflow_node_execution')

        for row in cursor.fetchall():
            node_execution = WorkflowNodeExecution(
                id=row['id'],
                workflow_execution_id=row['workflow_execution_id'],
                node_id=row['node_id'],
                execution_id=row['execution_id'] if 'execution_id' in columns else None,
                status=row['status'],
                output=row['output'] if 'output' in columns else None,
                error=row['error'] if 'error' in columns else None,
                start_time=datetime.fromisoformat(row['start_time']) if 'start_time' in columns and row['start_time'] else None,
                end_time=datetime.fromisoformat(row['end_time']) if 'end_time' in columns and row['end_time'] else None,
            )
            db.session.add(node_execution)
            self.stats['workflow_node_executions'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflow_node_executions']} 条工作流节点执行记录")

    def migrate_workflow_templates(self):
        """迁移工作流模板数据"""
        if not self.table_exists('workflow_template'):
            print("⚠️  workflow_template 表不存在，跳过")
            return

        print("开始迁移 workflow_templates...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM workflow_template")

        columns = self.get_columns('workflow_template')

        for row in cursor.fetchall():
            template = WorkflowTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'] if 'description' in columns else None,
                category=row['category'] if 'category' in columns else None,
                icon=row['icon'] if 'icon' in columns else None,
                template_data=row['template_data'] if 'template_data' in columns else '{}',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            )
            db.session.add(template)
            self.stats['workflow_templates'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['workflow_templates']} 个工作流模板")

    def migrate_global_variables(self):
        """迁移全局变量数据"""
        if not self.table_exists('global_variable'):
            print("⚠️  global_variable 表不存在，跳过")
            return

        print("开始迁移 global_variables...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM global_variable")

        columns = self.get_columns('global_variable')

        for row in cursor.fetchall():
            variable = GlobalVariable(
                id=row['id'],
                name=row['name'],
                value=row['value'],
                description=row['description'] if 'description' in columns else None,
                is_encrypted=bool(row['is_encrypted']) if 'is_encrypted' in columns else False,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if 'updated_at' in columns and row['updated_at'] else datetime.utcnow(),
            )
            db.session.add(variable)
            self.stats['global_variables'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['global_variables']} 个全局变量")

    def migrate_ai_configs(self):
        """迁移AI配置数据"""
        if not self.table_exists('ai_config'):
            print("⚠️  ai_config 表不存在，跳过")
            return

        print("开始迁移 ai_configs...")
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM ai_config")

        columns = self.get_columns('ai_config')

        for row in cursor.fetchall():
            config = AIConfig(
                id=row['id'],
                provider=row['provider'] if 'provider' in columns else 'openai',
                api_key=row['api_key'] if 'api_key' in columns else '',
                api_base=row['api_base'] if 'api_base' in columns else None,
                model=row['model'] if 'model' in columns else 'gpt-3.5-turbo',
                enabled=bool(row['enabled']) if 'enabled' in columns else False,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if 'updated_at' in columns and row['updated_at'] else datetime.utcnow(),
            )
            db.session.add(config)
            self.stats['ai_configs'] += 1

        db.session.commit()
        print(f"✓ 迁移了 {self.stats['ai_configs']} 个AI配置")

    def run(self):
        """执行迁移"""
        print("=" * 60)
        print("数据库迁移工具")
        print("=" * 60)

        # 连接老数据库
        self.connect_old_db()

        with self.app.app_context():
            # 创建新数据库表
            print("\n创建新数据库表...")
            db.create_all()
            print("✓ 数据库表创建完成")

            # 按依赖顺序迁移数据
            print("\n开始迁移数据...\n")

            try:
                # 基础数据
                self.migrate_categories()
                self.migrate_tags()
                self.migrate_environments()
                self.migrate_global_variables()
                self.migrate_ai_configs()

                # 脚本相关
                self.migrate_scripts()
                self.migrate_script_versions()
                self.migrate_script_tags()
                self.migrate_executions()
                self.migrate_schedules()

                # 工作流相关
                self.migrate_workflows()
                self.migrate_workflow_nodes()
                self.migrate_workflow_edges()
                self.migrate_workflow_executions()
                self.migrate_workflow_node_executions()
                self.migrate_workflow_templates()

                print("\n" + "=" * 60)
                print("迁移完成！统计信息：")
                print("=" * 60)
                for key, value in self.stats.items():
                    if value > 0:
                        print(f"{key:30s}: {value:6d}")
                print("=" * 60)

            except Exception as e:
                print(f"\n❌ 迁移失败: {str(e)}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                raise
            finally:
                if self.old_conn:
                    self.old_conn.close()


def main():
    """主函数"""
    # 获取老数据库路径
    if len(sys.argv) > 1:
        old_db_path = sys.argv[1]
    else:
        # 默认路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        old_db_path = os.path.join(base_dir, 'data', 'database_backup.db')

    # 检查新数据库路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_db_path = os.path.join(base_dir, 'data', 'database.db')

    print(f"老数据库: {old_db_path}")
    print(f"新数据库: {new_db_path}")

    # 确认操作
    if os.path.exists(new_db_path):
        # 备份当前数据库
        backup_path = new_db_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        print(f"\n警告: 新数据库已存在，将备份到: {backup_path}")
        response = input("是否继续? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("已取消迁移")
            return
        shutil.copy2(new_db_path, backup_path)
        print(f"✓ 已备份现有数据库")
        # 删除现有数据库
        os.remove(new_db_path)
        print(f"✓ 已删除现有数据库")

    # 创建应用
    app = create_app()

    # 执行迁移
    migration = DatabaseMigration(old_db_path, app)
    migration.run()

    print("\n✅ 数据库迁移成功完成！")


if __name__ == '__main__':
    main()
