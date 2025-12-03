<template>
  <div class="categories-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>分类管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建分类
          </el-button>
        </div>
      </template>

      <el-table :data="categories" stripe>
        <el-table-column prop="name" label="分类名称" width="200" />
        <el-table-column label="颜色" width="150">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 10px;">
              <div
                :style="{
                  width: '40px',
                  height: '20px',
                  backgroundColor: row.color,
                  borderRadius: '4px'
                }"
              />
              <span>{{ row.color }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="分类名称">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入分类描述" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" show-alpha />
          <span style="margin-left: 10px; color: #909399;">{{ form.color }}</span>
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="图标名称（可选）" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :step="1" />
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
import { getCategories, createCategory, updateCategory, deleteCategory } from '../api'
import { Plus } from '@element-plus/icons-vue'

const categories = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建分类')
const form = ref({
  name: '',
  description: '',
  color: '#409EFF',
  icon: '',
  sort_order: 0
})
const currentCategory = ref(null)

const loadCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载分类失败')
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建分类'
  form.value = {
    name: '',
    description: '',
    color: '#409EFF',
    icon: '',
    sort_order: 0
  }
  currentCategory.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑分类'
  form.value = { ...row }
  currentCategory.value = row
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!form.value.name) {
      ElMessage.warning('请输入分类名称')
      return
    }

    if (currentCategory.value) {
      await updateCategory(currentCategory.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCategory(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadCategories()
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此分类吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteCategory(row.id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.categories-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
