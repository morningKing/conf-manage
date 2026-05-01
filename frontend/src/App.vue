<template>
  <div class="glass-app" :class="{ 'light-mode': !isDark }">
    <el-container style="height: 100vh">
      <!-- Glass Sidebar -->
      <GlassSidebar
        :isDark="isDark"
        @toggleTheme="toggleTheme"
        @showGuide="showUsageGuide"
      />

      <el-container>
        <!-- Glass Header -->
        <el-header class="glass-header">
          <div class="header-left">
            <span class="header-title">脚本工具管理系统</span>
          </div>
          <div class="header-right">
            <!-- 快捷键提示 -->
            <el-tooltip content="快捷键：Ctrl+K" placement="bottom">
              <button class="glass-btn-secondary glass-btn-sm" @click="showShortcuts">
                <el-icon :size="16"><Search /></el-icon>
              </button>
            </el-tooltip>

            <!-- 全屏切换 -->
            <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏显示'" placement="bottom">
              <button class="glass-btn-secondary glass-btn-sm" @click="toggleFullscreen">
                <el-icon :size="16">
                  <FullScreen v-if="!isFullscreen" />
                  <OfficeBuilding v-else />
                </el-icon>
              </button>
            </el-tooltip>
          </div>
        </el-header>

        <!-- Main Content Area -->
        <el-main class="main-content">
          <!-- Global Loading Animation -->
          <transition name="fade" mode="out-in">
            <div v-if="loading" class="global-loading">
              <el-icon class="is-loading" :size="40" color="rgba(255,255,255,0.8)">
                <Loading />
              </el-icon>
              <p>加载中...</p>
            </div>
            <router-view v-else v-slot="{ Component }">
              <transition name="fade-slide" mode="out-in">
                <keep-alive :include="['Scripts', 'Executions']">
                  <component :is="Component" />
                </keep-alive>
              </transition>
            </router-view>
          </transition>
        </el-main>
      </el-container>
    </el-container>

    <!-- Shortcuts Dialog -->
    <el-dialog
      v-model="shortcutsVisible"
      title="快捷键"
      width="500px"
      :append-to-body="true"
    >
      <el-table :data="shortcuts" style="width: 100%">
        <el-table-column prop="key" label="快捷键" width="180" />
        <el-table-column prop="description" label="功能描述" />
      </el-table>
    </el-dialog>

    <!-- Usage Guide Dialog -->
    <el-dialog
      v-model="usageGuideVisible"
      title="使用指南"
      width="80%"
      top="5vh"
      :append-to-body="true"
    >
      <el-tabs v-model="activeGuideTab" type="border-card">
        <!-- Script Management -->
        <el-tab-pane label="脚本管理" name="scripts">
          <div class="guide-content">
            <h3>创建Python脚本示例</h3>
            <pre><code>import sys
import json

# 脚本可以接收命令行参数
if len(sys.argv) > 1:
    print(f"接收到参数: {sys.argv[1:]}")

# 输出结果
print("Hello from Python script!")

# 可以读写文件
with open('data/uploads/output.txt', 'w') as f:
    f.write("Script executed successfully")</code></pre>

            <h3>创建JavaScript脚本示例</h3>
            <pre><code>// Node.js脚本可以通过环境变量接收参数
const param1 = process.env.PARAM_KEY1;
const param2 = process.env.PARAM_KEY2;

console.log('Hello from JavaScript!');
console.log('Parameters:', param1, param2);

// 可以使用Node.js的fs模块读写文件
const fs = require('fs');
fs.writeFileSync('data/uploads/js-output.txt', 'JS Script executed');</code></pre>
          </div>
        </el-tab-pane>

        <!-- Execution Environment Recognition -->
        <el-tab-pane label="执行环境识别" name="environment">
          <div class="guide-content">
            <h3>区分执行环境（工作流 vs 单脚本）</h3>
            <p>脚本可以通过检查环境变量来判断自己是在工作流中执行还是单独执行。</p>

            <h4>Python 示例</h4>
            <pre><code>import os

# 检查是否在工作流中执行
workflow_space = os.environ.get('WORKFLOW_SPACE')

if workflow_space:
    print(f"在工作流中执行，共享空间: {workflow_space}")
    # 工作流执行逻辑
    # 所有节点共享同一个工作流空间，可以通过文件交换数据
    with open(os.path.join(workflow_space, 'shared_data.json'), 'w') as f:
        f.write('{"status": "completed"}')
else:
    print("单独执行")
    # 单脚本执行逻辑
    # 每次执行都有独立的执行空间</code></pre>

            <h4>JavaScript 示例</h4>
            <pre><code>// 检查是否在工作流中执行
const workflowSpace = process.env.WORKFLOW_SPACE;

if (workflowSpace) {
    console.log(`在工作流中执行，共享空间: ${workflowSpace}`);
    // 工作流执行逻辑
    const fs = require('fs');
    const path = require('path');
    fs.writeFileSync(
        path.join(workflowSpace, 'shared_data.json'),
        JSON.stringify({status: 'completed'})
    );
} else {
    console.log('单独执行');
    // 单脚本执行逻辑
}</code></pre>

            <h4>工作目录说明</h4>
            <ul>
              <li>
                <strong>单脚本执行</strong>: 脚本在独立的执行空间中运行 (<code>execution_spaces/execution_&lt;id&gt;</code>)
                <ul>
                  <li>每次执行都有独立的工作目录</li>
                  <li>上传的文件保存在该执行空间中</li>
                </ul>
              </li>
              <li>
                <strong>工作流执行</strong>: 脚本在共享的工作流空间中运行 (<code>workflow_execution_spaces/workflow_execution_&lt;id&gt;</code>)
                <ul>
                  <li>工作流中的所有节点共享同一个工作流空间</li>
                  <li>节点之间可以通过读写文件来传递数据</li>
                  <li><code>WORKFLOW_SPACE</code> 环境变量包含工作流空间的绝对路径</li>
                </ul>
              </li>
            </ul>

            <h4>实际应用场景</h4>

            <h5>场景1: 条件执行</h5>
            <pre><code>import os

workflow_space = os.environ.get('WORKFLOW_SPACE')

if workflow_space:
    # 在工作流中，读取前一个节点的输出
    import json
    with open(os.path.join(workflow_space, 'previous_result.json'), 'r') as f:
        prev_result = json.load(f)

    if prev_result.get('status') == 'success':
        print("继续执行")
    else:
        print("跳过执行")
        exit(0)
else:
    # 单独执行，直接处理
    print("开始处理...")</code></pre>

            <h5>场景2: 日志记录</h5>
            <pre><code>import os
from datetime import datetime

def log_message(msg):
    workflow_space = os.environ.get('WORKFLOW_SPACE')

    if workflow_space:
        # 工作流执行：追加到共享日志
        log_file = os.path.join(workflow_space, 'workflow.log')
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now()}] {msg}\\n")
    else:
        # 单独执行：直接打印
        print(f"[{datetime.now()}] {msg}")

log_message("脚本开始执行")</code></pre>
          </div>
        </el-tab-pane>

        <!-- Scheduled Tasks -->
        <el-tab-pane label="定时任务" name="schedule">
          <div class="guide-content">
            <h3>Cron表达式说明</h3>
            <p>格式: <code>分 时 日 月 周</code></p>

            <h4>常用示例</h4>
            <ul>
              <li><code>0 0 * * *</code> - 每天午夜12点执行</li>
              <li><code>0 */2 * * *</code> - 每2小时执行一次</li>
              <li><code>30 8 * * 1-5</code> - 周一到周五早上8:30执行</li>
              <li><code>0 0 1 * *</code> - 每月1号午夜执行</li>
              <li><code>*/5 * * * *</code> - 每5分钟执行一次</li>
            </ul>
          </div>
        </el-tab-pane>

        <!-- File Management -->
        <el-tab-pane label="文件管理" name="files">
          <div class="guide-content">
            <h3>脚本中访问文件</h3>

            <h4>Python示例</h4>
            <pre><code># 读取上传的文件
with open('data/uploads/input.txt', 'r') as f:
    content = f.read()
    print(content)

# 写入文件供下载
with open('data/uploads/output.txt', 'w') as f:
    f.write('Processing result')</code></pre>

            <h4>JavaScript示例</h4>
            <pre><code>const fs = require('fs');

// 读取文件
const content = fs.readFileSync('data/uploads/input.txt', 'utf-8');
console.log(content);

// 写入文件
fs.writeFileSync('data/uploads/output.txt', 'Processing result');</code></pre>
          </div>
        </el-tab-pane>

        <!-- Workflow -->
        <el-tab-pane label="工作流" name="workflow">
          <div class="guide-content">
            <h3>工作流节点间协作</h3>
            <p>工作流中的多个节点可以通过共享的工作流空间来交换数据。</p>

            <h4>节点A (数据生成器)</h4>
            <pre><code>import json
import os

workflow_space = os.environ.get('WORKFLOW_SPACE')
data = {"status": "success", "count": 100}

with open(os.path.join(workflow_space, 'shared_data.json'), 'w') as f:
    json.dump(data, f)</code></pre>

            <h4>节点B (数据处理器)</h4>
            <pre><code>import json
import os

workflow_space = os.environ.get('WORKFLOW_SPACE')

with open(os.path.join(workflow_space, 'shared_data.json'), 'r') as f:
    data = json.load(f)
    print(f"Received data: {data}")</code></pre>
          </div>
        </el-tab-pane>

        <!-- Notes -->
        <el-tab-pane label="注意事项" name="notes">
          <div class="guide-content">
            <h3>注意事项</h3>
            <ol>
              <li><strong>脚本超时</strong>: 默认脚本执行超时时间为300秒(5分钟),超时会被强制终止</li>
              <li><strong>文件路径</strong>: 脚本中使用相对路径访问文件,相对于项目根目录</li>
              <li><strong>依赖安装</strong>: 首次使用新依赖时可能需要较长时间安装</li>
              <li><strong>并发执行</strong>: 系统支持多个脚本同时执行</li>
              <li><strong>日志大小</strong>: 执行日志会被限制大小,避免占用过多磁盘空间</li>
            </ol>

            <h3>故障排查</h3>

            <h4>脚本执行失败</h4>
            <ol>
              <li>查看执行日志中的错误信息</li>
              <li>检查依赖是否正确配置</li>
              <li>检查脚本语法是否正确</li>
              <li>确认文件路径是否正确</li>
            </ol>

            <h4>定时任务未执行</h4>
            <ol>
              <li>确认任务状态为"启用"</li>
              <li>检查Cron表达式是否正确</li>
              <li>查看后端日志是否有错误信息</li>
              <li>查看"执行历史"确认任务是否被触发</li>
            </ol>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="usageGuideVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, FullScreen, OfficeBuilding, Loading
} from '@element-plus/icons-vue'

// Glass Components
import GlassSidebar from '@/components/GlassSidebar.vue'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'

// Glass Theme Styles
import '@/styles/glass-theme.scss'

const router = useRouter()

// Theme state
const isDark = ref(true) // Default to dark (gradient background)
const isFullscreen = ref(false)
const loading = ref(false)
const shortcutsVisible = ref(false)
const usageGuideVisible = ref(false)
const activeGuideTab = ref('environment')

// Shortcuts list
const shortcuts = ref([
  { key: 'Ctrl + K', description: '显示快捷键帮助' },
  { key: 'Ctrl + D', description: '切换深色/浅色模式' },
  { key: 'Ctrl + F11', description: '全屏/退出全屏' },
  { key: 'Ctrl + 1', description: '跳转到脚本管理' },
  { key: 'Ctrl + 2', description: '跳转到执行历史' },
  { key: 'Ctrl + 3', description: '跳转到定时任务' },
  { key: 'Ctrl + 4', description: '跳转到文件管理' },
])

// Toggle theme - use light-mode class
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')

  // Toggle light-mode class on documentElement
  if (isDark.value) {
    document.documentElement.classList.remove('light-mode')
  } else {
    document.documentElement.classList.add('light-mode')
  }
}

// Fullscreen toggle
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// Show shortcuts
const showShortcuts = () => {
  shortcutsVisible.value = true
}

// Show usage guide
const showUsageGuide = () => {
  usageGuideVisible.value = true
}

// Keyboard shortcuts handler
const handleKeydown = (e) => {
  // Ctrl + K: Show shortcuts
  if (e.ctrlKey && e.key === 'k') {
    e.preventDefault()
    showShortcuts()
  }

  // Ctrl + D: Toggle theme
  if (e.ctrlKey && e.key === 'd') {
    e.preventDefault()
    toggleTheme()
  }

  // Ctrl + F11: Fullscreen
  if (e.ctrlKey && e.key === 'F11') {
    e.preventDefault()
    toggleFullscreen()
  }

  // Ctrl + Number: Quick navigation
  if (e.ctrlKey && e.key >= '1' && e.key <= '4') {
    e.preventDefault()
    const routes = ['/scripts', '/executions', '/schedules', '/files']
    router.push(routes[parseInt(e.key) - 1])
  }
}

// Listen for fullscreen state change
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// Initialize
onMounted(() => {
  // Restore theme setting
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    isDark.value = false
    document.documentElement.classList.add('light-mode')
  } else {
    // Default dark mode - no light-mode class
    isDark.value = true
    document.documentElement.classList.remove('light-mode')
  }

  // Register keyboard shortcuts
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})

// Router loading animation
router.beforeEach((to, from, next) => {
  loading.value = true
  next()
})

router.afterEach(() => {
  setTimeout(() => {
    loading.value = false
  }, 300)
})
</script>

<style>
/* Global Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Glass App Container */
.glass-app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  min-height: 100vh;
}

/* Main Content Area */
.main-content {
  background: transparent;
  padding: 20px 20px 20px 15px; /* Left padding for compact sidebar */
  overflow-y: auto;
}

/* Glass Header Customization */
.glass-header {
  margin: 15px 15px 0 0; /* Match sidebar margin */
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Global Loading Animation */
.global-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 15px;
}

.global-loading p {
  color: var(--text-secondary);
  font-size: 16px;
}

/* Transition Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-slide-enter-active {
  transition: all 0.3s ease-out;
}

.fade-slide-leave-active {
  transition: all 0.2s ease-in;
}

.fade-slide-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.fade-slide-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* Usage Guide Dialog Styles */
.guide-content {
  padding: 20px;
  line-height: 1.8;
}

.guide-content h3 {
  color: var(--gradient-start);
  margin-top: 20px;
  margin-bottom: 15px;
  font-size: 18px;
  border-bottom: 2px solid var(--gradient-start);
  padding-bottom: 8px;
}

.guide-content h4 {
  color: var(--text-secondary);
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 16px;
}

.guide-content h5 {
  color: var(--text-muted);
  margin-top: 12px;
  margin-bottom: 8px;
  font-size: 14px;
}

.guide-content p {
  margin: 10px 0;
  color: var(--text-secondary);
}

.guide-content ul,
.guide-content ol {
  margin: 10px 0;
  padding-left: 30px;
}

.guide-content li {
  margin: 8px 0;
  color: var(--text-secondary);
}

.guide-content code {
  background: rgba(255, 255, 255, 0.15);
  color: #e96900;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.guide-content pre {
  background: rgba(30, 30, 50, 0.85);
  border: 1px solid var(--border-low);
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  overflow-x: auto;
}

.guide-content pre code {
  background: transparent;
  color: var(--text-primary);
  padding: 0;
  font-size: 13px;
  line-height: 1.6;
}

/* Light mode guide content adjustments */
.light-mode .guide-content h3 {
  color: #667eea;
  border-bottom-color: #667eea;
}

.light-mode .guide-content code {
  background: rgba(102, 126, 234, 0.15);
}

/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.light-mode ::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
}

.light-mode ::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.4);
}

/* Responsive Design */
@media (max-width: 768px) {
  .main-content {
    padding: 15px 15px 75px 15px; /* Extra bottom padding for mobile nav */
  }

  .glass-header {
    margin: 10px;
  }

  .header-title {
    font-size: 16px;
  }
}
</style>