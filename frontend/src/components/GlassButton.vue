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
  transition: all 0.2s ease;
  border-radius: 20px;
}

.glass-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Primary type */
.glass-button--primary {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.glass-button--primary:hover:not(.glass-button--disabled) {
  background: rgba(255, 255, 255, 0.25);
}

/* Secondary type */
.glass-button--secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
}

.glass-button--secondary:hover:not(.glass-button--disabled) {
  background: rgba(255, 255, 255, 0.15);
}

/* Success type */
.glass-button--success {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.glass-button--success:hover:not(.glass-button--disabled) {
  background: rgba(103, 194, 58, 0.3);
}

/* Warning type */
.glass-button--warning {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.glass-button--warning:hover:not(.glass-button--disabled) {
  background: rgba(230, 162, 60, 0.3);
}

/* Danger type */
.glass-button--danger {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.glass-button--danger:hover:not(.glass-button--disabled) {
  background: rgba(245, 108, 108, 0.3);
}

/* Size variations */
.glass-button--small {
  padding: 4px 10px;
  font-size: 10px;
  border-radius: 12px;
}

.glass-button--default {
  padding: 8px 16px;
  font-size: 12px;
}

.glass-button--large {
  padding: 10px 20px;
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