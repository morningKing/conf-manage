"""
测试数据库迁移问题
"""
import sys
import os
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from app import create_app
from models import db, Folder, Script

app = create_app()

with app.app_context():
    print("=" * 60)
    print("数据库迁移问题检测")
    print("=" * 60)

    # 1. 检查Folder表是否存在
    print("\n1. 检查 folders 表是否存在...")
    try:
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'"))
        table_exists = result.fetchone()
        if table_exists:
            print("   [OK] folders 表存在")
        else:
            print("   [ERROR] folders 表不存在 - 严重问题！")
            print("   >> Script模型使用folder_id，但folders表不存在")
    except Exception as e:
        print(f"   [ERROR] 检查失败: {e}")

    # 2. 检查scripts表的folder_id字段
    print("\n2. 检查 scripts 表的字段...")
    try:
        result = db.session.execute(db.text("PRAGMA table_info(scripts)"))
        columns = [col[1] for col in result.fetchall()]
        print(f"   当前字段: {', '.join(columns)}")

        has_category_id = 'category_id' in columns
        has_folder_id = 'folder_id' in columns

        if has_category_id and not has_folder_id:
            print("   [ERROR] 问题: 有category_id字段，但没有folder_id字段")
            print("   >> Script模型期望folder_id，数据库只有category_id")
        elif has_folder_id and not has_category_id:
            print("   [OK] 正常: 有folder_id字段，无category_id字段")
        elif has_folder_id and has_category_id:
            print("   [WARN] 警告: 同时有folder_id和category_id字段（冗余）")
        else:
            print("   [WARN] 异常: 既无folder_id也无category_id")
    except Exception as e:
        print(f"   [ERROR] 检查失败: {e}")

    # 3. 测试Folder模型查询
    print("\n3. 测试 Folder 模型查询...")
    try:
        folders = Folder.query.all()
        print(f"   [OK] 查询成功，找到 {len(folders)} 个文件夹")
    except Exception as e:
        print(f"   [ERROR] 查询失败: {type(e).__name__}")
        print(f"   >> 错误详情: {str(e)[:200]}")

    # 4. 测试Script模型查询
    print("\n4. 测试 Script 模型查询...")
    try:
        scripts = Script.query.limit(1).all()
        print(f"   [OK] 查询成功")
        if scripts:
            script = scripts[0]
            print(f"   脚本ID: {script.id}, 名称: {script.name}")
            try:
                folder = script.folder
                print(f"   folder关系: {folder}")
            except Exception as e:
                print(f"   [ERROR] 访问folder关系失败: {str(e)[:100]}")
    except Exception as e:
        print(f"   [ERROR] 查询失败: {type(e).__name__}")
        print(f"   >> 错误详情: {str(e)[:200]}")

    # 5. 检查外键约束
    print("\n5. 检查 scripts 表的外键约束...")
    try:
        result = db.session.execute(db.text("PRAGMA foreign_key_list(scripts)"))
        fks = result.fetchall()
        print(f"   找到 {len(fks)} 个外键:")
        for fk in fks:
            print(f"   - 字段 {fk[3]} -> {fk[2]}表")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")

    # 6. 检查数据一致性
    print("\n6. 检查数据一致性...")
    try:
        result = db.session.execute(db.text("SELECT id, name, category_id FROM scripts WHERE category_id IS NOT NULL LIMIT 5"))
        scripts_with_category = result.fetchall()
        if scripts_with_category:
            print(f"   [WARN] 发现 {len(scripts_with_category)} 个脚本使用category_id:")
            for s in scripts_with_category:
                print(f"   - Script ID {s[0]}: {s[1]} (category_id={s[2]})")
            print("   >> 这些脚本的数据需要迁移到folder_id")
        else:
            print("   [OK] 没有脚本使用category_id字段")
    except Exception as e:
        print(f"   [ERROR] 检查失败: {e}")

    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

    # 生成迁移建议
    print("\n需要的迁移步骤:")
    print("1. 创建folders表（树形结构）")
    print("2. 将categories数据迁移到folders表")
    print("3. 添加scripts.folder_id字段")
    print("4. 将scripts.category_id数据迁移到scripts.folder_id")
    print("5. 删除scripts.category_id字段")
    print("6. （可选）保留或删除categories表")