<template>
  <div class="script-node" :class="nodeClass">
    <Handle type="target" :position="Position.Top" />

    <div class="node-header">
      <el-icon class="node-icon"><Document /></el-icon>
      <span class="node-title">{{ data.label || '脚本节点' }}</span>
      <el-icon v-if="statusIcon" class="status-icon" :class="statusIconClass">
        <component :is="statusIcon" />
      </el-icon>
    </div>

    <div class="node-body">
      <div v-if="data.script" class="script-info">
        <div class="script-name">{{ data.script.name }}</div>
        <el-tag size="small" type="info">{{ data.script.language }}</el-tag>
      </div>
      <div v-else class="no-script">
        <el-text type="info" size="small">未选择脚本</el-text>
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
import { Document, Edit, Delete, Loading, CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'

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
.script-node {
  min-width: 200px;
  background: white;
  border: 2px solid #409eff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.script-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #66b1ff;
}

/* 节点状态样式 */
.script-node.node-pending {
  border-color: #909399;
}

.script-node.node-running {
  border-color: #409eff;
  box-shadow: 0 0 12px rgba(64, 158, 255, 0.5);
  animation: pulse 2s infinite;
}

.script-node.node-success {
  border-color: #67c23a;
}

.script-node.node-failed {
  border-color: #f56c6c;
}

.script-node.node-skipped {
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
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
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
  padding: 12px;
  min-height: 50px;
}

.script-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.script-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.no-script {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50px;
  color: #909399;
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
  background: #409eff;
  border: 2px solid white;
}

:deep(.vue-flow__handle:hover) {
  background: #66b1ff;
}
</style>
