<template>
  <div class="tags-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建标签
          </el-button>
        </div>
      </template>

      <el-table :data="tags" stripe>
        <el-table-column prop="name" label="标签名称" width="200" />
        <el-table-column label="标签预览" width="200">
          <template #default="{ row }">
            <el-tag :color="row.color" effect="plain">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
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
      width="500px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="标签名称">
          <el-input v-model="form.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" show-alpha />
          <span style="margin-left: 10px; color: #909399;">{{ form.color }}</span>
        </el-form-item>
        <el-form-item label="预览">
          <el-tag :color="form.color" effect="plain">{{ form.name || '标签预览' }}</el-tag>
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
import { getTags, createTag, updateTag, deleteTag } from '../api'
import { Plus } from '@element-plus/icons-vue'

const tags = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建标签')
const form = ref({
  name: '',
  color: '#67C23A'
})
const currentTag = ref(null)

const loadTags = async () => {
  try {
    const res = await getTags()
    tags.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载标签失败')
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建标签'
  form.value = {
    name: '',
    color: '#67C23A'
  }
  currentTag.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑标签'
  form.value = { ...row }
  currentTag.value = row
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (!form.value.name) {
      ElMessage.warning('请输入标签名称')
      return
    }

    if (currentTag.value) {
      await updateTag(currentTag.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createTag(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTags()
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此标签吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTag(row.id)
    ElMessage.success('删除成功')
    loadTags()
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
  loadTags()
})
</script>

<style scoped>
.tags-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
