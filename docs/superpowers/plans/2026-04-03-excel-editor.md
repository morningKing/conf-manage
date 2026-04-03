# Excel预览编辑系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 Luckysheet 实现 Excel 文件的在线预览和编辑，支持类原生 Excel 操作体验，编辑后直接保存到执行空间。

**Architecture:** 后端使用 openpyxl 解析 Excel 文件并转换为 Luckysheet JSON 格式，前端使用 Luckysheet 渲染表格并提供编辑功能。保存时将 Luckysheet 数据转换回 Excel 格式覆盖原文件。

**Tech Stack:** Luckysheet 2.x, openpyxl 3.x, xlrd 2.x, Flask, Vue 3

---

## 文件结构

```
backend/
├── requirements.txt             # 修改：添加 openpyxl, xlrd
├── api/
│   └── executions.py            # 修改：添加 Excel API 端点
└── utils/
    └── excel_converter.py       # 新建：Excel 与 Luckysheet 格式转换

frontend/src/
├── components/
│   ├── ExcelEditor.vue          # 新建：Excel 编辑器组件
│   └── ExecutionFiles.vue       # 修改：添加 Excel 编辑按钮
├── api/
│   └── index.js                 # 修改：添加 Excel API
└── main.js                      # 修改：引入 Luckysheet 样式
```

---

### Task 1: 添加后端依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 Excel 处理依赖**

在 `backend/requirements.txt` 末尾添加：

```
openpyxl==3.1.2
xlrd==2.0.1
```

- [ ] **Step 2: 安装依赖**

Run: `cd backend && pip install openpyxl==3.1.2 xlrd==2.0.1`
Expected: Successfully installed openpyxl xlrd

- [ ] **Step 3: 验证安装**

Run: `python -c "import openpyxl; import xlrd; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add openpyxl and xlrd for Excel processing"
```

---

### Task 2: 创建 Excel 转换工具

**Files:**
- Create: `backend/utils/excel_converter.py`

- [ ] **Step 1: 创建 utils 目录（如果不存在）**

Run: `mkdir -p backend/utils && touch backend/utils/__init__.py`

- [ ] **Step 2: 创建 Excel 转换模块**

创建 `backend/utils/excel_converter.py`：

```python
"""
Excel 文件与 Luckysheet 格式转换工具
"""
import json
import os
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime


def excel_to_luckysheet(file_path):
    """
    将 Excel 文件转换为 Luckysheet 格式
    
    Args:
        file_path: Excel 文件路径
        
    Returns:
        list: Luckysheet sheet 数据列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 加载工作簿
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xls':
        # 旧版 xls 格式，使用 xlrd 读取后转换
        import xlrd
        workbook = xlrd.open_workbook(file_path)
        return _xlrd_to_luckysheet(workbook, file_path)
    else:
        # xlsx 格式
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        return _openpyxl_to_luckysheet(workbook, file_path)


def _openpyxl_to_luckysheet(workbook, file_path):
    """使用 openpyxl 转换"""
    sheets = []
    
    for sheet_index, sheet_name in enumerate(workbook.sheetnames):
        sheet = workbook[sheet_name]
        
        # 构建单元格数据
        cell_data = []
        merge_cells = []
        
        # 获取合并单元格信息
        for merge_range in sheet.merged_cells.ranges:
            merge_cells.append({
                'r': merge_range.min_row - 1,  # Luckysheet 使用 0-based 索引
                'c': merge_range.min_col - 1,
                'rs': merge_range.max_row - merge_range.min_row + 1,
                'cs': merge_range.max_col - merge_range.min_col + 1
            })
        
        # 遍历所有有数据的行
        max_row = sheet.max_row
        max_col = sheet.max_column
        
        for row_idx in range(1, max_row + 1):
            for col_idx in range(1, max_col + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                if cell.value is not None:
                    cell_data.append({
                        'r': row_idx - 1,  # 0-based
                        'c': col_idx - 1,
                        'v': _convert_cell_value(cell.value)
                    })
        
        # 构建列宽信息
        col_info = []
        for col_idx in range(1, max_col + 1):
            col_letter = get_column_letter(col_idx)
            col_dim = sheet.column_dimensions.get(col_letter)
            if col_dim and col_dim.width:
                col_info.append({
                    'w': int(col_dim.width * 8)  # 转换为像素宽度
                })
        
        # 构建行高信息
        row_info = []
        for row_idx in range(1, max_row + 1):
            row_dim = sheet.row_dimensions.get(row_idx)
            if row_dim and row_dim.height:
                row_info.append({
                    'h': int(row_dim.height)
                })
        
        sheets.append({
            'name': sheet_name,
            'index': sheet_index,
            'order': sheet_index,
            'status': 1 if sheet_index == 0 else 0,
            'celldata': cell_data,
            'config': {
                'merge': merge_cells if merge_cells else None,
                'columnlen': col_info if col_info else None,
                'rowlen': row_info if row_info else None
            },
            'data': [],  # Luckysheet 会自动从 celldata 生成
            'row': max_row,
            'column': max_col
        })
    
    return sheets


def _xlrd_to_luckysheet(workbook, file_path):
    """使用 xlrd 转换旧版 xls 文件"""
    sheets = []
    
    for sheet_index in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(sheet_index)
        cell_data = []
        
        for row_idx in range(sheet.nrows):
            for col_idx in range(sheet.ncols):
                cell = sheet.cell(row_idx, col_idx)
                if cell.ctype != 0:  # 0 = empty
                    cell_data.append({
                        'r': row_idx,
                        'c': col_idx,
                        'v': _convert_xlrd_value(cell)
                    })
        
        sheets.append({
            'name': sheet.name,
            'index': sheet_index,
            'order': sheet_index,
            'status': 1 if sheet_index == 0 else 0,
            'celldata': cell_data,
            'config': {},
            'data': [],
            'row': sheet.nrows,
            'column': sheet.ncols
        })
    
    return sheets


def _convert_cell_value(value):
    """转换单元格值为 Luckysheet 格式"""
    if value is None:
        return {'v': '', 'm': ''}
    
    if isinstance(value, (int, float)):
        # 数字
        return {
            'v': value,
            'm': str(value),
            'ct': {'fa': 'General', 't': 'n'}
        }
    elif isinstance(value, datetime):
        # 日期
        return {
            'v': value.strftime('%Y-%m-%d'),
            'm': value.strftime('%Y-%m-%d'),
            'ct': {'fa': 'yyyy-mm-dd', 't': 'd'}
        }
    elif isinstance(value, str):
        return {
            'v': value,
            'm': value,
            'ct': {'fa': 'General', 't': 'g'}
        }
    else:
        return {
            'v': str(value),
            'm': str(value),
            'ct': {'fa': 'General', 't': 'g'}
        }


def _convert_xlrd_value(cell):
    """转换 xlrd 单元格值"""
    import xlrd
    
    if cell.ctype == xlrd.XL_CELL_TEXT:
        return {
            'v': cell.value,
            'm': cell.value,
            'ct': {'fa': 'General', 't': 'g'}
        }
    elif cell.ctype == xlrd.XL_CELL_NUMBER:
        return {
            'v': cell.value,
            'm': str(cell.value),
            'ct': {'fa': 'General', 't': 'n'}
        }
    elif cell.ctype == xlrd.XL_CELL_DATE:
        date_tuple = xlrd.xldate_as_tuple(cell.value, 0)
        date_str = '%04d-%02d-%02d' % date_tuple[:3]
        return {
            'v': date_str,
            'm': date_str,
            'ct': {'fa': 'yyyy-mm-dd', 't': 'd'}
        }
    else:
        return {
            'v': str(cell.value),
            'm': str(cell.value)
        }


def luckysheet_to_excel(grid_data, output_path):
    """
    将 Luckysheet 数据保存为 Excel 文件
    
    Args:
        grid_data: Luckysheet sheet 数据列表
        output_path: 输出文件路径
    """
    workbook = openpyxl.Workbook()
    
    # 删除默认工作表
    if 'Sheet' in workbook.sheetnames:
        workbook.remove(workbook['Sheet'])
    
    for sheet_data in grid_data:
        sheet_name = sheet_data.get('name', f'Sheet{sheet_data.get("index", 0) + 1}')
        sheet = workbook.create_sheet(title=sheet_name)
        
        # 处理单元格数据
        cell_data = sheet_data.get('celldata', [])
        for cell in cell_data:
            row = cell.get('r', 0) + 1  # openpyxl 使用 1-based 索引
            col = cell.get('c', 0) + 1
            value_info = cell.get('v', {})
            
            # 提取值
            if isinstance(value_info, dict):
                value = value_info.get('v', '')
            else:
                value = value_info
            
            sheet.cell(row=row, column=col, value=value)
        
        # 处理合并单元格
        config = sheet_data.get('config', {})
        merges = config.get('merge', [])
        if merges:
            for merge in merges:
                start_row = merge.get('r', 0) + 1
                start_col = merge.get('c', 0) + 1
                end_row = start_row + merge.get('rs', 1) - 1
                end_col = start_col + merge.get('cs', 1) - 1
                sheet.merge_cells(
                    start_row=start_row,
                    start_column=start_col,
                    end_row=end_row,
                    end_column=end_col
                )
        
        # 处理列宽
        col_len = config.get('columnlen', [])
        if col_len:
            for idx, col_info in enumerate(col_len):
                if col_info.get('w'):
                    col_letter = get_column_letter(idx + 1)
                    sheet.column_dimensions[col_letter].width = col_info['w'] / 8
    
    # 保存文件
    workbook.save(output_path)
    return output_path


def get_excel_info(file_path):
    """
    获取 Excel 文件基本信息
    
    Args:
        file_path: Excel 文件路径
        
    Returns:
        dict: 文件信息
    """
    if not os.path.exists(file_path):
        return None
    
    stat = os.stat(file_path)
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.xls':
            import xlrd
            workbook = xlrd.open_workbook(file_path)
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'sheets': workbook.sheet_names(),
                'sheet_count': workbook.nsheets
            }
        else:
            workbook = openpyxl.load_workbook(file_path, read_only=True)
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'sheets': workbook.sheetnames,
                'sheet_count': len(workbook.sheetnames)
            }
    except Exception as e:
        return {
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'error': str(e)
        }
```

- [ ] **Step 3: 验证模块**

Run: `cd backend && python -c "from utils.excel_converter import excel_to_luckysheet, luckysheet_to_excel; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/utils/excel_converter.py backend/utils/__init__.py
git commit -m "feat: add Excel to Luckysheet format converter"
```

---

### Task 3: 添加 Excel API 端点

**Files:**
- Modify: `backend/api/executions.py`

- [ ] **Step 1: 在 executions.py 末尾添加 Excel API**

在 `backend/api/executions.py` 末尾添加：

```python
@api_bp.route('/executions/<int:execution_id>/files/<path:file_path>/excel', methods=['GET'])
def get_excel_file(execution_id, file_path):
    """获取 Excel 文件内容（Luckysheet 格式）"""
    try:
        from config import Config
        from utils.excel_converter import excel_to_luckysheet, get_excel_info

        execution = Execution.query.get_or_404(execution_id)
        execution_space = Config.get_execution_space(execution_id)

        # 安全检查
        safe_path = os.path.normpath(file_path)
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            return jsonify({'code': 1, 'message': '非法的文件路径'}), 400

        full_path = os.path.join(execution_space, safe_path)

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({'code': 1, 'message': '文件不存在'}), 404

        # 检查文件类型
        ext = os.path.splitext(full_path)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            return jsonify({'code': 1, 'message': '不是有效的 Excel 文件'}), 400

        # 转换为 Luckysheet 格式
        try:
            grid_data = excel_to_luckysheet(full_path)
            info = get_excel_info(full_path)

            return jsonify({
                'code': 0,
                'data': {
                    'gridData': grid_data,
                    'filename': info.get('filename', os.path.basename(full_path)),
                    'sheets': info.get('sheets', []),
                    'sheet_count': info.get('sheet_count', 0),
                    'size': info.get('size', 0)
                }
            })
        except Exception as e:
            return jsonify({
                'code': 1,
                'message': f'Excel 文件解析失败: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@api_bp.route('/executions/<int:execution_id>/files/<path:file_path>/excel', methods=['POST'])
def save_excel_file(execution_id, file_path):
    """保存 Excel 文件（从 Luckysheet 格式）"""
    try:
        from config import Config
        from utils.excel_converter import luckysheet_to_excel

        execution = Execution.query.get_or_404(execution_id)
        execution_space = Config.get_execution_space(execution_id)

        # 安全检查
        safe_path = os.path.normpath(file_path)
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            return jsonify({'code': 1, 'message': '非法的文件路径'}), 400

        full_path = os.path.join(execution_space, safe_path)

        if not os.path.exists(full_path):
            return jsonify({'code': 1, 'message': '文件不存在'}), 404

        # 获取 Luckysheet 数据
        data = request.get_json()
        grid_data = data.get('gridData', [])

        if not grid_data:
            return jsonify({'code': 1, 'message': '无数据'}), 400

        # 备份原文件
        backup_path = full_path + '.bak'
        if os.path.exists(full_path):
            import shutil
            shutil.copy2(full_path, backup_path)

        # 保存
        try:
            luckysheet_to_excel(grid_data, full_path)

            # 删除备份
            if os.path.exists(backup_path):
                os.remove(backup_path)

            return jsonify({
                'code': 0,
                'message': '保存成功'
            })
        except Exception as e:
            # 恢复备份
            if os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, full_path)

            return jsonify({
                'code': 1,
                'message': f'保存失败: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
```

- [ ] **Step 2: 验证 API 语法**

Run: `cd backend && python -c "from api.executions import get_excel_file, save_excel_file; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/api/executions.py
git commit -m "feat: add Excel file API endpoints for Luckysheet"
```

---

### Task 4: 添加前端依赖和 API

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 安装 Luckysheet**

Run: `cd frontend && npm install luckysheet@2.1.13`
Expected: Successfully installed luckysheet

- [ ] **Step 2: 在 index.html 引入 Luckysheet 样式**

在 `frontend/index.html` 的 `<head>` 部分添加：

```html
<!-- Luckysheet CSS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/css/pluginsCss.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/plugins.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/css/luckysheet.css" />
```

或者使用本地安装的版本（推荐）：

```html
<!-- Luckysheet CSS (本地安装) -->
<link rel="stylesheet" href="/node_modules/luckysheet/dist/plugins/css/pluginsCss.css" />
<link rel="stylesheet" href="/node_modules/luckysheet/dist/plugins/plugins.css" />
<link rel="stylesheet" href="/node_modules/luckysheet/dist/css/luckysheet.css" />
```

- [ ] **Step 3: 添加前端 API 方法**

在 `frontend/src/api/index.js` 末尾添加：

```javascript
// Excel 文件操作
export const getExcelFile = (executionId, filePath) =>
  request.get(`/executions/${executionId}/files/${encodeURIComponent(filePath)}/excel`)

export const saveExcelFile = (executionId, filePath, data) =>
  request.post(`/executions/${executionId}/files/${encodeURIComponent(filePath)}/excel`, data)
```

- [ ] **Step 4: 验证前端构建**

Run: `cd frontend && npm run build 2>&1 | head -20`
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/src/api/index.js
git commit -m "feat: add Luckysheet dependency and Excel API methods"
```

---

### Task 5: 创建 ExcelEditor 组件

**Files:**
- Create: `frontend/src/components/ExcelEditor.vue`

- [ ] **Step 1: 创建 ExcelEditor.vue**

创建 `frontend/src/components/ExcelEditor.vue`：

```vue
<template>
  <div class="excel-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="filename">{{ filename }}</span>
        <el-tag size="small" type="info">{{ sheetCount }} 个工作表</el-tag>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="handleSave" :loading="saving">
          <el-icon><DocumentChecked /></el-icon>
          保存
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出下载
        </el-button>
        <el-button @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
      </div>
    </div>

    <!-- Luckysheet 容器 -->
    <div
      id="luckysheet-container"
      class="sheet-container"
      :class="{ fullscreen: isFullscreen }"
    ></div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <span v-if="loading">加载中...</span>
      <span v-else-if="error" class="error">{{ error }}</span>
      <span v-else>就绪</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentChecked, Download, Refresh, FullScreen } from '@element-plus/icons-vue'
import { getExcelFile, saveExcelFile, getExecutionFile } from '../api'

const props = defineProps({
  executionId: {
    type: Number,
    required: true
  },
  filePath: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['saved', 'error'])

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const filename = ref('')
const sheetCount = ref(0)
const isFullscreen = ref(false)
const gridData = ref([])

// 加载 Excel 文件
const loadExcel = async () => {
  loading.value = true
  error.value = ''

  try {
    const res = await getExcelFile(props.executionId, props.filePath)

    if (res.code === 0) {
      filename.value = res.data.filename
      sheetCount.value = res.data.sheet_count
      gridData.value = res.data.gridData

      // 等待 DOM 更新后初始化 Luckysheet
      await nextTick()
      initLuckysheet(res.data.gridData)
    } else {
      error.value = res.message || '加载失败'
    }
  } catch (err) {
    error.value = err.message || '加载失败'
    ElMessage.error('加载 Excel 文件失败: ' + error.value)
  } finally {
    loading.value = false
  }
}

// 初始化 Luckysheet
const initLuckysheet = (data) => {
  // 销毁现有实例
  if (window.luckysheet) {
    try {
      window.luckysheet.destroy()
    } catch (e) {
      console.warn('Destroy luckysheet error:', e)
    }
  }

  // 初始化配置
  const options = {
    container: 'luckysheet-container',
    data: data,
    showtoolbar: true,
    showinfobar: false,
    showsheetbar: true,
    showstatisticBar: true,
    enableAddRow: true,
    enableAddBackTop: true,
    lang: 'zh',
    hook: {
      // 编辑后自动标记为已修改
      cellUpdated: () => {
        // 可以添加未保存提示
      }
    }
  }

  // 创建实例
  window.luckysheet.create(options)
}

// 保存
const handleSave = async () => {
  saving.value = true

  try {
    // 获取当前数据
    const allSheets = window.luckysheet.getAllSheets()

    const res = await saveExcelFile(props.executionId, props.filePath, {
      gridData: allSheets
    })

    if (res.code === 0) {
      ElMessage.success('保存成功')
      emit('saved', { filename: filename.value })
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (err) {
    ElMessage.error('保存失败: ' + err.message)
    emit('error', err)
  } finally {
    saving.value = false
  }
}

// 导出下载
const handleExport = async () => {
  // 先保存当前修改
  try {
    await ElMessageBox.confirm(
      '导出前将先保存当前修改，是否继续？',
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' }
    )

    await handleSave()

    // 下载文件
    const url = `/api/executions/${props.executionId}/files/${encodeURIComponent(props.filePath)}?download=true`
    window.open(url, '_blank')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

// 刷新
const handleRefresh = async () => {
  try {
    await ElMessageBox.confirm(
      '刷新将丢失未保存的修改，是否继续？',
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    await loadExcel()
    ElMessage.success('已刷新')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

// 全屏切换
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value

  // 触发窗口 resize 事件，让 Luckysheet 重新计算尺寸
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'))
  }, 100)
}

onMounted(() => {
  loadExcel()
})

onBeforeUnmount(() => {
  // 销毁 Luckysheet 实例
  if (window.luckysheet) {
    try {
      window.luckysheet.destroy()
    } catch (e) {
      console.warn('Destroy luckysheet error:', e)
    }
  }
})

// 暴露方法
defineExpose({
  loadExcel,
  handleSave
})
</script>

<style scoped lang="scss">
.excel-editor {
  display: flex;
  flex-direction: column;
  height: 70vh;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f5f7fa;
    border-bottom: 1px solid #dcdfe6;

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .filename {
        font-weight: 600;
        color: #303133;
      }
    }

    .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }

  .sheet-container {
    flex: 1;
    min-height: 400px;
    background: #fff;

    &.fullscreen {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 9999;
      height: 100vh;
    }
  }

  .status-bar {
    padding: 8px 16px;
    background: #f5f7fa;
    border-top: 1px solid #dcdfe6;
    font-size: 13px;
    color: #606266;

    .error {
      color: #f56c6c;
    }
  }
}
</style>
```

- [ ] **Step 2: 验证组件语法**

Run: `cd frontend && npm run build 2>&1 | grep -i error || echo "Build OK"`
Expected: Build OK

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ExcelEditor.vue
git commit -m "feat: add ExcelEditor component with Luckysheet integration"
```

---

### Task 6: 在 ExecutionFiles 中集成 Excel 编辑

**Files:**
- Modify: `frontend/src/components/ExecutionFiles.vue`

- [ ] **Step 1: 导入 ExcelEditor 组件**

在 ExecutionFiles.vue 的 script 部分添加：

```javascript
import ExcelEditor from './ExcelEditor.vue'
```

- [ ] **Step 2: 添加 Excel 编辑状态和数据**

```javascript
const excelVisible = ref(false)
const currentExcelFile = ref(null)

// 判断是否为 Excel 文件
const isExcelFile = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  return ['xlsx', 'xls'].includes(ext)
}
```

- [ ] **Step 3: 在模板中添加 Excel 编辑按钮和对话框**

在操作列中，预览按钮前添加 Excel 编辑按钮：

```vue
<el-table-column label="操作" width="220" align="center">
  <template #default="{ row }">
    <el-button
      v-if="isExcelFile(row.path)"
      size="small"
      type="success"
      link
      @click="openExcelEditor(row)"
    >
      Excel编辑
    </el-button>
    <el-button
      v-if="canPreview(row.path) && !isExcelFile(row.path)"
      size="small"
      type="primary"
      link
      @click="previewFile(row)"
    >
      预览
    </el-button>
    <el-button
      size="small"
      type="success"
      link
      @click="downloadFile(row)"
    >
      下载
    </el-button>
  </template>
</el-table-column>
```

在文件末尾添加 Excel 编辑对话框：

```vue
<!-- Excel 编辑对话框 -->
<el-dialog
  v-model="excelVisible"
  :title="`Excel 编辑 - ${currentExcelFile?.path || ''}`"
  width="95%"
  top="2vh"
  destroy-on-close
>
  <ExcelEditor
    v-if="excelVisible && currentExcelFile"
    :execution-id="executionId"
    :file-path="currentExcelFile.path"
    @saved="handleExcelSaved"
    @error="handleExcelError"
  />
  <template #footer>
    <el-button @click="excelVisible = false">关闭</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 4: 添加 Excel 编辑方法**

```javascript
// 打开 Excel 编辑器
const openExcelEditor = (file) => {
  currentExcelFile.value = file
  excelVisible.value = true
}

// Excel 保存完成
const handleExcelSaved = () => {
  ElMessage.success('Excel 文件已保存')
}

// Excel 编辑错误
const handleExcelError = (err) => {
  console.error('Excel 编辑错误:', err)
}
```

- [ ] **Step 5: 验证构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ExecutionFiles.vue
git commit -m "feat: integrate Excel editor in ExecutionFiles component"
```

---

### Task 7: 集成测试

**Files:**
- 无文件修改，测试验证

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && python app.py`
Expected: Flask 在 port 5000 启动

- [ ] **Step 2: 启动前端服务**

Run: `cd frontend && npm run dev`
Expected: Vite 在 port 5173 启动

- [ ] **Step 3: 准备测试 Excel 文件**

创建一个测试 Excel 文件或使用现有的：
1. 上传一个 .xlsx 文件到脚本执行
2. 或使用已有的执行空间中的 Excel 文件

- [ ] **Step 4: 测试 Excel 预览和编辑**

在浏览器中：
1. 打开执行历史页面
2. 点击一个执行的"文件"按钮
3. 找到 Excel 文件，点击"Excel编辑"按钮
4. 验证 Luckysheet 正确加载文件内容
5. 编辑单元格内容
6. 点击"保存"按钮
7. 刷新页面重新打开，验证修改已保存

- [ ] **Step 5: 测试导出功能**

1. 在 Excel 编辑器中点击"导出下载"
2. 验证文件下载成功
3. 用本地 Excel 软件打开，验证内容正确

- [ ] **Step 6: 测试错误处理**

测试场景：
1. 打开损坏的 Excel 文件 → 显示错误提示
2. 尝试编辑只读文件（如果有）→ 显示错误提示

- [ ] **Step 7: Commit 测试通过**

```bash
git add -A
git commit -m "test: Excel editor integration test passed"
```

---

## 自检清单

**1. Spec覆盖检查:**
- ✓ Luckysheet集成 - Task 4, Task 5
- ✓ Excel读取API - Task 3
- ✓ Excel保存API - Task 3
- ✓ 格式转换工具 - Task 2
- ✓ 前端编辑组件 - Task 5
- ✓ ExecutionFiles集成 - Task 6

**2. Placeholder扫描:**
- 无 TBD、TODO
- 所有代码完整提供
- API 返回格式一致

**3. 类型一致性:**
- gridData 使用数组格式
- celldata 使用 {r, c, v} 结构
- API 响应使用 {code, data, message}

---

## 完成标记

Excel预览编辑系统已完成，支持：
- .xlsx 和 .xls 文件在线预览
- 类原生 Excel 编辑体验
- 多工作表支持
- 保存到原文件位置
- 导出下载功能