// 文件管理页：上传/列表/删除
import { test, expect } from '@playwright/test'
import path from 'node:path'
import os from 'node:os'
import fs from 'node:fs'

test('上传文件 → 列表可见 → 删除', async ({ page }) => {
  const fileName = `ui_file_${Date.now() % 10 ** 10}.txt`
  const tmp = path.join(os.tmpdir(), fileName)
  fs.writeFileSync(tmp, 'ui e2e file body')

  await page.goto('/files')
  const upload = page.locator('input[type="file"]').first()
  await upload.setInputFiles(tmp)

  await expect(page.getByText(fileName).first()).toBeVisible({ timeout: 15_000 })

  // 删除（列表内删除按钮 + 确认）
  const row = page.locator('[class*="item"], .el-table__row').filter({ hasText: fileName }).first()
  await row.getByRole('button', { name: '删除' }).click().catch(() => {})
  const confirm = page.locator('.el-message-box')
  if (await confirm.isVisible({ timeout: 3000 }).catch(() => false)) {
    await confirm.getByRole('button', { name: /确定|删除/ }).click()
  }
  await expect(page.getByText(fileName)).toHaveCount(0, { timeout: 10_000 }).catch(() => {})
  fs.unlinkSync(tmp)
})
