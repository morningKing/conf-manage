<template>
  <div class="environments-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">执行环境管理</span>
        <GlassButton label="新建环境" type="primary" size="small" @click="handleCreate">
          <template #icon><Plus /></template>
        </GlassButton>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="Python 环境" name="python">
          <el-table :data="pythonEnvironments" stripe>
            <el-table-column prop="name" label="环境名称" width="200" />
            <el-table-column prop="version" label="版本" width="200" />
            <el-table-column prop="executable_path" label="解释器路径" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <GlassButton label="编辑" type="secondary" size="small" @click="handleEdit(row)" />
                <GlassButton label="设为默认" type="success" size="small" @click="handleSetDefault(row)" :disabled="row.is_default" />
                <GlassButton label="删除" type="danger" size="small" @click="handleDelete(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="Node.js 环境" name="javascript">
          <el-table :data="nodeEnvironments" stripe>
            <el-table-column prop="name" label="环境名称" width="200" />
            <el-table-column prop="version" label="版本" width="200" />
            <el-table-column prop="executable_path" label="解释器路径" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <GlassButton label="编辑" type="secondary" size="small" @click="handleEdit(row)" />
                <GlassButton label="设为默认" type="success" size="small" @click="handleSetDefault(row)" :disabled="row.is_default" />
                <GlassButton label="删除" type="danger" size="small" @click="handleDelete(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑环境' : '新建环境'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：Python 3.12" />
        </el-form-item>
        <el-form-item label="环境类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择环境类型" :disabled="!!currentEnvironment">
            <el-option label="Python" value="python" />
            <el-option label="Node.js / JavaScript" value="javascript" />
          </el-select>
        </el-form-item>
        <el-form-item label="解释器路径" prop="executable_path">
          <div style="width: 100%;">
            <el-input
              v-model="form.executable_path"
              placeholder="例如：/usr/bin/python3 或 C:\Python312\python.exe"
            >
              <template #append>
                <el-button @click="handleDetectVersion" :loading="detecting">检测版本</el-button>
              </template>
            </el-input>
            <div v-if="detectedVersion" style="margin-top: 8px; color: #67C23A; font-size: 12px;">
              检测到版本: {{ detectedVersion }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import GlassButton from '../components/GlassButton.vue'
import {
  getEnvironments,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  setDefaultEnvironment,
  detectEnvironment
} from '../api'
import { useCrud } from '@/composables/useCrud'

const activeTab = ref('python')
const detecting = ref(false)
const saving = ref(false)
const detectedVersion = ref('')
const formRef = ref(null)

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  executable_path: [{ required: true, message: '请输入解释器路径', trigger: 'blur' }]
}

const {
  items: environments,
  dialogVisible,
  isEdit,
  current: currentEnvironment,
  form,
  load: loadEnvironments,
  openCreate,
  openEdit,
  save,
  removeRow,
} = useCrud({
  list: async () => (await getEnvironments()).data,
  create: (val) => createEnvironment(val),
  update: (id, val) => updateEnvironment(id, val),
  remove: (row) => deleteEnvironment(row.id),
  emptyForm: () => ({
    name: '',
    type: activeTab.value,
    executable_path: '',
    description: '',
    is_default: false,
  }),
  toForm: (row) => ({ ...row }),
  validate: () => new Promise((resolve) => {
    if (!formRef.value) {
      resolve(false)
      return
    }
    formRef.value.validate((valid) => resolve(valid))
  }),
  confirmText: (row) => `确定要删除环境 "${row.name}" 吗？`,
  name: '环境',
})

const pythonEnvironments = computed(() =>
  environments.value.filter(env => env.type === 'python')
)

const nodeEnvironments = computed(() =>
  environments.value.filter(env => env.type === 'javascript')
)

const handleCreate = () => {
  openCreate()
  detectedVersion.value = ''
}

const handleEdit = (row) => {
  openEdit(row)
  detectedVersion.value = row.version || ''
}

const handleSave = async () => {
  saving.value = true
  try {
    await save()
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => removeRow(row)

const handleDetectVersion = async () => {
  if (!form.value.executable_path || !form.value.type) {
    ElMessage.warning('请先填写解释器路径和类型')
    return
  }

  detecting.value = true
  try {
    const res = await detectEnvironment({
      executable_path: form.value.executable_path,
      type: form.value.type
    })
    detectedVersion.value = res.data.version
    ElMessage.success('版本检测成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '版本检测失败')
  } finally {
    detecting.value = false
  }
}

const handleSetDefault = async (row) => {
  try {
    await setDefaultEnvironment(row.id)
    ElMessage.success('设置成功')
    loadEnvironments()
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

onMounted(loadEnvironments)
</script>

<style scoped>
.environments-container {
  padding: 12px;
}

</style>
