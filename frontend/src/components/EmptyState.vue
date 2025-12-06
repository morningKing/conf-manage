<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon :size="iconSize" :color="iconColor">
        <component :is="icon" />
      </el-icon>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-description">{{ description }}</p>
    <div v-if="$slots.action" class="empty-action">
      <slot name="action"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document, Folder, VideoPlay, Setting } from '@element-plus/icons-vue'

const props = defineProps({
  icon: {
    type: [String, Object],
    default: 'Document'
  },
  title: {
    type: String,
    default: '暂无数据'
  },
  description: {
    type: String,
    default: ''
  },
  iconSize: {
    type: Number,
    default: 80
  },
  iconColor: {
    type: String,
    default: '#c0c4cc'
  }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  min-height: 300px;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.6;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.empty-title {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 500;
  color: #606266;
}

.dark-mode .empty-title {
  color: #b3b3b3;
}

.empty-description {
  margin: 0 0 20px;
  font-size: 14px;
  color: #909399;
  text-align: center;
  max-width: 400px;
}

.dark-mode .empty-description {
  color: #737373;
}

.empty-action {
  margin-top: 10px;
}
</style>
