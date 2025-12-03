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

        <el-form-item label="执行环境">
          <el-select v-model="executeForm.environment_id" placeholder="默认环境（可选）" clearable style="width: 100%;">
            <el-option
              v-for="env in executeEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            >
              <span>{{ env.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">{{ env.version }}</span>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ executeForm.environment_id
              ? '将使用指定环境的解释器执行'
              : currentScript?.environment_id
                ? '将使用脚本预设的环境'
                : '将使用系统默认解释器'
            }}
          </div>
        </el-form-item>

        <el-form-item label="上传文件">
          <FileUpload v-model="uploadFiles" />
          <el-alert
            type="info"
            :closable="false"
            style="margin-top: 10px;"
          >
            <template #title>
              <div style="font-size: 13px; line-height: 1.6;">
                <strong>文件访问说明：</strong>
                <div style="margin-top: 8px;">
                  <div style="margin-bottom: 10px;">
                    <strong style="color: #409eff;">1. 获取执行时上传的文件：</strong>
                    <div v-if="currentScript?.type === 'python'" style="background: #f5f7fa; padding: 8px; border-radius: 4px; margin-top: 5px;">
                      <code style="color: #303133;">
                        import os, json<br>
                        files = json.loads(os.environ.get('FILES', '[]'))<br>
                        # files 是文件名列表，如 ['test.txt', 'data.csv']<br>
                        # 文件在当前工作目录，可直接用文件名打开<br>
                        # 示例: with open(files[0], 'r') as f: ...
                      </code>
                    </div>
                    <div v-else-if="currentScript?.type === 'javascript'" style="background: #f5f7fa; padding: 8px; border-radius: 4px; margin-top: 5px;">
                      <code style="color: #303133;">
                        const fs = require('fs');<br>
                        const files = JSON.parse(process.env.FILES || '[]');<br>
                        // files 是文件名列表，如 ['test.txt', 'data.csv']<br>
                        // 文件在当前工作目录，可直接用文件名读取<br>
                        // 示例: const data = fs.readFileSync(files[0], 'utf8');
                      </code>
                    </div>
                  </div>
                  <div>
                    <strong style="color: #409eff;">2. 访问文件管理中的公共文件：</strong>
                    <div v-if="currentScript?.type === 'python'" style="background: #f5f7fa; padding: 8px; border-radius: 4px; margin-top: 5px;">
                      <code style="color: #303133;">
                        import os<br>
                        # 获取项目根目录<br>
                        base_dir = os.path.dirname(os.path.dirname(os.getcwd()))<br>
                        upload_dir = os.path.join(base_dir, 'data', 'uploads')<br>
                        file_path = os.path.join(upload_dir, 'your_file.txt')
                      </code>
                    </div>
                    <div v-else-if="currentScript?.type === 'javascript'" style="background: #f5f7fa; padding: 8px; border-radius: 4px; margin-top: 5px;">
                      <code style="color: #303133;">
                        const path = require('path');<br>
                        // 获取项目根目录<br>
                        const baseDir = path.dirname(path.dirname(process.cwd()));<br>
                        const uploadDir = path.join(baseDir, 'data', 'uploads');<br>
                        const filePath = path.join(uploadDir, 'your_file.txt');
                      </code>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </el-alert>
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
        <div class="log-actions">
          <el-button
            v-if="logStatus === 'running'"
            type="danger"
            size="small"
            @click="handleCancelExecution"
          >
            中断执行
          </el-button>
          <el-button
            v-if="logStatus === 'running'"
            type="info"
            size="small"
            @click="closeLogStream"
          >
            停止监听
          </el-button>
        </div>
      </div>

      <el-divider />

      <!-- 进度显示 -->
      <div class="progress-section">
        <ExecutionProgress
          :progress="logProgress"
          :stage="logStage"
          :status="logStatus"
          :show-detail="true"
        />
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
      <el-alert
        v-if="compareVersions.length > 0"
        type="info"
        :closable="false"
        style="margin-bottom: 16px;"
      >
        已选择 {{ compareVersions.length }} 个版本用于对比
        <el-button
          v-if="compareVersions.length === 2"
          type="primary"
          size="small"
          @click="showVersionDiff"
          style="margin-left: 10px;"
        >
          开始对比
        </el-button>
        <el-button
          size="small"
          @click="compareVersions = []"
          style="margin-left: 10px;"
        >
          清空选择
        </el-button>
      </el-alert>

      <el-table
        :data="versions"
        stripe
        @selection-change="handleVersionSelection"
      >
        <el-table-column type="selection" width="55" :selectable="() => compareVersions.length < 2" />
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
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

    <!-- 版本对比对话框 -->
    <el-dialog v-model="diffVisible" title="版本对比" width="95%" :close-on-click-modal="false">
      <CodeDiff
        v-if="diffVisible && compareVersions.length === 2"
        :old-code="compareVersions[0].code"
        :new-code="compareVersions[1].code"
        :old-version="`v${compareVersions[0].version}`"
        :new-version="`v${compareVersions[1].version}`"
        :language="currentScript?.type || 'python'"
        height="600px"
        theme="dark"
      />
      <template #footer>
        <el-button @click="diffVisible = false">关闭</el-button>
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
  getEnvironments,
  cancelExecution
} from '../api'
import FileUpload from '../components/FileUpload.vue'
import CodeEditor from '../components/CodeEditor.vue'
import CodeDiff from '../components/CodeDiff.vue'
import ParameterConfig from '../components/ParameterConfig.vue'
import ExecutionParams from '../components/ExecutionParams.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
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
const compareVersions = ref([])  // 用于对比的版本列表
const diffVisible = ref(false)  // 对比对话框显示状态

// 实时日志相关
const logVisible = ref(false)
const realTimeLogs = ref('')
const logError = ref('')
const logStatus = ref('pending')
const logProgress = ref(0)
const logStage = ref('pending')
const currentExecutionId = ref(null)
const logContainer = ref(null)
let eventSource = null

// 根据当前脚本类型过滤环境（用于创建/编辑脚本）
const filteredEnvironments = computed(() => {
  return environments.value.filter(env => env.type === form.value.type)
})

// 根据当前执行脚本类型过滤环境（用于执行脚本）
const executeEnvironments = computed(() => {
  if (!currentScript.value) return []
  return environments.value.filter(env => env.type === currentScript.value.type)
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
  executeForm.value = {
    environment_id: null  // 初始化为 null，用户可选择
  }
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

    // 添加执行环境ID（如果指定）
    if (executeForm.value.environment_id) {
      formData.append('environment_id', executeForm.value.environment_id)
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
  logProgress.value = 0
  logStage.value = 'pending'
  currentExecutionId.value = executionId
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
      } else if (data.type === 'progress') {
        // 更新进度信息
        logProgress.value = data.progress || 0
        logStage.value = data.stage || 'pending'
        // 根据阶段更新状态
        if (data.stage === 'running' || data.stage === 'preparing' || data.stage === 'installing_deps' || data.stage === 'finishing') {
          logStatus.value = 'running'
        }
      } else if (data.type === 'status') {
        // 更新状态
        logStatus.value = data.status
        logProgress.value = data.progress || 100
        logStage.value = data.stage || (data.status === 'success' ? 'completed' : 'failed')
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
    compareVersions.value = []  // 清空对比选择
    versionVisible.value = true
  } catch (error) {
    console.error(error)
  }
}

const handleVersionSelection = (selection) => {
  compareVersions.value = selection
}

const showVersionDiff = () => {
  if (compareVersions.value.length !== 2) {
    ElMessage.warning('请选择两个版本进行对比')
    return
  }
  diffVisible.value = true
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

const handleCancelExecution = async () => {
  try {
    await ElMessageBox.confirm('确定要中断当前执行吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await cancelExecution(currentExecutionId.value)
    ElMessage.success('执行已中断')

    // 更新状态
    logStatus.value = 'failed'
    logStage.value = 'cancelled'
    logProgress.value = 100

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('中断执行失败: ' + (error.message || error))
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

.log-actions {
  display: flex;
  gap: 8px;
}

.progress-section {
  margin-bottom: 16px;
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
