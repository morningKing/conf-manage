// 定时任务：新建（含脚本下拉）/ 立即运行 / 删除
import { test, expect } from '@playwright/test'

async function apiCreateScript(request, name) {
  const resp = await request.post('/api/scripts', {
    data: { name, type: 'python', code: 'print("sched-ui")' },
  })
  const created = await resp.json()
  return created?.data?.id ?? created?.id
}

test('新建定时任务并出现在表格', async ({ page }) => {
  const scriptId = await apiCreateScript(page.request, `ui_sched_script_${Date.now() % 10 ** 10}`)
  const name = `ui_sched_${Date.now() % 10 ** 10}`

  await page.goto('/schedules')
  await page.getByRole('button', { name: '新建任务' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()

  await dialog.getByPlaceholder('请输入任务名称').fill(name)
  // 选择脚本（Element Plus 下拉：点击下拉容器而非 placeholder）
  await dialog.locator('.el-select').first().click()
  const option = page.locator('.el-select-dropdown__item:visible').first()
  await expect(option).toBeVisible({ timeout: 10_000 })
  await option.click()
  await dialog.getByPlaceholder(/例如: 0 0/).fill('0 6 * * *')

  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  await expect(page.locator('.el-table__row').filter({ hasText: name })).toBeVisible()

  // 立即运行（覆盖 app context 修复路径）
  const row = page.locator('.el-table__row').filter({ hasText: name })
  await row.getByRole('button', { name: '立即运行' }).click()
  await expect(page.locator('.el-message').filter({ hasText: '启动' }).first()).toBeVisible({ timeout: 10_000 })

  // 清理
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|删除/ }).click()
  await expect(page.locator('.el-table__row').filter({ hasText: name })).toHaveCount(0, { timeout: 10_000 })

  await page.request.delete(`/api/scripts/${scriptId}`)
})
