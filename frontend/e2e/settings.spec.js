// 系统设置（AISettings）：AI 配置添加 + 掩码显示 + 清理管理区
import { test, expect } from '@playwright/test'

test('添加 AI 配置后 API Key 以掩码显示', async ({ page }) => {
  const name = `ui_ai_${Date.now() % 10 ** 10}`
  const apiKey = `sk-ui-e2e-${Date.now()}abcdef`

  await page.goto('/ai-settings')
  await page.getByRole('button', { name: '添加AI配置' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()

  // 名称字段（若存在）
  const nameInput = dialog.locator('.el-form-item').filter({ hasText: '名称' }).locator('input').first()
  if (await nameInput.count()) await nameInput.fill(name)

  // API Key（必填）
  const keyInput = dialog.locator('.el-form-item').filter({ hasText: 'API Key' }).locator('input').first()
  await keyInput.fill(apiKey)

  await dialog.getByRole('button', { name: '确定' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  // 表格里的 api_key 必须是掩码（不含明文）
  const table = page.locator('.el-table').first()
  await expect(table).toBeVisible()
  const cellText = await table.locator('tbody').textContent()
  expect(cellText).not.toContain(apiKey)
  expect(cellText).toContain('...')

  // 清理本条配置
  const row = page.locator('.el-table__row').filter({ hasText: '...' }).first()
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  if (await confirm.isVisible({ timeout: 3000 }).catch(() => false)) {
    await confirm.getByRole('button', { name: /确定|删除/ }).click()
  }
})

test('清理管理区展示统计', async ({ page }) => {
  await page.goto('/ai-settings')
  await expect(page.getByText('清理管理')).toBeVisible()
  await expect(page.getByText('待清理').first()).toBeVisible()
})
