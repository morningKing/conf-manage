<template>
  <div class="executions-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <div class="header-left">
          <span class="glass-card-title">执行历史</span>
          <span v-if="selectedExecutions.length > 0" class="selected-tag">
            已选择 {{ selectedExecutions.length }} 项
          </span>
        </div>
        <div class="header-right">
          <GlassButton v-if="selectedExecutions.length > 0" label="取消选择" type="secondary" size="small" @click="clearSelection" />
          <GlassButton label="刷新" type="secondary" size="small" @click="loadExecutions">
            <template #icon><Refresh /></template>
          </GlassButton>
          <GlassButton label="统计" type="secondary" size="small" @click="showStatistics">
            <template #icon><DataLine /></template>
          </GlassButton>
        </div>
      </div>

      <!-- 选择会话面板 -->
      <SelectionPanel
        ref="selectionPanelRef"
        @change="handleSelectionPanelChange"
        @deleted="handleSelectionDeleted"
      />

      <!-- 批量操作栏 -->
      <div v-if="selectedExecutions.length > 0" class="batch-actions glass-card">
        <div class="batch-title">批量操作</div>
        <div class="batch-buttons">
          <GlassButton
            label="删除选中"
            type="danger"
            size="small"
            :disabled="!canBatchDelete"
            @click="batchDelete"
          />
          <GlassButton
            label="取消运行"
            type="warning"
            size="small"
            :disabled="!canBatchCancel"
            @click="batchCancel"
          />
          <GlassButton
            label="重试失败"
            type="primary"
            size="small"
            :disabled="!canBatchRetry"
            @click="batchRetry"
          />
          <GlassButton
            label="清空选择"
            type="secondary"
            size="small"
            @click="clearSelection"
          />
        </div>
      </div>

      <el-table
        :data="executions"
        stripe
        @selection-change="handleSelectionChange"
        ref="executionsTable"
        @select-all="handleSelectAll"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type_name" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.execution_type === 'workflow' ? 'warning' : 'primary'" size="small">
              {{ row.type_name || '脚本执行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="script_name" label="名称" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              effect="dark"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <div v-if="row.status === 'running' || row.status === 'pending'">
              <ExecutionProgress
                :progress="row.progress || 0"
                :stage="row.stage || 'pending'"
                :status="row.status"
                :show-detail="false"
              />
            </div>
            <span v-else-if="row.status === 'success'" style="color: #67c23a;">
              100%
            </span>
            <span v-else-if="row.status === 'failed'" style="color: #f56c6c;">
              {{ row.stage === 'cancelled' ? '已取消' : '失败' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <GlassButton
              v-if="row.status === 'running'"
              label="中断"
              type="warning"
              size="small"
              @click="handleCancel(row)"
            />
            <GlassButton
              v-if="row.status !== 'running'"
              label="重新执行"
              type="success"
              size="small"
              @click="handleReExecute(row)"
            />
            <GlassButton label="日志" type="secondary" size="small" @click="handleViewLogs(row)" />
            <GlassButton label="文件" type="primary" size="small" @click="handleViewFiles(row)" />
            <GlassButton label="删除" type="danger" size="small" @click="handleDelete(row)" />
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px"
      />
    </div>

    <!-- 日志查看对话框 -->
    <el-dialog v-model="logVisible" title="执行日志" width="80%" top="5vh">
      <div v-if="currentExecution">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="脚本名称">
            {{ currentExecution.script_name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentExecution.status)">
              {{ getStatusText(currentExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatTime(currentExecution.start_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ formatTime(currentExecution.end_time) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 进度显示 -->
        <div v-if="currentExecution.status === 'running' || currentExecution.progress" class="progress-section">
          <el-divider>执行进度</el-divider>
          <ExecutionProgress
            :progress="currentExecution.progress || 0"
            :stage="currentExecution.stage || 'pending'"
            :status="currentExecution.status"
            :show-detail="true"
          />
        </div>

        <el-divider>执行日志</el-divider>
        <div class="log-container">
          <pre>{{ logs }}</pre>
        </div>

        <el-divider v-if="errorLogs">错误信息</el-divider>
        <div v-if="errorLogs" class="error-container">
          <pre>{{ errorLogs }}</pre>
        </div>
      </div>
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="logVisible = false" />
      </template>
    </el-dialog>

    <!-- 文件浏览对话框 -->
    <el-dialog
      v-model="filesVisible"
      :title="`执行空间文件 - ${currentExecution?.script_name || ''}`"
      width="90%"
      top="5vh"
    >
      <ExecutionFiles
        v-if="filesVisible && currentExecution"
        :execution-id="currentExecution.workflow_execution_id ? undefined : currentExecution.id"
        :workflow-execution-id="currentExecution.workflow_execution_id"
      />
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="filesVisible = false" />
      </template>
    </el-dialog>

    <!-- 统计对话框 -->
    <el-dialog
      v-model="statisticsVisible"
      title="执行统计"
      width="80%"
      top="5vh"
    >
      <div v-if="statisticsData">
        <!-- 总体统计 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-item">
                <div class="stat-value">{{ statisticsData.summary.total }}</div>
                <div class="stat-label">总执行数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card success">
              <div class="stat-item">
                <div class="stat-value">{{ statisticsData.summary.success }}</div>
                <div class="stat-label">成功</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card danger">
              <div class="stat-item">
                <div class="stat-value">{{ statisticsData.summary.failed }}</div>
                <div class="stat-label">失败</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card primary">
              <div class="stat-item">
                <div class="stat-value">{{ statisticsData.summary.success_rate }}%</div>
                <div class="stat-label">成功率</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 按状态统计 -->
        <el-divider>按状态统计</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>状态分布</span>
              </template>
              <div class="status-stats">
                <div v-for="item in statisticsData.by_status" :key="item.status" class="status-item">
                  <el-tag :type="getStatusType(item.status)" size="small">
                    {{ getStatusText(item.status) }}
                  </el-tag>
                  <span class="status-count">{{ item.count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>运行状态</span>
              </template>
              <div class="status-info">
                <div class="status-info-item">
                  <span>正在运行:</span>
                  <el-tag type="warning">{{ statisticsData.summary.running }}</el-tag>
                </div>
                <div class="status-info-item">
                  <span>等待中:</span>
                  <el-tag type="info">{{ statisticsData.summary.pending }}</el-tag>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 按脚本统计 -->
        <el-divider content-position="left">按脚本统计 (前10个)</el-divider>
        <el-table :data="statisticsData.by_script.slice(0, 10)" stripe size="small">
          <el-table-column prop="script_name" label="脚本名称" />
          <el-table-column prop="total" label="总次数" width="80" />
          <el-table-column prop="success" label="成功" width="80" />
          <el-table-column prop="failed" label="失败" width="80" />
          <el-table-column label="成功率" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="row.success_rate"
                :color="getProgressColor(row.success_rate)"
                :show-text="true"
                :stroke-width="8"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="statisticsVisible = false" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, VideoPause, RefreshRight, Close, DataLine, Select } from '@element-plus/icons-vue'
import { getExecutions, getExecutionLogs, deleteExecution, deleteWorkflowExecution, cancelExecution, batchManageExecutions, getExecutionsStatistics, reExecuteScript } from '../api'
import ExecutionFiles from '../components/ExecutionFiles.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
import SelectionPanel from '../components/SelectionPanel.vue'
import GlassButton from '../components/GlassButton.vue'

const executions = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const logVisible = ref(false)
const filesVisible = ref(false)
const statisticsVisible = ref(false)
const currentExecution = ref(null)
const logs = ref('')
const errorLogs = ref('')
const selectedExecutions = ref([])
const batchLoading = ref(false)
const statisticsData = ref(null)
const executionsTable = ref(null)
const selectionPanelRef = ref(null)
const selectionCount = ref(0)

const loadExecutions = async () => {
  try {
    const res = await getExecutions({
      page: currentPage.value,
      per_page: pageSize.value
    })
    executions.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error(error)
  }
}

const handleViewLogs = async (row) => {
  try {
    // 如果是工作流执行，提示用户
    if (row.execution_type === 'workflow') {
      ElMessage.info('工作流执行日志请在"工作流管理"页面中查看')
      return
    }

    currentExecution.value = row
    const res = await getExecutionLogs(row.id)
    logs.value = res.data.logs || '暂无日志'
    errorLogs.value = res.data.error || ''
    logVisible.value = true
  } catch (error) {
    console.error(error)
  }
}

const handleViewFiles = (row) => {
  // 如果是工作流执行
  if (row.execution_type === 'workflow') {
    // 工作流执行使用 workflow_execution_id
    currentExecution.value = { ...row, workflow_execution_id: row.id }
  } else {
    currentExecution.value = row
  }
  filesVisible.value = true
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要中断此执行吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await cancelExecution(row.id)
    ElMessage.success('执行已中断')
    loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('中断执行失败: ' + (error.message || error))
      console.error(error)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此执行记录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 根据执行类型调用不同的删除API
    if (row.execution_type === 'workflow') {
      await deleteWorkflowExecution(row.id)
    } else {
      await deleteExecution(row.id)
    }

    ElMessage.success('删除成功')
    loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleSizeChange = () => {
  loadExecutions()
}

const handleCurrentChange = () => {
  loadExecutions()
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败'
  }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getDuration = (row) => {
  if (!row.start_time || !row.end_time) return '-'
  const start = new Date(row.start_time)
  const end = new Date(row.end_time)
  const duration = Math.floor((end - start) / 1000)
  return `${duration}秒`
}

// 批量操作计算属性
const canBatchDelete = computed(() => {
  return selectedExecutions.value.length > 0
})

const canBatchCancel = computed(() => {
  return selectedExecutions.value.some(exec => exec.status === 'running')
})

const canBatchRetry = computed(() => {
  return selectedExecutions.value.some(exec => exec.status === 'failed' || exec.status === 'cancelled')
})

const getSelectedCount = (type) => {
  switch (type) {
    case 'canDelete':
      return selectedExecutions.value.length
    case 'canCancel':
      return selectedExecutions.value.filter(exec => exec.status === 'running').length
    case 'canRetry':
      return selectedExecutions.value.filter(exec => exec.status === 'failed' || exec.status === 'cancelled').length
    default:
      return 0
  }
}

// 批量操作方法
const handleSelectionChange = (selection) => {
  selectedExecutions.value = selection
}

const handleSelectAll = (selection) => {
  selectedExecutions.value = selection
}

const clearSelection = () => {
  if (executionsTable.value) {
    executionsTable.value.clearSelection()
  }
  selectedExecutions.value = []
}

const showStatistics = async () => {
  try {
    const res = await getExecutionsStatistics()
    statisticsData.value = res.data
    statisticsVisible.value = true
  } catch (error) {
    ElMessage.error('获取统计数据失败: ' + (error.message || error))
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedExecutions.value.length} 个执行记录吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    batchLoading.value = true
    const executionIds = selectedExecutions.value.map(exec => exec.id)
    const res = await batchManageExecutions({
      action: 'delete',
      execution_ids: executionIds
    })

    if (res.code === 0) {
      const { success, failed } = res.data
      if (success > 0 && failed === 0) {
        ElMessage.success(`成功删除 ${success} 个执行记录`)
      } else if (success > 0 && failed > 0) {
        ElMessage.warning(`部分删除成功: 成功 ${success} 个，失败 ${failed} 个`)
      } else {
        ElMessage.error('删除失败')
      }

      clearSelection()
      loadExecutions()
    } else {
      ElMessage.error(res.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + (error.message || error))
    }
  } finally {
    batchLoading.value = false
  }
}

const batchCancel = async () => {
  try {
    const runningCount = selectedExecutions.value.filter(exec => exec.status === 'running').length
    await ElMessageBox.confirm(
      `确定要取消选中的 ${runningCount} 个正在运行的执行吗？`,
      '批量取消确认',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    batchLoading.value = true
    const executionIds = selectedExecutions.value
      .filter(exec => exec.status === 'running')
      .map(exec => exec.id)

    const res = await batchManageExecutions({
      action: 'cancel',
      execution_ids: executionIds
    })

    if (res.code === 0) {
      const { success, failed } = res.data
      if (success > 0 && failed === 0) {
        ElMessage.success(`成功取消 ${success} 个执行`)
      } else if (success > 0 && failed > 0) {
        ElMessage.warning(`部分取消成功: 成功 ${success} 个，失败 ${failed} 个`)
      } else {
        ElMessage.error('取消失败')
      }

      clearSelection()
      loadExecutions()
    } else {
      ElMessage.error(res.message || '批量取消失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量取消失败: ' + (error.message || error))
    }
  } finally {
    batchLoading.value = false
  }
}

const batchRetry = async () => {
  try {
    const retryCount = selectedExecutions.value.filter(exec => exec.status === 'failed' || exec.status === 'cancelled').length
    await ElMessageBox.confirm(
      `确定要重试选中的 ${retryCount} 个失败的执行吗？这将创建新的执行记录。`,
      '批量重试确认',
      {
        confirmButtonText: '确定重试',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    batchLoading.value = true
    const executionIds = selectedExecutions.value
      .filter(exec => exec.status === 'failed' || exec.status === 'cancelled')
      .map(exec => exec.id)

    const res = await batchManageExecutions({
      action: 'retry',
      execution_ids: executionIds
    })

    if (res.code === 0) {
      const { success, failed } = res.data
      if (success > 0 && failed === 0) {
        ElMessage.success(`成功重试 ${success} 个执行`)
      } else if (success > 0 && failed > 0) {
        ElMessage.warning(`部分重试成功: 成功 ${success} 个，失败 ${failed} 个`)
      } else {
        ElMessage.error('重试失败')
      }

      clearSelection()
      loadExecutions()
    } else {
      ElMessage.error(res.message || '批量重试失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量重试失败: ' + (error.message || error))
    }
  } finally {
    batchLoading.value = false
  }
}

const getProgressColor = (percentage) => {
  if (percentage >= 90) return '#67c23a'
  if (percentage >= 70) return '#409eff'
  if (percentage >= 50) return '#e6a23c'
  return '#f56c6c'
}

// SelectionPanel 选择变化回调
const handleSelectionPanelChange = ({ count }) => {
  selectionCount.value = count
}

// 删除完成回调
const handleSelectionDeleted = () => {
  loadExecutions()
}

// 重新执行
const handleReExecute = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要重新执行此脚本吗？将创建新的执行记录。',
      '重新执行确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    const res = await reExecuteScript(row.id)
    if (res.code === 0) {
      ElMessage.success(`已创建新执行 #${res.data.new_execution_id}`)
      loadExecutions()
      // 脚本执行需要时间，轮询刷新直到完成
      const pollId = setInterval(async () => {
        await loadExecutions()
        const newExec = executions.value.find(e => e.id === res.data.new_execution_id)
        if (!newExec || newExec.status === 'success' || newExec.status === 'failed') {
          clearInterval(pollId)
        }
      }, 2000)
      // 最多轮询5分钟
      setTimeout(() => clearInterval(pollId), 300000)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新执行失败: ' + (error.message || error))
    }
  }
}

onMounted(() => {
  loadExecutions()
})
</script>

<style scoped>
.executions-container {
  padding: 20px;
}

.glass-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-low, rgba(102, 126, 234, 0.15));
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.selected-tag {
  background: var(--glass-active, rgba(102, 126, 234, 0.1));
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary, rgba(30, 30, 46, 0.8));
}

.progress-section {
  margin: 16px 0;
}

.log-container,
.error-container {
  background: rgba(30, 30, 50, 0.85);
  padding: 15px;
  border-radius: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.error-container {
  border: 1px solid rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* 批量操作样式 */
.batch-actions {
  margin-bottom: 16px;
  padding: 16px;
}

.batch-title {
  color: var(--text-secondary, rgba(30, 30, 46, 0.8));
  font-size: 14px;
  margin-bottom: 12px;
}

.batch-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 统计样式 */
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  background: var(--bg-tertiary, #fafafa);
  border: 1px solid var(--border-secondary, rgba(102, 126, 234, 0.3));
  border-radius: 12px;
}

.stat-card.success {
  border-color: rgba(103, 194, 58, 0.3);
}

.stat-card.danger {
  border-color: rgba(245, 108, 108, 0.3);
}

.stat-card.primary {
  border-color: rgba(64, 158, 255, 0.3);
}

.stat-item {
  padding: 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--accent-primary, #667eea);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted, rgba(30, 30, 46, 0.6));
}

.status-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-low, rgba(102, 126, 234, 0.15));
}

.status-count {
  font-weight: bold;
  color: var(--accent-primary, #667eea);
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
</style>
