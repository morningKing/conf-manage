<template>
  <div class="ai-settings">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">AI配置管理</span>
        <GlassButton label="添加配置" type="primary" size="small" @click="showAddDialog" />
      </div>

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
        <el-table-column label="操作" width="230">
          <template #default="{ row }">
            <GlassButton v-if="!row.is_active" label="激活" type="primary" size="small" @click="activateConfig(row)" />
            <GlassButton label="编辑" type="secondary" size="small" @click="editConfig(row)" />
            <GlassButton label="删除" type="danger" size="small" @click="deleteConfig(row)" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 清理管理 -->
    <div class="glass-card cleanup-section" style="margin-top: 20px">
      <div class="glass-card-header">
        <span class="glass-card-title">清理管理</span>
      </div>
      <div class="glass-card-body">
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :span="6">
            <el-statistic title="总执行记录" :value="cleanupStats.total_executions" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="白名单记录" :value="cleanupStats.whitelist_count" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="待清理" :value="cleanupStats.to_cleanup" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="执行空间(MB)" :value="cleanupStats.execution_space_size" :precision="2" />
          </el-col>
        </el-row>
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <div class="config-item">
              <span class="config-label">保留阈值：</span>
              <el-input-number
                v-model="cleanupThreshold"
                :min="50"
                :max="10000"
                :step="100"
                style="width: 150px"
              />
              <span class="config-hint">条记录</span>
            </div>
          </el-col>
          <el-col :span="8" :offset="8" style="text-align: right">
            <GlassButton
              label="保存配置"
              type="secondary"
              size="small"
              @click="handleSaveCleanupConfig"
              :loading="cleanupLoading"
              style="margin-right: 10px"
            />
            <GlassButton
              label="立即清理"
              type="danger"
              size="small"
              @click="handleExecuteCleanup"
              :loading="cleanupLoading"
            />
          </el-col>
        </el-row>
      </div>
    </div>

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
        <GlassButton label="取消" type="secondary" @click="dialogVisible = false" />
        <GlassButton label="确定" type="primary" @click="submitForm" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import GlassButton from '../components/GlassButton.vue'
import request from '@/api/request'
import { getCleanupStats, executeCleanup, getCleanupConfig, updateCleanupConfig } from '../api'

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

// 清理管理状态
const cleanupStats = ref({
  total_executions: 0,
  whitelist_count: 0,
  to_cleanup: 0,
  execution_space_size: 0
})
const cleanupThreshold = ref(500)
const cleanupLoading = ref(false)

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

// 清理管理方法
const loadCleanupStats = async () => {
  try {
    const response = await getCleanupStats()
    cleanupStats.value = {
      total_executions: response.data.total_executions || 0,
      whitelist_count: response.data.whitelisted_executions || 0,
      to_cleanup: response.data.to_cleanup || 0,
      execution_space_size: response.data.execution_spaces_size_mb || 0
    }
  } catch (error) {
    console.error('加载清理统计失败:', error)
  }
}

const handleSaveCleanupConfig = async () => {
  try {
    cleanupLoading.value = true
    await updateCleanupConfig({ threshold: cleanupThreshold.value })
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('保存配置失败')
  } finally {
    cleanupLoading.value = false
  }
}

const handleExecuteCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要执行清理吗？将清理 ${cleanupStats.value.to_cleanup} 条执行记录。`,
      '清理确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleanupLoading.value = true
    const response = await executeCleanup()
    ElMessage.success(`清理完成，删除了 ${response.data.deleted_executions || 0} 条记录`)
    loadCleanupStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理执行失败')
    }
  } finally {
    cleanupLoading.value = false
  }
}

onMounted(() => {
  loadConfigs()
  loadCleanupStats()
  getCleanupConfig().then(response => {
    cleanupThreshold.value = response.data.threshold || 500
  }).catch(() => {
    // 使用默认值
  })
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

.cleanup-section .glass-card-body {
  padding: 20px;
}

.config-item {
  display: flex;
  align-items: center;
}

.config-label {
  font-size: 14px;
  color: #606266;
  margin-right: 10px;
}

.config-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}
</style>
