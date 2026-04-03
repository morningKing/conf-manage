<template>
  <div class="selection-panel" v-if="sessionId">
    <!-- 选择计数 -->
    <div class="selection-info">
      <el-badge :value="count" :max="1000" class="selection-badge">
        <el-button size="small" @click="showDetail">
          <el-icon><Select /></el-icon>
          已选择
        </el-button>
      </el-badge>
      <span class="max-hint" v-if="count >= 1000">
        (已达上限)
      </span>
    </div>

    <!-- 批量操作按钮 -->
    <div class="selection-actions">
      <el-button
        type="danger"
        size="small"
        :disabled="count === 0"
        :loading="deleteLoading"
        @click="handleBatchDelete"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
      <el-button
        size="small"
        :disabled="count === 0"
        @click="handleClear"
      >
        清空选择
      </el-button>
    </div>

    <!-- 选中详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="已选择的执行记录"
      width="60%"
      top="10vh"
    >
      <el-table :data="selectedItems" max-height="400" v-loading="detailLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="script_name" label="脚本名称" min-width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              link
              @click="handleRemoveItem(row.id)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="danger" @click="handleBatchDelete" :disabled="selectedItems.length === 0">
          删除全部 ({{ selectedItems.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Select, Delete } from '@element-plus/icons-vue'
import {
  createSelectionSession,
  getSelectionSession,
  addToSelection,
  removeFromSelection,
  clearSelection,
  deleteSelectionBatch
} from '../api'

const props = defineProps({
  initialIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['change', 'deleted'])

const sessionId = ref(null)
const count = ref(0)
const selectedItems = ref([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const deleteLoading = ref(false)

const initSession = async () => {
  try {
    const res = await createSelectionSession()
    sessionId.value = res.data.session_id

    if (props.initialIds.length > 0) {
      await handleAddItems(props.initialIds)
    }
  } catch (error) {
    console.error('创建选择会话失败:', error)
  }
}

const handleAddItems = async (ids) => {
  if (!sessionId.value) return

  try {
    const res = await addToSelection(sessionId.value, ids)
    count.value = res.data.count

    if (res.data.max_reached) {
      ElMessage.warning('已达到最大选择数量1000条')
    }

    emit('change', { count: count.value, maxReached: res.data.max_reached })
  } catch (error) {
    ElMessage.error('添加选择失败: ' + error.message)
  }
}

const handleRemoveItem = async (id) => {
  if (!sessionId.value) return

  try {
    const res = await removeFromSelection(sessionId.value, [id])
    count.value = res.data.count
    selectedItems.value = selectedItems.value.filter(item => item.id !== id)
    emit('change', { count: count.value })
  } catch (error) {
    ElMessage.error('移除失败: ' + error.message)
  }
}

const showDetail = async () => {
  if (!sessionId.value) return

  detailVisible.value = true
  detailLoading.value = true

  try {
    const res = await getSelectionSession(sessionId.value)
    selectedItems.value = res.data.items || []
    count.value = res.data.count
  } catch (error) {
    ElMessage.error('获取选择详情失败: ' + error.message)
  } finally {
    detailLoading.value = false
  }
}

const handleClear = async () => {
  if (!sessionId.value) return

  try {
    await clearSelection(sessionId.value)
    count.value = 0
    selectedItems.value = []
    emit('change', { count: 0 })
    ElMessage.success('选择已清空')
  } catch (error) {
    ElMessage.error('清空失败: ' + error.message)
  }
}

const handleBatchDelete = async () => {
  if (!sessionId.value || count.value === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${count.value} 条执行记录？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleteLoading.value = true
    const res = await deleteSelectionBatch(sessionId.value)

    if (res.code === 0) {
      const { success, failed } = res.data
      if (success > 0) {
        ElMessage.success(`成功删除 ${success} 条记录`)
      }
      if (failed > 0) {
        ElMessage.warning(`失败 ${failed} 条`)
      }

      count.value = 0
      selectedItems.value = []
      detailVisible.value = false
      emit('deleted', res.data)
      emit('change', { count: 0 })
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + error.message)
    }
  } finally {
    deleteLoading.value = false
  }
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败'
  }
  return texts[status] || status
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

defineExpose({
  handleAddItems,
  handleRemoveItem,
  handleClear,
  showDetail,
  sessionId,
  count
})

onMounted(() => {
  initSession()
})
</script>

<style scoped>
.selection-panel {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background-color: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
  margin-bottom: 16px;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-badge {
  margin-right: 4px;
}

.max-hint {
  color: #e6a23c;
  font-size: 12px;
}

.selection-actions {
  display: flex;
  gap: 8px;
}
</style>