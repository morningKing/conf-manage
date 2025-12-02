<template>
  <div class="scripts-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>脚本列表</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建脚本
          </el-button>
        </div>
      </template>

      <el-table :data="scripts" stripe>
        <el-table-column prop="name" label="脚本名称" width="200" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'python' ? 'success' : 'warning'">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="handleExecute(row)">执行</el-button>
            <el-button size="small" type="info" @click="handleVersions(row)">版本</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="80%"
      :close-on-click-modal="false"
      class="script-dialog"
    >
      <el-form :model="form" label-width="100px" class="script-form">
        <el-form-item label="脚本名称">
          <el-input v-model="form.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本类型">
          <el-select v-model="form.type" placeholder="请选择脚本类型" @change="handleTypeChange">
            <el-option label="Python" value="python" />
            <el-option label="JavaScript" value="javascript" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="form.environment_id" placeholder="默认环境（可选）" clearable>
            <el-option
              v-for="env in filteredEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            >
              <span>{{ env.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">{{ env.version }}</span>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ form.environment_id ? '将使用指定环境的解释器执行' : '将使用系统默认解释器或环境类型的默认环境' }}
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="依赖配置">
          <el-input
            v-model="form.dependencies"
            type="textarea"
            rows="2"
            placeholder="多个依赖用逗号分隔,例如: requests,pandas"
          />
        </el-form-item>
        <el-form-item label="参数配置">
          <ParameterConfig v-model="form.parameters" />
        </el-form-item>
        <el-form-item label="脚本代码">
          <CodeEditor
            v-model="form.code"
            :language="form.type"
            height="400px"
            theme="dark"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行对话框 -->
    <el-dialog v-model="executeVisible" title="执行脚本" width="700px">
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="脚本名称">
          <el-input :value="currentScript?.name" disabled />
        </el-form-item>

        <el-form-item label="脚本参数" v-if="currentScript?.parameters">
          <ExecutionParams
            :parameters="currentScript.parameters"
            v-model="executeParamsObj"
          />
        </el-form-item>

        <el-form-item label="上传文件">
          <FileUpload v-model="uploadFiles" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteConfirm">执行</el-button>
      </template>
    </el-dialog>

    <!-- 实时日志对话框 -->
    <el-dialog
      v-model="logVisible"
      title="执行日志（实时）"
      width="80%"
      :close-on-click-modal="false"
      @close="closeLogStream"
    >
      <div class="log-header">
        <el-tag :type="getStatusType(logStatus)" size="large">
          {{ getStatusText(logStatus) }}
        </el-tag>
        <el-button
          v-if="logStatus === 'running'"
          type="danger"
          size="small"
          @click="closeLogStream"
        >
          停止监听
        </el-button>
      </div>

      <el-divider />

      <div class="log-container" ref="logContainer">
        <pre v-if="realTimeLogs">{{ realTimeLogs }}</pre>
        <div v-else class="log-empty">等待日志输出...</div>
      </div>

      <div v-if="logError" class="error-container">
        <el-divider>错误信息</el-divider>
        <pre>{{ logError }}</pre>
      </div>

      <template #footer>
        <el-button @click="closeLogStream">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 版本历史对话框 -->
    <el-dialog v-model="versionVisible" title="版本历史" width="80%">
      <el-table :data="versions" stripe>
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewVersion(row)">查看</el-button>
            <el-button
              size="small"
              type="warning"
              @click="handleRollback(row)"
              v-if="row.version !== currentScript?.version"
            >
              回滚
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 版本代码查看对话框 -->
    <el-dialog
      v-model="versionCodeVisible"
      :title="`版本 ${currentVersion?.version} 代码`"
      width="80%"
    >
      <CodeEditor
        v-if="currentVersion"
        :model-value="currentVersion.code"
        :language="currentScript?.type || 'python'"
        height="600px"
        theme="dark"
        :readonly="true"
      />
      <template #footer>
        <el-button @click="versionCodeVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScripts,
  createScript,
  updateScript,
  deleteScript,
  getScriptVersions,
  rollbackScript,
  executeScriptWithFiles,
  getEnvironments
} from '../api'
import FileUpload from '../components/FileUpload.vue'
import CodeEditor from '../components/CodeEditor.vue'
import ParameterConfig from '../components/ParameterConfig.vue'
import ExecutionParams from '../components/ExecutionParams.vue'
import { Plus } from '@element-plus/icons-vue'

const scripts = ref([])
const environments = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建脚本')
const form = ref({
  name: '',
  type: 'python',
  description: '',
  code: '',
  dependencies: '',
  parameters: '',
  environment_id: null
})
const currentScript = ref(null)
const executeVisible = ref(false)
const executeForm = ref({})
const executeParams = ref('')
const executeParamsObj = ref({})
const uploadFiles = ref([])
const versionVisible = ref(false)
const versions = ref([])
const versionCodeVisible = ref(false)
const currentVersion = ref(null)

// 实时日志相关
const logVisible = ref(false)
const realTimeLogs = ref('')
const logError = ref('')
const logStatus = ref('pending')
const logContainer = ref(null)
let eventSource = null

// 根据当前脚本类型过滤环境
const filteredEnvironments = computed(() => {
  return environments.value.filter(env => env.type === form.value.type)
})

const loadScripts = async () => {
  try {
    const res = await getScripts()
    scripts.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadEnvironments = async () => {
  try {
    const res = await getEnvironments()
    environments.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const handleTypeChange = () => {
  // 当脚本类型改变时，清空环境选择（如果当前选择的环境类型不匹配）
  if (form.value.environment_id) {
    const selectedEnv = environments.value.find(env => env.id === form.value.environment_id)
    if (selectedEnv && selectedEnv.type !== form.value.type) {
      form.value.environment_id = null
    }
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建脚本'
  form.value = {
    name: '',
    type: 'python',
    description: '',
    code: '',
    dependencies: '',
    parameters: '',
    environment_id: null
  }
  currentScript.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑脚本'
  form.value = { ...row }
  currentScript.value = row
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (currentScript.value) {
      await updateScript(currentScript.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createScript(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadScripts()
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此脚本吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScript(row.id)
    ElMessage.success('删除成功')
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleExecute = (row) => {
  currentScript.value = row
  executeParams.value = ''
  executeParamsObj.value = {}
  uploadFiles.value = []
  executeVisible.value = true
}

const handleExecuteConfirm = async () => {
  try {
    const formData = new FormData()

    // 添加文件
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })

    // 添加参数（使用ExecutionParams组件收集的参数）
    if (executeParamsObj.value && Object.keys(executeParamsObj.value).length > 0) {
      formData.append('params', JSON.stringify(executeParamsObj.value))
    }

    const res = await executeScriptWithFiles(currentScript.value.id, formData)
    const executionId = res.data.id

    ElMessage.success('脚本执行已启动')
    executeVisible.value = false

    // 打开实时日志窗口
    openLogStream(executionId)
  } catch (error) {
    ElMessage.error('参数格式错误或执行失败: ' + error.message)
    console.error(error)
  }
}

const openLogStream = (executionId) => {
  // 重置日志状态
  realTimeLogs.value = ''
  logError.value = ''
  logStatus.value = 'pending'
  logVisible.value = true

  // 关闭已有的连接
  if (eventSource) {
    eventSource.close()
  }

  // 创建 SSE 连接
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  eventSource = new EventSource(`${apiUrl}/executions/${executionId}/logs/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'log') {
        // 追加日志内容
        realTimeLogs.value += data.content
        // 自动滚动到底部
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      } else if (data.type === 'status') {
        // 更新状态
        logStatus.value = data.status
        if (data.error) {
          logError.value = data.error
        }
        // 关闭连接
        eventSource.close()
        eventSource = null
      } else if (data.error) {
        ElMessage.error(data.error)
        eventSource.close()
        eventSource = null
      }
    } catch (error) {
      console.error('解析日志数据失败:', error)
    }
  }

  eventSource.onerror = (error) => {
    console.error('日志流连接错误:', error)
    ElMessage.error('日志流连接中断')
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }
}

const closeLogStream = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  logVisible.value = false
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
    success: '执行成功',
    failed: '执行失败'
  }
  return texts[status] || '未知状态'
}

const handleVersions = async (row) => {
  try {
    currentScript.value = row
    const res = await getScriptVersions(row.id)
    versions.value = res.data
    versionVisible.value = true
  } catch (error) {
    console.error(error)
  }
}

const handleViewVersion = (row) => {
  currentVersion.value = row
  versionCodeVisible.value = true
}

const handleRollback = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要回滚到版本 ${row.version} 吗?`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await rollbackScript(currentScript.value.id, row.version)
    ElMessage.success('回滚成功')
    versionVisible.value = false
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadScripts()
  loadEnvironments()
})
</script>

<style scoped>
.scripts-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 脚本编辑对话框样式 */
.script-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
}

.script-form {
  padding-right: 10px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.log-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.error-container {
  margin-top: 16px;
}

.error-container pre {
  background-color: #fee;
  color: #c00;
  padding: 16px;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin: 0;
  overflow-x: auto;
}
</style>
