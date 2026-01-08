<template>
  <div class="backup-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>备份管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 系统备份 Tab -->
        <el-tab-pane label="系统备份" name="system">
          <div class="backup-actions">
            <el-button type="primary" @click="showCreateBackupDialog" :loading="creating">
              <el-icon><FolderAdd /></el-icon>
              创建系统备份
            </el-button>
            <el-button type="success" @click="exportDb" :loading="exporting">
              <el-icon><Download /></el-icon>
              导出数据库
            </el-button>
            <el-button type="warning" @click="showCleanDialog">
              <el-icon><Delete /></el-icon>
              清理旧备份
            </el-button>
            <el-button @click="loadBackups" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 备份列表 -->
          <el-table :data="backups" style="width: 100%; margin-top: 20px" v-loading="loading">
            <el-table-column prop="name" label="文件名" min-width="200" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'database' ? 'success' : 'primary'">
                  {{ row.type === 'database' ? '数据库' : '系统' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="size_mb" label="大小" width="120">
              <template #default="{ row }">
                {{ row.size_mb }} MB
              </template>
            </el-table-column>
            <el-table-column prop="created" label="创建时间" width="180" />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="downloadFile(row)">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
                <el-button link type="danger" @click="deleteFile(row)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="backups.length === 0 && !loading" class="empty-hint">
            <el-empty description="暂无备份文件" />
          </div>
        </el-tab-pane>

        <!-- 数据库信息 Tab -->
        <el-tab-pane label="数据库信息" name="database">
          <el-button type="primary" @click="loadDatabaseInfo" :loading="loadingDbInfo">
            <el-icon><Refresh /></el-icon>
            刷新数据库信息
          </el-button>

          <div v-if="databaseInfo" class="database-info">
            <el-descriptions :column="2" border style="margin-top: 20px">
              <el-descriptions-item label="数据库路径">
                {{ databaseInfo.path }}
              </el-descriptions-item>
              <el-descriptions-item label="数据库大小">
                {{ databaseInfo.size_mb }} MB
              </el-descriptions-item>
            </el-descriptions>

            <el-divider>数据表统计</el-divider>

            <el-table :data="databaseInfo.tables" style="width: 100%">
              <el-table-column prop="name" label="表名" />
              <el-table-column prop="count" label="记录数" width="150">
                <template #default="{ row }">
                  <el-tag>{{ row.count }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else-if="!loadingDbInfo" class="empty-hint">
            <el-empty description="点击刷新按钮加载数据库信息" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建系统备份对话框 -->
    <el-dialog
      v-model="createBackupDialogVisible"
      title="创建系统备份"
      width="500px"
    >
      <el-form :model="backupForm" label-width="140px">
        <el-form-item label="备份名称">
          <el-input
            v-model="backupForm.backup_name"
            placeholder="留空自动生成时间戳命名"
          />
        </el-form-item>
        <el-form-item label="包含日志文件">
          <el-switch v-model="backupForm.include_logs" />
        </el-form-item>
        <el-form-item label="包含执行空间">
          <el-switch v-model="backupForm.include_execution_spaces" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createBackupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createBackup" :loading="creating">
          创建备份
        </el-button>
      </template>
    </el-dialog>

    <!-- 清理旧备份对话框 -->
    <el-dialog
      v-model="cleanDialogVisible"
      title="清理旧备份"
      width="400px"
    >
      <el-form :model="cleanForm" label-width="120px">
        <el-form-item label="保留天数">
          <el-input-number
            v-model="cleanForm.keep_days"
            :min="1"
            :max="365"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px">
            将删除 {{ cleanForm.keep_days }} 天前的所有备份文件
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="cleanDialogVisible = false">取消</el-button>
        <el-button type="warning" @click="cleanBackups" :loading="cleaning">
          开始清理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderAdd,
  Download,
  Delete,
  Refresh
} from '@element-plus/icons-vue'
import {
  getBackupList,
  createSystemBackup,
  exportDatabase,
  downloadBackup,
  deleteBackup,
  cleanOldBackups,
  getDatabaseInfo
} from '@/api/backup'

// 状态
const activeTab = ref('system')
const backups = ref([])
const loading = ref(false)
const creating = ref(false)
const exporting = ref(false)
const cleaning = ref(false)
const loadingDbInfo = ref(false)
const databaseInfo = ref(null)

// 对话框
const createBackupDialogVisible = ref(false)
const cleanDialogVisible = ref(false)

// 表单
const backupForm = ref({
  backup_name: '',
  include_logs: false,
  include_execution_spaces: true
})

const cleanForm = ref({
  keep_days: 30
})

// 加载备份列表
const loadBackups = async () => {
  try {
    loading.value = true
    const data = await getBackupList()
    backups.value = data.items || []
  } catch (error) {
    ElMessage.error('加载备份列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示创建备份对话框
const showCreateBackupDialog = () => {
  backupForm.value = {
    backup_name: '',
    include_logs: false,
    include_execution_spaces: true
  }
  createBackupDialogVisible.value = true
}

// 创建系统备份
const createBackup = async () => {
  try {
    creating.value = true
    const data = await createSystemBackup(backupForm.value)
    ElMessage.success(data.message || '系统备份成功')
    createBackupDialogVisible.value = false
    await loadBackups()
  } catch (error) {
    ElMessage.error('创建备份失败: ' + error.message)
  } finally {
    creating.value = false
  }
}

// 导出数据库
const exportDb = async () => {
  try {
    exporting.value = true
    const data = await exportDatabase()
    ElMessage.success(data.message || '数据库导出成功')
    await loadBackups()
  } catch (error) {
    ElMessage.error('导出数据库失败: ' + error.message)
  } finally {
    exporting.value = false
  }
}

// 下载文件
const downloadFile = (row) => {
  const url = downloadBackup(row.name)
  window.open(url, '_blank')
}

// 删除文件
const deleteFile = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份文件 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteBackup(row.name)
    ElMessage.success('删除成功')
    await loadBackups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 显示清理对话框
const showCleanDialog = () => {
  cleanForm.value.keep_days = 30
  cleanDialogVisible.value = true
}

// 清理旧备份
const cleanBackups = async () => {
  try {
    cleaning.value = true
    const data = await cleanOldBackups(cleanForm.value.keep_days)
    ElMessage.success(data.message || '清理成功')
    cleanDialogVisible.value = false
    await loadBackups()
  } catch (error) {
    ElMessage.error('清理失败: ' + error.message)
  } finally {
    cleaning.value = false
  }
}

// 加载数据库信息
const loadDatabaseInfo = async () => {
  try {
    loadingDbInfo.value = true
    databaseInfo.value = await getDatabaseInfo()
  } catch (error) {
    ElMessage.error('加载数据库信息失败: ' + error.message)
  } finally {
    loadingDbInfo.value = false
  }
}

// 页面加载时获取备份列表
onMounted(() => {
  loadBackups()
})
</script>

<style scoped>
.backup-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.backup-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.empty-hint {
  padding: 40px 0;
  text-align: center;
}

.database-info {
  margin-top: 20px;
}
</style>
