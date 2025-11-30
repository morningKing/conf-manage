"""
配置文件
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 脚本存储路径
    SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

    # 脚本工作目录根路径（废弃，保留用于兼容）
    WORKSPACES_DIR = os.path.join(BASE_DIR, 'workspaces')

    # 执行空间根路径（每次执行独立的工作目录）
    EXECUTION_SPACES_DIR = os.path.join(BASE_DIR, 'execution_spaces')

    # 日志存储路径
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

    # 数据文件路径
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    # 支持的脚本类型
    SUPPORTED_SCRIPT_TYPES = ['python', 'javascript']

    # Python解释器路径
    PYTHON_EXECUTABLE = 'python3'

    # Node.js执行器路径
    NODE_EXECUTABLE = 'node'

    # 脚本执行超时时间（秒）
    EXECUTION_TIMEOUT = 300

    # 跨域配置
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']

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
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

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
