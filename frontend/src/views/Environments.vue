<template>
  <div class="environments-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行环境管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建环境
          </el-button>
        </div>
      </template>

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
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button
                  size="small"
                  type="success"
                  @click="handleSetDefault(row)"
                  :disabled="row.is_default"
                >
                  设为默认
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button
                  size="small"
                  type="success"
                  @click="handleSetDefault(row)"
                  :disabled="row.is_default"
                >
                  设为默认
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getEnvironments,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  setDefaultEnvironment,
  detectEnvironment
} from '../api'

const activeTab = ref('python')
const environments = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建环境')
const currentEnvironment = ref(null)
const detecting = ref(false)
const saving = ref(false)
const detectedVersion = ref('')
const formRef = ref(null)

const form = ref({
  name: '',
  type: 'python',
  executable_path: '',
  description: '',
  is_default: false
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  executable_path: [{ required: true, message: '请输入解释器路径', trigger: 'blur' }]
}

const pythonEnvironments = computed(() => {
  return environments.value.filter(env => env.type === 'python')
})

const nodeEnvironments = computed(() => {
  return environments.value.filter(env => env.type === 'javascript')
})

const loadEnvironments = async () => {
  try {
    const res = await getEnvironments()
    environments.value = res.data
  } catch (error) {
    ElMessage.error('加载环境列表失败')
    console.error(error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建环境'
  form.value = {
    name: '',
    type: activeTab.value,
    executable_path: '',
    description: '',
    is_default: false
  }
  currentEnvironment.value = null
  detectedVersion.value = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑环境'
  form.value = { ...row }
  currentEnvironment.value = row
  detectedVersion.value = row.version || ''
  dialogVisible.value = true
}

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

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (currentEnvironment.value) {
        await updateEnvironment(currentEnvironment.value.id, form.value)
        ElMessage.success('更新成功')
      } else {
        await createEnvironment(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadEnvironments()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '保存失败')
    } finally {
      saving.value = false
    }
  })
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

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteEnvironment(row.id)
    ElMessage.success('删除成功')
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.environments-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
