// 工作流：API 建图 → 页面执行 → 状态对话框 → 清理
import { test, expect } from '@playwright/test'

async function apiCreateWorkflow(request, name) {
  const mk = async (code) => {
    const r = await (await request.post('/api/scripts', {
      data: { name: `ui_wf_s_${Date.now() % 10 ** 10}_${Math.random().toString(36).slice(2, 6)}`, type: 'python', code },
    })).json()
    return r?.data?.id ?? r?.id
  }
  const s1 = await mk('print("wf ui step 1")')
  const s2 = await mk('print("wf ui step 2")')
  const resp = await request.post('/api/workflows', {
    data: {
      name,
      description: 'ui e2e',
      nodes: [
        { node_id: 'node_1', node_type: 'script', script_id: s1, config: {}, position: { x: 100, y: 100 } },
        { node_id: 'node_2', node_type: 'script', script_id: s2, config: {}, position: { x: 300, y: 100 } },
      ],
      edges: [{ edge_id: 'edge_1', source: 'node_1', target: 'node_2' }],
      enabled: true,
    },
  })
  const created = await resp.json()
  return { wf: created?.data ?? created, s1, s2 }
}

test('从页面执行工作流并弹出状态对话框', async ({ page }) => {
  const name = `ui_wf_${Date.now() % 10 ** 10}`
  const { wf, s1, s2 } = await apiCreateWorkflow(page.request, name)

  await page.goto('/workflows')
  const row = page.locator('.el-table__row, .workflow-card, [class*="item"]').filter({ hasText: name }).first()
  await expect(row).toBeVisible()

  // 执行（参数对话框）→ 确认执行
  await row.getByRole('button', { name: '执行' }).click()
  const execDialog = page.locator('.el-dialog:visible').first()
  await expect(execDialog).toBeVisible()
  await execDialog.getByRole('button', { name: '执行' }).click()

  // 状态对话框（SSE 驱动）出现并最终展示成功
  const statusDialog = page.locator('.el-dialog:visible').last()
  await expect(statusDialog).toBeVisible({ timeout: 15_000 })
  await expect(
    statusDialog.getByText(/成功|success|completed/i).first()
  ).toBeVisible({ timeout: 60_000 })

  // 清理
  await page.request.delete(`/api/workflows/${wf.id}`)
  await page.request.delete(`/api/scripts/${s1}`)
  await page.request.delete(`/api/scripts/${s2}`)
})
