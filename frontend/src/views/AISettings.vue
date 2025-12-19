<template>
  <div class="ai-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI配置管理</span>
          <el-button type="primary" @click="showAddDialog">添加配置</el-button>
        </div>
      </template>

      <el-table :data="configs" style="width: 100%">
        <el-table-column prop="provider" label="提供商" width="120" />
        <el-table-column prop="model" label="模型" width="150" />
        <el-table-column prop="api_key" label="API Key" width="200">
          <template #default="{ row }">
            <span>{{ row.api_key }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="Base URL">
          <template #default="{ row }">
            <span>{{ row.base_url || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button v-if="!row.is_active" size="small" type="primary" @click="activateConfig(row)">
              激活
            </el-button>
            <el-button size="small" @click="editConfig(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteConfig(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑AI配置' : '添加AI配置'"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="请选择提供商">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            placeholder="请输入API Key"
            show-password
          />
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="留空使用默认URL" />
          <div class="help-text">
            OpenAI默认: https://api.openai.com/v1
          </div>
        </el-form-item>

        <el-form-item label="模型" prop="model">
          <el-input v-model="form.model" placeholder="例如: gpt-4, claude-3-opus-20240229" />
        </el-form-item>

        <el-form-item label="设为激活">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const configs = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  provider: 'openai',
  api_key: '',
  base_url: '',
  model: 'gpt-4',
  is_active: true
})

const rules = {
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }]
}

const loadConfigs = async () => {
  try {
    const response = await request.get('/ai-configs')
    configs.value = response
  } catch (error) {
    ElMessage.error('加载AI配置失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = {
    provider: 'openai',
    api_key: '',
    base_url: '',
    model: 'gpt-4',
    is_active: true
  }
  dialogVisible.value = true
}

const editConfig = (config) => {
  isEdit.value = true
  form.value = {
    id: config.id,
    provider: config.provider,
    api_key: '',  // 安全起见，不回显API key
    base_url: config.base_url || '',
    model: config.model,
    is_active: config.is_active
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value.validate()

    if (isEdit.value) {
      await request.put(`/ai-configs/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/ai-configs', form.value)
      ElMessage.success('添加成功')
    }

    dialogVisible.value = false
    loadConfigs()
  } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data.error || '操作失败')
    }
  }
}

const activateConfig = async (config) => {
  try {
    await request.post(`/ai-configs/${config.id}/activate`)
    ElMessage.success('激活成功')
    loadConfigs()
  } catch (error) {
    ElMessage.error('激活失败')
  }
}

const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm('确定要删除此配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await request.delete(`/ai-configs/${config.id}`)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.ai-settings {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
