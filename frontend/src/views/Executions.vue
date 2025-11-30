<template>
  <div class="executions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行历史</span>
          <el-button @click="loadExecutions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="executions" stripe>
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
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getExecutions, getExecutionLogs, deleteExecution } from '../api'
import ExecutionFiles from '../components/ExecutionFiles.vue'

const executions = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const logVisible = ref(false)
const filesVisible = ref(false)
const currentExecution = ref(null)
const logs = ref('')
const errorLogs = ref('')

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
</style>
