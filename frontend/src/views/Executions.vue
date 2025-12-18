<template>
  <div class="executions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>执行历史</span>
            <el-tag v-if="selectedExecutions.length > 0" type="primary" class="selected-count">
              已选择 {{ selectedExecutions.length }} 项
            </el-tag>
          </div>
          <div class="header-right">
            <el-button v-if="selectedExecutions.length > 0" @click="clearSelection">
              取消选择
            </el-button>
            <el-button @click="loadExecutions">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="showStatistics">
              <el-icon><DataLine /></el-icon>
              统计
            </el-button>
          </div>
        </div>
      </template>

      <!-- 批量操作栏 -->
      <div v-if="selectedExecutions.length > 0" class="batch-actions">
        <el-divider content-position="left">批量操作</el-divider>
        <div class="batch-buttons">
          <el-button
            type="danger"
            :disabled="!canBatchDelete"
            @click="batchDelete"
            :loading="batchLoading"
          >
            <el-icon><Delete /></el-icon>
            删除选中 ({{ getSelectedCount('canDelete') }})
          </el-button>
          <el-button
            type="warning"
            :disabled="!canBatchCancel"
            @click="batchCancel"
            :loading="batchLoading"
          >
            <el-icon><VideoPause /></el-icon>
            取消运行 ({{ getSelectedCount('canCancel') }})
          </el-button>
          <el-button
            type="primary"
            :disabled="!canBatchRetry"
            @click="batchRetry"
            :loading="batchLoading"
          >
            <el-icon><RefreshRight /></el-icon>
            重试失败 ({{ getSelectedCount('canRetry') }})
          </el-button>
          <el-button @click="clearSelection">
            <el-icon><Close /></el-icon>
            清空选择
          </el-button>
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
        <el-table-column prop="script_name" label="脚本名称" width="200" />
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
            <el-button
              v-if="row.status === 'running'"
              size="small"
              type="warning"
              @click="handleCancel(row)"
            >
              中断
            </el-button>
            <el-button size="small" @click="handleViewLogs(row)">日志</el-button>
            <el-button size="small" type="primary" @click="handleViewFiles(row)">文件</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
    </el-card>

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
        <el-button @click="logVisible = false">关闭</el-button>
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
        :execution-id="currentExecution.id"
      />
      <template #footer>
        <el-button @click="filesVisible = false">关闭</el-button>
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
        <el-button @click="statisticsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, VideoPause, RefreshRight, Close, DataLine } from '@element-plus/icons-vue'
import { getExecutions, getExecutionLogs, deleteExecution, cancelExecution, batchManageExecutions, getExecutionsStatistics } from '../api'
import ExecutionFiles from '../components/ExecutionFiles.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'

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
  // 打开文件浏览对话框
  currentExecution.value = row
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
    await deleteExecution(row.id)
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

onMounted(() => {
  loadExecutions()
})
</script>

<style scoped>
.executions-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.selected-count {
  font-size: 12px;
}

.progress-section {
  margin: 16px 0;
}

.log-container,
.error-container {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.error-container {
  background-color: #fef0f0;
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
  background-color: #f8f9fa;
  border-radius: 4px;
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
}

.stat-card.success {
  border-color: #67c23a;
}

.stat-card.danger {
  border-color: #f56c6c;
}

.stat-card.primary {
  border-color: #409eff;
}

.stat-item {
  padding: 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
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
  border-bottom: 1px solid #f0f0f0;
}

.status-count {
  font-weight: bold;
  color: #303133;
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
