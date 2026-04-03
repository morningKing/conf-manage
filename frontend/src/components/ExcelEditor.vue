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
import { getExcelFile, saveExcelFile } from '../api'

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

.sheet-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  height: 100vh;
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