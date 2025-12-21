<template>
  <div class="ai-script-writer">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI脚本编写器</span>
          <div>
            <el-button @click="saveAsScript" type="success" :disabled="!generatedScript">
              保存为脚本
            </el-button>
          </div>
        </div>
      </template>

      <div class="writer-container">
        <!-- 左侧：AI交互区域 -->
        <div class="left-panel">
          <!-- 参数使用说明 -->
          <el-alert
            title="Python脚本参数规则"
            type="info"
            :closable="false"
            style="margin-bottom: 15px"
          >
            <template #default>
              <div style="font-size: 13px; line-height: 1.6">
                <p><strong>1. 参数传递：</strong>通过环境变量传递，使用 <code>os.environ.get('参数名', '默认值')</code> 获取</p>
                <p><strong>2. 文件上传：</strong>文件列表通过 <code>json.loads(os.environ.get('FILES', '[]'))</code> 获取</p>
                <p><strong>3. 文件访问：</strong>使用相对路径直接访问（文件在当前目录）</p>
              </div>
            </template>
          </el-alert>

          <!-- 提示词输入 -->
          <div class="prompt-section">
            <el-input
              v-model="prompt"
              type="textarea"
              :rows="4"
              placeholder="描述你想要的Python脚本功能，例如：
• 创建一个读取CSV文件并统计数据的脚本（需要参数：文件路径）
• 写一个批量处理图片的脚本（需要参数：输入目录、输出目录）
• 生成一个数据备份脚本（需要参数：源路径、目标路径）"
              @keydown.ctrl.enter="generateScript"
            />
            <div class="actions">
              <el-button
                type="primary"
                @click="generateScript"
                :loading="generating"
                :disabled="!prompt.trim()"
              >
                {{ generating ? '生成中...' : '生成脚本' }} (Ctrl+Enter)
              </el-button>
              <el-button v-if="generatedScript" @click="improveScript" :disabled="generating">
                改进脚本
              </el-button>
              <el-button v-if="generatedScript" @click="explainScript" :disabled="generating">
                解释脚本
              </el-button>
            </div>
          </div>

          <!-- 代码编辑器 -->
          <div class="editor-section">
            <div class="editor-header">
              <span>生成的脚本</span>
              <div>
                <el-button
                  size="small"
                  @click="copyScript"
                  :disabled="!generatedScript"
                >
                  复制
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="previewExecute"
                  :disabled="!generatedScript || executing"
                  :loading="executing"
                >
                  预览执行
                </el-button>
              </div>
            </div>
            <textarea
              v-model="generatedScript"
              class="code-editor"
              placeholder="生成的脚本将显示在这里..."
              spellcheck="false"
            />
          </div>

          <!-- AI解释 -->
          <div v-if="explanation" class="explanation-section">
            <div class="explanation-header">脚本说明</div>
            <div class="explanation-content" v-html="formatExplanation(explanation)"></div>
          </div>
        </div>

        <!-- 右侧：预览执行区域 -->
        <div class="right-panel">
          <!-- 执行参数 -->
          <div class="params-section">
            <div class="params-header">执行参数（可选）</div>
            <div class="params-input">
              <el-input
                v-model="executionParams"
                type="textarea"
                :rows="3"
                placeholder="输入参数（JSON格式）&#10;例如: {&#10;  &quot;PARAM_NAME&quot;: &quot;value&quot;,&#10;  &quot;HOST&quot;: &quot;localhost&quot;&#10;}"
              />
            </div>
          </div>

          <!-- 文件上传 -->
          <div class="files-upload-section">
            <div class="params-header">上传文件（可选）</div>
            <FileUpload v-model="uploadedFiles" />
          </div>

          <!-- 执行日志 -->
          <div class="preview-section">
            <div class="preview-header">
              <span>执行日志</span>
              <el-button
                v-if="executionLog"
                size="small"
                @click="clearLog"
              >
                清空
              </el-button>
            </div>
            <div class="log-container">
              <pre v-if="executionLog" class="log-content">{{ executionLog }}</pre>
              <div v-else class="log-placeholder">
                点击"预览执行"查看脚本执行结果
              </div>
            </div>
          </div>

          <!-- 文件预览 -->
          <div v-if="executionFiles.length > 0" class="files-section">
            <div class="files-header">生成的文件</div>
            <el-tree
              :data="executionFiles"
              :props="{ label: 'name', children: 'children' }"
              @node-click="handleFileClick"
            >
              <template #default="{ node, data }">
                <span class="file-node">
                  <el-icon v-if="data.type === 'file'"><Document /></el-icon>
                  <el-icon v-else><Folder /></el-icon>
                  <span>{{ data.name }}</span>
                </span>
              </template>
            </el-tree>
          </div>

          <!-- 文件内容预览 -->
          <el-dialog v-model="filePreviewVisible" title="文件预览" width="70%">
            <pre class="file-content">{{ currentFileContent }}</pre>
          </el-dialog>
        </div>
      </div>
    </el-card>

    <!-- 保存对话框 -->
    <el-dialog v-model="saveDialogVisible" title="保存为脚本" width="500px">
      <el-form :model="saveForm" :rules="saveRules" ref="saveFormRef" label-width="100px">
        <el-form-item label="脚本名称" prop="name">
          <el-input v-model="saveForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本描述" prop="description">
          <el-input v-model="saveForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="saveForm.category_id" placeholder="请选择分类">
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Folder } from '@element-plus/icons-vue'
import request from '@/api/request'
import { useRouter } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'

const router = useRouter()

const prompt = ref('')
const generatedScript = ref('')
const generating = ref(false)
const executing = ref(false)
const executionLog = ref('')
const executionParams = ref('')  // 执行参数
const uploadedFiles = ref([])  // 上传的文件
const executionFiles = ref([])
const explanation = ref('')
const filePreviewVisible = ref(false)
const currentFileContent = ref('')

const saveDialogVisible = ref(false)
const saveFormRef = ref(null)
const saveForm = ref({
  name: '',
  description: '',
  category_id: null
})
const saveRules = {
  name: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }]
}
const categories = ref([])

// 生成脚本
const generateScript = async () => {
  if (!prompt.value.trim()) {
    return
  }

  generating.value = true
  generatedScript.value = ''
  explanation.value = ''

  try {
    // 使用非流式接口
    const response = await request.post('/ai/generate-script', {
      prompt: prompt.value
    })

    generatedScript.value = response.script || ''
    ElMessage.success('脚本生成成功')
  } catch (error) {
    console.error('生成失败:', error)
    ElMessage.error(error.response?.data?.error || error.message || '生成失败')
  } finally {
    generating.value = false
  }
}

// 改进脚本
const improveScript = async () => {
  const improvementRequest = prompt.value.trim() || '优化代码质量和错误处理'

  generating.value = true
  try {
    const response = await request.post('/ai/improve-script', {
      script: generatedScript.value,
      request: improvementRequest
    })

    generatedScript.value = response.script || ''
    ElMessage.success('脚本改进成功')
  } catch (error) {
    console.error('改进失败:', error)
    ElMessage.error(error.response?.data?.error || error.message || '改进失败')
  } finally {
    generating.value = false
  }
}

// 解释脚本
const explainScript = async () => {
  generating.value = true
  try {
    const response = await request.post('/ai/explain-script', {
      script: generatedScript.value
    })

    explanation.value = response.explanation || ''
  } catch (error) {
    console.error('解释失败:', error)
    ElMessage.error(error.response?.data?.error || error.message || '解释失败')
  } finally {
    generating.value = false
  }
}

// 预览执行
const previewExecute = async () => {
  executing.value = true
  executionLog.value = ''
  executionFiles.value = []

  try {
    // 解析参数
    let params = {}
    if (executionParams.value.trim()) {
      try {
        params = JSON.parse(executionParams.value)
      } catch (e) {
        ElMessage.error('参数格式错误，请输入有效的JSON格式')
        executing.value = false
        return
      }
    }

    // 使用FormData上传代码、参数和文件
    const formData = new FormData()
    formData.append('code', generatedScript.value)
    formData.append('params', JSON.stringify(params))

    // 添加上传的文件
    if (uploadedFiles.value && uploadedFiles.value.length > 0) {
      uploadedFiles.value.forEach((file, index) => {
        formData.append('files', file)
      })
    }

    // 创建临时脚本执行
    const response = await request.post('/ai/preview-execute', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // 显示执行结果
    executionLog.value = response.output || ''

    if (response.error) {
      executionLog.value += '\n\n--- Error ---\n' + response.error
    }

    if (response.status === 'success') {
      ElMessage.success('执行成功')
    } else {
      ElMessage.warning('执行完成，但有错误')
    }

    // 预览执行暂不支持文件查看（因为是临时目录）
    // 如需查看生成的文件，请保存脚本后在脚本管理页面执行
  } catch (error) {
    executionLog.value = 'Error: ' + (error.response?.data?.error || error.message || '执行失败')
    ElMessage.error(error.response?.data?.error || error.message || '执行失败')
  } finally {
    executing.value = false
  }
}

// 加载执行空间的文件
const loadExecutionFiles = async (executionId, tempDir) => {
  try {
    const response = await request.get(`/executions/${executionId}/files`)

    // 将文件列表转换为树结构
    const files = response.files || []
    const fileTree = []

    files.forEach(file => {
      fileTree.push({
        name: file.name,
        path: file.path,
        type: 'file',
        executionId: executionId
      })
    })

    executionFiles.value = fileTree
  } catch (error) {
    console.error('加载文件失败:', error)
  }
}

// 处理文件点击
const handleFileClick = async (data) => {
  if (data.type === 'file' && data.executionId) {
    try {
      const response = await request.get(`/executions/${data.executionId}/files/${encodeURIComponent(data.path)}/preview`)
      currentFileContent.value = response.content || ''
      filePreviewVisible.value = true
    } catch (error) {
      ElMessage.error('读取文件失败: ' + (error.message || '未知错误'))
    }
  }
}

// 复制脚本
const copyScript = () => {
  navigator.clipboard.writeText(generatedScript.value)
  ElMessage.success('已复制到剪贴板')
}

// 清空日志
const clearLog = () => {
  executionLog.value = ''
  executionFiles.value = []
}

// 格式化解释
const formatExplanation = (text) => {
  return text.replace(/\n/g, '<br>')
}

// 保存为脚本
const saveAsScript = () => {
  saveForm.value = {
    name: '',
    description: prompt.value,
    category_id: null
  }
  saveDialogVisible.value = true
}

// 确认保存
const confirmSave = async () => {
  try {
    await saveFormRef.value.validate()

    const scriptData = {
      name: saveForm.value.name,
      description: saveForm.value.description,
      code: generatedScript.value,  // 使用 code 字段
      type: 'python'  // 固定为 Python 类型
    }

    if (saveForm.value.category_id) {
      scriptData.category_id = saveForm.value.category_id
    }

    await request.post('/scripts', scriptData)

    ElMessage.success('保存成功')
    saveDialogVisible.value = false
    router.push('/scripts')
  } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data.error || '保存失败')
    } else if (error.message) {
      // 验证错误，不需要显示消息
    } else {
      ElMessage.error('保存失败')
    }
  }
}

// 加载分类
const loadCategories = async () => {
  try {
    const response = await request.get('/categories')
    categories.value = response
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.ai-script-writer {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.writer-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 200px);
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow: auto;
}

.right-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.params-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.files-upload-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.files-upload-section .params-header {
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
  font-size: 14px;
}

.params-header {
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
  font-size: 14px;
}

.params-input {
  padding: 10px;
}

.params-input .el-textarea__inner {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
}

.prompt-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.actions {
  display: flex;
  gap: 10px;
}

.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.code-editor {
  flex: 1;
  padding: 15px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  border: none;
  resize: none;
  outline: none;
  background: #282c34;
  color: #abb2bf;
}

.explanation-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.explanation-header {
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.explanation-content {
  padding: 15px;
  line-height: 1.8;
}

.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.log-container {
  flex: 1;
  overflow: auto;
  background: #1e1e1e;
}

.log-content {
  padding: 15px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-placeholder {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}

.files-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
}

.files-header {
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.file-node {
  display: flex;
  align-items: center;
  gap: 5px;
}

.file-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  background: #282c34;
  color: #abb2bf;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow: auto;
}

/* 参数说明样式 */
.el-alert code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #e83e8c;
}

.dark-mode .el-alert code {
  background: #2a2a2a;
  color: #f78fb3;
}

.el-alert p {
  margin: 5px 0;
}

.el-alert p:first-child {
  margin-top: 0;
}

.el-alert p:last-child {
  margin-bottom: 0;
}
</style>
