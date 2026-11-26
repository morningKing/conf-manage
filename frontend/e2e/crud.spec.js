// useCrud 采用页面的 CRUD 冒烟：标签 / 全局变量 / 执行环境
import { execSync } from 'node:child_process'
import { test, expect } from '@playwright/test'

function resolvePythonPath() {
  const out = execSync('where python', { encoding: 'utf8' })
  const first = out.split(/\r?\n/).map(line => line.trim()).filter(Boolean)[0]
  expect(first, '找不到 python 可执行文件').toBeTruthy()
  return first
}

test('标签管理：新建与删除', async ({ page }) => {
  const name = `ui_tag_${Date.now() % 10 ** 10}`
  await page.goto('/tags')
  await page.getByRole('button', { name: '新建标签' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
  await dialog.getByPlaceholder('请输入标签名称').fill(name)
  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  const row = page.locator('.el-table__row').filter({ hasText: name }).first()
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|OK/ }).click()
  await expect(page.locator('.el-table__row').filter({ hasText: name })).toHaveCount(0, { timeout: 10_000 })
})

test('全局变量：新建与删除', async ({ page }) => {
  const key = `UI_GV_${Date.now() % 10 ** 9}`
  await page.goto('/global-variables')
  await page.getByRole('button', { name: '新增变量' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
  await dialog.getByPlaceholder(/请输入变量名/).fill(key)
  await dialog.getByPlaceholder('请输入变量值').fill('smoke-value')
  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  const row = page.locator('.el-table__row').filter({ hasText: key }).first()
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|OK/ }).click()
  await expect(page.locator('.el-table__row').filter({ hasText: key })).toHaveCount(0, { timeout: 10_000 })
})

test('执行环境：新建（默认类型）与删除', async ({ page }) => {
  const name = `ui_env_${Date.now() % 10 ** 10}`
  const pythonPath = resolvePythonPath()

  await page.goto('/environments')
  await page.getByRole('button', { name: '新建环境' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()

  // 默认类型为当前 Tab（python）；后端要求解释器路径真实存在
  await dialog.getByRole('textbox', { name: '* 环境名称' }).fill(name)
  await dialog.getByRole('textbox', { name: '* 解释器路径' }).fill(pythonPath)
  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 15_000 })

  const row = page.locator('.el-table__row').filter({ hasText: name }).first()
  await expect(row).toBeVisible()

  // 清理
  await row.getByRole('button', { name: '删除' }).click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|OK/ }).click()
  await expect(page.locator('.el-table__row').filter({ hasText: name })).toHaveCount(0, { timeout: 10_000 })
})
