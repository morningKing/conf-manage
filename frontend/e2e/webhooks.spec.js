// Webhook：新建 / 出现在表格 / 删除
import { test, expect } from '@playwright/test'

test('新建 Webhook 并出现在表格', async ({ page }) => {
  const scriptResp = await (await page.request.post('/api/scripts', {
    data: { name: `ui_wh_script_${Date.now() % 10 ** 10}`, type: 'python', code: 'print("wh")' },
  })).json()
  const scriptId = scriptResp?.data?.id ?? scriptResp?.id
  const name = `ui_wh_${Date.now() % 10 ** 10}`

  await page.goto('/webhooks')
  await page.getByRole('button', { name: '新建Webhook' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()

  await dialog.getByPlaceholder('输入Webhook名称').fill(name)
  // 关联脚本（filterable 下拉：点击下拉容器）
  await dialog.locator('.el-select').first().click()
  const option = page.locator('.el-select-dropdown__item:visible').first()
  await expect(option).toBeVisible({ timeout: 10_000 })
  await option.click()

  await dialog.getByRole('button', { name: '确定' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  await expect(page.locator('.el-table__row').filter({ hasText: name })).toBeVisible()

  const row = page.locator('.el-table__row').filter({ hasText: name })
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|删除|OK/ }).click()
  await expect(page.locator('.el-table__row').filter({ hasText: name })).toHaveCount(0, { timeout: 10_000 })

  await page.request.delete(`/api/scripts/${scriptId}`)
})
