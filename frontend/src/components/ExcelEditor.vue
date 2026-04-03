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
      </div>
    </div>

    <!-- Univer 容器 -->
    <div ref="containerRef" class="sheet-container"></div>

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
import { DocumentChecked, Download, Refresh } from '@element-plus/icons-vue'
import { getExcelFile, saveExcelFile } from '../api'

// Univer 相关
import { Univer, LocaleType } from '@univerjs/core'
import { defaultTheme } from '@univerjs/design'
import { UniverDocsPlugin } from '@univerjs/docs'
import { UniverDocsUIPlugin } from '@univerjs/docs-ui'
import { UniverFormulaEnginePlugin } from '@univerjs/engine-formula'
import { UniverRenderEnginePlugin } from '@univerjs/engine-render'
import { UniverSheetsPlugin } from '@univerjs/sheets'
import { UniverSheetsFormulaPlugin } from '@univerjs/sheets-formula'
import { UniverSheetsUIPlugin } from '@univerjs/sheets-ui'
import { UniverUIPlugin } from '@univerjs/ui'

import '@univerjs/design/lib/index.css'
import '@univerjs/ui/lib/index.css'
import '@univerjs/docs-ui/lib/index.css'
import '@univerjs/sheets-ui/lib/index.css'

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

const containerRef = ref(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const filename = ref('')
const sheetCount = ref(0)

let univer = null
let workbook = null

// 加载 Excel 文件
const loadExcel = async () => {
  loading.value = true
  error.value = ''

  try {
    const res = await getExcelFile(props.executionId, props.filePath)

    if (res.code === 0) {
      filename.value = res.data.filename
      sheetCount.value = res.data.sheet_count

      // 等待 DOM 更新后初始化 Univer
      await nextTick()
      initUniver(res.data.gridData)
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

// 初始化 Univer
const initUniver = (sheetsData) => {
  try {
    // 清理旧实例
    if (univer) {
      univer.dispose()
      univer = null
      workbook = null
    }

    // 创建 Univer 实例
    univer = new Univer({
      theme: defaultTheme,
      locale: LocaleType.ZH_CN,
    })

    // 注册插件
    univer.registerPlugin(UniverRenderEnginePlugin)
    univer.registerPlugin(UniverFormulaEnginePlugin)
    univer.registerPlugin(UniverUIPlugin, { container: containerRef.value })
    univer.registerPlugin(UniverDocsPlugin)
    univer.registerPlugin(UniverDocsUIPlugin)
    univer.registerPlugin(UniverSheetsPlugin)
    univer.registerPlugin(UniverSheetsUIPlugin)
    univer.registerPlugin(UniverSheetsFormulaPlugin)

    // 转换数据格式并创建工作簿
    const workbookData = convertToUniverFormat(sheetsData)
    workbook = univer.createUniverSheet(workbookData)

    console.log('Univer initialized successfully')
  } catch (e) {
    error.value = 'Excel编辑器初始化失败: ' + e.message
    ElMessage.error('Excel编辑器初始化失败')
    console.error('Univer init error:', e)
  }
}

// 转换 Luckysheet 格式到 Univer 格式
const convertToUniverFormat = (sheetsData) => {
  if (!sheetsData || sheetsData.length === 0) {
    return { id: 'workbook', sheetOrder: [], sheets: {} }
  }

  const workbookData = {
    id: 'workbook',
    sheetOrder: [],
    sheets: {}
  }

  sheetsData.forEach((sheet, index) => {
    const sheetId = `sheet-${index}`
    workbookData.sheetOrder.push(sheetId)

    const cellData = sheet.data || []
    const rowCount = sheet.row || cellData.length || 10
    const colCount = sheet.column || (cellData[0]?.length || 10)

    // 构建 Univer 单元格数据格式
    const sheetCellData = {}
    for (let r = 0; r < rowCount; r++) {
      sheetCellData[r] = {}
      for (let c = 0; c < colCount; c++) {
        const cell = cellData[r]?.[c]
        if (cell && cell.v !== undefined && cell.v !== null) {
          sheetCellData[r][c] = {
            v: cell.v,
            t: cell.ct?.t === 'n' ? 2 : 1, // 1=string, 2=number
          }
        }
      }
    }

    workbookData.sheets[sheetId] = {
      id: sheetId,
      name: sheet.name || `Sheet${index + 1}`,
      rowCount: rowCount,
      columnCount: colCount,
      cellData: sheetCellData,
      defaultColumnWidth: 93,
      defaultRowHeight: 27,
    }
  })

  return workbookData
}

// 从 Univer 格式转换回保存格式
const convertFromUniverFormat = () => {
  if (!workbook) return []

  const sheets = workbook.getSheets()
  const result = []

  sheets.forEach((sheet, index) => {
    const sheetData = {
      name: sheet.getName(),
      index: index,
      order: index,
      status: index === 0 ? 1 : 0,
      row: sheet.getRowCount(),
      column: sheet.getColumnCount(),
      celldata: [],
      data: []
    }

    const cellData = sheet.getCellData()
    const data = []
    const celldata = []

    for (let r = 0; r < sheetData.row; r++) {
      const rowData = []
      for (let c = 0; c < sheetData.column; c++) {
        const cell = cellData?.[r]?.[c]
        if (cell && cell.v !== undefined && cell.v !== null) {
          const cellValue = {
            r: r,
            c: c,
            v: {
              v: cell.v,
              m: String(cell.v),
              ct: { fa: 'General', t: cell.t === 2 ? 'n' : 'g' }
            }
          }
          celldata.push(cellValue)
          rowData.push(cellValue.v)
        } else {
          rowData.push(null)
        }
      }
      data.push(rowData)
    }

    sheetData.data = data
    sheetData.celldata = celldata
    result.push(sheetData)
  })

  return result
}

// 保存
const handleSave = async () => {
  saving.value = true

  try {
    const allSheets = convertFromUniverFormat()

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

onMounted(() => {
  loadExcel()
})

onBeforeUnmount(() => {
  if (univer) {
    univer.dispose()
  }
})

// 暴露方法
defineExpose({
  loadExcel,
  handleSave
})
</script>

<style scoped>
.excel-editor {
  display: flex;
  flex-direction: column;
  height: 70vh;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-left .filename {
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.sheet-container {
  flex: 1;
  min-height: 400px;
  background: #fff;
}

.status-bar {
  padding: 8px 16px;
  background: #f5f7fa;
  border-top: 1px solid #dcdfe6;
  font-size: 13px;
  color: #606266;
}

.status-bar .error {
  color: #f56c6c;
}
</style>