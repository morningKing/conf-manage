<template>
  <div class="global-variables-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>全局变量管理</span>
          <el-button type="primary" @click="showCreateDialog">新增变量</el-button>
        </div>
      </template>

      <!-- 变量列表 -->
      <el-table :data="variables" style="width: 100%">
        <el-table-column prop="key" label="变量名" width="200" />
        <el-table-column prop="value" label="变量值" :show-overflow-tooltip="true">
          <template #default="{ row }">
            <span v-if="row.is_encrypted" class="encrypted-value">{{ row.value }}</span>
            <span v-else>{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" :show-overflow-tooltip="true" />
        <el-table-column prop="is_encrypted" label="加密" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_encrypted" type="warning" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editVariable(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteVariable(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="variables.length === 0" description="暂无全局变量" />
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentVariable ? '编辑全局变量' : '新增全局变量'"
      width="600px"
    >
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="变量名" prop="key">
          <el-input
            v-model="form.key"
            placeholder="请输入变量名（如：API_KEY、DB_HOST）"
            :disabled="!!currentVariable"
          />
          <div class="form-tip">变量名只能包含字母、数字和下划线</div>
        </el-form-item>
        <el-form-item label="变量值" prop="value">
          <el-input
            v-model="form.value"
            :type="form.is_encrypted ? 'password' : 'text'"
            placeholder="请输入变量值"
            show-password
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            rows="3"
            placeholder="请输入变量描述"
          />
        </el-form-item>
        <el-form-item label="是否加密">
          <el-switch v-model="form.is_encrypted" />
          <div class="form-tip">加密后的变量值在列表中会显示为 ******</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getGlobalVariables,
  createGlobalVariable,
  updateGlobalVariable,
  deleteGlobalVariable as deleteGlobalVariableApi
} from '@/api/globalVariables'

const variables = ref([])
const dialogVisible = ref(false)
const currentVariable = ref(null)
const formRef = ref(null)

const form = ref({
  key: '',
  value: '',
  description: '',
  is_encrypted: false
})

const rules = {
  key: [
    { required: true, message: '请输入变量名', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9_]+$/,
      message: '变量名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  value: [{ required: true, message: '请输入变量值', trigger: 'blur' }]
}

// 加载全局变量列表
const loadVariables = async () => {
  try {
    const res = await getGlobalVariables()
    variables.value = res.data
  } catch (error) {
    ElMessage.error('加载全局变量列表失败')
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  currentVariable.value = null
  form.value = {
    key: '',
    value: '',
    description: '',
    is_encrypted: false
  }
  dialogVisible.value = true
}

// 编辑变量
const editVariable = async (variable) => {
  try {
    currentVariable.value = variable
    form.value = {
      key: variable.key,
      value: variable.value,
      description: variable.description || '',
      is_encrypted: variable.is_encrypted
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载变量详情失败')
  }
}

// 保存变量
const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (currentVariable.value) {
        await updateGlobalVariable(currentVariable.value.id, form.value)
        ElMessage.success('更新成功')
      } else {
        await createGlobalVariable(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadVariables()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '保存失败')
    }
  })
}

// 删除变量
const deleteVariable = async (variable) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除变量 "${variable.key}" 吗？删除后脚本将无法使用该变量。`,
      '提示',
      {
        type: 'warning'
      }
    )

    await deleteGlobalVariableApi(variable.id)
    ElMessage.success('删除成功')
    loadVariables()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadVariables()
})
</script>

<style scoped>
.global-variables-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.encrypted-value {
  color: #909399;
  font-style: italic;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
