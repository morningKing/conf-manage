"""
添加工作流模板表

运行方式：
PYTHONPATH=/path/to/backend:$PYTHONPATH python3 backend/migrations/add_workflow_template_table.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from models import db
from models.workflow_template import WorkflowTemplate
import json


def create_tables():
    """创建工作流模板表"""
    app = create_app()

    with app.app_context():
        # 创建表
        db.create_all()
        print("✅ 工作流模板表创建成功")

        # 创建内置模板
        create_builtin_templates()


def create_builtin_templates():
    """创建内置模板"""

    # 检查是否已有内置模板
    if WorkflowTemplate.query.filter_by(is_builtin=True).first():
        print("ℹ️ 内置模板已存在，跳过创建")
        return

    templates = [
        {
            'name': '简单顺序执行',
            'description': '按顺序执行多个脚本，适合简单的数据处理流程',
            'category': '基础模板',
            'icon': 'List',
            'template_config': {
                'nodes': [
                    {
                        'node_id': 'node_1',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '步骤1'},
                        'position': {'x': 150, 'y': 100}
                    },
                    {
                        'node_id': 'node_2',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '步骤2'},
                        'position': {'x': 150, 'y': 220}
                    },
                    {
                        'node_id': 'node_3',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '步骤3'},
                        'position': {'x': 150, 'y': 340}
                    }
                ],
                'edges': [
                    {
                        'edge_id': 'edge_1',
                        'source': 'node_1',
                        'target': 'node_2',
                        'condition': None
                    },
                    {
                        'edge_id': 'edge_2',
                        'source': 'node_2',
                        'target': 'node_3',
                        'condition': None
                    }
                ]
            },
            'is_builtin': True
        },
        {
            'name': '条件分支执行',
            'description': '根据脚本执行结果选择不同的分支，适合需要错误处理的场景',
            'category': '基础模板',
            'icon': 'Share',
            'template_config': {
                'nodes': [
                    {
                        'node_id': 'node_1',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '数据验证'},
                        'position': {'x': 150, 'y': 100}
                    },
                    {
                        'node_id': 'node_2',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '成功处理'},
                        'position': {'x': 50, 'y': 250}
                    },
                    {
                        'node_id': 'node_3',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '失败告警'},
                        'position': {'x': 250, 'y': 250}
                    }
                ],
                'edges': [
                    {
                        'edge_id': 'edge_1',
                        'source': 'node_1',
                        'target': 'node_2',
                        'condition': {
                            'type': 'success',
                            'node_id': 'node_1'
                        }
                    },
                    {
                        'edge_id': 'edge_2',
                        'source': 'node_1',
                        'target': 'node_3',
                        'condition': {
                            'type': 'failed',
                            'node_id': 'node_1'
                        }
                    }
                ]
            },
            'is_builtin': True
        },
        {
            'name': '数据处理流水线',
            'description': '完整的数据处理流程：提取、转换、加载（ETL）',
            'category': '数据处理',
            'icon': 'DataAnalysis',
            'template_config': {
                'nodes': [
                    {
                        'node_id': 'node_1',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '数据提取'},
                        'position': {'x': 150, 'y': 80}
                    },
                    {
                        'node_id': 'node_2',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '数据清洗'},
                        'position': {'x': 150, 'y': 180}
                    },
                    {
                        'node_id': 'node_3',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '数据转换'},
                        'position': {'x': 150, 'y': 280}
                    },
                    {
                        'node_id': 'node_4',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '数据加载'},
                        'position': {'x': 150, 'y': 380}
                    },
                    {
                        'node_id': 'node_5',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '生成报告'},
                        'position': {'x': 150, 'y': 480}
                    }
                ],
                'edges': [
                    {'edge_id': 'edge_1', 'source': 'node_1', 'target': 'node_2', 'condition': None},
                    {'edge_id': 'edge_2', 'source': 'node_2', 'target': 'node_3', 'condition': None},
                    {'edge_id': 'edge_3', 'source': 'node_3', 'target': 'node_4', 'condition': None},
                    {'edge_id': 'edge_4', 'source': 'node_4', 'target': 'node_5', 'condition': None}
                ]
            },
            'is_builtin': True
        },
        {
            'name': '延迟执行模板',
            'description': '在脚本执行之间添加延迟，适合需要等待的场景',
            'category': '基础模板',
            'icon': 'Timer',
            'template_config': {
                'nodes': [
                    {
                        'node_id': 'node_1',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '启动任务'},
                        'position': {'x': 150, 'y': 80}
                    },
                    {
                        'node_id': 'node_2',
                        'node_type': 'delay',
                        'config': {'label': '等待5秒', 'delay': 5},
                        'position': {'x': 150, 'y': 180}
                    },
                    {
                        'node_id': 'node_3',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '检查状态'},
                        'position': {'x': 150, 'y': 280}
                    }
                ],
                'edges': [
                    {'edge_id': 'edge_1', 'source': 'node_1', 'target': 'node_2', 'condition': None},
                    {'edge_id': 'edge_2', 'source': 'node_2', 'target': 'node_3', 'condition': None}
                ]
            },
            'is_builtin': True
        },
        {
            'name': 'API调用链',
            'description': '连续调用多个API接口，适合微服务场景',
            'category': 'API调用',
            'icon': 'Link',
            'template_config': {
                'nodes': [
                    {
                        'node_id': 'node_1',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '获取Token'},
                        'position': {'x': 150, 'y': 80}
                    },
                    {
                        'node_id': 'node_2',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '调用API-1'},
                        'position': {'x': 150, 'y': 180}
                    },
                    {
                        'node_id': 'node_3',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '调用API-2'},
                        'position': {'x': 150, 'y': 280}
                    },
                    {
                        'node_id': 'node_4',
                        'node_type': 'script',
                        'script_id': None,
                        'config': {'label': '处理结果'},
                        'position': {'x': 150, 'y': 380}
                    }
                ],
                'edges': [
                    {'edge_id': 'edge_1', 'source': 'node_1', 'target': 'node_2', 'condition': None},
                    {'edge_id': 'edge_2', 'source': 'node_2', 'target': 'node_3', 'condition': None},
                    {'edge_id': 'edge_3', 'source': 'node_3', 'target': 'node_4', 'condition': None}
                ]
            },
            'is_builtin': True
        }
    ]

    for template_data in templates:
        template = WorkflowTemplate(
            name=template_data['name'],
            description=template_data['description'],
            category=template_data['category'],
            icon=template_data['icon'],
            template_config=json.dumps(template_data['template_config']),
            is_builtin=template_data['is_builtin']
        )
        db.session.add(template)

    db.session.commit()
    print(f"✅ 成功创建 {len(templates)} 个内置模板")


if __name__ == '__main__':
    create_tables()
    print("\n✨ 迁移完成！")
