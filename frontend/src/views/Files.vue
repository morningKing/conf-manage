<template>
  <div class="files-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 常规文件管理 -->
        <el-tab-pane label="常规文件" name="regular">
          <div class="tab-header">
            <div>
              <el-button @click="handleCreateFolder">
                <el-icon><FolderAdd /></el-icon>
                新建文件夹
              </el-button>
              <el-upload
                :action="uploadUrl"
                :data="{ path: currentPath }"
                :on-success="handleUploadSuccess"
                :show-file-list="false"
                style="display: inline-block; margin-left: 10px"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  上传文件
                </el-button>
              </el-upload>
            </div>
          </div>

          <el-breadcrumb separator="/" style="margin: 20px 0">
            <el-breadcrumb-item @click="navigateTo('')" style="cursor: pointer">
              根目录
            </el-breadcrumb-item>
            <el-breadcrumb-item
              v-for="(part, index) in pathParts"
              :key="index"
              @click="navigateTo(pathParts.slice(0, index + 1).join('/'))"
              style="cursor: pointer"
            >
              {{ part }}
            </el-breadcrumb-item>
          </el-breadcrumb>

          <el-table :data="files" stripe>
            <el-table-column label="名称" min-width="300">
              <template #default="{ row }">
                <div
                  style="display: flex; align-items: center; cursor: pointer"
                  @click="handleItemClick(row)"
                >
                  <el-icon v-if="row.is_dir" style="margin-right: 5px; color: #409eff">
                    <Folder />
                  </el-icon>
                  <el-icon v-else style="margin-right: 5px; color: #67c23a">
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
                <el-button
                  v-if="!row.is_dir && canPreview(row.name)"
                  size="small"
                  type="success"
                  @click.stop="handlePreview(row)"
                >
                  预览
                </el-button>
                <el-button
                  v-if="!row.is_dir"
                  size="small"
                  type="primary"
                  @click.stop="handleDownload(row)"
                >
                  下载
                </el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(row)">
                  删除
                </el-button>
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
              style="width: 400px"
            >
              <el-option
                v-for="exec in executions"
                :key="exec.id"
                :label="`#${exec.id} - ${exec.script_name} (${formatExecutionTime(exec.created_at)})`"
                :value="exec.id"
              >
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>#{{ exec.id }} - {{ exec.script_name }}</span>
                  <el-tag :type="getStatusType(exec.status)" size="small" style="margin-left: 10px">
                    {{ getStatusText(exec.status) }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button
              :icon="Refresh"
              @click="loadExecutions"
              style="margin-left: 10px"
            >
              刷新列表
            </el-button>
          </div>

          <div v-if="selectedExecution" style="margin-top: 20px">
            <ExecutionFiles :execution-id="selectedExecution" />
          </div>
          <el-empty v-else description="请选择一个执行记录查看文件" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新建文件夹对话框 -->
    <el-dialog v-model="folderVisible" title="新建文件夹" width="400px">
      <el-input v-model="folderName" placeholder="请输入文件夹名称" />
      <template #footer>
        <el-button @click="folderVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateFolderConfirm">创建</el-button>
      </template>
    </el-dialog>

    <!-- Excel预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="`预览: ${currentPreviewFile?.name || ''}`"
      width="90%"
      top="5vh"
    >
      <div v-loading="previewLoading" style="min-height: 200px">
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
              style="width: 100%"
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
        <div v-else-if="previewData?.type === 'text' || previewData?.type === 'json'" style="max-height: 600px; overflow: auto">
          <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
            <el-switch
              v-if="isEditable(currentPreviewFile?.name)"
              v-model="editMode"
              active-text="编辑模式"
              inactive-text="预览模式"
            />
            <div v-if="previewData.encoding" style="color: #909399; font-size: 12px;">
              编码: {{ previewData.encoding }}
            </div>
          </div>
          <el-input
            v-if="editMode"
            v-model="editContent"
            type="textarea"
            :rows="25"
            style="font-family: 'Courier New', monospace;"
          />
          <pre v-else style="background: #f5f5f5; padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace; line-height: 1.6; margin: 0;">{{ previewData.content }}</pre>
        </div>

        <!-- 图片预览 -->
        <div v-else-if="previewData?.type === 'image'" style="text-align: center; max-height: 600px; overflow: auto">
          <img
            :src="`data:${previewData.mime_type};base64,${previewData.content}`"
            style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;"
            alt="预览图片"
          />
        </div>

        <!-- PDF预览 -->
        <div v-else-if="previewData?.type === 'pdf'" style="height: 600px">
          <iframe
            :src="`data:application/pdf;base64,${previewData.content}`"
            style="width: 100%; height: 100%; border: none"
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

const handleTabChange = (tab) => {
  if (tab === 'execution') {
    loadExecutions()
  }
}

const handleExecutionChange = () => {
  // 执行空间改变时，ExecutionFiles 组件会自动重新加载
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
.files-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
