<template>
  <div class="file-manager">
    <!-- 左侧文件夹树 -->
    <div class="folder-tree-panel">
      <div class="tree-header">
        <span class="tree-title">文件夹</span>
      </div>
      <div class="tree-content">
        <div
          class="tree-item root-item"
          :class="{ active: currentFolderId === null && !searchMode }"
          @click="navigateToRoot"
          @dragover.prevent="handleTreeDragOver($event, null)"
          @dragleave="handleTreeDragLeave($event)"
          @drop.prevent="handleTreeDrop($event, null)"
        >
          <el-icon><FolderOpened /></el-icon>
          <span>全部脚本</span>
        </div>
        <el-tree
          ref="folderTreeRef"
          :data="folderTree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          :expand-on-click-node="false"
          :highlight-current="true"
          default-expand-all
          @node-click="handleTreeNodeClick"
          @node-contextmenu="handleTreeContextMenu"
        >
          <template #default="{ node, data }">
            <div
              class="tree-node-content"
              @dragover.prevent="handleTreeDragOver($event, data.id)"
              @dragleave="handleTreeDragLeave($event)"
              @drop.prevent="handleTreeDrop($event, data.id)"
            >
              <el-icon :style="{ color: data.color || '#E6A23C' }"><Folder /></el-icon>
              <span class="tree-node-label">{{ data.name }}</span>
              <span v-if="data.script_count" class="tree-node-count">{{ data.script_count }}</span>
            </div>
          </template>
        </el-tree>
      </div>
      <div class="tree-footer">
        <GlassButton label="新建文件夹" icon="Plus" type="secondary" size="small" @click="handleCreateRootFolder" />
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="content-panel">
      <!-- 顶部工具栏 -->
      <div class="content-header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item @click="navigateToRoot" class="breadcrumb-clickable">
            全部脚本
          </el-breadcrumb-item>
          <el-breadcrumb-item
            v-for="item in breadcrumbPath"
            :key="item.id"
            @click="navigateToFolder(item.id)"
            class="breadcrumb-clickable"
          >
            {{ item.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>

        <div class="header-actions">
          <el-input
            v-model="searchText"
            placeholder="搜索脚本"
            style="width: 200px;"
            clearable
            @input="handleSearch"
            @clear="handleSearchClear"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <GlassButton label="新建文件夹" icon="FolderAdd" type="secondary" @click="handleCreateFolder" />
          <GlassButton label="新建脚本" icon="Plus" type="primary" @click="handleCreateScript" />
        </div>
      </div>

      <!-- 内容网格 -->
      <div class="content-grid" v-if="!searchMode">
        <!-- 文件夹 -->
        <div
          v-for="folder in currentFolders"
          :key="'folder-' + folder.id"
          class="grid-item folder-item"
          @dblclick="navigateToFolder(folder.id)"
          @contextmenu.prevent="showFolderContextMenu($event, folder)"
          @dragover.prevent="handleGridFolderDragOver($event, folder.id)"
          @dragleave="handleGridFolderDragLeave($event)"
          @drop.prevent="handleGridFolderDrop($event, folder.id)"
        >
          <div class="item-icon folder-icon" :style="{ color: folder.color || '#E6A23C' }">
            <el-icon :size="40"><Folder /></el-icon>
          </div>
          <div class="item-name">{{ folder.name }}</div>
        </div>

        <!-- 脚本 -->
        <div
          v-for="script in currentScripts"
          :key="'script-' + script.id"
          class="grid-item script-item"
          draggable="true"
          @dragstart="handleDragStart($event, script)"
          @dragend="handleDragEnd"
          @contextmenu.prevent="showScriptContextMenu($event, script)"
        >
          <div class="item-icon script-icon" :class="script.type">
            <el-icon :size="40"><Document /></el-icon>
            <span class="type-badge">{{ script.type === 'python' ? '.py' : '.js' }}</span>
          </div>
          <div class="item-name">{{ script.name }}</div>
        </div>

        <!-- 空状态 -->
        <div v-if="currentFolders.length === 0 && currentScripts.length === 0" class="empty-state">
          <el-empty description="此文件夹为空">
            <div class="empty-actions">
              <GlassButton label="新建脚本" type="primary" @click="handleCreateScript" />
              <GlassButton label="新建文件夹" type="secondary" @click="handleCreateFolder" />
            </div>
          </el-empty>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div class="content-grid" v-else>
        <div
          v-for="script in searchResults"
          :key="'search-' + script.id"
          class="grid-item script-item"
          @contextmenu.prevent="showScriptContextMenu($event, script)"
        >
          <div class="item-icon script-icon" :class="script.type">
            <el-icon :size="40"><Document /></el-icon>
            <span class="type-badge">{{ script.type === 'python' ? '.py' : '.js' }}</span>
          </div>
          <div class="item-name">{{ script.name }}</div>
          <div class="item-path" v-if="script.folder">{{ script.folder.name }}</div>
        </div>
        <div v-if="searchResults.length === 0" class="empty-state">
          <el-empty description="没有找到匹配的脚本" />
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <!-- 脚本右键菜单 -->
      <template v-if="contextMenu.type === 'script'">
        <div class="context-menu-item" @click="handleExecute(contextMenu.target)">
          <el-icon><VideoPlay /></el-icon>
          <span>执行</span>
        </div>
        <div class="context-menu-item" @click="handleEdit(contextMenu.target)">
          <el-icon><Edit /></el-icon>
          <span>编辑</span>
        </div>
        <div class="context-menu-item" @click="handleView(contextMenu.target)">
          <el-icon><View /></el-icon>
          <span>查看</span>
        </div>
        <div class="context-menu-item" @click="handleTogglePreserve(contextMenu.target)">
          <el-icon :style="{ color: contextMenu.target.preserve ? '#E6A23C' : '#C0C4CC' }">
            <StarFilled v-if="contextMenu.target.preserve" />
            <Star v-else />
          </el-icon>
          <span>{{ contextMenu.target.preserve ? '取消保护' : '加入白名单' }}</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" @click="handleDeleteScript(contextMenu.target)">
          <el-icon><Delete /></el-icon>
          <span>删除</span>
        </div>
      </template>
      <!-- 文件夹右键菜单 -->
      <template v-if="contextMenu.type === 'folder'">
        <div class="context-menu-item" @click="handleCreateSubFolder(contextMenu.target)">
          <el-icon><FolderAdd /></el-icon>
          <span>新建子文件夹</span>
        </div>
        <div class="context-menu-item" @click="handleRenameFolder(contextMenu.target)">
          <el-icon><EditPen /></el-icon>
          <span>重命名</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" @click="handleDeleteFolder(contextMenu.target)">
          <el-icon><Delete /></el-icon>
          <span>删除</span>
        </div>
      </template>
    </div>

    <!-- 创建/编辑文件夹对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      :title="folderDialogTitle"
      width="500px"
    >
      <el-form :model="folderForm" label-width="100px">
        <el-form-item label="文件夹名称">
          <el-input v-model="folderForm.name" placeholder="请输入文件夹名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <ColorPicker
            v-model="folderForm.color"
            :preview-text="folderForm.name || '文件夹'"
            :show-alpha="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <GlassButton label="取消" type="secondary" @click="folderDialogVisible = false" />
        <GlassButton label="保存" type="primary" @click="handleSaveFolder" />
      </template>
    </el-dialog>

    <!-- 创建/编辑脚本对话框 -->
    <el-dialog
      v-model="scriptDialogVisible"
      :title="scriptDialogTitle"
      width="80%"
      :close-on-click-modal="false"
      class="script-dialog"
    >
      <el-form :model="scriptForm" label-width="100px" class="script-form">
        <el-form-item label="脚本名称">
          <el-input v-model="scriptForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本类型">
          <el-select v-model="scriptForm.type" placeholder="请选择脚本类型" @change="handleTypeChange">
            <el-option label="Python" value="python" />
            <el-option label="JavaScript" value="javascript" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="scriptForm.tag_ids"
            placeholder="选择标签（可选）"
            multiple
            clearable
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            >
              <el-tag :color="tag.color" size="small" effect="plain">{{ tag.name }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="收藏">
          <el-switch v-model="scriptForm.is_favorite" />
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="scriptForm.environment_id" placeholder="默认环境（可选）" clearable>
            <el-option
              v-for="env in filteredEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="scriptForm.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="依赖配置">
          <el-input v-model="scriptForm.dependencies" type="textarea" rows="2" placeholder="多个依赖用逗号分隔" />
        </el-form-item>
        <el-form-item label="参数配置">
          <ParameterConfig v-model="scriptForm.parameters" />
        </el-form-item>
        <el-form-item label="脚本代码">
          <CodeEditor
            v-model="scriptForm.code"
            :language="scriptForm.type"
            height="400px"
            theme="dark"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <GlassButton label="取消" type="secondary" @click="scriptDialogVisible = false" />
        <GlassButton label="保存" type="primary" @click="handleSaveScript" />
      </template>
    </el-dialog>

    <!-- 查看脚本对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="`查看脚本: ${viewScript?.name || ''}`"
      width="80%"
    >
      <el-descriptions :column="2" border v-if="viewScript">
        <el-descriptions-item label="名称">{{ viewScript.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="viewScript.type === 'python' ? 'success' : 'warning'">{{ viewScript.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">v{{ viewScript.version }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(viewScript.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ viewScript.description || '无' }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 16px;">
        <CodeEditor
          v-if="viewScript"
          :model-value="viewScript.code"
          :language="viewScript.type"
          height="500px"
          theme="dark"
          :readonly="true"
        />
      </div>
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="viewDialogVisible = false" />
        <GlassButton label="编辑" type="primary" @click="handleEdit(viewScript); viewDialogVisible = false" />
        <GlassButton label="执行" type="success" @click="handleExecute(viewScript); viewDialogVisible = false" />
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
            :key="`exec-params-${currentScript.id}-${executeVisible}`"
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
            />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件">
          <FileUpload v-model="uploadFiles" />
        </el-form-item>
      </el-form>
      <template #footer>
        <GlassButton label="取消" type="secondary" @click="executeVisible = false" />
        <GlassButton label="执行" type="primary" @click="handleExecuteConfirm" />
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
        <el-tag :type="getStatusType(logStatus)" size="large">{{ getStatusText(logStatus) }}</el-tag>
        <div class="log-actions">
          <GlassButton v-if="logStatus === 'running'" label="中断执行" type="danger" size="small" @click="handleCancelExecution" />
          <GlassButton v-if="logStatus === 'running'" label="停止监听" type="secondary" size="small" @click="closeLogStream" />
        </div>
      </div>
      <el-divider />
      <div class="progress-section">
        <ExecutionProgress :progress="logProgress" :stage="logStage" :status="logStatus" :show-detail="true" />
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
      <div v-if="logStatus === 'success' || logStatus === 'failed'" class="files-section">
        <el-divider>执行空间文件</el-divider>
        <div v-if="filesLoading" style="text-align: center; padding: 20px;">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span style="margin-left: 8px;">加载文件列表中...</span>
        </div>
        <div v-else-if="executionFiles.length === 0" class="files-empty">执行空间中没有文件</div>
        <el-table v-else :data="executionFiles" stripe max-height="300">
          <el-table-column prop="name" label="文件名" min-width="200" />
          <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <GlassButton v-if="row.is_text" label="预览" type="secondary" size="small" @click="handleFilePreview(row)" />
              <GlassButton label="下载" type="primary" size="small" @click="handleFileDownload(row)" />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="closeLogStream" />
      </template>
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog v-model="filePreviewVisible" :title="`预览: ${selectedFile?.name || ''}`" width="80%">
      <div class="file-preview-container">
        <pre v-if="filePreviewType === 'text'">{{ filePreviewContent }}</pre>
        <div v-else style="color: #909399; text-align: center; padding: 40px;">{{ filePreviewContent }}</div>
      </div>
      <template #footer>
        <GlassButton label="关闭" type="secondary" @click="filePreviewVisible = false" />
        <GlassButton label="下载" type="primary" @click="handleFileDownload(selectedFile)" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScripts,
  createScript,
  updateScript,
  deleteScript,
  executeScriptWithFiles,
  getEnvironments,
  cancelExecution,
  getTags,
  getExecutionFiles,
  getExecutionFile,
  previewExecutionFile,
  getFolderTree,
  getFolderContents,
  getRootContents,
  createScriptFolder,
  updateFolder,
  deleteScriptFolder,
  getFolderPath,
  moveScript,
  toggleScriptPreserve
} from '../api'
import FileUpload from '../components/FileUpload.vue'
import CodeEditor from '../components/CodeEditor.vue'
import ParameterConfig from '../components/ParameterConfig.vue'
import ExecutionParams from '../components/ExecutionParams.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
import ColorPicker from '../components/ColorPicker.vue'
import GlassCard from '../components/GlassCard.vue'
import GlassButton from '../components/GlassButton.vue'
import {
  Plus, Search, Folder, FolderOpened, FolderAdd, Document, Edit, EditPen,
  Delete, VideoPlay, View, Loading, Star, StarFilled
} from '@element-plus/icons-vue'

// ===== 文件夹树 =====
const folderTreeRef = ref(null)
const folderTree = ref([])
const currentFolderId = ref(null)
const breadcrumbPath = ref([])

// ===== 当前文件夹内容 =====
const currentFolders = ref([])
const currentScripts = ref([])

// ===== 搜索 =====
const searchText = ref('')
const searchMode = ref(false)
const searchResults = ref([])

// ===== 基础数据 =====
const environments = ref([])
const tags = ref([])

// ===== 右键菜单 =====
const contextMenu = ref({ visible: false, x: 0, y: 0, type: '', target: null })

// ===== 文件夹编辑对话框 =====
const folderDialogVisible = ref(false)
const folderDialogTitle = ref('新建文件夹')
const folderForm = ref({ name: '', color: '#E6A23C' })
const editingFolder = ref(null)
const folderParentId = ref(null)

// ===== 脚本编辑对话框 =====
const scriptDialogVisible = ref(false)
const scriptDialogTitle = ref('新建脚本')
const scriptForm = ref({
  name: '', type: 'python', description: '', code: '',
  dependencies: '', parameters: '', environment_id: null,
  folder_id: null, tag_ids: [], is_favorite: false
})
const editingScript = ref(null)

// ===== 查看对话框 =====
const viewDialogVisible = ref(false)
const viewScript = ref(null)

// ===== 执行对话框 =====
const currentScript = ref(null)
const executeVisible = ref(false)
const executeForm = ref({})
const executeParamsObj = ref({})
const uploadFiles = ref([])

// ===== 日志 =====
const logVisible = ref(false)
const realTimeLogs = ref('')
const logError = ref('')
const logStatus = ref('pending')
const logProgress = ref(0)
const logStage = ref('pending')
const currentExecutionId = ref(null)
const logContainer = ref(null)
let eventSource = null

// ===== 执行文件 =====
const executionFiles = ref([])
const filesLoading = ref(false)
const selectedFile = ref(null)
const filePreviewVisible = ref(false)
const filePreviewContent = ref('')
const filePreviewType = ref('text')

// ===== 拖拽 =====
let dragScript = null

// ===== 计算属性 =====
const filteredEnvironments = computed(() => {
  return environments.value.filter(env => env.type === scriptForm.value.type)
})

const executeEnvironments = computed(() => {
  if (!currentScript.value) return []
  return environments.value.filter(env => env.type === currentScript.value.type)
})

// ===== 数据加载 =====
const loadFolderTree = async () => {
  try {
    const res = await getFolderTree()
    folderTree.value = res.data
  } catch (error) {
    console.error('加载文件夹树失败:', error)
  }
}

const loadFolderContents = async (folderId) => {
  try {
    let res
    if (folderId === null) {
      res = await getRootContents()
    } else {
      res = await getFolderContents(folderId)
    }
    currentFolders.value = res.data.folders
    currentScripts.value = res.data.scripts
  } catch (error) {
    console.error('加载文件夹内容失败:', error)
  }
}

const loadBreadcrumb = async (folderId) => {
  if (folderId === null) {
    breadcrumbPath.value = []
    return
  }
  try {
    const res = await getFolderPath(folderId)
    breadcrumbPath.value = res.data
  } catch (error) {
    console.error('加载面包屑失败:', error)
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

const loadTags = async () => {
  try {
    const res = await getTags()
    tags.value = res.data
  } catch (error) {
    console.error(error)
  }
}

// ===== 导航 =====
const navigateToRoot = () => {
  currentFolderId.value = null
  searchMode.value = false
  searchText.value = ''
  loadFolderContents(null)
  loadBreadcrumb(null)
  if (folderTreeRef.value) {
    folderTreeRef.value.setCurrentKey(null)
  }
}

const navigateToFolder = (folderId) => {
  currentFolderId.value = folderId
  searchMode.value = false
  searchText.value = ''
  loadFolderContents(folderId)
  loadBreadcrumb(folderId)
  if (folderTreeRef.value) {
    folderTreeRef.value.setCurrentKey(folderId)
  }
}

const handleTreeNodeClick = (data) => {
  navigateToFolder(data.id)
}

// ===== 搜索 =====
let searchTimer = null
const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!searchText.value.trim()) {
      handleSearchClear()
      return
    }
    searchMode.value = true
    try {
      const res = await getScripts({ search: searchText.value })
      searchResults.value = res.data
    } catch (error) {
      console.error(error)
    }
  }, 300)
}

const handleSearchClear = () => {
  searchMode.value = false
  searchResults.value = []
  loadFolderContents(currentFolderId.value)
}

// ===== 右键菜单 =====
const showScriptContextMenu = (event, script) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'script',
    target: script
  }
}

const showFolderContextMenu = (event, folder) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    type: 'folder',
    target: folder
  }
}

const handleTreeContextMenu = (event, data) => {
  event.preventDefault()
  showFolderContextMenu(event, data)
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

// ===== 文件夹操作 =====
const handleCreateRootFolder = () => {
  promptCreateFolder(null)
}

const handleCreateFolder = () => {
  promptCreateFolder(currentFolderId.value)
}

const handleCreateSubFolder = (folder) => {
  hideContextMenu()
  promptCreateFolder(folder.id)
}

const promptCreateFolder = (parentId) => {
  folderDialogTitle.value = '新建文件夹'
  folderForm.value = { name: '', color: '#E6A23C' }
  editingFolder.value = null
  folderParentId.value = parentId
  folderDialogVisible.value = true
}

const handleRenameFolder = (folder) => {
  hideContextMenu()
  folderDialogTitle.value = '编辑文件夹'
  folderForm.value = { name: folder.name, color: folder.color || '#E6A23C' }
  editingFolder.value = folder
  folderParentId.value = null
  folderDialogVisible.value = true
}

const handleSaveFolder = async () => {
  if (!folderForm.value.name.trim()) {
    ElMessage.warning('文件夹名称不能为空')
    return
  }
  try {
    if (editingFolder.value) {
      await updateFolder(editingFolder.value.id, {
        name: folderForm.value.name.trim(),
        color: folderForm.value.color
      })
      ElMessage.success('文件夹更新成功')
    } else {
      await createScriptFolder({
        name: folderForm.value.name.trim(),
        parent_id: folderParentId.value,
        color: folderForm.value.color
      })
      ElMessage.success('文件夹创建成功')
    }
    folderDialogVisible.value = false
    loadFolderTree()
    loadFolderContents(currentFolderId.value)
  } catch (error) {
    ElMessage.error((editingFolder.value ? '更新' : '创建') + '文件夹失败: ' + (error.message || error))
  }
}

const handleDeleteFolder = async (folder) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm(`确定要删除文件夹「${folder.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScriptFolder(folder.id)
    ElMessage.success('文件夹删除成功')
    loadFolderTree()
    if (currentFolderId.value === folder.id) {
      navigateToRoot()
    } else {
      loadFolderContents(currentFolderId.value)
    }
  } catch (error) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || error))
    }
  }
}

// ===== 脚本操作 =====
const handleCreateScript = () => {
  scriptDialogTitle.value = '新建脚本'
  scriptForm.value = {
    name: '', type: 'python', description: '', code: '',
    dependencies: '', parameters: '', environment_id: null,
    folder_id: currentFolderId.value, tag_ids: [], is_favorite: false
  }
  editingScript.value = null
  scriptDialogVisible.value = true
}

const handleEdit = (script) => {
  hideContextMenu()
  scriptDialogTitle.value = '编辑脚本'
  scriptForm.value = {
    ...script,
    tag_ids: script.tags ? script.tags.map(t => t.id) : []
  }
  editingScript.value = script
  scriptDialogVisible.value = true
}

const handleView = (script) => {
  hideContextMenu()
  viewScript.value = script
  viewDialogVisible.value = true
}

const handleSaveScript = async () => {
  try {
    if (editingScript.value) {
      await updateScript(editingScript.value.id, scriptForm.value)
      ElMessage.success('更新成功')
    } else {
      await createScript(scriptForm.value)
      ElMessage.success('创建成功')
    }
    scriptDialogVisible.value = false
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败: ' + (error.message || error))
  }
}

const handleTogglePreserve = async (script) => {
  hideContextMenu()
  try {
    const res = await toggleScriptPreserve(script.id)
    if (res.code === 0) {
      script.preserve = res.data.preserve
      ElMessage.success(res.message)
      // 更新本地数据
      const localScript = currentScripts.value.find(s => s.id === script.id)
      if (localScript) {
        localScript.preserve = res.data.preserve
      }
    } else {
      ElMessage.error(res.message)
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('操作失败')
  }
}

const handleDeleteScript = async (script) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm(`确定要删除脚本「${script.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScript(script.id)
    ElMessage.success('删除成功')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const handleTypeChange = () => {
  if (scriptForm.value.environment_id) {
    const selectedEnv = environments.value.find(env => env.id === scriptForm.value.environment_id)
    if (selectedEnv && selectedEnv.type !== scriptForm.value.type) {
      scriptForm.value.environment_id = null
    }
  }
}

// ===== 执行 =====
const handleExecute = (script) => {
  hideContextMenu()
  currentScript.value = script
  executeParamsObj.value = {}
  uploadFiles.value = []
  executeForm.value = { environment_id: null }
  executeVisible.value = true
}

const handleExecuteConfirm = async () => {
  try {
    const formData = new FormData()
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })
    if (executeParamsObj.value && Object.keys(executeParamsObj.value).length > 0) {
      formData.append('params', JSON.stringify(executeParamsObj.value))
    }
    if (executeForm.value.environment_id) {
      formData.append('environment_id', executeForm.value.environment_id)
    }

    const res = await executeScriptWithFiles(currentScript.value.id, formData)
    const executionId = res.data.id
    ElMessage.success('脚本执行已启动')
    executeVisible.value = false
    openLogStream(executionId)
  } catch (error) {
    ElMessage.error('执行失败: ' + error.message)
    console.error(error)
  }
}

// ===== 日志流 =====
const openLogStream = (executionId) => {
  realTimeLogs.value = ''
  logError.value = ''
  logStatus.value = 'pending'
  logProgress.value = 0
  logStage.value = 'pending'
  currentExecutionId.value = executionId
  logVisible.value = true

  if (eventSource) eventSource.close()

  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  eventSource = new EventSource(`${apiUrl}/executions/${executionId}/logs/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'log') {
        realTimeLogs.value += data.content
        nextTick(() => {
          if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
        })
      } else if (data.type === 'progress') {
        logProgress.value = data.progress || 0
        logStage.value = data.stage || 'pending'
        if (['running', 'preparing', 'installing_deps', 'finishing'].includes(data.stage)) {
          logStatus.value = 'running'
        }
      } else if (data.type === 'status') {
        logStatus.value = data.status
        logProgress.value = data.progress || 100
        logStage.value = data.stage || (data.status === 'success' ? 'completed' : 'failed')
        if (data.error) logError.value = data.error
        eventSource.close()
        eventSource = null
        loadExecutionFiles()
      }
    } catch (error) {
      console.error('解析日志数据失败:', error)
    }
  }

  eventSource.onerror = () => {
    ElMessage.error('日志流连接中断')
    if (eventSource) { eventSource.close(); eventSource = null }
  }
}

const loadExecutionFiles = async () => {
  if (!currentExecutionId.value) return
  filesLoading.value = true
  try {
    const res = await getExecutionFiles(currentExecutionId.value)
    executionFiles.value = res.data.files || []
  } catch (error) {
    console.error('加载执行文件失败:', error)
  } finally {
    filesLoading.value = false
  }
}

const closeLogStream = () => {
  if (eventSource) { eventSource.close(); eventSource = null }
  logVisible.value = false
  executionFiles.value = []
}

const handleCancelExecution = async () => {
  try {
    await ElMessageBox.confirm('确定要中断当前执行吗？', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await cancelExecution(currentExecutionId.value)
    ElMessage.success('执行已中断')
    logStatus.value = 'failed'
    logStage.value = 'cancelled'
    logProgress.value = 100
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('中断执行失败: ' + (error.message || error))
  }
}

// ===== 文件操作 =====
const handleFilePreview = async (file) => {
  selectedFile.value = file
  if (file.is_text) {
    try {
      const res = await previewExecutionFile(currentExecutionId.value, file.path)
      filePreviewContent.value = res.data.content
      filePreviewType.value = res.data.type
      filePreviewVisible.value = true
    } catch (error) {
      ElMessage.error('预览文件失败: ' + error.message)
    }
  } else {
    handleFileDownload(file)
  }
}

const handleFileDownload = (file) => {
  const url = getExecutionFile(currentExecutionId.value, file.path, true)
  window.open(url, '_blank')
}

// ===== 拖拽 =====
const handleDragStart = (event, script) => {
  dragScript = script
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', script.id.toString())
}

const handleDragEnd = () => {
  dragScript = null
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))
}

const handleTreeDragOver = (event, folderId) => {
  if (!dragScript) return
  if (dragScript.folder_id === folderId) return
  event.currentTarget.classList.add('drag-over')
}

const handleTreeDragLeave = (event) => {
  event.currentTarget.classList.remove('drag-over')
}

const handleTreeDrop = async (event, folderId) => {
  event.currentTarget.classList.remove('drag-over')
  if (!dragScript) return
  if (dragScript.folder_id === folderId) return

  try {
    await moveScript(dragScript.id, { folder_id: folderId })
    ElMessage.success('脚本已移动')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    ElMessage.error('移动失败: ' + (error.message || error))
  }
  dragScript = null
}

const handleGridFolderDragOver = (event, folderId) => {
  if (!dragScript) return
  event.currentTarget.classList.add('drag-over')
}

const handleGridFolderDragLeave = (event) => {
  event.currentTarget.classList.remove('drag-over')
}

const handleGridFolderDrop = async (event, folderId) => {
  event.currentTarget.classList.remove('drag-over')
  if (!dragScript) return

  try {
    await moveScript(dragScript.id, { folder_id: folderId })
    ElMessage.success('脚本已移动')
    loadFolderContents(currentFolderId.value)
    loadFolderTree()
  } catch (error) {
    ElMessage.error('移动失败: ' + (error.message || error))
  }
  dragScript = null
}

// ===== 工具函数 =====
const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const getStatusType = (status) => {
  const types = { pending: 'info', running: '', success: 'success', failed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '等待中', running: '运行中', success: '执行成功', failed: '执行失败' }
  return texts[status] || '未知状态'
}

// ===== 生命周期 =====
onMounted(() => {
  loadFolderTree()
  loadFolderContents(null)
  loadEnvironments()
  loadTags()
  document.addEventListener('click', hideContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
  if (eventSource) { eventSource.close(); eventSource = null }
})
</script>

<style scoped>
.file-manager {
  display: flex;
  height: calc(100vh - 60px);
  background: var(--el-bg-color);
}

/* ===== 左侧文件夹树 ===== */
.folder-tree-panel {
  width: 250px;
  min-width: 250px;
  border-right: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tree-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  color: var(--text-secondary, rgba(30, 30, 46, 0.8));
  transition: all 0.3s ease;
  background: transparent;
}

.tree-item:hover {
  background: var(--glass-active, rgba(102, 126, 234, 0.1));
}

.tree-item.active {
  background: var(--glass-highlight, rgba(102, 126, 234, 0.15));
  color: var(--accent-primary, #667eea);
  font-weight: 500;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 4px 0;
}

.tree-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary, rgba(30, 30, 46, 0.8));
}

.tree-node-count {
  font-size: 12px;
  color: var(--text-muted, rgba(30, 30, 46, 0.6));
  background: var(--glass-base, rgba(102, 126, 234, 0.05));
  padding: 0 6px;
  border-radius: 10px;
}

.tree-footer {
  padding: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* ===== 右侧内容区 ===== */
.content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.breadcrumb-clickable {
  cursor: pointer;
}

.breadcrumb-clickable:hover :deep(.el-breadcrumb__inner) {
  color: var(--el-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ===== 内容网格 ===== */
.content-grid {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 16px;
  padding: 4px;
}

.grid-item {
  width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
  background: var(--bg-tertiary, #fafafa);
  border: 1px solid var(--border-secondary, rgba(102, 126, 234, 0.3));
}

.grid-item:hover {
  background: var(--bg-secondary, #ffffff);
  border-color: var(--border-main, rgba(102, 126, 234, 0.5));
}

.grid-item.drag-over {
  background: rgba(102, 126, 234, 0.15);
  outline: 2px dashed rgba(102, 126, 234, 0.50);
}

.item-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  position: relative;
}

.folder-icon {
  color: inherit;
}

.script-icon.python {
  color: #3776AB;
}

.script-icon.javascript {
  color: #F7DF1E;
}

.type-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  font-size: 10px;
  background: var(--el-bg-color);
  padding: 0 4px;
  border-radius: 3px;
  color: var(--el-text-color-secondary);
  border: 1px solid var(--el-border-color-lighter);
}

.item-name {
  font-size: 13px;
  text-align: center;
  word-break: break-all;
  line-height: 1.3;
  max-width: 100%;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: var(--text-primary, #1e1e2e);
}

.item-path {
  font-size: 11px;
  color: var(--text-muted, rgba(30, 30, 46, 0.5));
  margin-top: 2px;
}

.empty-state {
  width: 100%;
  padding: 60px 0;
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

/* ===== 右键菜单 ===== */
.context-menu {
  position: fixed;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 6px 0;
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 3000;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
  transition: all 0.15s;
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

.context-menu-item.danger:hover {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.context-menu-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: 4px 0;
}

/* ===== 拖拽高亮 ===== */
.drag-over {
  background: rgba(102, 126, 234, 0.15) !important;
  outline: 2px dashed rgba(102, 126, 234, 0.50);
}

/* ===== 对话框样式 ===== */
.script-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
}

.script-form {
  padding-right: 10px;
}

/* ===== 日志样式 ===== */
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
}

.files-section {
  margin-top: 16px;
}

.files-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.file-preview-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.file-preview-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
