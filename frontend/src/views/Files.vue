<template>
  <div class="files-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">文件管理</span>
      </div>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 常规文件管理 -->
        <el-tab-pane label="常规文件" name="regular">
          <div class="tab-header">
            <div>
              <GlassButton label="新建文件夹" type="secondary" size="small" @click="handleCreateFolder">
                <template #icon><FolderAdd /></template>
              </GlassButton>
              <el-upload
                :action="uploadUrl"
                :data="{ path: currentPath }"
                :on-success="handleUploadSuccess"
                :show-file-list="false"
                class="inline-ml10"
              >
                <GlassButton label="上传文件" type="primary" size="small">
                  <template #icon><Upload /></template>
                </GlassButton>
              </el-upload>
            </div>
          </div>

          <el-breadcrumb separator="/" class="breadcrumb-bar">
            <el-breadcrumb-item @click="navigateTo('')" class="cursor-pointer">
              根目录
            </el-breadcrumb-item>
            <el-breadcrumb-item
              v-for="(part, index) in pathParts"
              :key="index"
              @click="navigateTo(pathParts.slice(0, index + 1).join('/'))"
              class="cursor-pointer"
            >
              {{ part }}
            </el-breadcrumb-item>
          </el-breadcrumb>

          <el-table :data="files" stripe>
            <el-table-column label="名称" min-width="300">
              <template #default="{ row }">
                <div
                  class="file-name-cell"
                  @click="handleItemClick(row)"
                >
                  <el-icon v-if="row.is_dir" class="row-icon-dir">
                    <Folder />
                  </el-icon>
                  <el-icon v-else class="row-icon-file">
                    <Document />
                  </el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="150">
              <template #default="{ row }">
                {{ row.is_dir ? '-' : formatSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="modified_at" label="修改时间" width="200">
              <template #default="{ row }">
                {{ formatTime(row.modified_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <GlassButton
                  v-if="!row.is_dir && canPreview(row.name)"
                  label="预览"
                  type="success"
                  size="small"
                  @click.stop="handlePreview(row)"
                />
                <GlassButton
                  v-if="!row.is_dir"
                  label="下载"
                  type="primary"
                  size="small"
                  @click.stop="handleDownload(row)"
                />
                <GlassButton label="删除" type="danger" size="small" @click.stop="handleDelete(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 执行空间文件 -->
        <el-tab-pane label="执行空间" name="execution">
          <div class="tab-header">
            <el-select
              v-model="selectedExecution"
              placeholder="选择执行记录"
              filterable
              @change="handleExecutionChange"
              class="w-select"
            >
              <el-option
                v-for="exec in executions"
                :key="exec.id"
                :label="`#${exec.id} - ${exec.script_name} (${formatExecutionTime(exec.created_at)})`"
                :value="exec.id"
              >
                <div class="exec-item-header">
                  <span>#{{ exec.id }} - {{ exec.script_name }}</span>
                  <el-tag :type="getStatusType(exec.status)" size="small" class="tag-ml10">
                    {{ getStatusText(exec.status) }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button
              :icon="Refresh"
              @click="refreshExecutionFiles"
              class="tag-ml10"
            >
              刷新文件
            </el-button>
          </div>

          <div v-if="selectedExecution" class="detail-block">
            <ExecutionFiles ref="executionFilesRef" :execution-id="selectedExecution" />
          </div>
          <el-empty v-else description="请选择一个执行记录查看文件" />
        </el-tab-pane>

        <!-- 工作流执行空间 -->
        <el-tab-pane label="工作流执行空间" name="workflow">
          <div class="tab-header">
            <el-select
              v-model="selectedWorkflowExecution"
              placeholder="选择工作流执行记录"
              filterable
              @change="handleWorkflowExecutionChange"
              class="w-select"
            >
              <el-option
                v-for="exec in workflowExecutions"
                :key="exec.id"
                :label="`#${exec.id} - ${exec.workflow?.name || '未知工作流'} (${formatExecutionTime(exec.created_at)})`"
                :value="exec.id"
              >
                <div class="exec-item-header">
                  <span>#{{ exec.id }} - {{ exec.workflow?.name || '未知工作流' }}</span>
                  <el-tag :type="getStatusType(exec.status)" size="small" class="tag-ml10">
                    {{ getStatusText(exec.status) }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button
              :icon="Refresh"
              @click="refreshWorkflowExecutionFiles"
              class="tag-ml10"
            >
              刷新文件
            </el-button>
          </div>

          <div v-if="selectedWorkflowExecution" class="detail-block">
            <ExecutionFiles ref="workflowExecutionFilesRef" :workflow-execution-id="selectedWorkflowExecution" />
          </div>
          <el-empty v-else description="请选择一个工作流执行记录查看文件" />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新建文件夹对话框 -->
    <el-dialog v-model="folderVisible" title="新建文件夹" width="400px">
      <el-input v-model="folderName" placeholder="请输入文件夹名称" />
      <template #footer>
        <GlassButton label="取消" type="secondary" @click="folderVisible = false" />
        <GlassButton label="创建" type="primary" @click="handleCreateFolderConfirm" />
      </template>
    </el-dialog>

    <!-- Excel预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="`预览: ${currentPreviewFile?.name || ''}`"
      width="90%"
      top="5vh"
    >
      <div v-loading="previewLoading" class="preview-loading">
        <!-- Excel预览 -->
        <el-tabs v-if="previewData?.type === 'excel' && previewData.sheets" v-model="activeSheet" type="border-card">
          <el-tab-pane
            v-for="(sheet, index) in previewData.sheets"
            :key="index"
            :label="sheet.name"
            :name="String(index)"
          >
            <el-table
              :data="sheet.rows"
              stripe
              border
              class="code-editor-full"
              max-height="600"
            >
              <el-table-column
                v-for="(col, colIndex) in getColumnCount(sheet.rows)"
                :key="colIndex"
                :label="getColumnLabel(colIndex)"
                :prop="String(colIndex)"
                min-width="120"
              >
                <template #default="{ row }">
                  {{ row[colIndex] }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>

        <!-- 文本预览/编辑 -->
        <div v-else-if="previewData?.type === 'text' || previewData?.type === 'json'" class="preview-scroll">
          <div class="preview-toolbar">
            <el-switch
              v-if="isEditable(currentPreviewFile?.name)"
              v-model="editMode"
              active-text="编辑模式"
              inactive-text="预览模式"
            />
            <div v-if="previewData.encoding" class="preview-encoding">
              编码: {{ previewData.encoding }}
            </div>
          </div>
          <el-input
            v-if="editMode"
            v-model="editContent"
            type="textarea"
            :rows="25"
            class="preview-code"
          />
          <pre v-else class="preview-pre">{{ previewData.content }}</pre>
        </div>

        <!-- 图片预览 -->
        <div v-else-if="previewData?.type === 'image'" class="preview-scroll preview-center">
          <img
            :src="`data:${previewData.mime_type};base64,${previewData.content}`"
            class="preview-image"
            alt="预览图片"
          />
        </div>

        <!-- PDF预览 -->
        <div v-else-if="previewData?.type === 'pdf'" class="preview-pdf">
          <iframe
            :src="`data:application/pdf;base64,${previewData.content}`"
            class="preview-iframe"
          ></iframe>
        </div>

        <el-empty v-else-if="!previewLoading" description="无法加载预览数据" />
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button
          v-if="editMode"
          type="warning"
          @click="handleSaveFile"
          :loading="saving"
        >
          保存
        </el-button>
        <el-button v-else type="primary" @click="handleDownload(currentPreviewFile)">
          下载文件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderAdd, Upload, Folder, Document, Refresh } from '@element-plus/icons-vue'
import { getFiles, deleteFile, createFolder, downloadFile, getExecutions } from '../api'
import ExecutionFiles from '../components/ExecutionFiles.vue'
import GlassButton from '../components/GlassButton.vue'
import request from '../api/request'

const activeTab = ref('regular')
const files = ref([])
const currentPath = ref('')
const uploadUrl = ref('/api/files/upload')
const folderVisible = ref(false)
const folderName = ref('')

// 执行空间相关
const executions = ref([])
const selectedExecution = ref(null)
const executionFilesRef = ref(null)

// 工作流执行空间相关
const workflowExecutions = ref([])
const selectedWorkflowExecution = ref(null)
const workflowExecutionFilesRef = ref(null)

// Excel预览相关
const previewVisible = ref(false)
const previewLoading = ref(false)
const currentPreviewFile = ref(null)
const previewData = ref(null)
const activeSheet = ref('0')

// 编辑相关
const editMode = ref(false)
const editContent = ref('')
const saving = ref(false)

const pathParts = computed(() => {
  return currentPath.value ? currentPath.value.split('/').filter(Boolean) : []
})

const loadFiles = async (path = '') => {
  try {
    const res = await getFiles(path)
    files.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadExecutions = async () => {
  try {
    const res = await getExecutions({ page: 1, per_page: 100 })
    executions.value = res.data.items
  } catch (error) {
    console.error(error)
    ElMessage.error('加载执行列表失败')
  }
}

const loadWorkflowExecutions = async () => {
  try {
    const res = await request.get('/workflow-executions', {
      params: { page: 1, per_page: 100 }
    })
    workflowExecutions.value = res.data.items
  } catch (error) {
    console.error(error)
    ElMessage.error('加载工作流执行列表失败')
  }
}

const handleTabChange = (tab) => {
  if (tab === 'execution') {
    loadExecutions()
  } else if (tab === 'workflow') {
    loadWorkflowExecutions()
  }
}

const handleExecutionChange = () => {
  // 执行空间改变时，ExecutionFiles 组件会自动重新加载
}

const refreshExecutionFiles = () => {
  if (executionFilesRef.value && selectedExecution.value) {
    executionFilesRef.value.loadFiles()
  } else if (!selectedExecution.value) {
    ElMessage.warning('请先选择一个执行记录')
  }
}

const handleWorkflowExecutionChange = () => {
  // 工作流执行空间改变时，ExecutionFiles 组件会自动重新加载
}

const refreshWorkflowExecutionFiles = () => {
  if (workflowExecutionFilesRef.value && selectedWorkflowExecution.value) {
    workflowExecutionFilesRef.value.loadFiles()
  } else if (!selectedWorkflowExecution.value) {
    ElMessage.warning('请先选择一个工作流执行记录')
  }
}

const navigateTo = (path) => {
  currentPath.value = path
  loadFiles(path)
}

const handleItemClick = (row) => {
  if (row.is_dir) {
    navigateTo(row.path)
  }
}

const handleDownload = (row) => {
  window.open(downloadFile(row.path), '_blank')
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除${row.is_dir ? '文件夹' : '文件'} "${row.name}" 吗?`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteFile(row.path)
    ElMessage.success('删除成功')
    loadFiles(currentPath.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleCreateFolder = () => {
  folderName.value = ''
  folderVisible.value = true
}

const handleCreateFolderConfirm = async () => {
  if (!folderName.value.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  try {
    await createFolder({
      path: currentPath.value,
      name: folderName.value
    })
    ElMessage.success('创建成功')
    folderVisible.value = false
    loadFiles(currentPath.value)
  } catch (error) {
    console.error(error)
  }
}

const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  loadFiles(currentPath.value)
}

const canPreview = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  const supportedExts = [
    // 文本文件
    'txt', 'md', 'log', 'py', 'js', 'json', 'xml', 'html', 'css', 'yaml', 'yml', 'ini', 'conf', 'sh', 'bat', 'csv',
    // 图片文件
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico',
    // Excel文件
    'xlsx', 'xls',
    // PDF文件
    'pdf'
  ]
  return supportedExts.includes(ext)
}

const isExcelFile = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  return ext === 'xlsx' || ext === 'xls'
}

const isEditable = (filename) => {
  if (!filename) return false
  const ext = filename.toLowerCase().split('.').pop()
  const editableExts = [
    'txt', 'md', 'log', 'py', 'js', 'json', 'xml', 'html',
    'css', 'yaml', 'yml', 'ini', 'conf', 'sh', 'bat', 'csv', 'sql'
  ]
  return editableExts.includes(ext)
}

const handlePreview = async (row) => {
  // Excel files open in Excel editor instead of preview dialog
  if (isExcelFile(row.name)) {
    window.open(`/excel-editor?path=${encodeURIComponent(row.path)}`, '_blank')
    return
  }

  currentPreviewFile.value = row
  previewVisible.value = true
  previewLoading.value = true
  previewData.value = null
  activeSheet.value = '0'
  editMode.value = false
  editContent.value = ''

  try {
    const res = await request.get(`/files/preview?path=${encodeURIComponent(row.path)}`)
    previewData.value = res.data
    // 如果是可编辑的文本文件，初始化编辑内容
    if (res.data.type === 'text' || res.data.type === 'json') {
      editContent.value = res.data.content
    }
  } catch (error) {
    console.error('Preview error:', error)
    ElMessage.error('预览失败: ' + (error.message || '未知错误'))
  } finally {
    previewLoading.value = false
  }
}

const handleSaveFile = async () => {
  if (!currentPreviewFile.value) {
    ElMessage.error('未选择文件')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要保存对文件的修改吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    saving.value = true

    await request.put('/files/update', {
      path: currentPreviewFile.value.path,
      content: editContent.value
    })

    ElMessage.success('文件保存成功')

    // 更新预览数据
    previewData.value.content = editContent.value

    // 切换回预览模式
    editMode.value = false

    // 刷新文件列表
    loadFiles(currentPath.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Save error:', error)
      ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

const getColumnCount = (rows) => {
  if (!rows || rows.length === 0) return 0
  return Math.max(...rows.map(row => row.length))
}

const getColumnLabel = (index) => {
  // Convert index to Excel column label (A, B, C, ..., Z, AA, AB, ...)
  let label = ''
  let num = index
  while (num >= 0) {
    label = String.fromCharCode(65 + (num % 26)) + label
    num = Math.floor(num / 26) - 1
    if (num < 0) break
  }
  return label
}

const formatSize = (size) => {
  if (size < 1024) return `${size}B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)}KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)}MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)}GB`
}

const formatTime = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

const formatExecutionTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待',
    running: '运行',
    success: '成功',
    failed: '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
/* —— 由 inline style 收敛而来 —— */
.inline-ml10 { display: inline-block; margin-left: 10px; }
.breadcrumb-bar { margin: 12px 0; }
.cursor-pointer { cursor: pointer; }
.file-name-cell { display: flex; align-items: center; cursor: pointer; }
.row-icon-dir { margin-right: 5px; color: var(--el-color-primary); }
.row-icon-file { margin-right: 5px; color: var(--el-color-success); }
.w-select { width: 280px; }
.exec-item-header { display: flex; justify-content: space-between; align-items: center; }
.tag-ml10 { margin-left: 10px; }
.detail-block { margin-top: 12px; }
.preview-loading { min-height: 160px; }
.code-editor-full { width: 100%; }
.preview-scroll { max-height: 600px; overflow: auto; }
.preview-center { text-align: center; }
.preview-toolbar { margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.preview-encoding { color: var(--el-text-color-secondary); font-size: 12px; }
.preview-code { font-family: 'Courier New', monospace; }
.preview-pre { background: var(--el-fill-color-darker); padding: 12px; border-radius: 4px; font-family: 'Courier New', monospace; line-height: 1.6; margin: 0; }
.preview-image { max-width: 100%; height: auto; border: 1px solid var(--el-border-color); border-radius: 4px; }
.preview-pdf { height: 600px; }
.preview-iframe { width: 100%; height: 100%; border: none; }

.files-container {
  padding: 12px;
}


.tab-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
