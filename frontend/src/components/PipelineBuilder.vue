<template>
  <div class="pipeline-builder">
    <div v-if="steps.length === 0" class="pipeline-empty">
      管道为空——按顺序添加步骤，前一步的输出文件可供后续步骤读取
    </div>

    <div v-for="(step, idx) in steps" :key="idx" class="pipeline-step-wrap">
      <div class="pipeline-step">
        <div class="step-index">{{ idx + 1 }}</div>

        <div class="step-body">
          <div class="step-toolbar">
            <el-select
              v-if="step.type === 'script'"
              v-model="step.script_id"
              placeholder="选择脚本"
              filterable
              size="small"
              class="step-script-select"
            >
              <el-option
                v-for="s in scripts"
                :key="s.id"
                :label="`${s.name} (${s.type})`"
                :value="s.id"
              />
            </el-select>

            <template v-if="step.type === 'delay'">
              <span class="delay-label">延时</span>
              <el-input-number v-model="step.delay_seconds" :min="1" :max="3600" size="small" />
              <span class="delay-label">秒</span>
            </template>

            <div class="step-actions">
              <el-tooltip content="上移" placement="top">
                <el-button size="small" :disabled="idx === 0" @click="move(idx, -1)">
                  <el-icon><ArrowUp /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="下移" placement="top">
                <el-button size="small" :disabled="idx === steps.length - 1" @click="move(idx, 1)">
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除步骤" placement="top">
                <el-button size="small" type="danger" plain @click="remove(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>

          <el-input
            v-if="step.type === 'script'"
            v-model="step.params_text"
            type="textarea"
            :rows="2"
            size="small"
            class="step-params"
            placeholder='步骤独立参数（可选 JSON 对象，如 {"MODE": "fast"}）'
          />
        </div>
      </div>

      <div v-if="idx < steps.length - 1" class="pipeline-arrow">
        <el-icon><ArrowDown /></el-icon>
      </div>
    </div>

    <div class="pipeline-add">
      <el-button size="small" @click="addStep('script')">
        <el-icon><Plus /></el-icon> 添加脚本步骤
      </el-button>
      <el-button size="small" @click="addStep('delay')">
        <el-icon><Clock /></el-icon> 添加延时步骤
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ArrowUp, ArrowDown, Delete, Plus, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  scripts: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:steps'])

function emitSteps(next) {
  emit('update:steps', next)
}

function addStep(type) {
  const step =
    type === 'delay'
      ? { type: 'delay', delay_seconds: 5, script_id: null, params_text: '' }
      : { type: 'script', script_id: null, params_text: '', delay_seconds: 0 }
  emitSteps([...props.steps, step])
}

function remove(idx) {
  const next = [...props.steps]
  next.splice(idx, 1)
  emitSteps(next)
}

function move(idx, delta) {
  const target = idx + delta
  if (target < 0 || target >= props.steps.length) return
  const next = [...props.steps]
  ;[next[idx], next[target]] = [next[target], next[idx]]
  emitSteps(next)
}
</script>

<style scoped>
.pipeline-builder {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 10px;
  background: var(--el-fill-color-lighter);
}

.pipeline-empty {
  text-align: center;
  padding: 16px 0;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.pipeline-step-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pipeline-step {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 8px 10px;
}

.step-index {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary);
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.step-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-script-select {
  flex: 1;
  min-width: 0;
}

.step-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.step-params :deep(textarea) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.delay-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.pipeline-arrow {
  color: var(--el-text-color-placeholder);
  padding: 2px 0;
}

.pipeline-add {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  justify-content: center;
}
</style>
