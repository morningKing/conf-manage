# 定时任务应用上下文错误修复

## 错误现象

```
RuntimeError: Working outside of application context.
This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
```

错误在 `db.session.remove()` 时发生。

## 根本原因

在 APScheduler 的后台线程中执行定时任务时，即使使用 `with current_app.app_context():`，仍然无法正确访问 Flask 应用上下文。原因是：

1. **Flask 的 LocalProxy 限制**: `current_app` 是一个 `LocalProxy` 对象，只在请求或应用上下文中有效
2. **后台线程问题**: APScheduler 在独立的后台线程中运行，这个线程没有自动的应用上下文
3. **时序问题**: `db.session.remove()` 被调用时，应用上下文可能还没有完全建立

## 解决方案

采用**应用实例保存法**：

### 修改 1：SchedulerManager 保存应用实例

**文件**: `backend/services/scheduler.py`

```python
class SchedulerManager:
    """调度器管理类"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='Asia/Shanghai'
        )
        self.app = None  # ✅ 保存应用实例
        self.scheduler.start()

    def set_app(self, app):
        """设置 Flask 应用实例"""
        self.app = app
```

**原理**:
- 在 `__init__` 中添加 `self.app = None`
- 添加 `set_app()` 方法用于保存应用实例
- 这样在后台线程中就能访问应用实例

### 修改 2：使用保存的应用实例创建上下文

**文件**: `backend/services/scheduler.py` - `_execute_scheduled_task()` 方法

```python
def _execute_scheduled_task(self, schedule_id):
    """执行定时任务"""
    from models import db, Schedule, Execution
    from services.executor import execute_script
    from threading import Thread

    print(f'[定时任务] 准备执行任务 {schedule_id}')
    
    # ✅ 检查应用实例是否存在
    if not self.app:
        print(f'[定时任务] 错误: 应用未初始化，无法执行任务 {schedule_id}')
        return

    def run_task_in_context():
        """在应用上下文中执行任务"""
        # ... 任务执行代码 ...

    # ✅ 使用保存的应用实例而不是 current_app
    try:
        with self.app.app_context():
            run_task_in_context()
    except Exception as e:
        print(f'[定时任务] 在应用上下文中执行任务失败: {str(e)}')
        import traceback
        traceback.print_exc()
```

**关键点**:
- 用 `self.app.app_context()` 替代 `current_app.app_context()`
- `self.app` 是应用创建时保存的实例，总是可用的
- 使用 `with self.app.app_context():` 确保在正确的上下文中执行

### 修改 3：应用初始化时设置调度器的应用实例

**文件**: `backend/app.py` - `create_app()` 函数

```python
def create_app(config_class=Config):
    """创建Flask应用"""
    app = Flask(__name__)
    # ... 其他初始化代码 ...

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # ✅ 设置调度器的应用实例
        scheduler_manager.set_app(app)
        # 重新加载定时任务
        scheduler_manager.reload_schedules()

    return app
```

**为什么这样做**:
- `create_app()` 是唯一创建应用实例的地方
- 在这里调用 `scheduler_manager.set_app(app)`，确保调度器持有应用的引用
- 之后调度器在任何线程中都能访问到应用实例

## 修改文件清单

| 文件 | 修改内容 | 行号 |
|------|---------|------|
| `backend/services/scheduler.py` | 添加 `self.app` 属性和 `set_app()` 方法 | 10-23 |
| `backend/services/scheduler.py` | 修改 `_execute_scheduled_task()` 使用 `self.app.app_context()` | 86-151 |
| `backend/app.py` | 在应用初始化时调用 `scheduler_manager.set_app(app)` | 40-41 |

## 验证修复

重启后端服务后，应该看到：

```
[调度器] 任务 1 (任务名) 已添加，下次执行: 2025-12-26 22:00:00
[调度器] 已加载 3 个定时任务
```

任务执行时：

```
[定时任务] 准备执行任务 1
[定时任务] 开始执行任务 1 - 任务名
[定时任务] 创建执行记录成功, 执行ID: 123
[定时任务] 脚本执行线程已启动
```

✅ 不再出现 `RuntimeError: Working outside of application context` 错误

## 技术总结

| 方案 | 优点 | 缺点 |
|------|------|------|
| ❌ 使用 `current_app` | Flask 官方推荐 | 在后台线程中不可靠 |
| ✅ 保存应用实例 | 在任何线程都可用，更稳定 | 需要手动初始化 |

使用**应用实例保存法**是解决后台任务中应用上下文问题的最可靠方案。
