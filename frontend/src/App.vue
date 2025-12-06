<template>
  <div id="app" :class="{ 'dark-mode': isDark }">
    <el-container style="height: 100vh">
      <!-- 侧边栏 -->
      <el-aside
        :width="isCollapse ? '64px' : '200px'"
        :class="['sidebar', { 'sidebar-dark': isDark }]"
        class="sidebar-transition"
      >
        <div class="logo">
          <h2 v-if="!isCollapse">脚本管理</h2>
          <el-icon v-else :size="24" style="color: #fff"><Document /></el-icon>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          :collapse="isCollapse"
          :background-color="isDark ? '#1f1f1f' : '#304156'"
          :text-color="isDark ? '#b3b3b3' : '#bfcbd9'"
          :active-text-color="isDark ? '#409EFF' : '#409EFF'"
        >
          <el-menu-item index="/scripts">
            <el-icon><Document /></el-icon>
            <template #title>脚本管理</template>
          </el-menu-item>
          <el-menu-item index="/executions">
            <el-icon><VideoPlay /></el-icon>
            <template #title>执行历史</template>
          </el-menu-item>
          <el-menu-item index="/schedules">
            <el-icon><Clock /></el-icon>
            <template #title>定时任务</template>
          </el-menu-item>
          <el-menu-item index="/categories">
            <el-icon><Menu /></el-icon>
            <template #title>分类管理</template>
          </el-menu-item>
          <el-menu-item index="/tags">
            <el-icon><CollectionTag /></el-icon>
            <template #title>标签管理</template>
          </el-menu-item>
          <el-menu-item index="/environments">
            <el-icon><Setting /></el-icon>
            <template #title>执行环境</template>
          </el-menu-item>
          <el-menu-item index="/files">
            <el-icon><Folder /></el-icon>
            <template #title>文件管理</template>
          </el-menu-item>
          <el-menu-item index="/workflows">
            <el-icon><Share /></el-icon>
            <template #title>工作流管理</template>
          </el-menu-item>
          <el-menu-item index="/global-variables">
            <el-icon><Setting /></el-icon>
            <template #title>全局变量</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 顶部栏 -->
        <el-header :class="['header', { 'header-dark': isDark }]">
          <div class="header-left">
            <el-button
              :icon="isCollapse ? Expand : Fold"
              circle
              @click="toggleCollapse"
              class="collapse-btn"
            />
            <span class="header-title">脚本工具管理系统</span>
          </div>
          <div class="header-right">
            <!-- 快捷键提示 -->
            <el-tooltip content="快捷键：Ctrl+K" placement="bottom">
              <el-button :icon="Search" circle @click="showShortcuts" />
            </el-tooltip>

            <!-- 主题切换 -->
            <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到深色模式'" placement="bottom">
              <el-button
                :icon="isDark ? Sunny : Moon"
                circle
                @click="toggleTheme"
                class="theme-toggle"
              />
            </el-tooltip>

            <!-- 全屏切换 -->
            <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏显示'" placement="bottom">
              <el-button
                :icon="isFullscreen ? OfficeBuilding : FullScreen"
                circle
                @click="toggleFullscreen"
              />
            </el-tooltip>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main :class="['main-content', { 'main-dark': isDark }]">
          <!-- 全局加载动画 -->
          <transition name="fade" mode="out-in">
            <div v-if="loading" class="global-loading">
              <el-icon class="is-loading" :size="40" color="#409EFF">
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

    <!-- 快捷键对话框 -->
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document, VideoPlay, Clock, Menu, CollectionTag, Setting, Folder, Share,
  Sunny, Moon, Search, FullScreen, OfficeBuilding, Expand, Fold, Loading
} from '@element-plus/icons-vue'

const router = useRouter()

// 主题状态
const isDark = ref(false)
const isCollapse = ref(false)
const isFullscreen = ref(false)
const loading = ref(false)
const shortcutsVisible = ref(false)

// 快捷键列表
const shortcuts = ref([
  { key: 'Ctrl + K', description: '显示快捷键帮助' },
  { key: 'Ctrl + D', description: '切换深色/浅色模式' },
  { key: 'Ctrl + B', description: '折叠/展开侧边栏' },
  { key: 'Ctrl + F11', description: '全屏/退出全屏' },
  { key: 'Ctrl + 1', description: '跳转到脚本管理' },
  { key: 'Ctrl + 2', description: '跳转到执行历史' },
  { key: 'Ctrl + 3', description: '跳转到定时任务' },
  { key: 'Ctrl + 4', description: '跳转到文件管理' },
])

// 切换主题
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')

  // 同时切换 Element Plus 的主题
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 折叠侧边栏
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
  localStorage.setItem('sidebarCollapse', isCollapse.value)
}

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 显示快捷键
const showShortcuts = () => {
  shortcutsVisible.value = true
}

// 快捷键处理
const handleKeydown = (e) => {
  // Ctrl + K: 显示快捷键
  if (e.ctrlKey && e.key === 'k') {
    e.preventDefault()
    showShortcuts()
  }

  // Ctrl + D: 切换主题
  if (e.ctrlKey && e.key === 'd') {
    e.preventDefault()
    toggleTheme()
  }

  // Ctrl + B: 折叠侧边栏
  if (e.ctrlKey && e.key === 'b') {
    e.preventDefault()
    toggleCollapse()
  }

  // Ctrl + F11: 全屏
  if (e.ctrlKey && e.key === 'F11') {
    e.preventDefault()
    toggleFullscreen()
  }

  // Ctrl + 数字: 快速导航
  if (e.ctrlKey && e.key >= '1' && e.key <= '4') {
    e.preventDefault()
    const routes = ['/scripts', '/executions', '/schedules', '/files']
    router.push(routes[parseInt(e.key) - 1])
  }
}

// 监听全屏状态变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// 初始化
onMounted(() => {
  // 恢复主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }

  // 恢复侧边栏状态
  const savedCollapse = localStorage.getItem('sidebarCollapse')
  if (savedCollapse === 'true') {
    isCollapse.value = true
  }

  // 注册快捷键
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})

// 路由变化时显示加载动画
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  transition: background-color 0.3s, color 0.3s;
}

/* 深色模式全局样式 */
.dark-mode {
  background-color: #141414;
  color: #e8e8e8;
}

/* 侧边栏样式 */
.sidebar {
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.08);
  transition: width 0.3s, background-color 0.3s;
}

.sidebar-dark {
  background-color: #1f1f1f !important;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.3);
}

.sidebar-transition {
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  transition: opacity 0.3s;
}

/* 顶部栏样式 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.header-dark {
  background-color: #1f1f1f;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  color: #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
}

.collapse-btn {
  transition: transform 0.3s;
}

.collapse-btn:hover {
  transform: rotate(180deg);
}

.theme-toggle {
  transition: transform 0.3s;
}

.theme-toggle:hover {
  transform: rotate(180deg);
}

/* 主内容区样式 */
.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  transition: background-color 0.3s;
  overflow-y: auto;
}

.main-dark {
  background-color: #141414;
}

/* 全局加载动画 */
.global-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 15px;
}

.global-loading p {
  color: #409EFF;
  font-size: 16px;
}

/* 过渡动画 */
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

/* 深色模式下的 Element Plus 组件样式调整 */
.dark-mode .el-card {
  background-color: #1f1f1f;
  border-color: #303030;
  color: #e8e8e8;
}

.dark-mode .el-table {
  background-color: #1f1f1f;
  color: #e8e8e8;
}

.dark-mode .el-table th,
.dark-mode .el-table tr {
  background-color: #1f1f1f;
  color: #e8e8e8;
}

.dark-mode .el-table--enable-row-hover .el-table__body tr:hover > td {
  background-color: #2a2a2a !important;
}

.dark-mode .el-dialog {
  background-color: #1f1f1f;
  color: #e8e8e8;
}

.dark-mode .el-dialog__header {
  border-bottom-color: #303030;
}

.dark-mode .el-form-item__label {
  color: #b3b3b3;
}

.dark-mode .el-input__wrapper {
  background-color: #2a2a2a;
  box-shadow: 0 0 0 1px #303030 inset;
}

.dark-mode .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #409EFF inset;
}

.dark-mode .el-textarea__inner {
  background-color: #2a2a2a;
  color: #e8e8e8;
  border-color: #303030;
}

.dark-mode .el-select .el-input__wrapper {
  background-color: #2a2a2a;
}

.dark-mode .el-button {
  background-color: #2a2a2a;
  border-color: #303030;
  color: #e8e8e8;
}

.dark-mode .el-button--primary {
  background-color: #409EFF;
  border-color: #409EFF;
  color: #fff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-title {
    font-size: 16px;
  }

  .sidebar {
    position: fixed;
    z-index: 1000;
    height: 100vh;
  }

  .main-content {
    padding: 10px;
  }
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.dark-mode ::-webkit-scrollbar-track {
  background: #1f1f1f;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.dark-mode ::-webkit-scrollbar-thumb {
  background: #444;
}

.dark-mode ::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>
