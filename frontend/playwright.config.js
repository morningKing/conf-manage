// @ts-check
import { defineConfig, devices } from '@playwright/test'

const BACKEND_PORT = process.env.E2E_PORT || '5101'
const FRONTEND_PORT = '5177'

/**
 * 双 webServer：独立 PG 库上的真实后端（5101）+ Vite dev 前端（5177）
 * 后端经由 run_server.py 装配 E2E 数据库（dbsetup.py）后启动，绝不连接业务库
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: `python ../backend/tests_e2e/run_server.py`,
      url: `http://localhost:${BACKEND_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
      env: {
        ...process.env,
        E2E_PORT: BACKEND_PORT,
        HOST_DEBUG: 'false',
      },
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        ...process.env,
        VITE_PROXY_TARGET: `http://localhost:${BACKEND_PORT}`,
      },
    },
  ],
})
