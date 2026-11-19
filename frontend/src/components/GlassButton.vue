<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <component v-if="icon" :is="iconComponent" class="button-icon" />
    <span v-if="label" class="button-label">{{ label }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const props = defineProps({
  label: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'success', 'warning', 'danger'].includes(value)
  },
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

// Dynamic icon component
const iconComponent = computed(() => {
  if (!props.icon) return null
  return ElementPlusIconsVue[props.icon]
})

// Computed button classes
const buttonClasses = computed(() => {
  const classes = [
    'glass-button',
    `glass-button--${props.type}`,
    `glass-button--${props.size}`
  ]

  if (props.disabled) {
    classes.push('glass-button--disabled')
  }

  return classes
})
</script>

<style scoped>
.glass-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s ease, border-color 0.15s ease;
  border-radius: 4px;
  font-size: 13px;
}

.glass-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Primary type - 使用实色背景 */
.glass-button--primary {
  background: var(--el-color-primary);
  color: white;
}

.glass-button--primary:hover:not(.glass-button--disabled) {
  background: var(--el-color-primary-dark-2);
}

/* Secondary type - 亮色描边 */
.glass-button--secondary {
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  border: 1px solid var(--el-border-color);
}

.glass-button--secondary:hover:not(.glass-button--disabled) {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary);
  color: var(--el-text-color-primary);
}

/* Success type - 使用实色 */
.glass-button--success {
  background: #67c23a;
  color: white;
}

.glass-button--success:hover:not(.glass-button--disabled) {
  background: #85ce61;
}

/* Warning type - 使用实色 */
.glass-button--warning {
  background: #e6a23c;
  color: white;
}

.glass-button--warning:hover:not(.glass-button--disabled) {
  background: #ebb563;
}

/* Danger type - 使用实色 */
.glass-button--danger {
  background: #f56c6c;
  color: white;
}

.glass-button--danger:hover:not(.glass-button--disabled) {
  background: #f78989;
}

/* Size variations */
.glass-button--small {
  padding: 5px 10px;
  font-size: 12px;
}

.glass-button--default {
  padding: 7px 14px;
  font-size: 13px;
}

.glass-button--large {
  padding: 9px 18px;
  font-size: 14px;
}

.button-icon {
  width: 1em;
  height: 1em;
}

.button-label {
  white-space: nowrap;
}
</style>