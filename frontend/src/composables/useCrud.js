/**
 * 通用 CRUD 组合式函数
 *
 * 收敛列表页的"加载 / 新建 / 编辑 / 保存 / 删除"样板：
 * 对话框状态、表单初值、ElMessage/ElMessageBox 提示统一在此处理，
 * 视图只保留业务列定义与特殊行操作（如启用/激活/立即运行）。
 *
 * @param {object} opts
 * - list:   () => Promise<Array>          加载列表（返回数组）
 * - create: (form) => Promise              新建
 * - update: (id, form) => Promise          更新
 * - remove: (row) => Promise               删除
 * - emptyForm: () => object                新建时表单初值（默认 {}）
 * - toForm: (row) => object                编辑时从行构造表单（默认浅拷贝）
 * - validate: (form) => boolean|Promise<boolean> 可选：保存前校验（返回 false 中止）
 * - confirmText: (row) => string           可选：删除确认文案
 * - name: string                           实体名，用于默认提示（默认"记录"）
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export function useCrud({
  list,
  create,
  update,
  remove,
  emptyForm = () => ({}),
  toForm = (row) => ({ ...row }),
  validate,
  confirmText,
  name = '记录',
} = {}) {
  const items = ref([])
  const loading = ref(false)
  const dialogVisible = ref(false)
  const isEdit = ref(false)
  const form = ref(emptyForm())
  const current = ref(null)

  const load = async () => {
    loading.value = true
    try {
      items.value = (await list()) || []
    } catch (error) {
      ElMessage.error(error?.response?.data?.error || error?.response?.data?.message || `加载${name}列表失败`)
    } finally {
      loading.value = false
    }
  }

  const openCreate = () => {
    isEdit.value = false
    current.value = null
    form.value = emptyForm()
    dialogVisible.value = true
  }

  const openEdit = (row) => {
    isEdit.value = true
    current.value = row
    form.value = toForm(row)
    dialogVisible.value = true
  }

  const save = async () => {
    try {
      if (validate) {
        const ok = await validate(form.value)
        if (ok === false) return false
      }
      if (isEdit.value) {
        await update(current.value.id, form.value)
        ElMessage.success('更新成功')
      } else {
        await create(form.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      await load()
      return true
    } catch (error) {
      ElMessage.error(error?.response?.data?.error || error?.response?.data?.message || '操作失败')
      return false
    }
  }

  const removeRow = async (row) => {
    try {
      await ElMessageBox.confirm(
        confirmText ? confirmText(row) : `确定要删除此${name}吗？`,
        '提示',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      )
      await remove(row)
      ElMessage.success('删除成功')
      await load()
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(error?.response?.data?.error || error?.response?.data?.message || '删除失败')
      }
      return false
    }
  }

  return {
    items,
    loading,
    dialogVisible,
    isEdit,
    form,
    current,
    load,
    openCreate,
    openEdit,
    save,
    removeRow,
  }
}
