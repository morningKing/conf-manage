<template>
  <div class="tags-container">
    <div class="glass-card">
      <div class="glass-card-header">
        <span class="glass-card-title">标签管理</span>
        <el-button size="small" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新建标签
        </el-button>
      </div>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="name" label="标签名称" width="200" />
        <el-table-column label="标签预览" width="200">
          <template #default="{ row }">
            <el-tag :color="row.color" effect="plain">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="颜色" width="150">
          <template #default="{ row }">
            <div class="color-cell">
              <div class="color-chip" :style="{ backgroundColor: row.color }" />
              <span>{{ row.color }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeRow(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑标签' : '新建标签'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="标签名称">
          <el-input v-model="form.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <ColorPicker
            v-model="form.color"
            :preview-text="form.name || '标签'"
            :show-alpha="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getTags, createTag, updateTag, deleteTag } from '../api'
import { Plus } from '@element-plus/icons-vue'
import ColorPicker from '../components/ColorPicker.vue'
import { useCrud } from '@/composables/useCrud'

const {
  items, loading, dialogVisible, isEdit, form,
  load, openCreate, openEdit, save, removeRow,
} = useCrud({
  list: async () => (await getTags()).data,
  create: (val) => createTag(val),
  update: (id, val) => updateTag(id, val),
  remove: (row) => deleteTag(row.id),
  emptyForm: () => ({ name: '', color: '#67C23A' }),
  toForm: (row) => ({ ...row }),
  validate: (val) => {
    if (!val.name) {
      ElMessage.warning('请输入标签名称')
      return false
    }
    return true
  },
  confirmText: () => '确定要删除此标签吗？',
  name: '标签',
})

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(load)
</script>

<style scoped>
.tags-container {
  padding: 0;
}

.color-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-chip {
  width: 40px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
}
</style>
