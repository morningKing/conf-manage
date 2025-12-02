<template>
  <div class="parameter-config">
    <div class="header">
      <el-text class="title">参数配置</el-text>
      <el-tooltip content="脚本执行时可通过 os.getenv('参数名') 获取参数值" placement="top">
        <el-icon><QuestionFilled /></el-icon>
      </el-tooltip>
    </div>

    <div class="parameters-list">
      <el-empty v-if="!localParameters || localParameters.length === 0" description="暂无参数，点击下方按钮添加" :image-size="60" />

      <div v-for="(param, index) in localParameters" :key="index" class="parameter-item">
        <el-row :gutter="10">
          <el-col :span="5">
            <el-input
              v-model="param.key"
              placeholder="参数名（如：API_KEY）"
              size="small"
              @input="emitChange"
            />
          </el-col>
          <el-col :span="7">
            <el-input
              v-model="param.description"
              placeholder="参数说明"
              size="small"
              @input="emitChange"
            />
          </el-col>
          <el-col :span="5">
            <el-input
              v-model="param.default_value"
              placeholder="默认值（可选）"
              size="small"
              @input="emitChange"
            />
          </el-col>
          <el-col :span="4">
            <el-checkbox v-model="param.required" @change="emitChange">必填</el-checkbox>
          </el-col>
          <el-col :span="3">
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              @click="removeParameter(index)"
            />
          </el-col>
        </el-row>
      </div>
    </div>

    <el-button
      type="primary"
      :icon="Plus"
      size="small"
      @click="addParameter"
      style="margin-top: 10px;"
    >
      添加参数
    </el-button>

    <el-collapse v-model="activeCollapse" style="margin-top: 15px;">
      <el-collapse-item name="usage" title="使用说明">
        <div class="usage-hint">
          <div class="code-example">
            <el-text tag="pre" size="small">
# Python 脚本中获取参数
import os
api_key = os.getenv('API_KEY', '默认值')
timeout = os.getenv('TIMEOUT', '30')
            </el-text>
          </div>
          <div class="code-example">
            <el-text tag="pre" size="small">
// JavaScript 脚本中获取参数
const apiKey = process.env.API_KEY || '默认值';
const timeout = process.env.TIMEOUT || '30';
            </el-text>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus, Delete, QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

// 本地参数列表
const localParameters = ref([])

// 折叠面板状态（默认收起）
const activeCollapse = ref([])

// 初始化参数列表
const initParameters = () => {
  if (props.modelValue) {
    try {
      const params = JSON.parse(props.modelValue)
      localParameters.value = Array.isArray(params) ? params : []
    } catch (e) {
      localParameters.value = []
    }
  } else {
    localParameters.value = []
  }
}

// 监听外部值变化
watch(() => props.modelValue, () => {
  initParameters()
}, { immediate: true })

// 添加参数
const addParameter = () => {
  localParameters.value.push({
    key: '',
    description: '',
    default_value: '',
    required: false
  })
  emitChange()
}

// 删除参数
const removeParameter = (index) => {
  localParameters.value.splice(index, 1)
  emitChange()
}

// 发送变化
const emitChange = () => {
  emit('update:modelValue', JSON.stringify(localParameters.value))
}
</script>

<style scoped>
.parameter-config {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.title {
  font-size: 14px;
  font-weight: bold;
}

.parameters-list {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 10px;
  padding-right: 5px;
}

/* 滚动条样式 */
.parameters-list::-webkit-scrollbar {
  width: 6px;
}

.parameters-list::-webkit-scrollbar-thumb {
  background-color: #c1c1c1;
  border-radius: 3px;
}

.parameters-list::-webkit-scrollbar-track {
  background-color: #f1f1f1;
  border-radius: 3px;
}

.parameter-item {
  margin-bottom: 8px;
  padding: 10px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.usage-hint {
  padding: 10px;
}

.code-example {
  margin-top: 8px;
  padding: 8px;
  background-color: #f4f4f5;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.code-example pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #303133;
  white-space: pre;
  overflow-x: auto;
  line-height: 1.4;
}
</style>
