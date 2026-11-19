// 侧边栏导航全量走查：12 个页面可达且渲染核心元素
import { test, expect } from '@playwright/test'

const PAGES = [
  { path: '/scripts', title: '脚本管理', anchor: '新建脚本' },
  { path: '/executions', title: '执行记录', anchor: '刷新' },
  { path: '/schedules', title: '定时任务', anchor: '新建任务' },
  { path: '/webhooks', title: 'Webhook', anchor: '新建Webhook' },
  { path: '/workflows', title: '工作流', anchor: '创建工作流' },
  { path: '/files', title: '文件管理', anchor: null },
  { path: '/environments', title: '环境配置', anchor: null },
  { path: '/global-variables', title: '全局变量', anchor: '新增变量' },
  { path: '/tags', title: '标签管理', anchor: '新建标签' },
  { path: '/backup', title: '备份管理', anchor: '创建系统备份' },
  { path: '/ai-settings', title: '系统设置', anchor: '清理管理' },
  { path: '/ai-script-writer', title: 'AI脚本助手', anchor: null },
]

test.describe('导航走查', () => {
  for (const p of PAGES) {
    test(`页面 ${p.path} 可达`, async ({ page }) => {
      await page.goto('/')
      await page.getByTitle(p.title).click()
      await expect(page).toHaveURL(new RegExp(p.path.replace(/\//g, '\\/') + '(\\?|$)'))
      if (p.anchor) {
        await expect(page.getByText(p.anchor).first()).toBeVisible()
      } else {
        // 宽松断言：页面容器渲染出内容
        await expect(page.locator('.main-content, .page-container, [class*="view"]').first()).toBeVisible()
      }
    })
  }
})
