# 脚本管理系统增强设计文档

**日期**: 2026-04-02  
**项目**: conf-manage（脚本工具管理系统）  
**设计者**: Claude Code  

---

## 一、项目概述

本次设计涵盖5个子项目，按优先级和依赖关系分三个阶段实现：

### 子项目列表
1. **执行历史增强** - 重新执行功能 + 批量删除支持1000条
2. **Excel预览编辑系统** - Luckysheet集成，支持类原生Excel操作
3. **PostgreSQL数据库迁移** - 从SQLite迁移到PostgreSQL
4. **UI现代化** - Soybean Admin风格改造
5. **颜色预设选择器** - Material Design精选色板 + RGB自定义

### 实施阶段划分

```
阶段1：基础设施迁移（阻塞后端开发）
├── PostgreSQL数据库迁移

阶段2：前端小改动（与阶段1并行）
├── 执行历史增强
└── 颜色预设选择器

阶段3：大改动（阶段1完成后并行）
├── Excel预览编辑系统
└── UI现代化
```

---

## 二、执行历史增强

### 2.1 功能概述

**功能1：重新执行**
- 所有执行记录（除running状态）均可重新执行
- 创建新执行记录，复制原参数和文件，不覆盖原记录

**功能2：批量删除（支持1000条）**
- 服务端选择会话管理，跨页保持选择状态
- 上限1000条，批量删除执行记录及相关文件

### 2.2 服务端选择会话设计

#### 数据模型

新增 `SelectionSession` 表：

```python
class SelectionSession(db.Model):
    """选择会话表 - 用于批量操作的状态管理"""
    __tablename__ = 'selection_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(32), unique=True, nullable=False)  # UUID，前端生成或后端返回
    execution_ids = db.Column(db.Text, default='[]')  # JSON数组存储选中ID
    count = db.Column(db.Integer, default=0)  # 选中数量（便于快速查询）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_ids(self):
        return json.loads(self.execution_ids) if self.execution_ids else []
    
    def set_ids(self, ids):
        self.execution_ids = json.dumps(ids)
        self.count = len(ids)
```

**说明**：当前系统无用户认证，使用前端生成的UUID作为session_id标识会话。

#### API设计

```
POST /api/executions/selection/create
Request: {}  # 无需参数，后端生成session_id
Response: { code: 0, data: { session_id: "abc123def456" } }

POST /api/executions/selection/<session_id>/add
Request: { execution_ids: [1, 2, 3] }
Response: { code: 0, data: { count: 15, max_reached: false } }
注意：超过1000条返回 max_reached: true 并拒绝添加

POST /api/executions/selection/<session_id>/remove
Request: { execution_ids: [1, 2] }
Response: { code: 0, data: { count: 13 } }

POST /api/executions/selection/<session_id>/clear
Response: { code: 0, data: { count: 0 } }

GET /api/executions/selection/<session_id>
Response: { 
  code: 0, 
  data: { 
    count: 15, 
    ids: [1,2,3...], 
    max_limit: 1000,
    items: [
      { id: 1, script_name: "xxx", status: "success" },
      ...
    ]  # 可选，返回选中项基本信息供前端展示
  } 
}

POST /api/executions/selection/<session_id>/delete
Response: { 
  code: 0, 
  data: { 
    success: 14, 
    failed: 1, 
    details: [{ id: 1, status: "success" }, ...]
  } 
}
删除完成后自动清空会话
```

### 2.3 重新执行API

```
POST /api/executions/<id>/re-execute
Response: { 
  code: 0, 
  data: { 
    new_execution_id: 456,
    message: "已创建新执行"
  } 
}

执行流程：
1. 获取原执行记录（script_id, environment_id, params）
2. 创建新Execution记录，状态pending
3. 复制原执行空间文件到新执行空间（如果有）
4. 启动后台线程执行脚本
5. 返回新执行ID
```

### 2.4 前端改动

#### Executions.vue 改动要点

```vue
<!-- 操作列新增"重新执行"按钮 -->
<el-button 
  v-if="row.status !== 'running'" 
  size="small" 
  type="success"
  @click="handleReExecute(row)"
>
  重新执行
</el-button>

<!-- 批量选择面板 -->
<div class="selection-panel" v-if="selectionSession">
  <el-badge :value="selectionCount" :max="1000">
    <el-button @click="showSelectionDetail">已选择</el-button>
  </el-badge>
  <el-button type="danger" @click="batchDelete" :disabled="selectionCount === 0">
    批量删除 ({{ selectionCount }})
  </el-button>
  <el-button @click="clearSelection">清空选择</el-button>
</div>

<!-- 选中详情弹窗 -->
<el-dialog v-model="selectionDetailVisible" title="已选择项">
  <el-table :data="selectedItems" max-height="400">
    <el-table-column prop="id" label="ID" width="80" />
    <el-table-column prop="script_name" label="脚本名称" />
    <el-table-column prop="status" label="状态" />
    <el-table-column label="操作" width="100">
      <template #default="{ row }">
        <el-button size="small" @click="removeFromSelection(row.id)">移除</el-button>
      </template>
    </el-table-column>
  </el-table>
</el-dialog>
```

#### 前端交互逻辑

```javascript
// 页面加载时创建选择会话
onMounted(async () => {
  const res = await createSelectionSession()
  sessionId.value = res.data.session_id
})

// 勾选时添加到会话
const handleSelect = async (row) => {
  if (selectionCount.value >= 1000) {
    ElMessage.warning('最多选择1000条')
    return
  }
  await addToSelection(sessionId.value, [row.id])
  selectionCount.value++
}

// 切换页面时选择状态保持（服务端存储）
// 批量删除
const batchDelete = async () => {
  await ElMessageBox.confirm(`确定删除选中的 ${selectionCount.value} 条记录？`)
  const res = await deleteSelection(sessionId.value)
  // 显示结果统计
}
```

---

## 三、Excel预览编辑系统

### 3.1 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| Excel库 | Luckysheet 2.x | 国产开源，功能接近原生Excel |
| 文件大小 | 无前端限制 | 让浏览器自行处理 |
| 保存方式 | 覆盖原文件 | 直接保存到执行空间 |

### 3.2 后端API

```
GET /api/executions/<id>/files/<path>/excel
功能：读取Excel文件并转换为Luckysheet JSON格式
Response: { 
  code: 0, 
  data: {
    gridData: [...],  // Luckysheet格式数据
    filename: "output.xlsx",
    sheets: ["Sheet1", "Sheet2"]
  }
}

POST /api/executions/<id>/files/<path>/excel
功能：保存Luckysheet JSON数据为Excel文件（覆盖原文件）
Request: { gridData: [...] }
Response: { code: 0, message: "保存成功" }
```

### 3.3 数据转换流程

**读取流程：**
```
.xlsx/.xls文件 → openpyxl解析 → 转换为Luckysheet JSON → 返回前端
```

**保存流程：**
```
Luckysheet JSON → 转换为openpyxl对象 → 保存到原路径（覆盖）
```

### 3.4 前端组件设计

#### ExcelEditor.vue 结构

```vue
<template>
  <div class="excel-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleSave" :loading="saving">
        <el-icon><DocumentChecked /></el-icon> 保存
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon> 导出下载
      </el-button>
      <el-button @click="handleRefresh">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
      <el-button @click="toggleFullscreen">
        <el-icon><FullScreen /></el-icon> 全屏
      </el-button>
    </div>
    
    <!-- Luckysheet容器 -->
    <div id="luckysheet-container" class="sheet-container"></div>
    
    <!-- 状态栏 -->
    <div class="status-bar">
      <span>{{ filename }}</span>
      <span>{{ fileSize }}</span>
      <span>当前sheet: {{ currentSheet }}</span>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import luckysheet from 'luckysheet'

const loadExcel = async () => {
  const res = await getExcelFile(executionId, filePath)
  luckysheet.create({
    container: 'luckysheet-container',
    data: res.data.gridData,
    showtoolbar: true,
    showinfobar: false,
    showsheetbar: true,
    showstatisticBar: true,
    enableAddRow: true,
    enableAddBackTop: true,
    // 中文界面
    lang: 'zh'
  })
}

const handleSave = async () => {
  const gridData = luckysheet.getAllSheets()
  await saveExcelFile(executionId, filePath, { gridData })
  ElMessage.success('保存成功')
}
</script>
```

### 3.5 集成位置

- `ExecutionFiles.vue`：检测 `.xlsx/.xls` 文件时显示"Excel编辑"按钮
- 点击按钮打开全屏弹窗，嵌入ExcelEditor组件

### 3.6 错误处理

| 场景 | 处理方式 |
|------|----------|
| 文件损坏 | 提示"文件格式错误"，显示原始下载按钮 |
| 保存失败 | 提示错误信息，不关闭编辑器，允许重试或导出 |
| 并发编辑 | 后保存者提示"文件已被修改，是否覆盖？" |

### 3.7 新增依赖

**后端：**
```
requirements.txt新增：
- openpyxl 3.1.x
- xlrd 2.x（支持旧版.xls）
```

**前端：**
```
package.json新增：
- luckysheet 2.x
```

---

## 四、PostgreSQL数据库迁移

### 4.1 配置信息

```
主机：localhost
端口：5432
用户：postgres
密码：jay123
数据库：confmanage
```

### 4.2 配置文件改动

#### config.py

```python
import os

# 环境变量支持（便于部署切换）
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'jay123')
DB_NAME = os.environ.get('DB_NAME', 'confmanage')

class Config:
    # PostgreSQL配置（默认）
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # 连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # SQLite路径保留（供迁移脚本使用）
    SQLITE_DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'database.db')
    
    # SQLite URI（迁移时使用）
    SQLITE_DATABASE_URI = f'sqlite:///{SQLITE_DATABASE_PATH}'
```

### 4.3 迁移脚本设计

#### migrate_to_postgres.py

```python
"""
SQLite到PostgreSQL数据迁移脚本

使用方式：
cd backend
python migrate_to_postgres.py [--sqlite-path PATH] [--skip-verify]

参数：
--sqlite-path: SQLite数据库路径（默认data/database.db）
--skip-verify: 跳过迁移验证

流程：
1. 连接SQLite读取所有表数据
2. 连接PostgreSQL创建表结构（使用SQLAlchemy models）
3. 逐表迁移数据（处理JSON字段）
4. 验证迁移完整性（记录数对比）
5. 生成迁移报告
"""

import sys
import json
from datetime import datetime

def migrate():
    # 1. 连接源数据库（SQLite）
    sqlite_engine = create_engine(Config.SQLITE_DATABASE_URI)
    sqlite_conn = sqlite_engine.connect()
    
    # 2. 连接目标数据库（PostgreSQL）
    postgres_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    postgres_conn = postgres_engine.connect()
    
    # 3. 创建表结构
    Base.metadata.create_all(postgres_engine)
    
    # 4. 逐表迁移
    tables_order = [
        'categories', 'tags', 'script_tags', 'global_variables',
        'scripts', 'script_versions', 'environments',
        'executions', 'schedules', 'webhooks',
        'workflows', 'workflow_nodes', 'workflow_edges', 'workflow_executions'
    ]
    
    for table in tables_order:
        migrate_table(sqlite_conn, postgres_conn, table)
    
    # 5. 验证
    if not skip_verify:
        verify_migration(sqlite_conn, postgres_conn)
    
    # 6. 报告
    print_report()

def migrate_table(source, target, table_name):
    """迁移单表数据"""
    rows = source.execute(f"SELECT * FROM {table_name}")
    
    for row in rows:
        # 处理JSON字段（SQLite存储为字符串）
        # 插入PostgreSQL
        ...
```

### 4.4 迁移数据表顺序

按依赖关系排序，确保外键约束有效：

```
1. categories（分类） - 无外键依赖
2. tags（标签） - 无外键依赖
3. script_tags（关联表） - 依赖scripts和tags
4. global_variables（全局变量） - 无外键依赖
5. environments（执行环境） - 无外键依赖
6. scripts（脚本） - 依赖categories
7. script_versions（脚本版本） - 依赖scripts
8. executions（执行记录） - 依赖scripts, environments
9. schedules（定时任务） - 依赖scripts
10. webhooks（Webhook） - 依赖scripts
11. workflows（工作流） - 无外键依赖
12. workflow_nodes（工作流节点） - 依赖workflows, scripts
13. workflow_edges（工作流边） - 依赖workflows, nodes
14. workflow_executions（工作流执行） - 依赖workflows
```

### 4.5 迁移执行步骤

```bash
# 1. 确保PostgreSQL服务运行
# 2. 创建数据库（如果未创建）
psql -U postgres -c "CREATE DATABASE confmanage;"

# 3. 执行迁移
cd backend
python migrate_to_postgres.py

# 4. 查看迁移报告
# 脚本输出：
# - 各表迁移记录数
# - 成功/失败统计
# - 数据完整性验证结果

# 5. 启动应用验证
python app.py
```

### 4.6 回退方案

```bash
# 出问题时回退到SQLite
export DB_TYPE=sqlite
python app.py

# 或修改config.py临时切换
```

### 4.7 新增依赖

```
requirements.txt新增：
- psycopg2-binary 2.9.x
```

---

## 五、UI现代化（Soybean Admin风格）

### 5.1 实现方式

**混合方案**：引入Soybean Admin核心布局组件和主题系统，保留现有业务页面代码

### 5.2 引入的核心组件

```
frontend/src/layouts/
├── base-layout/
│   ├── index.vue          # 基础布局入口
│   └── content.vue        # 内容区域包裹
├── header/
│   ├── index.vue          # 顶部导航栏
│   ├── breadcrumb.vue     # 面包屑导航
│   └── search.vue         # 搜索组件
├── sidebar/
│   ├── index.vue          # 侧边栏主体
│   ├── menu.vue           # 菜单组件（彩色图标）
│   └── mix-menu.vue       # 混合菜单模式（可选）
├── tab/
│   └── index.vue          # 多标签页（可选）
└── footer/
│   └── index.vue          # 底部栏（可选）

frontend/src/styles/
├── theme/
│   ├── settings.json      # 主题配置
│   ├── dark.scss          # 深色主题变量
│   └── light.scss         # 浅色主题变量
├── variables.scss         # 全局样式变量
└── transitions.scss       # 过渡动画
```

### 5.3 主题系统设计

```javascript
// theme/settings.json
{
  "mode": "light",
  "themeColor": "#409EFF",
  "sidebar": {
    "collapsed": false,
    "width": 200,
    "collapsedWidth": 64,
    "mix": false
  },
  "header": {
    "height": 60,
    "visible": true
  },
  "footer": {
    "visible": false
  },
  "page": {
    "animate": true,
    "transition": "fade-slide"
  }
}
```

### 5.4 样式改造要点

#### 侧边栏现代化

| 改造项 | 描述 |
|--------|------|
| 彩色图标 | 每个一级菜单图标添加彩色背景圆形 |
| Hover动画 | 菜单项hover添加渐变背景动画 |
| 子菜单展开 | 过渡动画，平滑展开收起 |
| 收起状态 | 图标居中，悬停展开菜单浮层 |
| 深色模式 | 背景深灰渐变，文字柔白 |

#### 顶部栏现代化

| 改造项 | 描述 |
|--------|------|
| 面包屑导航 | 显示当前页面路径，支持点击跳转 |
| 工具按钮 | 圆形按钮，悬停缩放动画 |
| 搜索框 | 图标触发，展开式搜索输入 |
| 主题切换 | 日/月图标动画过渡 |

#### 内容区卡片改造

| 改造项 | 描述 |
|--------|------|
| 卡片阴影 | 微阴影(0 2px 12px rgba)，圆角8px |
| 表格悬停 | 行hover渐变背景 |
| 按钮 | 渐变色背景，hover亮度提升 |
| 分页 | 圆角按钮，紧凑布局 |
| 输入框 | 聚焦时边框动画发光 |

### 5.5 需适配的页面

```
Scripts.vue       # 脚本管理（主要页面）
Executions.vue    # 执行历史（主要页面）
Schedules.vue     # 定时任务
Workflows.vue     # 工作流管理
Files.vue         # 文件管理
Categories.vue    # 分类管理
Tags.vue          # 标签管理
Environments.vue  # 执行环境
GlobalVariables.vue # 全局变量
Webhooks.vue      # Webhook管理
Backup.vue        # 备份管理
AIScriptWriter.vue # AI脚本编写
AISettings.vue    # AI配置
```

### 5.6 新增依赖

```
package.json新增：
- sass 1.x
- @vueuse/core（可选，用于主题状态管理）
```

---

## 六、颜色预设选择器

### 6.1 设计概述

- **预设色板**：精选50种Material Design颜色
- **自定义输入**：RGB三值输入 + HEX输入
- **展示方式**：简化色板面板，平铺展示

### 6.2 预设颜色列表

```javascript
const materialColors = [
  // 红色系（6种）
  { name: '红色', hex: '#F44336' },
  { name: '深红', hex: '#D32F2F' },
  { name: '玫红', hex: '#E91E63' },
  { name: '粉红', hex: '#EC407A' },
  { name: '紫红', hex: '#C2185B' },
  { name: '浅红', hex: '#FFCDD2' },
  
  // 紫色系（4种）
  { name: '紫色', hex: '#9C27B0' },
  { name: '深紫', hex: '#7B1FA2' },
  { name: '浅紫', hex: '#BA68C8' },
  { name: '淡紫', hex: '#E1BEE7' },
  
  // 蓝色系（8种）
  { name: '靛蓝', hex: '#3F51B5' },
  { name: '蓝色', hex: '#2196F3' },
  { name: '深蓝', hex: '#1976D2' },
  { name: '天蓝', hex: '#03A9F4' },
  { name: '亮蓝', hex: '#00BCD4' },
  { name: '青色', hex: '#0097A7' },
  { name: 'Teal', hex: '#009688' },
  { name: '蓝灰', hex: '#607D8B' },
  
  // 绿色系（6种）
  { name: '绿色', hex: '#4CAF50' },
  { name: '深绿', hex: '#388E3C' },
  { name: '亮绿', hex: '#8BC34A' },
  { name: '柠檬', hex: '#CDDC39' },
  { name: '黄绿', hex: '#AEEA00' },
  { name: '淡绿', hex: '#C8E6C9' },
  
  // 黄/橙色系（6种）
  { name: '黄色', hex: '#FFEB3B' },
  { name: '琥珀', hex: '#FFC107' },
  { name: '橙色', hex: '#FF9800' },
  { name: '深橙', hex: '#FF5722' },
  { name: '金橙', hex: '#FF6F00' },
  { name: '浅黄', hex: '#FFF9C4' },
  
  // 棕/灰色系（8种）
  { name: '棕色', hex: '#795548' },
  { name: '深棕', hex: '#5D4037' },
  { name: '灰色', hex: '#9E9E9E' },
  { name: '深灰', hex: '#616161' },
  { name: '浅灰', hex: '#BDBDBD' },
  { name: '白色', hex: '#FFFFFF' },
  { name: '黑色', hex: '#000000' },
  { name: '炭灰', hex: '#424242' },
  
  // Element UI常用色（6种）
  { name: '主色蓝', hex: '#409EFF' },
  { name: '成功绿', hex: '#67C23A' },
  { name: '警告橙', hex: '#E6A23C' },
  { name: '危险红', hex: '#F56C6C' },
  { name: '信息灰', hex: '#909399' },
  { name: '链接蓝', hex: '#1890ff' },
  
  // 补充色（6种，总计50种）
  { name: '青绿', hex: '#00BFA5' },
  { name: '藏青', hex: '#304FFE' },
  { name: '珊瑚', hex: '#FF7043' },
  { name: '薰衣草', hex: '#B388FF' },
  { name: '薄荷', hex: '#69F0AE' },
  { name: '奶油', hex: '#FFF8E1' }
]
```

### 6.3 前端组件设计

#### ColorPicker.vue

```vue
<template>
  <div class="color-picker-panel">
    <!-- 预设色板区 -->
    <div class="preset-section">
      <div class="color-grid">
        <div 
          v-for="color in materialColors"
          :key="color.hex"
          class="color-item"
          :class="{ selected: selectedColor === color.hex }"
          :style="{ backgroundColor: color.hex }"
          :title="color.name"
          @click="selectPreset(color.hex)"
        >
          <el-icon v-if="selectedColor === color.hex" class="check-icon">
            <Check />
          </el-icon>
        </div>
      </div>
    </div>
    
    <!-- 分隔线 -->
    <el-divider content-position="left">自定义颜色</el-divider>
    
    <!-- 自定义区 -->
    <div class="custom-section">
      <!-- 颜色选择器 -->
      <el-color-picker 
        v-model="customColor"
        :show-alpha="showAlpha"
        @change="handleCustomChange"
      />
      
      <!-- HEX输入 -->
      <el-input 
        v-model="hexInput"
        placeholder="#409EFF"
        class="hex-input"
        @change="handleHexChange"
      >
        <template #prefix>#</template>
      </el-input>
      
      <!-- RGB输入 -->
      <div class="rgb-inputs">
        <el-input-number 
          v-model="rgb.r" 
          :min="0" :max="255" 
          size="small" 
          @change="handleRgbChange"
        />
        <el-input-number 
          v-model="rgb.g" 
          :min="0" :max="255" 
          size="small"
          @change="handleRgbChange"
        />
        <el-input-number 
          v-model="rgb.b" 
          :min="0" :max="255" 
          size="small"
          @change="handleRgbChange"
        />
      </div>
    </div>
    
    <!-- 预览 -->
    <div class="preview-section">
      <span>预览效果：</span>
      <el-tag :color="selectedColor" effect="plain">
        {{ previewText || '示例标签' }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '#409EFF' },
  showAlpha: { type: Boolean, default: false },
  previewText: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedColor = ref(props.modelValue)
const customColor = ref(props.modelValue)
const hexInput = ref(props.modelValue.replace('#', ''))

const rgb = computed({
  get: () => hexToRgb(selectedColor.value),
  set: (val) => { /* handled by watch */ }
})

// HEX转RGB
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 64, g: 158, b: 255 }
}

// RGB转HEX
const rgbToHex = (r, g, b) => {
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')
}

// 选择预设色
const selectPreset = (hex) => {
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  emit('update:modelValue', hex)
  emit('change', hex)
}

// HEX输入变化
const handleHexChange = (val) => {
  const hex = '#' + val.replace('#', '')
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    selectedColor.value = hex
    customColor.value = hex
    emit('update:modelValue', hex)
    emit('change', hex)
  }
}

// RGB输入变化
const handleRgbChange = () => {
  const hex = rgbToHex(rgb.value.r, rgb.value.g, rgb.value.b)
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  emit('update:modelValue', hex)
  emit('change', hex)
}
</script>

<style scoped lang="scss">
.color-picker-panel {
  padding: 12px;
  
  .preset-section {
    .color-grid {
      display: grid;
      grid-template-columns: repeat(10, 1fr);
      gap: 6px;
      
      .color-item {
        width: 28px;
        height: 28px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid transparent;
        position: relative;
        
        &:hover {
          transform: scale(1.1);
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        &.selected {
          border-color: #409EFF;
          box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
        }
        
        .check-icon {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: #fff;
          font-size: 14px;
          text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
      }
    }
  }
  
  .custom-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 12px;
    
    .hex-input {
      width: 120px;
    }
    
    .rgb-inputs {
      display: flex;
      gap: 8px;
      
      .el-input-number {
        width: 80px;
      }
    }
  }
  
  .preview-section {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #eee;
    display: flex;
    align-items: center;
    gap: 10px;
  }
}
</style>
```

### 6.4 集成位置

| 页面 | 原组件 | 替换为 |
|------|--------|--------|
| Categories.vue | `el-color-picker` | `ColorPicker` |
| Tags.vue | `el-color-picker` | `ColorPicker` |

### 6.5 API改动

无后端改动，颜色值仍以HEX字符串存储。

---

## 七、实施计划

### 7.1 阶段时间估算

| 阶段 | 内容 | 估算工作量 |
|------|------|-----------|
| 阶段1 | PostgreSQL迁移 | 后端2-3天 |
| 阶段2 | 执行历史+颜色选择器 | 前端2-3天（与阶段1并行） |
| 阶段3 | Excel预览+UI现代化 | 前后端并行，5-7天 |

### 7.2 依赖关系图

```
阶段1 PostgreSQL ──┬──► 阶段3 Excel预览（需要稳定数据库）
                   │
                   └──► 阶段3 UI现代化
                   
阶段2 执行历史 ────┘（不阻塞，可独立部署）
阶段2 颜色选择器 ──┘（不阻塞，可独立部署）
```

---

## 八、风险与回退

### 8.1 PostgreSQL迁移风险

| 风险 | 缓解措施 |
|------|----------|
| 数据丢失 | 迁移前备份SQLite，迁移后验证记录数 |
| 连接失败 | 环境变量支持快速回退SQLite |
| 性能下降 | 连接池配置，预测试压力 |

### 8.2 Excel编辑风险

| 风险 | 缓解措施 |
|------|----------|
| 大文件卡顿 | 无限制但提示，浏览器自行处理 |
| 文件覆盖误操作 | 保存按钮需确认，提供导出备份 |
| 格式不兼容 | 错误提示，提供原始下载 |

### 8.3 UI改造风险

| 风险 | 缓解措施 |
|------|----------|
| 样式冲突 | 逐步适配，保留原有CSS备份 |
| 组件不兼容 | 混合方案，保留业务代码 |

---

## 九、附录

### 9.1 新增依赖汇总

**后端 requirements.txt：**
```
psycopg2-binary==2.9.9
openpyxl==3.1.2
xlrd==2.0.1
```

**前端 package.json：**
```
"luckysheet": "^2.1.13",
"sass": "^1.69.0",
"@vueuse/core": "^10.7.0"
```

### 9.2 新增文件列表

```
backend/
├── migrate_to_postgres.py        # 迁移脚本
├── models/selection_session.py   # 选择会话模型
└── api/
    └── selection.py               # 选择会话API

frontend/src/
├── components/
│   ├── ColorPicker.vue           # 颜色选择器
│   └── ExcelEditor.vue           # Excel编辑器
├── layouts/
│   ├── base-layout/
│   ├── header/
│   ├── sidebar/
│   └── ...
└── styles/theme/
    ├── settings.json
    ├── dark.scss
    └── light.scss
```

---

**文档结束**

**下一步**：调用 writing-plans 技术创建详细实现计划