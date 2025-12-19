<template>
  <div class="delay-node" :class="nodeClass">
    <Handle type="target" :position="Position.Top" />

    <div class="node-header">
      <el-icon class="node-icon"><Clock /></el-icon>
      <span class="node-title">{{ data.label || '延迟节点' }}</span>
      <el-icon v-if="statusIcon" class="status-icon" :class="statusIconClass">
        <component :is="statusIcon" />
      </el-icon>
    </div>

    <div class="node-body">
      <div class="delay-info">
        <el-icon class="delay-icon"><Timer /></el-icon>
        <span class="delay-text">延迟 {{ data.delay || 5 }} 秒</span>
      </div>
      <div v-if="status" class="node-status">
        <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
      </div>
    </div>

    <div v-if="!readonly" class="node-actions">
      <el-button size="small" text @click="$emit('edit', id)">
        <el-icon><Edit /></el-icon>
      </el-button>
      <el-button size="small" text type="danger" @click="$emit('delete', id)">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>

    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Clock, Timer, Edit, Delete, Loading, CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  id: String,
  data: {
    type: Object,
    default: () => ({})
  },
  status: {
    type: String,
    default: null
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit', 'delete'])

// 节点状态样式
const nodeClass = computed(() => {
  if (!props.status) return ''
  return `node-${props.status}`
})

// 状态文本
const statusText = computed(() => {
  const statusMap = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败',
    skipped: '已跳过'
  }
  return statusMap[props.status] || props.status
})

// 状态标签类型
const statusTagType = computed(() => {
  const typeMap = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger',
    skipped: 'warning'
  }
  return typeMap[props.status] || 'info'
})

// 状态图标
const statusIcon = computed(() => {
  const iconMap = {
    running: Loading,
    success: CircleCheck,
    failed: CircleClose,
    skipped: Warning
  }
  return iconMap[props.status]
})

// 状态图标样式
const statusIconClass = computed(() => {
  return `status-${props.status}`
})
</script>

<style scoped>
.delay-node {
  min-width: 180px;
  background: white;
  border: 2px solid #e6a23c;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.delay-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #ebb563;
}

/* 节点状态样式 */
.delay-node.node-pending {
  border-color: #909399;
}

.delay-node.node-running {
  border-color: #409eff;
  box-shadow: 0 0 12px rgba(64, 158, 255, 0.5);
  animation: pulse 2s infinite;
}

.delay-node.node-success {
  border-color: #67c23a;
}

.delay-node.node-failed {
  border-color: #f56c6c;
}

.delay-node.node-skipped {
  border-color: #e6a23c;
  opacity: 0.7;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 12px rgba(64, 158, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.8);
  }
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
  color: white;
  border-radius: 6px 6px 0 0;
  font-weight: 500;
}

.node-icon {
  font-size: 18px;
}

.node-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-icon {
  font-size: 20px;
  margin-left: auto;
}

.status-icon.status-running {
  animation: spin 1s linear infinite;
}

.status-icon.status-success {
  color: #67c23a;
}

.status-icon.status-failed {
  color: #f56c6c;
}

.status-icon.status-skipped {
  color: #e6a23c;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.node-body {
  padding: 16px;
}

.delay-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #606266;
}

.delay-icon {
  font-size: 20px;
  color: #e6a23c;
}

.delay-text {
  font-size: 14px;
  font-weight: 500;
}

.node-status {
  margin-top: 8px;
  display: flex;
  justify-content: center;
}

.node-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 8px 12px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
  border-radius: 0 0 6px 6px;
}

:deep(.vue-flow__handle) {
  width: 10px;
  height: 10px;
  background: #e6a23c;
  border: 2px solid white;
}

:deep(.vue-flow__handle:hover) {
  background: #ebb563;
}
</style>
