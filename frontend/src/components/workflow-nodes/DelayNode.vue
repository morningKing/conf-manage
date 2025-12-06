<template>
  <div class="delay-node">
    <Handle type="target" :position="Position.Top" />

    <div class="node-header">
      <el-icon class="node-icon"><Clock /></el-icon>
      <span class="node-title">{{ data.label || '延迟节点' }}</span>
    </div>

    <div class="node-body">
      <div class="delay-info">
        <el-icon class="delay-icon"><Timer /></el-icon>
        <span class="delay-text">延迟 {{ data.delay || 5 }} 秒</span>
      </div>
    </div>

    <div class="node-actions">
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
import { Handle, Position } from '@vue-flow/core'
import { Clock, Timer, Edit, Delete } from '@element-plus/icons-vue'

defineProps({
  id: String,
  data: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['edit', 'delete'])
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
