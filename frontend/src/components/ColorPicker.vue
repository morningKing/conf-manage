<template>
  <div class="color-picker-panel">
    <!-- 预设色板区 -->
    <div class="preset-section">
      <div class="section-title">预设颜色</div>
      <div class="color-grid">
        <div
          v-for="color in materialColors"
          :key="color.hex"
          class="color-item"
          :class="{ selected: selectedColor === color.hex }"
          :style="{ backgroundColor: color.hex }"
          :title="color.name"
          @click="selectPreset(color.hex)"
        >
          <el-icon v-if="selectedColor === color.hex" class="check-icon">
            <Check />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 分隔线 -->
    <el-divider content-position="left">自定义颜色</el-divider>

    <!-- 自定义区 -->
    <div class="custom-section">
      <!-- 颜色选择器 -->
      <el-color-picker
        v-model="customColor"
        :show-alpha="showAlpha"
        @change="handleCustomChange"
      />

      <!-- HEX输入 -->
      <el-input
        v-model="hexInput"
        placeholder="409EFF"
        class="hex-input"
        @change="handleHexChange"
      >
        <template #prefix>#</template>
      </el-input>

      <!-- RGB输入 -->
      <div class="rgb-inputs">
        <el-input-number
          v-model="rgb.r"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
        <el-input-number
          v-model="rgb.g"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
        <el-input-number
          v-model="rgb.b"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
      </div>
    </div>

    <!-- 预览 -->
    <div class="preview-section">
      <span class="preview-label">预览效果：</span>
      <el-tag :color="selectedColor" effect="plain" class="preview-tag">
        {{ previewText || '示例标签' }}
      </el-tag>
      <span class="preview-hex">{{ selectedColor }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '#409EFF' },
  showAlpha: { type: Boolean, default: false },
  previewText: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'change'])

// Material Design 预设颜色（50种）
const materialColors = [
  // 红色系（6种）
  { name: '红色', hex: '#F44336' },
  { name: '深红', hex: '#D32F2F' },
  { name: '玫红', hex: '#E91E63' },
  { name: '粉红', hex: '#EC407A' },
  { name: '紫红', hex: '#C2185B' },
  { name: '浅红', hex: '#FFCDD2' },

  // 紫色系（4种）
  { name: '紫色', hex: '#9C27B0' },
  { name: '深紫', hex: '#7B1FA2' },
  { name: '浅紫', hex: '#BA68C8' },
  { name: '淡紫', hex: '#E1BEE7' },

  // 蓝色系（8种）
  { name: '靛蓝', hex: '#3F51B5' },
  { name: '蓝色', hex: '#2196F3' },
  { name: '深蓝', hex: '#1976D2' },
  { name: '天蓝', hex: '#03A9F4' },
  { name: '亮蓝', hex: '#00BCD4' },
  { name: '青色', hex: '#0097A7' },
  { name: 'Teal', hex: '#009688' },
  { name: '蓝灰', hex: '#607D8B' },

  // 绿色系（6种）
  { name: '绿色', hex: '#4CAF50' },
  { name: '深绿', hex: '#388E3C' },
  { name: '亮绿', hex: '#8BC34A' },
  { name: '柠檬', hex: '#CDDC39' },
  { name: '黄绿', hex: '#AEEA00' },
  { name: '淡绿', hex: '#C8E6C9' },

  // 黄/橙色系（6种）
  { name: '黄色', hex: '#FFEB3B' },
  { name: '琥珀', hex: '#FFC107' },
  { name: '橙色', hex: '#FF9800' },
  { name: '深橙', hex: '#FF5722' },
  { name: '金橙', hex: '#FF6F00' },
  { name: '浅黄', hex: '#FFF9C4' },

  // 棕/灰色系（8种）
  { name: '棕色', hex: '#795548' },
  { name: '深棕', hex: '#5D4037' },
  { name: '灰色', hex: '#9E9E9E' },
  { name: '深灰', hex: '#616161' },
  { name: '浅灰', hex: '#BDBDBD' },
  { name: '白色', hex: '#FFFFFF' },
  { name: '黑色', hex: '#000000' },
  { name: '炭灰', hex: '#424242' },

  // Element UI常用色（6种）
  { name: '主色蓝', hex: '#409EFF' },
  { name: '成功绿', hex: '#67C23A' },
  { name: '警告橙', hex: '#E6A23C' },
  { name: '危险红', hex: '#F56C6C' },
  { name: '信息灰', hex: '#909399' },
  { name: '链接蓝', hex: '#1890ff' },

  // 补充色（6种）
  { name: '青绿', hex: '#00BFA5' },
  { name: '藏青', hex: '#304FFE' },
  { name: '珊瑚', hex: '#FF7043' },
  { name: '薰衣草', hex: '#B388FF' },
  { name: '薄荷', hex: '#69F0AE' },
  { name: '奶油', hex: '#FFF8E1' }
]

const selectedColor = ref(props.modelValue)
const customColor = ref(props.modelValue)
const hexInput = ref(props.modelValue.replace('#', ''))

const rgb = ref({ r: 64, g: 158, b: 255 })

// HEX转RGB
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 64, g: 158, b: 255 }
}

// RGB转HEX
const rgbToHex = (r, g, b) => {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('').toUpperCase()
}

// 初始化RGB值
rgb.value = hexToRgb(selectedColor.value)

// 选择预设色
const selectPreset = (hex) => {
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  rgb.value = hexToRgb(hex)
  emit('update:modelValue', hex)
  emit('change', hex)
}

// 自定义颜色变化
const handleCustomChange = (hex) => {
  if (hex) {
    selectedColor.value = hex
    hexInput.value = hex.replace('#', '')
    rgb.value = hexToRgb(hex)
    emit('update:modelValue', hex)
    emit('change', hex)
  }
}

// HEX输入变化
const handleHexChange = (val) => {
  const hex = '#' + val.replace('#', '')
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    selectedColor.value = hex.toUpperCase()
    customColor.value = hex.toUpperCase()
    rgb.value = hexToRgb(hex)
    emit('update:modelValue', hex.toUpperCase())
    emit('change', hex.toUpperCase())
  } else {
    hexInput.value = selectedColor.value.replace('#', '')
  }
}

// RGB输入变化
const handleRgbChange = () => {
  const hex = rgbToHex(rgb.value.r, rgb.value.g, rgb.value.b)
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  emit('update:modelValue', hex)
  emit('change', hex)
}

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal !== selectedColor.value) {
    selectedColor.value = newVal
    customColor.value = newVal
    hexInput.value = newVal.replace('#', '')
    rgb.value = hexToRgb(newVal)
  }
})
</script>

<style scoped>
.color-picker-panel {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.preset-section .section-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 6px;
}

.color-item {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-item:hover {
  transform: scale(1.15);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  z-index: 1;
}

.color-item.selected {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.color-item .check-icon {
  color: #fff;
  font-size: 14px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.custom-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.custom-section .hex-input {
  width: 120px;
}

.custom-section .rgb-inputs {
  display: flex;
  gap: 6px;
}

.custom-section .rgb-inputs .el-input-number {
  width: 70px;
}

.preview-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  gap: 10px;
}

.preview-section .preview-label {
  font-size: 13px;
  color: #606266;
}

.preview-section .preview-tag {
  padding: 4px 12px;
}

.preview-section .preview-hex {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}
</style>