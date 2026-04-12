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

      <el-table
        v-else
        :data="localParameters"
        border
        stripe
        @row-click="handleRowClick"
        style="width: 100%"
      >
        <el-table-column prop="key" label="参数名" min-width="150">
          <template #default="{ row }">
            <el-input
              v-model="row.key"
              placeholder="参数名（如：API_KEY）"
              size="small"
              @input="emitChange"
            />
          </template>
        </el-table-column>

        <el-table-column prop="type" label="参数类型" width="140">
          <template #default="{ row }">
            <el-select v-model="row.type" placeholder="选择类型" size="small" @change="handleTypeChange(row)">
              <el-option label="文本" value="text" />
              <el-option label="多行文本" value="textarea" />
              <el-option label="数字" value="number" />
              <el-option label="密码" value="password" />
              <el-option label="下拉选择" value="select" />
              <el-option label="多选下拉" value="multiselect" />
              <el-option label="单选按钮" value="radio" />
              <el-option label="复选框组" value="checkbox" />
              <el-option label="文件上传" value="file" />
              <el-option label="日期" value="date" />
              <el-option label="开关" value="switch" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="参数说明" min-width="150">
          <template #default="{ row }">
            <el-input
              v-model="row.description"
              placeholder="参数说明"
              size="small"
              @input="emitChange"
            />
          </template>
        </el-table-column>

        <el-table-column prop="default_value" label="默认值" min-width="120">
          <template #default="{ row }">
            <el-input
              v-if="row.type === 'text' || row.type === 'password' || !row.type"
              v-model="row.default_value"
              placeholder="默认值"
              size="small"
              @input="emitChange"
            />
            <el-input-number
              v-else-if="row.type === 'number'"
              v-model="row.default_value"
              size="small"
              @input="emitChange"
            />
            <el-switch
              v-else-if="row.type === 'switch'"
              v-model="row.default_value"
              @change="emitChange"
            />
            <el-text v-else-if="row.type === 'multiselect' || row.type === 'checkbox'" size="small">
              {{ Array.isArray(row.default_value) ? row.default_value.join(', ') : '[]' }}
            </el-text>
            <el-text v-else size="small">{{ row.default_value || '-' }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="required" label="必填" width="60" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.required" @change="emitChange" />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" align="center">
          <template #default="{ $index }">
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              @click="removeParameter($index)"
            />
          </template>
        </el-table-column>
      </el-table>
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

    <!-- 类型配置面板 -->
    <el-collapse v-if="currentEditParam" style="margin-top: 15px" v-model="activeConfigCollapse">
      <el-collapse-item name="typeConfig" title="类型配置">
        <el-form label-width="140px">

          <!-- 文本类配置 -->
          <div v-if="['text', 'textarea', 'password'].includes(currentEditParam.type) || !currentEditParam.type">
            <el-form-item label="最小长度">
              <el-input-number v-model="currentEditParam.validation.min_length" :min="0" size="small" @change="emitChange" />
            </el-form-item>
            <el-form-item label="最大长度">
              <el-input-number v-model="currentEditParam.validation.max_length" :min="0" size="small" @change="emitChange" />
            </el-form-item>
            <el-form-item label="正则校验">
              <el-input v-model="currentEditParam.validation.pattern" placeholder="例如: ^[a-zA-Z]+$" size="small" @input="emitChange" />
            </el-form-item>
          </div>

          <!-- 数字配置 -->
          <div v-if="currentEditParam.type === 'number'">
            <el-form-item label="最小值">
              <el-input-number v-model="currentEditParam.validation.min_value" size="small" @change="emitChange" />
            </el-form-item>
            <el-form-item label="最大值">
              <el-input-number v-model="currentEditParam.validation.max_value" size="small" @change="emitChange" />
            </el-form-item>
          </div>

          <!-- 选择类配置 -->
          <div v-if="['select', 'multiselect', 'radio', 'checkbox'].includes(currentEditParam.type)">
            <el-form-item label="选项列表">
              <el-button size="small" @click="addOption" style="margin-bottom: 10px">
                添加选项
              </el-button>
              <el-table v-if="currentEditParam.options && currentEditParam.options.length > 0" :data="currentEditParam.options" border size="small">
                <el-table-column prop="label" label="显示文本" width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.label" size="small" @input="emitChange" />
                  </template>
                </el-table-column>
                <el-table-column prop="value" label="值" width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.value" size="small" @input="emitChange" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <el-button size="small" type="danger" link @click="removeOption($index)">
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="请添加选项" :image-size="40" />
            </el-form-item>
          </div>

          <!-- 文件配置 -->
          <div v-if="currentEditParam.type === 'file'">
            <el-form-item label="最大文件大小(MB)">
              <el-input-number v-model="currentEditParam.validation.max_size_mb" :min="1" :max="100" size="small" @change="emitChange" />
            </el-form-item>
            <el-form-item label="允许的扩展名">
              <el-select v-model="currentEditParam.validation.allowed_extensions" multiple placeholder="选择扩展名" size="small" @change="emitChange">
                <el-option label="Excel (.xlsx)" value="xlsx" />
                <el-option label="Excel (.xls)" value="xls" />
                <el-option label="CSV (.csv)" value="csv" />
                <el-option label="JSON (.json)" value="json" />
                <el-option label="TXT (.txt)" value="txt" />
                <el-option label="图片 (.jpg)" value="jpg" />
                <el-option label="图片 (.png)" value="png" />
                <el-option label="PDF (.pdf)" value="pdf" />
                <el-option label="ZIP (.zip)" value="zip" />
              </el-select>
            </el-form-item>
          </div>

          <!-- 日期配置 -->
          <div v-if="currentEditParam.type === 'date'">
            <el-form-item label="最小日期">
              <el-date-picker v-model="currentEditParam.validation.min_date" type="date" size="small" @change="emitChange" />
            </el-form-item>
            <el-form-item label="最大日期">
              <el-date-picker v-model="currentEditParam.validation.max_date" type="date" size="small" @change="emitChange" />
            </el-form-item>
          </div>

        </el-form>
      </el-collapse-item>
    </el-collapse>

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
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

// 本地参数列表
const localParameters = ref([])

// 当前编辑的参数
const currentEditParam = ref(null)

// 折叠面板状态
const activeCollapse = ref([])
const activeConfigCollapse = ref(['typeConfig'])

// 初始化参数列表
const initParameters = () => {
  if (props.modelValue) {
    try {
      const params = JSON.parse(props.modelValue)
      localParameters.value = Array.isArray(params) ? params : []

      // 为每个参数初始化validation和options字段（向后兼容）
      localParameters.value.forEach(param => {
        if (!param.type) {
          param.type = 'text' // 默认类型
        }
        if (!param.validation) {
          param.validation = {}
        }
        if (['select', 'multiselect', 'radio', 'checkbox'].includes(param.type) && !param.options) {
          param.options = []
        }
      })
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
  const newParam = {
    key: '',
    type: 'text',
    description: '',
    default_value: '',
    required: false,
    validation: {},
    options: []
  }
  localParameters.value.push(newParam)
  currentEditParam.value = newParam
  emitChange()
}

// 删除参数
const removeParameter = (index) => {
  if (currentEditParam.value === localParameters.value[index]) {
    currentEditParam.value = null
  }
  localParameters.value.splice(index, 1)
  emitChange()
}

// 点击参数行选中编辑
const handleRowClick = (row) => {
  currentEditParam.value = row
}

// 类型切换时初始化字段
const handleTypeChange = (param) => {
  currentEditParam.value = param

  // 初始化validation对象
  if (!param.validation) {
    param.validation = {}
  }

  // 初始化options数组（选择类）
  if (['select', 'multiselect', 'radio', 'checkbox'].includes(param.type)) {
    if (!param.options) {
      param.options = []
    }
  }

  // 转换default_value类型
  if (param.type === 'number') {
    param.default_value = Number(param.default_value) || 0
  } else if (param.type === 'multiselect' || param.type === 'checkbox') {
    if (!Array.isArray(param.default_value)) {
      param.default_value = []
    }
  } else if (param.type === 'switch') {
    param.default_value = Boolean(param.default_value)
  } else {
    // 其他类型转为字符串
    param.default_value = String(param.default_value || '')
  }

  emitChange()
}

// 添加选项
const addOption = () => {
  if (!currentEditParam.value.options) {
    currentEditParam.value.options = []
  }
  currentEditParam.value.options.push({ label: '', value: '' })
  emitChange()
}

// 删除选项
const removeOption = (index) => {
  currentEditParam.value.options.splice(index, 1)
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
  max-height: 300px;
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