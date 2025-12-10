<template>
  <div class="workflows-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工作流管理</span>
          <el-space>
            <el-button type="primary" @click="showCreateDialog">创建工作流</el-button>
            <el-button @click="showTemplateDialog">从模板创建</el-button>
          </el-space>
        </div>
      </template>

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
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editWorkflow(row)">编辑</el-button>
            <el-button size="small" type="success" @click="executeWorkflow(row)">
              执行
            </el-button>
            <el-button size="small" @click="toggleWorkflow(row)">
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteWorkflow(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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
    <el-dialog v-model="executeVisible" title="执行工作流" width="500px">
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
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecute">执行</el-button>
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
  List, Share, DataAnalysis, Timer, Link, Document
} from '@element-plus/icons-vue'
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
import WorkflowEditor from '@/components/WorkflowEditor.vue'

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

// 执行状态相关
const statusVisible = ref(false)
const executionStatus = ref('pending')
const currentExecutionId = ref(null)
const nodeStatuses = ref({})
const statusNodes = ref([])
const statusEdges = ref([])
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
  executeVisible.value = true
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
    const res = await executeWorkflowApi(currentWorkflow.value.id, params)
    const executionId = res.data.id

    ElMessage.success('工作流执行已启动')
    executeVisible.value = false

    // 获取工作流详情用于状态显示
    const workflowRes = await getWorkflowApi(currentWorkflow.value.id)
    statusNodes.value = workflowRes.data.nodes || []
    statusEdges.value = workflowRes.data.edges || []

    // 打开状态监控窗口
    openStatusStream(executionId)
  } catch (error) {
    ElMessage.error('执行失败: ' + (error.message || error))
  }
}

// 打开状态监控
const openStatusStream = (executionId) => {
  currentExecutionId.value = executionId
  executionStatus.value = 'pending'
  nodeStatuses.value = {}
  statusVisible.value = true

  // 关闭已有的连接
  if (statusEventSource) {
    statusEventSource.close()
  }

  // 创建 SSE 连接
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  statusEventSource = new EventSource(`${apiUrl}/workflow-executions/${executionId}/stream`)

  statusEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'nodes') {
        // 更新节点状态
        data.nodes.forEach(node => {
          nodeStatuses.value[node.node_id] = node.status
        })
      } else if (data.type === 'status') {
        // 更新总体状态
        executionStatus.value = data.status
      } else if (data.type === 'complete') {
        // 执行完成
        executionStatus.value = data.status
        if (statusEventSource) {
          statusEventSource.close()
          statusEventSource = null
        }
      }
    } catch (error) {
      console.error('解析状态数据失败:', error)
    }
  }

  statusEventSource.onerror = (error) => {
    console.error('状态流连接错误:', error)
    if (statusEventSource) {
      statusEventSource.close()
      statusEventSource = null
    }
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
</style>

