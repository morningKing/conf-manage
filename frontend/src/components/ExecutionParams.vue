<template>
  <div class="execution-params">
    <el-empty v-if="!params || params.length === 0" description="此脚本无需参数" :image-size="60" />

    <div v-else class="params-form">
      <el-form label-width="140px">
        <el-form-item
          v-for="(param, index) in params"
          :key="index"
          :label="param.description || param.key"
          :required="param.required"
        >
          <!-- 文本输入 -->
          <el-input
            v-if="param.type === 'text' || !param.type"
            v-model="paramValues[param.key]"
            :placeholder="`请输入${param.description || param.key}`"
            clearable
            @input="emitChange"
          >
            <template #append v-if="param.default_value">
              <el-tooltip :content="`默认值: ${param.default_value}`" placement="top">
                <el-button @click="useDefaultValue(param.key, param.default_value)">
                  使用默认值
                </el-button>
              </el-tooltip>
            </template>
          </el-input>

          <!-- 多行文本 -->
          <el-input
            v-else-if="param.type === 'textarea'"
            v-model="paramValues[param.key]"
            type="textarea"
            :rows="3"
            :placeholder="`请输入${param.description || param.key}`"
            @input="emitChange"
          />

          <!-- 数字输入 -->
          <el-input-number
            v-else-if="param.type === 'number'"
            v-model="paramValues[param.key]"
            :min="param.validation?.min_value"
            :max="param.validation?.max_value"
            @change="emitChange"
          />

          <!-- 密码输入 -->
          <el-input
            v-else-if="param.type === 'password'"
            v-model="paramValues[param.key]"
            type="password"
            show-password
            :placeholder="`请输入${param.description || param.key}`"
            @input="emitChange"
          />

          <!-- 单选下拉 -->
          <el-select
            v-else-if="param.type === 'select'"
            v-model="paramValues[param.key]"
            :placeholder="`请选择${param.description || param.key}`"
            clearable
            @change="emitChange"
          >
            <el-option
              v-for="option in param.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <!-- 多选下拉 -->
          <el-select
            v-else-if="param.type === 'multiselect'"
            v-model="paramValues[param.key]"
            multiple
            :placeholder="`请选择${param.description || param.key}`"
            clearable
            @change="emitChange"
          >
            <el-option
              v-for="option in param.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <!-- 单选按钮组 -->
          <el-radio-group
            v-else-if="param.type === 'radio'"
            v-model="paramValues[param.key]"
            @change="emitChange"
          >
            <el-radio
              v-for="option in param.options"
              :key="option.value"
              :label="option.value"
            >
              {{ option.label }}
            </el-radio>
          </el-radio-group>

          <!-- 复选框组 -->
          <el-checkbox-group
            v-else-if="param.type === 'checkbox'"
            v-model="paramValues[param.key]"
            @change="emitChange"
          >
            <el-checkbox
              v-for="option in param.options"
              :key="option.value"
              :label="option.value"
            >
              {{ option.label }}
            </el-checkbox>
          </el-checkbox-group>

          <!-- 文件上传 -->
          <FileUpload
            v-else-if="param.type === 'file'"
            v-model="paramValues[param.key]"
            :max-size="param.validation?.max_size_mb ? param.validation.max_size_mb * 1024 * 1024 : null"
            :allowed-extensions="param.validation?.allowed_extensions"
            mode="single"
            @update:modelValue="emitChange"
          />

          <!-- 日期选择 -->
          <el-date-picker
            v-else-if="param.type === 'date'"
            v-model="paramValues[param.key]"
            type="date"
            :placeholder="`请选择${param.description || param.key}`"
            @change="emitChange"
          />

          <!-- 开关 -->
          <el-switch
            v-else-if="param.type === 'switch'"
            v-model="paramValues[param.key]"
            @change="emitChange"
          />

          <!-- 参数说明 -->
          <div v-if="param.description && param.type !== 'text' && param.type !== 'textarea'" style="color: #909399; font-size: 12px; margin-top: 5px">
            {{ param.description }}
          </div>
        </el-form-item>
      </el-form>
    </div>

    <el-alert
      v-if="params && params.length > 0"
      type="info"
      :closable="false"
      style="margin-top: 10px;"
    >
      <template #title>
        <el-text size="small">这些参数将作为环境变量传递给脚本，可通过 <code>os.getenv('参数名')</code> 或 <code>process.env.参数名</code> 获取</el-text>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import FileUpload from './FileUpload.vue'

const props = defineProps({
  // 参数定义（JSON字符串或数组）
  parameters: {
    type: [String, Array],
    default: ''
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

// 参数定义
const params = ref([])

// 参数值
const paramValues = ref({})

// 初始化参数
const initParams = () => {
  try {
    if (typeof props.parameters === 'string') {
      params.value = props.parameters ? JSON.parse(props.parameters) : []
    } else {
      params.value = props.parameters || []
    }

    // 初始化参数值（根据类型）
    const values = {}
    params.value.forEach(param => {
      // 根据类型初始化default_value
      if (param.type === 'multiselect' || param.type === 'checkbox') {
        // 数组类型
        values[param.key] = Array.isArray(param.default_value)
          ? [...param.default_value]
          : []
      } else if (param.type === 'number') {
        // 数字类型
        values[param.key] = Number(param.default_value) || 0
      } else if (param.type === 'switch') {
        // 布尔类型
        values[param.key] = Boolean(param.default_value)
      } else if (param.type === 'file') {
        // 文件类型 - 存储上传后的文件路径
        values[param.key] = param.default_value || ''
      } else {
        // 文本类型（包括text, textarea, password, select, radio, date）
        values[param.key] = param.default_value || ''
      }
    })
    paramValues.value = values

    // 发送初始值
    emitChange()
  } catch (e) {
    console.error('解析参数定义失败:', e)
    params.value = []
  }
}

// 使用默认值
const useDefaultValue = (key, defaultValue) => {
  paramValues.value[key] = defaultValue
  emitChange()
}

// 发送变化
const emitChange = () => {
  emit('update:modelValue', { ...paramValues.value })
}

// 监听参数定义变化
watch(() => props.parameters, () => {
  initParams()
}, { immediate: true, deep: true })

onMounted(() => {
  initParams()
})

// 暴露paramValues供父组件获取
defineExpose({
  paramValues
})
</script>

<style scoped>
.execution-params {
  padding: 10px;
}

.params-form {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

code {
  background-color: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>