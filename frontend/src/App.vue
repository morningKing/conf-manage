<template>
  <div class="glass-app">
    <el-config-provider size="small">
      <el-container style="height: 100vh">
        <GlassSidebar :isDark="isDark" @toggleTheme="toggleTheme" @showGuide="helpVisible = true" />

        <el-container>
          <el-header class="glass-header">
            <div class="header-left">
              <span class="header-title">脚本工具管理系统</span>
            </div>
            <div class="header-right">
              <el-tooltip content="快捷键：Ctrl+K" placement="bottom">
                <button class="glass-btn-secondary glass-btn-sm" @click="shortcutsVisible = true">
                  <el-icon :size="15"><Search /></el-icon>
                </button>
              </el-tooltip>

              <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏显示'" placement="bottom">
                <button class="glass-btn-secondary glass-btn-sm" @click="toggleFullscreen">
                  <el-icon :size="15">
                    <FullScreen v-if="!isFullscreen" />
                    <CopyDocument v-else />
                  </el-icon>
                </button>
              </el-tooltip>
            </div>
          </el-header>

          <el-main class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="fade-slide" mode="out-in">
                <keep-alive :include="['Scripts', 'Executions']">
                  <component :is="Component" />
                </keep-alive>
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>

      <!-- 快捷键 -->
      <el-dialog v-model="shortcutsVisible" title="快捷键" width="480px" :append-to-body="true">
        <el-table :data="shortcuts">
          <el-table-column prop="key" label="快捷键" width="160" />
          <el-table-column prop="description" label="功能描述" />
        </el-table>
      </el-dialog>

      <!-- 使用指南（内容在独立组件中维护） -->
      <HelpDialog v-model="helpVisible" />
    </el-config-provider>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { Search, FullScreen, CopyDocument } from '@element-plus/icons-vue'
import GlassSidebar from '@/components/GlassSidebar.vue'
import HelpDialog from '@/components/HelpDialog.vue'

const router = useRouter()

// 主题：Element Plus 官方 html.dark 机制，localStorage 持久化
const isDark = ref(true)

watchEffect(() => {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
})

const toggleTheme = () => {
  isDark.value = !isDark.value
}

const isFullscreen = ref(false)

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const shortcutsVisible = ref(false)
const helpVisible = ref(false)

const shortcuts = ref([
  { key: 'Ctrl + K', description: '使用指南' },
  { key: 'Ctrl + D', description: '切换深色/浅色模式' },
  { key: 'Ctrl + F11', description: '全屏/退出全屏' },
  { key: 'Ctrl + 1', description: '跳转到脚本管理' },
  { key: 'Ctrl + 2', description: '跳转到执行历史' },
  { key: 'Ctrl + 3', description: '跳转到定时任务' },
  { key: 'Ctrl + 4', description: '跳转到文件管理' },
])

const handleKeydown = (e) => {
  if (e.ctrlKey && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    helpVisible.value = true
  }
  if (e.ctrlKey && e.key.toLowerCase() === 'd') {
    e.preventDefault()
    toggleTheme()
  }
  if (e.ctrlKey && e.key === 'F11') {
    e.preventDefault()
    toggleFullscreen()
  }
  if (e.ctrlKey && e.key >= '1' && e.key <= '4') {
    e.preventDefault()
    const routes = ['/scripts', '/executions', '/schedules', '/files']
    router.push(routes[parseInt(e.key) - 1])
  }
}

onMounted(() => {
  isDark.value = localStorage.getItem('theme') !== 'light'
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>
