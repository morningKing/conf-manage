<template>
  <div class="file-upload">
    <!-- 单文件模式 -->
    <div v-if="mode === 'single'">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        :limit="1"
      >
        <el-button type="primary" size="small">
          <el-icon><UploadFilled /></el-icon>
          选择文件
        </el-button>
      </el-upload>

      <div v-if="fileName" class="single-file-info">
        <el-icon class="file-icon"><Document /></el-icon>
        <span class="file-name">{{ fileName }}</span>
        <el-button
          link
          type="danger"
          @click="clearSingleFile"
          :icon="Delete"
          size="small"
        />
      </div>
    </div>

    <!-- 多文件模式 -->
    <div v-else>
      <div
        class="upload-area"
        :class="{ 'is-dragover': isDragOver }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />

        <div class="upload-icon">
          <el-icon :size="48"><upload-filled /></el-icon>
        </div>

        <div class="upload-text">
          <p class="main-text">点击或拖拽文件到此处上传</p>
          <p class="sub-text">支持多文件上传</p>
        </div>
      </div>

      <div v-if="fileList.length > 0" class="file-list">
        <div class="list-header">
          <span>已选择文件 ({{ fileList.length }})</span>
          <el-button link type="danger" @click="clearFiles" size="small">清空</el-button>
        </div>

        <div class="list-items">
          <div
            v-for="(file, index) in fileList"
            :key="index"
            class="file-item"
          >
            <el-icon class="file-icon"><document /></el-icon>
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <el-button
              link
              type="danger"
              @click="removeFile(index)"
              :icon="Delete"
              size="small"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { UploadFilled, Document, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const props = defineProps({
  modelValue: {
    type: [String, Array],
    default: ''
  },
  mode: {
    type: String,
    default: 'multiple', // 'single' 或 'multiple'
    validator: (value) => ['single', 'multiple'].includes(value)
  },
  maxSize: {
    type: Number,
    default: null // 最大文件大小（字节）
  },
  allowedExtensions: {
    type: Array,
    default: null // 允许的文件扩展名数组
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const uploadRef = ref(null)

// 多文件模式状态
const fileList = ref([])
const isDragOver = ref(false)

// 单文件模式状态
const fileName = ref('')
const filePath = ref('')

// 初始化状态
const initValue = () => {
  if (props.mode === 'single') {
    // 单文件模式：modelValue是文件路径字符串
    filePath.value = props.modelValue || ''
    // 从路径中提取文件名（如果有）
    if (filePath.value && typeof filePath.value === 'string') {
      fileName.value = filePath.value.split(/[\\/]/).pop() || ''
    } else {
      fileName.value = ''
    }
  } else {
    // 多文件模式：modelValue是文件数组
    fileList.value = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  }
}

// 监听外部值变化
watch(() => props.modelValue, () => {
  initValue()
}, { immediate: true })

// ========== 单文件模式 ==========

const handleFileChange = async (uploadFile) => {
  const file = uploadFile.raw

  // 校验文件大小
  if (props.maxSize && file.size > props.maxSize) {
    ElMessage.error(`文件大小超过限制: ${(props.maxSize / 1024 / 1024).toFixed(2)}MB`)
    return false
  }

  // 校验文件扩展名
  if (props.allowedExtensions && props.allowedExtensions.length > 0) {
    const ext = file.name.split('.').pop().toLowerCase()
    if (!props.allowedExtensions.includes(ext)) {
      ElMessage.error(`文件类型不支持，仅支持: ${props.allowedExtensions.join(', ')}`)
      return false
    }
  }

  // 上传文件到临时目录
  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await request.post('/upload/temp', formData)

    if (res.code === 0) {
      fileName.value = file.name
      filePath.value = res.data.file_path
      emit('update:modelValue', filePath.value)
      ElMessage.success('文件上传成功')
      return true
    } else {
      ElMessage.error(res.message || '上传失败')
      return false
    }
  } catch (err) {
    ElMessage.error('上传失败: ' + (err.response?.data?.message || err.message))
    return false
  }
}

const clearSingleFile = () => {
  fileName.value = ''
  filePath.value = ''
  emit('update:modelValue', '')
  uploadRef.value?.clearFiles()
}

// ========== 多文件模式 ==========

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFiles(files)
  event.target.value = '' // 清空input以允许重复选择同一文件
}

const handleDrop = (event) => {
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  addFiles(files)
}

const addFiles = (files) => {
  // 校验文件大小和扩展名
  const validFiles = files.filter(file => {
    // 校验文件大小
    if (props.maxSize && file.size > props.maxSize) {
      ElMessage.warning(`文件 ${file.name} 大小超过限制，已跳过`)
      return false
    }

    // 校验文件扩展名
    if (props.allowedExtensions && props.allowedExtensions.length > 0) {
      const ext = file.name.split('.').pop().toLowerCase()
      if (!props.allowedExtensions.includes(ext)) {
        ElMessage.warning(`文件 ${file.name} 类型不支持，已跳过`)
        return false
      }
    }

    return true
  })

  fileList.value.push(...validFiles)
  emit('update:modelValue', fileList.value)

  if (validFiles.length > 0) {
    ElMessage.success(`成功添加 ${validFiles.length} 个文件`)
  }
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
  emit('update:modelValue', fileList.value)
}

const clearFiles = () => {
  fileList.value = []
  emit('update:modelValue', fileList.value)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.file-upload {
  width: 100%;
}

/* 单文件模式样式 */
.single-file-info {
  display: flex;
  align-items: center;
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.single-file-info .file-icon {
  color: #409eff;
  margin-right: 10px;
  font-size: 18px;
}

.single-file-info .file-name {
  flex: 1;
  color: #606266;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}

/* 多文件模式样式 */
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.upload-area.is-dragover {
  border-color: #409eff;
  background-color: #ecf5ff;
  transform: scale(1.02);
}

.upload-icon {
  color: #909399;
  margin-bottom: 16px;
}

.upload-area:hover .upload-icon {
  color: #409eff;
}

.upload-text .main-text {
  font-size: 16px;
  color: #606266;
  margin: 0 0 8px 0;
}

.upload-text .sub-text {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.file-list {
  margin-top: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.list-items {
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.file-item:hover {
  background-color: #f5f7fa;
}

.file-icon {
  color: #409eff;
  margin-right: 10px;
  font-size: 20px;
}

.file-name {
  flex: 1;
  color: #606266;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}

.file-size {
  color: #909399;
  font-size: 12px;
  margin-right: 10px;
  min-width: 60px;
  text-align: right;
}
</style>