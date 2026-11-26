<template>
  <div class="global-variables-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">全局变量管理</span>
        <GlassButton label="新增变量" type="primary" size="small" @click="showCreateDialog" />
      </div>

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
            <GlassButton label="编辑" type="secondary" size="small" @click="editVariable(row)" />
            <GlassButton label="删除" type="danger" size="small" @click="deleteVariable(row)" />
          </template>
        </el-table-column>
      </el-table>

          </div>

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
        <GlassButton label="取消" type="secondary" @click="dialogVisible = false" />
        <GlassButton label="保存" type="primary" @click="handleSave" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import GlassButton from '../components/GlassButton.vue'
import {
  getGlobalVariables,
  createGlobalVariable,
  updateGlobalVariable,
  deleteGlobalVariable as deleteGlobalVariableApi
} from '@/api/globalVariables'
import { useCrud } from '@/composables/useCrud'

const formRef = ref(null)

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

const {
  items: variables,
  dialogVisible,
  current: currentVariable,
  form,
  load: loadVariables,
  openCreate: showCreateDialog,
  openEdit: editVariable,
  save: handleSave,
  removeRow: deleteVariable,
} = useCrud({
  list: async () => (await getGlobalVariables()).data,
  create: (val) => createGlobalVariable(val),
  update: (id, val) => updateGlobalVariable(id, val),
  remove: (row) => deleteGlobalVariableApi(row.id),
  emptyForm: () => ({ key: '', value: '', description: '', is_encrypted: false }),
  toForm: (row) => ({
    key: row.key,
    value: row.value,
    description: row.description || '',
    is_encrypted: row.is_encrypted,
  }),
  validate: () => new Promise((resolve) => {
    if (!formRef.value) {
      resolve(false)
      return
    }
    formRef.value.validate((valid) => resolve(valid))
  }),
  confirmText: (row) => `确定要删除变量 "${row.key}" 吗？删除后脚本将无法使用该变量。`,
  name: '变量',
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(loadVariables)
</script>

<style scoped>
.global-variables-container {
  padding: 12px;
}


.encrypted-value {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
