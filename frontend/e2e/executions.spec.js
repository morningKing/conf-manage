// 执行记录页：API 触发执行 → 列表出现 → 日志对话框
import { test, expect } from '@playwright/test'

async function createAndRun(request, name) {
  const created = await (await request.post('/api/scripts', {
    data: { name, type: 'python', code: 'print("ui-e2e output marker")' },
  })).json()
  const id = created?.data?.id ?? created?.id
  const run = await (await request.post(`/api/scripts/${id}/execute`, { data: { params: {} } })).json()
  const execId = run?.data?.id ?? run?.id ?? run?.data?.execution?.id
  // 轮询到终态
  for (let i = 0; i < 40; i++) {
    const st = await (await request.get(`/api/executions/${execId}`)).json()
    const status = st?.data?.status
    if (['success', 'failed', 'cancelled'].includes(status)) return { id, execId, status }
    await new Promise(r => setTimeout(r, 1000))
  }
  throw new Error('执行未在期限内到达终态')
}

test('执行完成后出现在执行记录并可通过日志查看输出', async ({ page }) => {
  const name = `ui_exec_${Date.now() % 10 ** 10}`
  const { execId } = await createAndRun(page.request, name)

  await page.goto('/executions')
  const row = page.locator('.el-table__row, .executions-list-item, [class*="item"]').filter({ hasText: name }).first()
  await expect(row).toBeVisible()

  // 日志对话框
  await row.getByRole('button', { name: '日志' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
  await expect(dialog.getByText('ui-e2e output marker').first()).toBeVisible({ timeout: 15_000 })
})

test('统计对话框可打开', async ({ page }) => {
  await page.goto('/executions')
  await page.getByRole('button', { name: '统计' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
})
