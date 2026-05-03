"""
配置文件
"""
import os

# PostgreSQL数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'jay123')
DB_NAME = os.environ.get('DB_NAME', 'confmanage')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """应用配置类"""

    # 基础路径
    BASE_DIR = BASE_DIR

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # PostgreSQL数据库配置
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }

    # 脚本存储路径
    SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

    # 脚本工作目录根路径（废弃，保留用于兼容）
    WORKSPACES_DIR = os.path.join(BASE_DIR, 'workspaces')

    # 执行空间根路径（每次执行独立的工作目录）
    EXECUTION_SPACES_DIR = os.path.join(BASE_DIR, 'execution_spaces')

    # 工作流执行空间根路径（每次工作流执行的共享工作目录）
    WORKFLOW_EXECUTION_SPACES_DIR = os.path.join(BASE_DIR, 'workflow_execution_spaces')

    # 日志存储路径
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

    # 数据文件路径
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    # 备份文件路径
    BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

    # 支持的脚本类型
    SUPPORTED_SCRIPT_TYPES = ['python', 'javascript']

    # Python解释器路径
    PYTHON_EXECUTABLE = 'python'

    # Node.js执行器路径
    NODE_EXECUTABLE = 'node'

    # 脚本执行超时时间（秒）
    EXECUTION_TIMEOUT = 300

    # 清理阈值：保留最近N条执行记录
    CLEANUP_THRESHOLD = 500

    # 跨域配置
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175', 'http://localhost:5176', 'http://localhost:3000']

    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        os.makedirs(Config.SCRIPTS_DIR, exist_ok=True)
        os.makedirs(Config.WORKSPACES_DIR, exist_ok=True)
        os.makedirs(Config.EXECUTION_SPACES_DIR, exist_ok=True)
        os.makedirs(Config.WORKFLOW_EXECUTION_SPACES_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.BACKUPS_DIR, exist_ok=True)

    @staticmethod
    def get_script_workspace(script_id):
        """获取脚本的工作目录路径（废弃，保留用于兼容）"""
        return os.path.join(Config.WORKSPACES_DIR, f'script_{script_id}')

    @staticmethod
    def ensure_script_workspace(script_id):
        """确保脚本工作目录存在（废弃，保留用于兼容）"""
        workspace_path = Config.get_script_workspace(script_id)
        os.makedirs(workspace_path, exist_ok=True)
        return workspace_path

    @staticmethod
    def get_execution_space(execution_id):
        """获取执行空间路径"""
        return os.path.join(Config.EXECUTION_SPACES_DIR, f'execution_{execution_id}')

    @staticmethod
    def ensure_execution_space(execution_id):
        """确保执行空间存在"""
        space_path = Config.get_execution_space(execution_id)
        os.makedirs(space_path, exist_ok=True)
        return space_path

    @staticmethod
    def get_workflow_execution_space(workflow_execution_id):
        """获取工作流执行空间路径"""
        return os.path.join(Config.WORKFLOW_EXECUTION_SPACES_DIR, f'workflow_execution_{workflow_execution_id}')

    @staticmethod
    def ensure_workflow_execution_space(workflow_execution_id):
        """确保工作流执行空间存在"""
        space_path = Config.get_workflow_execution_space(workflow_execution_id)
        os.makedirs(space_path, exist_ok=True)
        return space_path
