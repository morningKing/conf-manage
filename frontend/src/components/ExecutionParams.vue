<template>
  <div class="execution-params">
    <el-empty v-if="!params || params.length === 0" description="此脚本无需参数" :image-size="60" />

    <div v-else class="params-form">
      <el-form label-width="120px">
        <el-form-item
          v-for="(param, index) in params"
          :key="index"
          :label="param.key"
          :required="param.required"
        >
          <el-input
            v-model="paramValues[param.key]"
            :placeholder="param.description || '请输入参数值'"
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
          <div v-if="param.description" class="param-description">
            <el-text type="info" size="small">{{ param.description }}</el-text>
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

    // 初始化参数值（使用默认值）
    const values = {}
    params.value.forEach(param => {
      if (param.default_value) {
        values[param.key] = param.default_value
      } else {
        values[param.key] = ''
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
}, { immediate: true })

onMounted(() => {
  initParams()
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

.param-description {
  margin-top: 5px;
  padding-left: 2px;
}

code {
  background-color: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>
