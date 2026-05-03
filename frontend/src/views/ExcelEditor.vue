<template>
  <div class="excel-editor-container">
    <!-- Top toolbar -->
    <div class="excel-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button :icon="RefreshLeft" @click="handleUndo" :disabled="!canUndo">撤销</el-button>
          <el-button :icon="RefreshRight" @click="handleRedo" :disabled="!canRedo">重做</el-button>
        </el-button-group>
        <el-button type="primary" :icon="Check" @click="handleSave" :loading="saving">
          保存
        </el-button>
      </div>
      <div class="toolbar-center">
        <span class="file-name">{{ fileName || '未加载文件' }}</span>
        <el-tag v-if="hasUnsavedChanges" type="warning" size="small" style="margin-left: 8px">未保存</el-tag>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Plus" @click="handleAddSheet">添加工作表</el-button>
        <el-button :icon="Delete" @click="handleDeleteSheet" :disabled="sheetCount <= 1">删除工作表</el-button>
        <span class="collaborator-info" v-if="collaboratorCount > 0">
          <el-icon><User /></el-icon>
          {{ collaboratorCount }} 人协作中
        </span>
      </div>
    </div>

    <!-- Main editor area -->
    <div class="excel-main">
      <div v-loading="loading" class="luckysheet-container">
        <div id="luckysheet" style="width: 100%; height: 100%"></div>
      </div>
    </div>

    <!-- Bottom status bar -->
    <div class="excel-statusbar">
      <div class="sheet-tabs">
        <el-tag
          v-for="(sheet, index) in sheets"
          :key="index"
          :type="currentSheetIndex === index ? 'primary' : 'info'"
          :effect="currentSheetIndex === index ? 'dark' : 'plain'"
          @click="handleSwitchSheet(index)"
          @dblclick="handleRenameSheet(index)"
          class="sheet-tab"
        >
          {{ sheet.name }}
        </el-tag>
      </div>
      <div class="save-status">
        <el-icon v-if="saving" class="is-loading"><Loading /></el-icon>
        <span v-else-if="lastSaveTime">上次保存: {{ formatTime(lastSaveTime) }}</span>
        <span v-else>未保存</span>
      </div>
    </div>

    <!-- Add sheet dialog -->
    <el-dialog v-model="addSheetVisible" title="添加工作表" width="400px">
      <el-input v-model="newSheetName" placeholder="请输入工作表名称" />
      <template #footer>
        <el-button @click="addSheetVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddSheet">确定</el-button>
      </template>
    </el-dialog>

    <!-- Rename sheet dialog -->
    <el-dialog v-model="renameSheetVisible" title="重命名工作表" width="400px">
      <el-input v-model="renameSheetName" placeholder="请输入新的工作表名称" />
      <template #footer>
        <el-button @click="renameSheetVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRenameSheet">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, RefreshRight, Check, Plus, Delete, User, Loading } from '@element-plus/icons-vue'
import { getExcelInfo, getExcelSheet, saveExcel, addExcelSheet, deleteExcelSheet, renameExcelSheet } from '../api'
import excelSocket from '../utils/excel-socket'

// Import Luckysheet
import luckysheet from 'luckysheet'
import 'luckysheet/dist/plugins/css/pluginsCss.css'
import 'luckysheet/dist/plugins/plugins.css'
import 'luckysheet/dist/css/luckysheet.css'

const route = useRoute()
const router = useRouter()

// State
const loading = ref(false)
const saving = ref(false)
const fileName = ref('')
const filePath = ref('')
const sheets = ref([])
const currentSheetIndex = ref(0)
const hasUnsavedChanges = ref(false)
const lastSaveTime = ref(null)
const collaboratorCount = ref(0)
const canUndo = ref(false)
const canRedo = ref(false)

// Collaboration state
const collaborators = ref([])
const myUserInfo = ref({ name: '', color: '' })

// Dialog state
const addSheetVisible = ref(false)
const newSheetName = ref('')
const renameSheetVisible = ref(false)
const renameSheetName = ref('')
const renameSheetIndex = ref(-1)

// Pending changes for incremental save
const pendingChanges = ref([])

// Luckysheet instance initialized flag
const initialized = ref(false)

const sheetCount = computed(() => sheets.value.length)

// Load file info
const loadFileInfo = async () => {
  const path = route.query.path
  if (!path) {
    ElMessage.error('未指定文件路径')
    return
  }

  loading.value = true
  try {
    const res = await getExcelInfo({ path })
    if (res.code === 0) {
      fileName.value = res.data.filename
      filePath.value = res.data.path
      sheets.value = res.data.sheets
      // Load the first sheet
      if (sheets.value.length > 0) {
        await loadSheetData(0)
      }
    } else {
      ElMessage.error(res.message || '加载文件信息失败')
    }
  } catch (error) {
    console.error('Load file info error:', error)
    ElMessage.error('加载文件信息失败')
  } finally {
    loading.value = false
  }
}

// Convert row data to Luckysheet celldata format
const convertToLuckysheetData = (rows, sheetName, sheetIndex) => {
  const celldata = []
  const maxRows = rows.length
  const maxCols = rows.length > 0 ? Math.max(...rows.map(r => r ? r.length : 0)) : 0

  for (let r = 0; r < maxRows; r++) {
    const row = rows[r] || []
    for (let c = 0; c < maxCols; c++) {
      const value = row[c]
      if (value !== null && value !== undefined && value !== '') {
        celldata.push({
          r: r,
          c: c,
          v: typeof value === 'object' ? JSON.stringify(value) : String(value)
        })
      }
    }
  }

  return {
    name: sheetName,
    index: String(sheetIndex),
    celldata: celldata,
    row: maxRows,
    column: maxCols > 0 ? maxCols : 20,
    config: {
      columnlen: {}
    }
  }
}

// Load sheet data
const loadSheetData = async (sheetIndex) => {
  const sheet = sheets.value[sheetIndex]
  if (!sheet) return

  try {
    // Load all rows (up to 1000 for better editing experience)
    const res = await getExcelSheet({
      path: filePath.value,
      sheet: String(sheetIndex),
      offset: 0,
      limit: 1000,
      cols: 100
    })

    if (res.code === 0) {
      const sheetData = convertToLuckysheetData(res.data.rows, sheet.name, sheetIndex)

      if (!initialized.value) {
        // Initialize Luckysheet
        luckysheet.create({
          container: 'luckysheet',
          data: [sheetData],
          showinfobar: false,
          showsheetbar: true,
          showsheetbarConfig: {
            add: false,
            menu: false
          },
          showstatisticBar: true,
          enableAddRow: true,
          enableAddBackTop: true,
          userInfo: false,
          showConfigWindowResize: true,
          forceCalculation: false,
          hook: {
            cellUpdated: handleCellUpdated,
            rangeSelect: handleRangeSelect,
            sheetActivate: handleSheetActivate
          }
        })
        initialized.value = true
      } else {
        // Update existing sheet data
        luckysheet.setSheetData({ index: String(sheetIndex), value: sheetData })
        luckysheet.setSheetActive(String(sheetIndex))
      }

      currentSheetIndex.value = sheetIndex
    } else {
      ElMessage.error(res.message || '加载工作表失败')
    }
  } catch (error) {
    console.error('Load sheet data error:', error)
    ElMessage.error('加载工作表数据失败')
  }
}

// Handle cell updated event
const handleCellUpdated = (r, c, oldValue, newValue, isRefresh) => {
  if (!isRefresh && oldValue !== newValue) {
    hasUnsavedChanges.value = true
    pendingChanges.value.push({
      row: r,
      col: c,
      value: newValue
    })

    // Send edit to other collaborators via WebSocket
    if (excelSocket.isConnected() && filePath.value) {
      const cellRef = `${String.fromCharCode(65 + c)}${r + 1}` // e.g., 'A1'
      excelSocket.sendEdit(filePath.value, String(currentSheetIndex.value), cellRef, newValue)
    }
  }
}

// Handle range select event - send cursor position
const handleRangeSelect = (range) => {
  if (excelSocket.isConnected() && filePath.value && range) {
    const cellRef = range[0]?.row ? `${String.fromCharCode(65 + range[0].column[0])}${range[0].row[0] + 1}` : 'A1'
    excelSocket.sendCursor(filePath.value, String(currentSheetIndex.value), cellRef)
  }
}

// Handle sheet activate event
const handleSheetActivate = (index) => {
  currentSheetIndex.value = parseInt(index)
}

// Switch sheet
const handleSwitchSheet = async (index) => {
  if (index === currentSheetIndex.value) return

  // Save pending changes before switching
  if (pendingChanges.value.length > 0) {
    await autoSave()
  }

  await loadSheetData(index)
}

// Add sheet
const handleAddSheet = () => {
  newSheetName.value = ''
  addSheetVisible.value = true
}

const confirmAddSheet = async () => {
  if (!newSheetName.value.trim()) {
    ElMessage.warning('请输入工作表名称')
    return
  }

  try {
    const res = await addExcelSheet({
      path: filePath.value,
      name: newSheetName.value.trim()
    })

    if (res.code === 0) {
      ElMessage.success('添加工作表成功')
      addSheetVisible.value = false
      // Reload file info
      await loadFileInfo()
    } else {
      ElMessage.error(res.message || '添加工作表失败')
    }
  } catch (error) {
    console.error('Add sheet error:', error)
    ElMessage.error('添加工作表失败')
  }
}

// Delete sheet
const handleDeleteSheet = async () => {
  if (sheetCount.value <= 1) {
    ElMessage.warning('无法删除最后一个工作表')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除工作表 "${sheets.value[currentSheetIndex.value].name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await deleteExcelSheet({
      path: filePath.value,
      sheet: String(currentSheetIndex.value)
    })

    if (res.code === 0) {
      ElMessage.success('删除工作表成功')
      // Reload file info
      await loadFileInfo()
    } else {
      ElMessage.error(res.message || '删除工作表失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete sheet error:', error)
      ElMessage.error('删除工作表失败')
    }
  }
}

// Rename sheet
const handleRenameSheet = (index) => {
  renameSheetIndex.value = index
  renameSheetName.value = sheets.value[index].name
  renameSheetVisible.value = true
}

const confirmRenameSheet = async () => {
  if (!renameSheetName.value.trim()) {
    ElMessage.warning('请输入工作表名称')
    return
  }

  try {
    const res = await renameExcelSheet({
      path: filePath.value,
      sheet: String(renameSheetIndex.value),
      new_name: renameSheetName.value.trim()
    })

    if (res.code === 0) {
      ElMessage.success('重命名工作表成功')
      renameSheetVisible.value = false
      // Reload file info
      await loadFileInfo()
    } else {
      ElMessage.error(res.message || '重命名工作表失败')
    }
  } catch (error) {
    console.error('Rename sheet error:', error)
    ElMessage.error('重命名工作表失败')
  }
}

// Save
const handleSave = async () => {
  if (!pendingChanges.value.length && !hasUnsavedChanges.value) {
    ElMessage.info('没有需要保存的更改')
    return
  }

  saving.value = true
  try {
    // Get all data from Luckysheet
    const allData = luckysheet.getAllSheets()

    // Save each sheet
    for (let i = 0; i < allData.length; i++) {
      const sheet = allData[i]
      const rows = convertLuckysheetToRows(sheet)

      await saveExcel({
        path: filePath.value,
        sheet: String(i),
        data: { rows }
      })
    }

    ElMessage.success('保存成功')
    hasUnsavedChanges.value = false
    pendingChanges.value = []
    lastSaveTime.value = new Date()

    // Notify other collaborators via WebSocket
    if (excelSocket.isConnected() && filePath.value) {
      excelSocket.notifySaved(filePath.value)
    }
  } catch (error) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// Auto save (incremental)
const autoSave = async () => {
  if (pendingChanges.value.length === 0) return

  try {
    await saveExcel({
      path: filePath.value,
      sheet: String(currentSheetIndex.value),
      data: { cells: pendingChanges.value }
    })
    pendingChanges.value = []
  } catch (error) {
    console.error('Auto save error:', error)
  }
}

// Convert Luckysheet data back to rows
const convertLuckysheetToRows = (sheet) => {
  const celldata = sheet.celldata || []
  const rows = []
  let maxRow = 0
  let maxCol = 0

  // Find max row and col
  celldata.forEach(cell => {
    if (cell.r > maxRow) maxRow = cell.r
    if (cell.c > maxCol) maxCol = cell.c
  })

  // Create empty rows
  for (let r = 0; r <= maxRow; r++) {
    rows[r] = []
    for (let c = 0; c <= maxCol; c++) {
      rows[r][c] = null
    }
  }

  // Fill in values
  celldata.forEach(cell => {
    if (rows[cell.r]) {
      rows[cell.r][cell.c] = cell.v
    }
  })

  return rows
}

// Undo/Redo
const handleUndo = () => {
  luckysheet.undo()
}

const handleRedo = () => {
  luckysheet.redo()
}

// Format time
const formatTime = (date) => {
  if (!date) return ''
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Keyboard shortcuts
const handleKeydown = (e) => {
  // Ctrl+S to save
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    handleSave()
  }
  // Ctrl+Z to undo
  if (e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    handleUndo()
  }
  // Ctrl+Y to redo
  if (e.ctrlKey && e.key === 'y') {
    e.preventDefault()
    handleRedo()
  }
}

// Connect to WebSocket for collaboration
const connectWebSocket = () => {
  const path = route.query.path
  if (!path) return

  // Generate user name
  const userName = '用户' + Math.floor(Math.random() * 10000)

  excelSocket.connect(path, userName)

  excelSocket.on('joined', (data) => {
    myUserInfo.value = {
      name: data.user_id,
      color: data.color
    }
    collaboratorCount.value = collaborators.value.length + 1
  })

  excelSocket.on('user_joined', (data) => {
    collaborators.value.push({
      id: data.user_id,
      name: data.user_name,
      color: data.color
    })
    collaboratorCount.value = collaborators.value.length + 1
    ElMessage.info(`${data.user_name} 加入了编辑`)
  })

  excelSocket.on('user_left', (data) => {
    const idx = collaborators.value.findIndex(u => u.id === data.user_id)
    if (idx !== -1) {
      collaborators.value.splice(idx, 1)
    }
    collaboratorCount.value = collaborators.value.length + 1
    ElMessage.info(`${data.user_id} 离开了编辑`)
  })

  excelSocket.on('cell_update', (data) => {
    // Apply other user's edit to Luckysheet
    if (initialized.value && data.cell) {
      // Parse cell reference (e.g., 'A1' -> row 0, col 0)
      const colLetter = data.cell.match(/[A-Z]+/)[0]
      const rowNum = parseInt(data.cell.match(/\d+/)[0])
      const colNum = colLetter.charCodeAt(0) - 65 // A=0, B=1...

      // Update cell value (row-1 because cell reference is 1-based)
      try {
        luckysheet.setCellValue(rowNum - 1, colNum, data.value)
      } catch (e) {
        console.warn('Failed to sync cell update:', e)
      }
    }
  })

  excelSocket.on('file_saved', (data) => {
    ElMessage.info(`${data.user_id} 保存了文档`)
    lastSaveTime.value = new Date()
  })

  excelSocket.on('error', (data) => {
    console.error('WebSocket error:', data.message)
  })
}

// Watch for route changes
watch(() => route.query.path, (newPath, oldPath) => {
  if (newPath && newPath !== oldPath) {
    initialized.value = false
    // Disconnect old WebSocket connection
    excelSocket.disconnect()
    loadFileInfo()
    // Reconnect WebSocket for new file
    setTimeout(() => connectWebSocket(), 500)
  }
})

onMounted(() => {
  loadFileInfo()
  window.addEventListener('keydown', handleKeydown)
  // Connect WebSocket after a short delay
  setTimeout(() => connectWebSocket(), 1000)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  // Disconnect WebSocket
  excelSocket.disconnect()
  // Destroy Luckysheet instance
  if (initialized.value) {
    try {
      luckysheet.destroy()
    } catch (e) {
      console.error('Destroy luckysheet error:', e)
    }
  }
})
</script>

<style scoped>
.excel-editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color, #f5f7fa);
}

.excel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--card-bg, #ffffff);
  border-bottom: 1px solid var(--border-color, #e4e7ed);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-center {
  display: flex;
  align-items: center;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #303133);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collaborator-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-color-secondary, #909399);
  font-size: 14px;
}

.excel-main {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.luckysheet-container {
  width: 100%;
  height: 100%;
}

.excel-statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  background: var(--card-bg, #ffffff);
  border-top: 1px solid var(--border-color, #e4e7ed);
}

.sheet-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sheet-tab {
  cursor: pointer;
  user-select: none;
}

.sheet-tab:hover {
  opacity: 0.8;
}

.save-status {
  font-size: 12px;
  color: var(--text-color-secondary, #909399);
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>