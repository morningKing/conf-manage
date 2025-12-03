<template>
  <div class="execution-progress">
    <div class="progress-header">
      <span class="progress-percentage">{{ progress }}%</span>
      <span class="progress-stage">{{ stageText }}</span>
    </div>
    <el-progress
      :percentage="progress"
      :status="progressStatus"
      :stroke-width="showDetail ? 20 : 6"
      :show-text="false"
    />
    <div v-if="showDetail && stage" class="progress-detail">
      <el-steps :active="currentStep" align-center finish-status="success">
        <el-step title="准备" description="初始化执行环境" />
        <el-step title="依赖安装" description="安装脚本依赖" />
        <el-step title="执行中" description="脚本正在运行" />
        <el-step title="完成" :description="finalStepDescription" />
      </el-steps>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: {
    type: Number,
    default: 0
  },
  stage: {
    type: String,
    default: 'pending'
  },
  status: {
    type: String,
    default: 'pending'
  },
  showDetail: {
    type: Boolean,
    default: false
  }
})

// 阶段文本映射
const stageTextMap = {
  pending: '等待中',
  preparing: '准备中',
  installing_deps: '安装依赖',
  running: '执行中',
  finishing: '收尾中',
  completed: '已完成',
  failed: '执行失败',
  cancelled: '已取消'
}

const stageText = computed(() => {
  return stageTextMap[props.stage] || '未知状态'
})

// 进度条状态
const progressStatus = computed(() => {
  if (props.status === 'success' || props.stage === 'completed') return 'success'
  if (props.status === 'failed' || props.stage === 'failed') return 'exception'
  if (props.stage === 'cancelled') return 'warning'
  return undefined
})

// 当前步骤
const currentStep = computed(() => {
  const stageStepMap = {
    pending: 0,
    preparing: 1,
    installing_deps: 2,
    running: 3,
    finishing: 3,
    completed: 4,
    failed: 4,
    cancelled: 4
  }
  return stageStepMap[props.stage] || 0
})

// 最终步骤描述
const finalStepDescription = computed(() => {
  if (props.status === 'success') return '执行成功'
  if (props.status === 'failed') return '执行失败'
  if (props.stage === 'cancelled') return '已取消'
  return '等待完成'
})
</script>

<style scoped>
.execution-progress {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-percentage {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

.progress-stage {
  font-size: 12px;
  color: #909399;
}

.progress-detail {
  margin-top: 20px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.progress-detail :deep(.el-step__title) {
  font-size: 13px;
}

.progress-detail :deep(.el-step__description) {
  font-size: 12px;
}
</style>
