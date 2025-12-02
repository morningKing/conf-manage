<template>
  <div class="code-diff-container">
    <div class="diff-header">
      <div class="version-info old-version">
        <span class="version-label">原版本:</span>
        <el-tag type="warning">{{ oldVersion }}</el-tag>
      </div>
      <div class="version-info new-version">
        <span class="version-label">新版本:</span>
        <el-tag type="success">{{ newVersion }}</el-tag>
      </div>
    </div>

    <div class="diff-editors">
      <div class="editor-panel">
        <div class="editor-title">原代码</div>
        <CodeEditor
          :model-value="oldCode"
          :language="language"
          :readonly="true"
          :height="height"
          :theme="theme"
        />
      </div>

      <div class="editor-panel">
        <div class="editor-title">新代码</div>
        <CodeEditor
          :model-value="newCode"
          :language="language"
          :readonly="true"
          :height="height"
          :theme="theme"
        />
      </div>
    </div>

    <div class="diff-stats">
      <el-space>
        <el-tag type="success" size="small">
          <el-icon><Plus /></el-icon>
          {{ stats.additions }} 行新增
        </el-tag>
        <el-tag type="danger" size="small">
          <el-icon><Minus /></el-icon>
          {{ stats.deletions }} 行删除
        </el-tag>
        <el-tag type="info" size="small">
          {{ stats.changes }} 处修改
        </el-tag>
      </el-space>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Minus } from '@element-plus/icons-vue'
import CodeEditor from './CodeEditor.vue'

const props = defineProps({
  oldCode: {
    type: String,
    default: ''
  },
  newCode: {
    type: String,
    default: ''
  },
  oldVersion: {
    type: String,
    default: '旧版本'
  },
  newVersion: {
    type: String,
    default: '新版本'
  },
  language: {
    type: String,
    default: 'python'
  },
  height: {
    type: String,
    default: '500px'
  },
  theme: {
    type: String,
    default: 'dark'
  }
})

// 计算差异统计
const stats = computed(() => {
  const oldLines = props.oldCode.split('\n')
  const newLines = props.newCode.split('\n')

  let additions = 0
  let deletions = 0
  let changes = 0

  // 简单的行差异计算
  const maxLines = Math.max(oldLines.length, newLines.length)

  for (let i = 0; i < maxLines; i++) {
    const oldLine = oldLines[i] || ''
    const newLine = newLines[i] || ''

    if (!oldLine && newLine) {
      additions++
    } else if (oldLine && !newLine) {
      deletions++
    } else if (oldLine !== newLine) {
      changes++
    }
  }

  return { additions, deletions, changes }
})
</script>

<style scoped>
.code-diff-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.diff-header {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.diff-editors {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.editor-panel {
  display: flex;
  flex-direction: column;
}

.editor-title {
  padding: 8px 12px;
  background-color: #409eff;
  color: white;
  font-size: 14px;
  font-weight: 500;
  border-radius: 4px 4px 0 0;
}

.old-version .editor-title {
  background-color: #e6a23c;
}

.new-version .editor-title {
  background-color: #67c23a;
}

.diff-stats {
  display: flex;
  justify-content: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .diff-editors {
    grid-template-columns: 1fr;
  }

  .editor-panel:first-child {
    margin-bottom: 16px;
  }
}
</style>
