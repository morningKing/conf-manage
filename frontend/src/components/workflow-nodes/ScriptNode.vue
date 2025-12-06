<template>
  <div class="script-node">
    <Handle type="target" :position="Position.Top" />

    <div class="node-header">
      <el-icon class="node-icon"><Document /></el-icon>
      <span class="node-title">{{ data.label || '脚本节点' }}</span>
    </div>

    <div class="node-body">
      <div v-if="data.script" class="script-info">
        <div class="script-name">{{ data.script.name }}</div>
        <el-tag size="small" type="info">{{ data.script.language }}</el-tag>
      </div>
      <div v-else class="no-script">
        <el-text type="info" size="small">未选择脚本</el-text>
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
import { Document, Edit, Delete } from '@element-plus/icons-vue'

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
