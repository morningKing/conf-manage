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

test('管道编辑器：步骤增删与旧图降级提示', async ({ page }) => {
  // 建两个脚本供下拉选择
  const s1 = await mkScript(page, 'print("pb 1")')
  const s2 = await mkScript(page, 'print("pb 2")')

  await page.goto('/workflows')
  await page.getByRole('button', { name: '创建工作流' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()

  // 初始无步骤
  await expect(dialog.getByText('管道为空')).toBeVisible()

  // 添加两个脚本步骤
  const addBtn = dialog.getByRole('button', { name: /添加脚本步骤/ })
  await addBtn.click()
  await addBtn.click()
  await expect(dialog.locator('.pipeline-step')).toHaveCount(2)

  // 删除一个 -> 只剩 1 步；再添加恢复
  await dialog.locator('.pipeline-step').nth(0).getByRole('button').last().click()
  await expect(dialog.locator('.pipeline-step')).toHaveCount(1)
  await addBtn.click()
  await expect(dialog.locator('.pipeline-step')).toHaveCount(2)

  await dialog.getByRole('button', { name: '取消' }).click()
  await page.request.delete(`/api/scripts/${s1}`)
  await page.request.delete(`/api/scripts/${s2}`)
})

test('旧 DAG 工作流在编辑器中拍平为线性步骤', async ({ page }) => {
  // 带 3 个节点的旧结构（含位置坐标），通过 API 创建
  const ids = []
  for (const code of ['print("a")', 'print("b")', 'print("c")']) {
    const r = await (await page.request.post('/api/scripts', {
      data: { name: `ui_dag_s_${Date.now() % 10 ** 10}_${Math.random().toString(36).slice(2, 5)}`, type: 'python', code },
    })).json()
    ids.push(r?.data?.id ?? r?.id)
  }
  const nodes = ids.map((id, i) => ({
    node_id: `node_${i + 1}`, node_type: 'script', script_id: id,
    config: {}, position: { x: i * 100, y: 50 },
  }))
  const edges = [
    { edge_id: 'e1', source: 'node_1', target: 'node_2' },
    { edge_id: 'e2', source: 'node_2', target: 'node_3' },
  ]
  const created = await (await page.request.post('/api/workflows', {
    data: { name: `ui_dag_${Date.now() % 10 ** 10}`, nodes, edges, enabled: true },
  })).json()
  const wfId = created?.data?.id ?? created?.id

  await page.goto('/workflows')
  await page.reload()
  const rowByName = page.locator('.el-table__row, [class*="item"]').filter({ hasText: 'ui_dag_' }).first()
  await expect(rowByName).toBeVisible()

  // 打开编辑：应看到 3 个线性步骤（拍平），且没有 Vue Flow 画布
  await rowByName.getByRole('button', { name: '编辑' }).click()
  const dialog = page.locator('.el-dialog:visible').first()
  await expect(dialog).toBeVisible()
  await expect(dialog.locator('.pipeline-step')).toHaveCount(3)
  await expect(dialog.locator('.vue-flow')).toHaveCount(0)

  await dialog.getByRole('button', { name: '取消' }).click()
  await page.request.delete(`/api/workflows/${wfId}`)
  for (const id of ids) await page.request.delete(`/api/scripts/${id}`)
})

async function mkScript(page, code) {
  const r = await (await page.request.post('/api/scripts', {
    data: { name: `ui_pb_s_${Date.now() % 10 ** 10}_${Math.random().toString(36).slice(2, 6)}`, type: 'python', code },
  })).json()
  return r?.data?.id ?? r?.id
}
