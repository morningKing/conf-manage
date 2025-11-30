<template>
  <div class="file-upload">
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
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled, Document, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const fileList = ref([...props.modelValue])
const isDragOver = ref(false)

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
  fileList.value.push(...files)
  emit('update:modelValue', fileList.value)
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
