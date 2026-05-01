<template>
  <div class="webhooks-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">Webhook管理</span>
        <div class="header-actions">
          <GlassButton label="使用指南" type="secondary" size="small" @click="showGuide = true">
            <template #icon><Document /></template>
          </GlassButton>
          <GlassButton label="新建Webhook" type="primary" size="small" @click="handleCreate">
            <template #icon><Plus /></template>
          </GlassButton>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input
          v-model="searchText"
          placeholder="搜索Webhook名称或描述"
          style="width: 300px;"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- Webhook列表 -->
      <el-table :data="webhooks" stripe v-loading="loading">
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="script_name" label="关联脚本" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.execution_mode === 'sync' ? 'warning' : 'info'">
              {{ row.execution_mode === 'sync' ? '同步' : '异步' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Token验证" width="100" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.token_enabled" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#ccc"><Close /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="统计" width="180">
          <template #default="{ row }">
            <div class="stats">
              <span>调用: {{ row.call_count }}</span>
              <span style="color: #67c23a;">成功: {{ row.success_count }}</span>
              <span style="color: #f56c6c;">失败: {{ row.failed_count }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最后调用" width="160">
          <template #default="{ row }">
            {{ formatTime(row.last_called_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <GlassButton label="URL" type="secondary" size="small" @click="showWebhookUrl(row)">
              <template #icon><Link /></template>
            </GlassButton>
            <GlassButton label="测试" type="primary" size="small" @click="handleTest(row)">
              <template #icon><VideoPlay /></template>
            </GlassButton>
            <GlassButton label="编辑" type="secondary" size="small" @click="handleEdit(row)" />
            <GlassButton label="删除" type="danger" size="small" @click="handleDelete(row)" />
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadWebhooks"
          @current-change="loadWebhooks"
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑Webhook' : '新建Webhook'"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="Webhook名称" prop="name">
          <el-input v-model="form.name" placeholder="输入Webhook名称" />
        </el-form-item>

        <el-form-item label="Webhook路径" prop="webhook_key">
          <el-input v-model="form.webhook_key" placeholder="留空自动生成，或自定义如: my-webhook">
            <template #append>
              <el-button @click="generateRandomKey">随机生成</el-button>
            </template>
          </el-input>
          <div class="form-tip">
            URL将为: /api/webhook/{{ form.webhook_key || '(自动生成)' }}<br>
            只能包含字母、数字、连字符和下划线
          </div>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="输入描述信息"
          />
        </el-form-item>

        <el-form-item label="关联脚本" prop="script_id">
          <el-select v-model="form.script_id" placeholder="选择脚本" style="width: 100%;" filterable>
            <el-option
              v-for="script in scripts"
              :key="script.id"
              :label="`${script.name} (${script.type})`"
              :value="script.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="执行模式" prop="execution_mode">
          <el-radio-group v-model="form.execution_mode">
            <el-radio label="async">异步执行</el-radio>
            <el-radio label="sync">同步执行</el-radio>
          </el-radio-group>
          <div class="form-tip">
            异步：立即返回，脚本在后台执行<br>
            同步：等待脚本执行完成后返回结果
          </div>
        </el-form-item>

        <el-form-item v-if="form.execution_mode === 'sync'" label="超时时间" prop="timeout">
          <el-input-number v-model="form.timeout" :min="5" :max="300" />
          <span style="margin-left: 10px;">秒</span>
        </el-form-item>

        <el-form-item label="Token验证">
          <el-switch v-model="form.token_enabled" />
          <div class="form-tip">
            启用后，调用Webhook需要提供Token
          </div>
        </el-form-item>

        <el-form-item label="保存请求信息">
          <el-switch v-model="form.pass_full_request" />
          <div class="form-tip">
            将完整请求信息（headers、body、query）保存到文件供脚本读取
          </div>
        </el-form-item>

        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <GlassButton label="取消" type="secondary" @click="dialogVisible = false" />
        <GlassButton label="确定" type="primary" @click="handleSubmit" :disabled="submitting" />
      </template>
    </el-dialog>

    <!-- Webhook URL对话框 -->
    <el-dialog v-model="urlDialogVisible" title="Webhook URL" width="700px">
      <div class="webhook-info">
        <el-form label-width="100px">
          <el-form-item label="Webhook URL">
            <el-input v-model="webhookUrl" readonly>
              <template #append>
                <el-button @click="copyToClipboard(webhookUrl)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item v-if="currentWebhook.token_enabled" label="Token">
            <el-input v-model="currentWebhook.token" readonly type="password" show-password>
              <template #append>
                <el-button @click="copyToClipboard(currentWebhook.token)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item v-if="currentWebhook.token_enabled">
            <el-button type="warning" @click="regenerateToken">
              <el-icon><Refresh /></el-icon>
              重新生成Token
            </el-button>
          </el-form-item>
        </el-form>

        <el-divider />

        <h4>调用示例</h4>
        <el-tabs>
          <el-tab-pane label="cURL">
            <pre class="code-block">{{ getCurlExample() }}</pre>
            <el-button size="small" @click="copyToClipboard(getCurlExample())">复制</el-button>
          </el-tab-pane>
          <el-tab-pane label="Python">
            <pre class="code-block">{{ getPythonExample() }}</pre>
            <el-button size="small" @click="copyToClipboard(getPythonExample())">复制</el-button>
          </el-tab-pane>
          <el-tab-pane label="JavaScript">
            <pre class="code-block">{{ getJavaScriptExample() }}</pre>
            <el-button size="small" @click="copyToClipboard(getJavaScriptExample())">复制</el-button>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 测试对话框 -->
    <el-dialog v-model="testDialogVisible" title="测试Webhook" width="700px">
      <el-form label-width="100px">
        <el-form-item label="请求方法">
          <el-select v-model="testRequest.method" style="width: 200px;">
            <el-option label="POST" value="POST" />
            <el-option label="GET" value="GET" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
        </el-form-item>

        <el-form-item label="请求Body">
          <el-input
            v-model="testRequest.body"
            type="textarea"
            :rows="10"
            placeholder='{"key": "value"}'
          />
        </el-form-item>

        <el-form-item label="Query参数">
          <el-input
            v-model="testRequest.query"
            placeholder="key1=value1&key2=value2"
          />
        </el-form-item>
      </el-form>

      <div v-if="testResponse" class="test-response">
        <h4>响应结果</h4>
        <el-tag :type="testResponse.success ? 'success' : 'danger'">
          {{ testResponse.success ? '成功' : '失败' }}
        </el-tag>
        <pre class="code-block">{{ JSON.stringify(testResponse.data, null, 2) }}</pre>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="executeTest" :loading="testing">发送测试</el-button>
      </template>
    </el-dialog>

    <!-- 使用指南对话框 -->
    <el-dialog v-model="showGuide" title="Webhook使用指南" width="800px">
      <div class="guide-content">
        <h3>什么是Webhook？</h3>
        <p>Webhook允许外部系统通过HTTP请求触发脚本执行，实现系统间的自动化集成。</p>

        <h3>使用步骤</h3>
        <ol>
          <li>创建Webhook，选择要执行的脚本</li>
          <li>配置执行模式（同步/异步）和安全选项</li>
          <li>获取Webhook URL和Token（如启用）</li>
          <li>在外部系统中配置Webhook URL</li>
          <li>外部系统发送HTTP请求触发脚本</li>
        </ol>

        <h3>参数传递</h3>
        <ul>
          <li><strong>环境变量：</strong>请求Body中的JSON字段自动转换为环境变量</li>
          <li><strong>完整请求：</strong>启用"保存请求信息"后，完整请求保存在 webhook_request.json</li>
          <li><strong>元数据：</strong>自动注入 WEBHOOK_ID、WEBHOOK_NAME、WEBHOOK_METHOD 等变量</li>
        </ul>

        <h3>脚本示例（Python）</h3>
        <pre class="code-block">
import os
import json

# 读取环境变量
user_id = os.environ.get('USER_ID')
action = os.environ.get('ACTION')

# 读取完整请求信息
with open('webhook_request.json', 'r') as f:
    request_data = json.load(f)
    headers = request_data['headers']
    body = request_data['body']

print(f'处理用户 {user_id} 的 {action} 请求')
        </pre>

        <h3>脚本示例（JavaScript）</h3>
        <pre class="code-block">
const fs = require('fs');

// 读取环境变量
const userId = process.env.USER_ID;
const action = process.env.ACTION;

// 读取完整请求信息
const request = JSON.parse(fs.readFileSync('webhook_request.json', 'utf8'));
const headers = request.headers;
const body = request.body;

console.log(`处理用户 ${userId} 的 ${action} 请求`);
        </pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Plus, Search, Link, VideoPlay, Check, Close,
  CopyDocument, Refresh
} from '@element-plus/icons-vue'
import axios from 'axios'
import {
  getWebhooks, getWebhook, createWebhook, updateWebhook,
  deleteWebhook, regenerateWebhookToken, toggleWebhook
} from '@/api/webhooks'
import GlassButton from '../components/GlassButton.vue'

// 数据
const webhooks = ref([])
const scripts = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchText = ref('')
const loading = ref(false)
const submitting = ref(false)

// 对话框
const dialogVisible = ref(false)
const urlDialogVisible = ref(false)
const testDialogVisible = ref(false)
const showGuide = ref(false)
const isEdit = ref(false)

// 表单
const formRef = ref(null)
const form = ref({
  name: '',
  webhook_key: '',
  description: '',
  script_id: null,
  execution_mode: 'async',
  timeout: 30,
  token_enabled: false,
  pass_full_request: true,
  enabled: true
})

const rules = {
  name: [{ required: true, message: '请输入Webhook名称', trigger: 'blur' }],
  script_id: [{ required: true, message: '请选择脚本', trigger: 'change' }]
}

// 当前webhook
const currentWebhook = ref({})
const webhookUrl = ref('')

// 测试
const testRequest = ref({
  method: 'POST',
  body: '{\n  "param1": "value1",\n  "param2": "value2"\n}',
  query: ''
})
const testResponse = ref(null)
const testing = ref(false)

// 方法
const loadWebhooks = async () => {
  loading.value = true
  try {
    const response = await getWebhooks({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchText.value
    })
    webhooks.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载Webhook列表失败')
  } finally {
    loading.value = false
  }
}

const loadScripts = async () => {
  try {
    const response = await axios.get('/api/scripts')
    scripts.value = response.data.data
  } catch (error) {
    ElMessage.error('加载脚本列表失败')
  }
}

const handleCreate = () => {
  isEdit.value = false
  form.value = {
    name: '',
    webhook_key: '',
    description: '',
    script_id: null,
    execution_mode: 'async',
    timeout: 30,
    token_enabled: false,
    pass_full_request: true,
    enabled: true
  }
  dialogVisible.value = true
}

const handleEdit = (webhook) => {
  isEdit.value = true
  form.value = { ...webhook }
  dialogVisible.value = true
}

const generateRandomKey = () => {
  // 生成随机的webhook_key，格式为：小写字母+数字，长度16位
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 16; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  form.value.webhook_key = result
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await updateWebhook(form.value.id, form.value)
        ElMessage.success('更新成功')
      } else {
        await createWebhook(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadWebhooks()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (webhook) => {
  try {
    await ElMessageBox.confirm('确定要删除这个Webhook吗？', '确认删除', {
      type: 'warning'
    })
    await deleteWebhook(webhook.id)
    ElMessage.success('删除成功')
    loadWebhooks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const showWebhookUrl = (webhook) => {
  currentWebhook.value = webhook
  webhookUrl.value = `${window.location.origin}${webhook.webhook_url}`
  urlDialogVisible.value = true
}

const handleTest = (webhook) => {
  currentWebhook.value = webhook
  testResponse.value = null
  testDialogVisible.value = true
}

const executeTest = async () => {
  testing.value = true
  testResponse.value = null

  try {
    const url = `${window.location.origin}${currentWebhook.value.webhook_url}`
    let body = null

    try {
      body = JSON.parse(testRequest.value.body)
    } catch {
      body = testRequest.value.body
    }

    const config = {
      method: testRequest.value.method,
      url: url,
      data: body
    }

    if (currentWebhook.value.token_enabled) {
      config.headers = {
        'Authorization': `Bearer ${currentWebhook.value.token}`
      }
    }

    const response = await axios(config)
    testResponse.value = {
      success: true,
      data: response.data
    }
  } catch (error) {
    testResponse.value = {
      success: false,
      data: error.response?.data || { error: error.message }
    }
  } finally {
    testing.value = false
  }
}

const regenerateToken = async () => {
  try {
    await ElMessageBox.confirm('重新生成Token后，旧Token将失效，确定继续吗？', '确认', {
      type: 'warning'
    })

    const response = await regenerateWebhookToken(currentWebhook.value.id)
    currentWebhook.value.token = response.data.data.token
    ElMessage.success('Token已重新生成')
    loadWebhooks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('生成失败')
    }
  }
}

const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

const getCurlExample = () => {
  const url = webhookUrl.value
  const token = currentWebhook.value.token

  let cmd = `curl -X POST "${url}" \\\n`
  if (token) {
    cmd += `  -H "Authorization: Bearer ${token}" \\\n`
  }
  cmd += `  -H "Content-Type: application/json" \\\n`
  cmd += `  -d '{"param1": "value1", "param2": "value2"}'`

  return cmd
}

const getPythonExample = () => {
  const url = webhookUrl.value
  const token = currentWebhook.value.token

  return `import requests

url = "${url}"
headers = {
    "Content-Type": "application/json",
${token ? `    "Authorization": "Bearer ${token}",\n` : ''}}
data = {
    "param1": "value1",
    "param2": "value2"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())`
}

const getJavaScriptExample = () => {
  const url = webhookUrl.value
  const token = currentWebhook.value.token

  return `fetch('${url}', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
${token ? `    'Authorization': 'Bearer ${token}',\n` : ''}  },
  body: JSON.stringify({
    param1: 'value1',
    param2: 'value2'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));`
}

const handleSearch = () => {
  currentPage.value = 1
  loadWebhooks()
}

const formatTime = (time) => {
  if (!time) return '从未调用'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadWebhooks()
  loadScripts()
})
</script>

<style scoped>
.webhooks-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  margin-bottom: 20px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.webhook-info {
  padding: 10px;
}

.code-block {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.test-response {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.guide-content {
  padding: 10px;
}

.guide-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #409eff;
}

.guide-content ol, .guide-content ul {
  padding-left: 25px;
}

.guide-content li {
  margin-bottom: 8px;
}
</style>
