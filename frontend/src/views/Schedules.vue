<template>
  <div class="schedules-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>

      <el-table :data="schedules" stripe>
        <el-table-column prop="name" label="任务名称" width="200" />
        <el-table-column prop="script_name" label="脚本名称" width="200" />
        <el-table-column prop="cron" label="Cron表达式" width="150" />
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run" label="上次运行" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_run) }}
          </template>
        </el-table-column>
        <el-table-column prop="next_run" label="下次运行" width="180">
          <template #default="{ row }">
            {{ formatTime(row.next_run) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.enabled ? 'warning' : 'success'"
              @click="handleToggle(row)"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="info" @click="handleRunNow(row)">立即运行</el-button>
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
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="选择脚本">
          <el-select v-model="form.script_id" placeholder="请选择脚本" style="width: 100%">
            <el-option
              v-for="script in scripts"
              :key="script.id"
              :label="script.name"
              :value="script.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="form.cron" placeholder="例如: 0 0 * * * (每天零点)" />
          <div style="font-size: 12px; color: #999; margin-top: 5px">
            格式: 分 时 日 月 周 (例如: 0 0 * * * 表示每天零点)
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="执行参数">
          <el-input
            v-model="form.params"
            type="textarea"
            rows="3"
            placeholder='JSON格式,例如: {"key": "value"}'
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
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
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  toggleSchedule,
  runScheduleNow,
  getScripts
} from '../api'

const schedules = ref([])
const scripts = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const form = ref({
  name: '',
  script_id: null,
  cron: '',
  description: '',
  params: '{}',
  enabled: true
})
const currentSchedule = ref(null)

const loadSchedules = async () => {
  try {
    const res = await getSchedules()
    schedules.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadScripts = async () => {
  try {
    const res = await getScripts()
    scripts.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建任务'
  form.value = {
    name: '',
    script_id: null,
    cron: '',
    description: '',
    params: '{}',
    enabled: true
  }
  currentSchedule.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑任务'
  form.value = { ...row }
  currentSchedule.value = row
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (currentSchedule.value) {
      await updateSchedule(currentSchedule.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createSchedule(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadSchedules()
  } catch (error) {
    console.error(error)
  }
}

const handleToggle = async (row) => {
  try {
    await toggleSchedule(row.id)
    ElMessage.success(row.enabled ? '已禁用' : '已启用')
    loadSchedules()
  } catch (error) {
    console.error(error)
  }
}

const handleRunNow = async (row) => {
  try {
    await runScheduleNow(row.id)
    ElMessage.success('任务已启动,请在执行历史中查看')
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteSchedule(row.id)
    ElMessage.success('删除成功')
    loadSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadSchedules()
  loadScripts()
})
</script>

<style scoped>
.schedules-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
