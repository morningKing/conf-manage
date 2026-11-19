// 脚本管理页：对话框 CRUD + 三 Tab 结构 + 卡片列表
import { test, expect } from '@playwright/test'

const uniq = () => `ui_script_${Date.now() % 10 ** 10}`

test('新建脚本（三 Tab 对话框）并出现在列表', async ({ page }) => {
  const name = uniq()
  await page.goto('/scripts')
  await page.getByRole('button', { name: '新建脚本' }).first().click()

  const dialog = page.locator('.el-dialog').filter({ hasText: '新建脚本' }).first()
  await expect(dialog).toBeVisible()

  // 基础信息 Tab
  await dialog.getByPlaceholder('请输入脚本名称').fill(name)

  // 输入信息 Tab 存在
  await expect(dialog.getByRole('tab', { name: '输入信息' })).toBeVisible()

  // 脚本 Tab：CodeMirror 中输入代码（后端要求 code 非空）
  await dialog.getByRole('tab', { name: '脚本' }).click()
  const cm = dialog.locator('.cm-content').first()
  await expect(cm).toBeVisible()
  await cm.click()
  await page.keyboard.type('print("ui e2e")')
  await dialog.getByRole('tab', { name: '基础信息' }).click()

  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })

  await expect(page.locator('.item-name', { hasText: name })).toBeVisible()
})

test('编辑脚本改名后列表同步', async ({ page }) => {
  const name = uniq()
  const renamed = `${name}_r`
  // 经统一 API 层建脚本（走前端代理，同时覆盖代理链路）
  const resp = await page.request.post('/api/scripts', {
    data: { name, type: 'python', code: 'print("ui")' },
  })
  expect(resp.ok()).toBeTruthy()
  const created = await resp.json()
  const id = created?.data?.id ?? created?.id

  await page.goto('/scripts')
  await page.reload()
  const nameEl = page.locator('.item-name', { hasText: name }).first()
  await expect(nameEl).toBeVisible()

  // 右键卡片 → 上下文菜单 → 编辑
  await nameEl.click({ button: 'right' })
  await page.locator('.context-menu-item', { hasText: '编辑' }).first().click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
  await dialog.getByPlaceholder('请输入脚本名称').fill(renamed)
  await dialog.getByRole('button', { name: '保存' }).click()
  await expect(dialog).toBeHidden({ timeout: 10_000 })
  await expect(page.locator('.item-name', { hasText: renamed }).first()).toBeVisible()

  await page.request.delete(`/api/scripts/${id}`)
})

test('删除脚本（确认框）', async ({ page }) => {
  const name = uniq()
  const resp = await page.request.post('/api/scripts', {
    data: { name, type: 'python', code: 'print("x")' },
  })
  const created = await resp.json()
  const id = created?.data?.id ?? created?.id

  await page.goto('/scripts')
  await page.reload()
  await expect(page.locator('.item-name', { hasText: name })).toBeVisible()

  // 删除：右键菜单 → 删除 → 确认框（ElMessageBox）
  await page.locator('.item-name', { hasText: name }).first().click({ button: 'right' })
  await page.locator('.context-menu-item', { hasText: '删除' }).first().click()
  const confirm = page.locator('.el-message-box')
  await expect(confirm).toBeVisible()
  await confirm.getByRole('button', { name: /确定|删除/ }).click()
  await expect(page.locator('.item-name', { hasText: name })).toHaveCount(0, { timeout: 10_000 })
})
