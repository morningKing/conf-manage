<template>
  <div class="workflows-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">工作流管理</span>
        <div class="header-actions">
          <GlassButton label="创建工作流" type="primary" size="small" @click="showCreateDialog" />
          <GlassButton label="从模板创建" type="secondary" size="small" @click="showTemplateDialog" />
        </div>
      </div>

      <!-- 工作流列表 -->
      <el-table :data="workflows" style="width: 100%">
        <el-table-column prop="name" label="工作流名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="nodes_count" label="节点数" width="100" />
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <GlassButton label="编辑" type="secondary" size="small" @click="editWorkflow(row)" />
            <GlassButton label="执行" type="success" size="small" @click="executeWorkflow(row)" />
            <GlassButton :label="row.enabled ? '禁用' : '启用'" type="primary" size="small" @click="toggleWorkflow(row)" />
            <GlassButton label="删除" type="danger" size="small" @click="deleteWorkflow(row)" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑工作流对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentWorkflow ? '编辑工作流' : '创建工作流'"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="工作流名称">
          <el-input v-model="form.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="2"
            placeholder="请输入工作流描述"
          />
        </el-form-item>
        <el-form-item label="工作流图">
          <WorkflowEditor
            v-model:nodes="form.nodes"
            v-model:edges="form.edges"
            :scripts="scripts"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行工作流对话框 -->
    <el-dialog v-model="executeVisible" title="执行工作流" width="600px">
      <el-form label-width="100px">
        <el-form-item label="工作流名称">
          <el-input :value="currentWorkflow?.name" disabled />
        </el-form-item>
        <el-form-item label="执行参数">
          <el-input
            v-model="executeParams"
            type="textarea"
            rows="4"
            placeholder='输入JSON格式参数，例如: {"key": "value"}'
          />
        </el-form-item>
        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :file-list="uploadFileList"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            multiple
            drag
            class="workflow-upload"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持批量上传，上传的文件将保存到工作流执行空间，可在脚本中访问
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecute" :loading="executing">执行</el-button>
      </template>
    </el-dialog>

    <!-- 执行状态显示对话框 -->
    <el-dialog
      v-model="statusVisible"
      title="工作流执行状态"
      width="90%"
      :close-on-click-modal="false"
      @close="closeStatusStream"
    >
      <div class="status-header">
        <el-tag :type="getStatusType(executionStatus)" size="large">
          {{ getStatusText(executionStatus) }}
        </el-tag>
        <div v-if="executionStatus === 'running'">
          <el-button type="danger" size="small" @click="handleCancelWorkflow">
            取消执行
          </el-button>
        </div>
      </div>

      <!-- 整体进度条 -->
      <div class="workflow-progress">
        <div class="progress-info">
          <span class="progress-label">整体进度</span>
          <span class="progress-text">{{ workflowProgress }}%</span>
        </div>
        <el-progress
          :percentage="workflowProgress"
          :status="progressStatus"
          :stroke-width="20"
        />
        <div class="node-stats">
          <span>总节点: {{ totalNodes }}</span>
          <span>已完成: {{ completedNodes }}</span>
          <span>执行中: {{ runningNodes }}</span>
          <span>等待中: {{ pendingNodes }}</span>
        </div>
      </div>

      <el-divider />

      <!-- 工作流图显示，节点状态实时更新 -->
      <div class="workflow-status-container">
        <WorkflowEditor
          v-model:nodes="statusNodes"
          v-model:edges="statusEdges"
          :scripts="scripts"
          :readonly="true"
          :node-statuses="nodeStatuses"
        />
      </div>

      <el-divider />

      <!-- 执行详情 - 使用标签页 -->
      <el-tabs v-model="activeDetailTab" type="border-card">
        <!-- 节点执行日志标签页 -->
        <el-tab-pane label="节点执行日志" name="logs">
          <div class="execution-logs">
            <div v-if="Object.keys(nodeStatuses).length === 0" class="no-logs">
              暂无执行日志
            </div>
            <div v-else class="logs-container">
              <el-collapse v-model="activeNodeLogs" accordion>
                <el-collapse-item
                  v-for="(nodeData, nodeId) in nodeStatuses"
                  :key="nodeId"
                  :name="nodeId"
                >
                  <template #title>
                    <div class="log-node-title">
                      <span class="node-name">{{ getNodeName(nodeId) }}</span>
                      <el-tag
                        :type="getNodeStatusType(nodeData.status)"
                        size="small"
                        style="margin-left: 10px"
                      >
                        {{ getNodeStatusText(nodeData.status) }}
                      </el-tag>
                      <span v-if="nodeData.start_time" class="node-time">
                        {{ formatDate(nodeData.start_time) }}
                      </span>
                    </div>
                  </template>

                  <div class="log-content">
                    <!-- 显示节点执行的脚本日志 -->
                    <div v-if="nodeData.execution">
                      <div class="log-section">
                        <h4>标准输出</h4>
                        <pre class="log-output">{{ nodeData.execution.output || '(无输出)' }}</pre>
                      </div>

                      <div v-if="nodeData.execution.error" class="log-section">
                        <h4>错误信息</h4>
                        <pre class="log-error">{{ nodeData.execution.error }}</pre>
                      </div>

                      <div class="log-section">
                        <h4>执行信息</h4>
                        <div class="log-info">
                          <p>执行ID: {{ nodeData.execution.id }}</p>
                          <p>状态: {{ nodeData.execution.status }}</p>
                          <p>进度: {{ nodeData.execution.progress }}%</p>
                          <p>阶段: {{ nodeData.execution.stage }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- 节点本身的输出和错误 -->
                    <div v-if="nodeData.output && !nodeData.execution">
                      <div class="log-section">
                        <h4>输出</h4>
                        <pre class="log-output">{{ nodeData.output }}</pre>
                      </div>
                    </div>

                    <div v-if="nodeData.error && !nodeData.execution">
                      <div class="log-section">
                        <h4>错误</h4>
                        <pre class="log-error">{{ nodeData.error }}</pre>
                      </div>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </el-tab-pane>

        <!-- 文件结果列表标签页 -->
        <el-tab-pane label="文件结果" name="files">
          <div v-if="currentExecutionId">
            <ExecutionFiles ref="workflowExecutionFilesRef" :workflow-execution-id="currentExecutionId" />
          </div>
          <el-empty v-else description="暂无文件" />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="closeStatusStream">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog v-model="templateDialogVisible" title="选择工作流模板" width="900px">
      <el-form label-width="80px" style="margin-bottom: 16px">
        <el-form-item label="模板分类">
          <el-select v-model="selectedCategory" placeholder="全部分类" clearable style="width: 200px">
            <el-option
              v-for="category in categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div class="template-grid">
        <el-card
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
          shadow="hover"
          @click="selectTemplate(template)"
        >
          <div class="template-icon">
            <el-icon :size="40">
              <component :is="getIconComponent(template.icon)" />
            </el-icon>
          </div>
          <div class="template-info">
            <div class="template-name">{{ template.name }}</div>
            <div class="template-desc">{{ template.description }}</div>
            <el-tag v-if="template.is_builtin" size="small" type="success">内置</el-tag>
            <el-tag v-if="template.category" size="small">{{ template.category }}</el-tag>
          </div>
        </el-card>
      </div>

      <el-empty v-if="filteredTemplates.length === 0" description="暂无模板" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  List, Share, DataAnalysis, Timer, Link, Document, Upload, UploadFilled
} from '@element-plus/icons-vue'
import GlassButton from '../components/GlassButton.vue'
import {
  getWorkflowTemplates,
  useWorkflowTemplate
} from '@/api/workflow'
import {
  getScripts,
  getWorkflows as getWorkflowsApi,
  getWorkflow as getWorkflowApi,
  createWorkflow as createWorkflowApi,
  updateWorkflow as updateWorkflowApi,
  deleteWorkflow as deleteWorkflowApi,
  executeWorkflow as executeWorkflowApi,
  toggleWorkflow as toggleWorkflowApi,
  cancelWorkflowExecution
} from '@/api'
import request from '@/api/request'
import WorkflowEditor from '@/components/WorkflowEditor.vue'
import ExecutionFiles from '@/components/ExecutionFiles.vue'

const workflows = ref([])
const scripts = ref([])
const templates = ref([])
const categories = ref([])
const dialogVisible = ref(false)
const executeVisible = ref(false)
const templateDialogVisible = ref(false)
const currentWorkflow = ref(null)
const executeParams = ref('')
const selectedCategory = ref('')
const uploadFileList = ref([])
const uploadRef = ref(null)
const executing = ref(false)

// 执行状态相关
const statusVisible = ref(false)
const executionStatus = ref('pending')
const currentExecutionId = ref(null)
const nodeStatuses = ref({})
const statusNodes = ref([])
const statusEdges = ref([])
const activeNodeLogs = ref([])  // 当前展开的日志节点
const activeDetailTab = ref('logs')  // 当前激活的详情标签页
const workflowExecutionFilesRef = ref(null)  // 工作流执行文件组件引用
let statusEventSource = null

const form = ref({
  name: '',
  description: '',
  nodes: [],
  edges: []
})

// 加载工作流列表
const loadWorkflows = async () => {
  try {
    const res = await getWorkflowsApi()
    workflows.value = res.data  // 修复：响应拦截器已经返回了 response.data
  } catch (error) {
    ElMessage.error('加载工作流列表失败')
  }
}

// 加载脚本列表
const loadScripts = async () => {
  try {
    const res = await getScripts()
    scripts.value = res.data  // 修复
  } catch (error) {
    ElMessage.error('加载脚本列表失败')
  }
}

// 加载模板列表
const loadTemplates = async () => {
  try {
    const res = await getWorkflowTemplates()
    console.log('Templates response:', res)
    templates.value = res.data  // 修复
    // 提取分类
    const cats = new Set()
    templates.value.forEach(t => {
      if (t.category) cats.add(t.category)
    })
    categories.value = Array.from(cats)
    console.log('Templates loaded:', templates.value.length)
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error(`加载模板列表失败: ${error.message || error}`)
  }
}

// 过滤模板
const filteredTemplates = computed(() => {
  if (!selectedCategory.value) {
    return templates.value
  }
  return templates.value.filter(t => t.category === selectedCategory.value)
})

// 获取图标组件
const getIconComponent = (iconName) => {
  const icons = {
    List,
    Share,
    DataAnalysis,
    Timer,
    Link,
    Document
  }
  return icons[iconName] || Document
}

// 显示模板对话框
const showTemplateDialog = () => {
  selectedCategory.value = ''
  templateDialogVisible.value = true
}

// 选择模板
const selectTemplate = async (template) => {
  try {
    const res = await useWorkflowTemplate(template.id, {
      name: `${template.name} - 副本`
    })

    currentWorkflow.value = null
    form.value = {
      name: res.data.name,
      description: res.data.description,
      nodes: res.data.nodes || [],
      edges: res.data.edges || []
    }

    templateDialogVisible.value = false
    dialogVisible.value = true
    ElMessage.success('模板加载成功，请配置脚本')
  } catch (error) {
    ElMessage.error('加载模板失败')
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  currentWorkflow.value = null
  form.value = {
    name: '',
    description: '',
    nodes: [],
    edges: []
  }
  dialogVisible.value = true
}

// 编辑工作流
const editWorkflow = async (workflow) => {
  try {
    const res = await getWorkflowApi(workflow.id)
    const data = res.data

    currentWorkflow.value = workflow
    form.value = {
      name: data.name,
      description: data.description,
      nodes: data.nodes || [],
      edges: data.edges || []
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载工作流详情失败')
  }
}

// 保存工作流
const handleSave = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  try {
    if (currentWorkflow.value) {
      await updateWorkflowApi(currentWorkflow.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createWorkflowApi(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadWorkflows()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  }
}

// 删除工作流
const deleteWorkflow = async (workflow) => {
  try {
    await ElMessageBox.confirm('确定要删除该工作流吗？', '提示', {
      type: 'warning'
    })

    await deleteWorkflowApi(workflow.id)
    ElMessage.success('删除成功')
    loadWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 执行工作流
const executeWorkflow = (workflow) => {
  currentWorkflow.value = workflow
  executeParams.value = ''
  uploadFileList.value = []
  executeVisible.value = true
}

// 文件选择变化
const handleFileChange = (file, fileList) => {
  uploadFileList.value = fileList
}

// 文件移除
const handleFileRemove = (file, fileList) => {
  uploadFileList.value = fileList
}

// 确认执行
const handleExecute = async () => {
  let params = {}
  if (executeParams.value.trim()) {
    try {
      params = JSON.parse(executeParams.value)
    } catch (error) {
      ElMessage.error('参数格式错误')
      return
    }
  }

  try {
    executing.value = true

    // 先创建执行记录
    const res = await executeWorkflowApi(currentWorkflow.value.id, params)
    const executionId = res.data.id

    // 如果有文件需要上传，上传到工作流执行空间
    if (uploadFileList.value.length > 0) {
      const apiUrl = import.meta.env.VITE_API_URL || '/api'
      const uploadPromises = uploadFileList.value.map(fileItem => {
        const formData = new FormData()
        formData.append('file', fileItem.raw)

        return request.post(
          `${apiUrl}/workflow-executions/${executionId}/upload`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
      })

      await Promise.all(uploadPromises)
      ElMessage.success(`已上传 ${uploadFileList.value.length} 个文件`)
    }

    ElMessage.success('工作流执行已启动')
    executeVisible.value = false
    executing.value = false

    // 获取工作流详情用于状态显示
    const workflowRes = await getWorkflowApi(currentWorkflow.value.id)
    statusNodes.value = workflowRes.data.nodes || []
    statusEdges.value = workflowRes.data.edges || []

    // 打开状态监控窗口
    openStatusStream(executionId)
  } catch (error) {
    executing.value = false
    ElMessage.error('执行失败: ' + (error.message || error))
  }
}

// 打开状态监控
const openStatusStream = (executionId) => {
  console.log('[SSE] 打开状态监控, executionId:', executionId)
  currentExecutionId.value = executionId
  executionStatus.value = 'pending'
  nodeStatuses.value = {}
  activeDetailTab.value = 'logs'  // 重置为日志标签页
  statusVisible.value = true
  console.log('[SSE] statusNodes数量:', statusNodes.value.length)
  console.log('[SSE] statusNodes:', statusNodes.value)

  // 关闭已有的连接
  if (statusEventSource) {
    console.log('[SSE] 关闭已有连接')
    statusEventSource.close()
  }

  // 创建 SSE 连接
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  const sseUrl = `${apiUrl}/workflow-executions/${executionId}/stream`
  console.log('[SSE] 创建连接:', sseUrl)
  statusEventSource = new EventSource(sseUrl)

  statusEventSource.onmessage = (event) => {
    try {
      console.log('[SSE] 收到消息:', event.data)
      const data = JSON.parse(event.data)
      console.log('[SSE] 解析后的数据:', data)

      if (data.type === 'nodes') {
        // 更新节点状态 - 存储完整的节点数据（包括日志）
        console.log('[SSE] 更新节点状态, 节点数量:', data.nodes.length)
        data.nodes.forEach(node => {
          nodeStatuses.value[node.node_id] = node
          console.log('[SSE] 更新节点:', node.node_id, '状态:', node.status)
        })
        console.log('[SSE] nodeStatuses:', nodeStatuses.value)
      } else if (data.type === 'status') {
        // 更新总体状态
        console.log('[SSE] 更新总体状态:', data.status)
        executionStatus.value = data.status
      } else if (data.type === 'complete') {
        // 执行完成
        console.log('[SSE] 工作流执行完成:', data.status)
        executionStatus.value = data.status
        if (statusEventSource) {
          statusEventSource.close()
          statusEventSource = null
        }
      }
    } catch (error) {
      console.error('解析状态数据失败:', error, event.data)
    }
  }

  statusEventSource.onerror = (error) => {
    console.error('[SSE] 状态流连接错误:', error)
    console.error('[SSE] EventSource readyState:', statusEventSource?.readyState)
    if (statusEventSource) {
      statusEventSource.close()
      statusEventSource = null
    }
  }

  statusEventSource.onopen = () => {
    console.log('[SSE] 连接已建立')
  }
}

// 关闭状态监控
const closeStatusStream = () => {
  if (statusEventSource) {
    statusEventSource.close()
    statusEventSource = null
  }
  statusVisible.value = false
}

// 取消工作流执行
const handleCancelWorkflow = async () => {
  try {
    await ElMessageBox.confirm('确定要取消执行吗？', '提示', {
      type: 'warning'
    })

    await cancelWorkflowExecution(currentExecutionId.value)
    ElMessage.success('执行已取消')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '执行中',
    success: '执行成功',
    failed: '执行失败',
    cancelled: '已取消'
  }
  return texts[status] || '未知状态'
}

// 计算工作流整体进度
const totalNodes = computed(() => {
  const count = statusNodes.value.length
  console.log('[Progress] totalNodes:', count)
  return count
})

const completedNodes = computed(() => {
  const count = Object.values(nodeStatuses.value).filter(
    node => node.status === 'success' || node.status === 'failed' || node.status === 'skipped'
  ).length
  console.log('[Progress] completedNodes:', count, 'nodeStatuses:', nodeStatuses.value)
  return count
})

const runningNodes = computed(() => {
  const count = Object.values(nodeStatuses.value).filter(
    node => node.status === 'running'
  ).length
  console.log('[Progress] runningNodes:', count)
  return count
})

const pendingNodes = computed(() => {
  const count = Object.values(nodeStatuses.value).filter(
    node => node.status === 'pending' || !node.status
  ).length
  console.log('[Progress] pendingNodes:', count)
  return count
})

const workflowProgress = computed(() => {
  if (totalNodes.value === 0) {
    console.log('[Progress] workflowProgress: 0 (totalNodes is 0)')
    return 0
  }
  const progress = Math.round((completedNodes.value / totalNodes.value) * 100)
  console.log('[Progress] workflowProgress:', progress, '=', completedNodes.value, '/', totalNodes.value)
  return progress
})

const progressStatus = computed(() => {
  if (executionStatus.value === 'success') return 'success'
  if (executionStatus.value === 'failed') return 'exception'
  return undefined
})

// 启用/禁用工作流
const toggleWorkflow = async (workflow) => {
  try {
    await toggleWorkflowApi(workflow.id)
    ElMessage.success(workflow.enabled ? '已禁用' : '已启用')
    loadWorkflows()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取节点名称
const getNodeName = (nodeId) => {
  const node = statusNodes.value.find(n => n.node_id === nodeId)
  if (node && node.script) {
    return node.script.name || nodeId
  }
  return nodeId
}

// 获取节点状态类型（用于Tag颜色）
const getNodeStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger',
    skipped: 'warning'
  }
  return types[status] || 'info'
}

// 获取节点状态文本
const getNodeStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败',
    skipped: '跳过'
  }
  return texts[status] || status
}

onMounted(() => {
  loadWorkflows()
  loadScripts()
  loadTemplates()
})

</script>

<style scoped>
.workflows-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.template-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80px;
  color: #409eff;
}

.template-info {
  text-align: center;
  padding-top: 12px;
}

.template-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
}

.template-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
  min-height: 40px;
  line-height: 1.5;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.workflow-progress {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.progress-text {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.node-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
}

.node-stats span {
  padding: 4px 12px;
  background: white;
  border-radius: 4px;
}

.workflow-status-container {
  min-height: 400px;
}

/* 执行日志样式 */
.execution-logs {
  margin-top: 20px;
}

.execution-logs h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  color: #303133;
}

.no-logs {
  text-align: center;
  padding: 40px;
  color: #909399;
  font-size: 14px;
}

.logs-container {
  max-height: 500px;
  overflow-y: auto;
}

.log-node-title {
  display: flex;
  align-items: center;
  flex: 1;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.node-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.log-content {
  padding: 12px;
  background: #f5f7fa;
}

.log-section {
  margin-bottom: 16px;
}

.log-section:last-child {
  margin-bottom: 0;
}

.log-section h4 {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #606266;
}

.log-output, .log-error {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.log-error {
  background: #fef0f0;
  border-color: #fbc4c4;
  color: #f56c6c;
}

.log-info {
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
}

.log-info p {
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

/* 工作流上传组件样式 */
.workflow-upload {
  width: 100%;
}

.workflow-upload .el-upload {
  width: 100%;
}

.workflow-upload .el-upload-dragger {
  width: 100%;
  padding: 40px 20px;
}

.workflow-upload .el-icon--upload {
  font-size: 67px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.workflow-upload .el-upload__text {
  color: #606266;
  font-size: 14px;
  text-align: center;
}

.workflow-upload .el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.workflow-upload .el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
}

</style>

