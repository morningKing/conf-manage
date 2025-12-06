<template>
  <div class="execution-files">
    <div class="files-header">
      <div class="header-info">
        <el-icon><Folder /></el-icon>
        <span class="space-id">执行空间 #{{ executionId }}</span>
        <el-tag v-if="fileData" size="small" type="info">
          {{ fileData.files.length }} 个文件
        </el-tag>
        <el-tag v-if="fileData" size="small" type="success">
          {{ formatSize(fileData.total_size) }}
        </el-tag>
      </div>
      <el-button
        size="small"
        :icon="Refresh"
        @click="loadFiles"
        :loading="loading"
      >
        刷新
      </el-button>
    </div>

    <div v-loading="loading" class="files-content">
      <el-empty v-if="!loading && (!fileData || fileData.files.length === 0)"
                description="执行空间为空" />

      <el-table v-else :data="fileData?.files" stripe style="width: 100%">
        <el-table-column prop="path" label="文件路径" min-width="200">
          <template #default="{ row }">
            <div class="file-path">
              <el-icon v-if="row.is_text"><Document /></el-icon>
              <el-icon v-else><Files /></el-icon>
              <span>{{ row.path }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="size" label="大小" width="100" align="right">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>

        <el-table-column prop="modified_time" label="修改时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.modified_time) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button
              v-if="canPreview(row.path)"
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
      </el-table>
    </div>

    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="`预览: ${currentFile?.name || currentFile?.path}`"
      width="80%"
      top="5vh"
    >
      <div v-loading="previewLoading" class="preview-content">
        <!-- 文本内容 -->
        <pre v-if="previewType === 'text' && fileContent" class="file-preview">{{ fileContent }}</pre>

        <!-- 图片内容 -->
        <div v-else-if="previewType === 'image' && fileContent" style="text-align: center">
          <img
            :src="fileContent"
            style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;"
            alt="预览图片"
          />
        </div>

        <el-empty v-else description="无法加载文件内容" />
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadFile(currentFile)">
          下载文件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, Refresh, Document, Files } from '@element-plus/icons-vue'
import request from '../api/request'

const props = defineProps({
  executionId: {
    type: Number,
    required: true
  }
})

const loading = ref(false)
const fileData = ref(null)
const previewVisible = ref(false)
const previewLoading = ref(false)
const currentFile = ref(null)
const fileContent = ref('')
const previewType = ref('text')

const canPreview = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  const supportedExts = [
    // 文本文件
    'txt', 'md', 'log', 'py', 'js', 'json', 'xml', 'html', 'css', 'yaml', 'yml', 'ini', 'conf', 'sh', 'bat', 'csv', 'sql',
    // 图片文件
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'
  ]
  return supportedExts.includes(ext)
}

const getFileExtension = (filename) => {
  return filename.toLowerCase().split('.').pop()
}

const isImageFile = (filename) => {
  const ext = getFileExtension(filename)
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'].includes(ext)
}

const loadFiles = async () => {
  loading.value = true
  try {
    const res = await request.get(`/executions/${props.executionId}/files`)
    fileData.value = res.data
  } catch (error) {
    console.error('Load files error:', error)
    ElMessage.error('加载文件列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const previewFile = async (file) => {
  currentFile.value = file
  previewVisible.value = true
  previewLoading.value = true
  fileContent.value = ''

  try {
    // 判断文件类型
    if (isImageFile(file.path)) {
      // 图片文件 - 直接使用下载URL作为图片源
      const apiUrl = import.meta.env.VITE_API_URL || '/api'
      fileContent.value = `${apiUrl}/executions/${props.executionId}/files/${encodeURIComponent(file.path)}`
      previewType.value = 'image'
    } else {
      // 文本文件
      const res = await request.get(
        `/executions/${props.executionId}/files/${encodeURIComponent(file.path)}`
      )
      fileContent.value = res.data.content
      previewType.value = 'text'
    }
  } catch (error) {
    ElMessage.error('加载文件内容失败: ' + error.message)
  } finally {
    previewLoading.value = false
  }
}

const downloadFile = (file) => {
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  const url = `${apiUrl}/executions/${props.executionId}/files/${encodeURIComponent(file.path)}?download=true`
  window.open(url, '_blank')
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

const formatTime = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadFiles()
})

defineExpose({
  loadFiles
})
</script>

<style scoped>
.execution-files {
  width: 100%;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px 4px 0 0;
  border: 1px solid #dcdfe6;
  border-bottom: none;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.header-info .el-icon {
  font-size: 18px;
  color: #409eff;
}

.space-id {
  font-weight: 600;
  color: #303133;
}

.files-content {
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  min-height: 200px;
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-path .el-icon {
  font-size: 16px;
  color: #909399;
}

.preview-content {
  max-height: 70vh;
  overflow: auto;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 16px;
}

.file-preview {
  margin: 0;
  padding: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 滚动条样式 */
.preview-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.preview-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
