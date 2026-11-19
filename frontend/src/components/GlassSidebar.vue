<template>
  <div class="glass-sidebar">
    <!-- Logo Area -->
    <div class="logo-area">
      <div class="logo-icon">
        <span class="logo-letter">S</span>
      </div>
    </div>

    <!-- Navigation Icons -->
    <div class="nav-area">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        :title="item.title"
      >
        <el-icon :size="20">
          <component :is="item.icon" />
        </el-icon>
      </router-link>
    </div>

    <!-- Bottom Tools -->
    <div class="tools-area">
      <button class="tool-btn" @click="$emit('toggleTheme')" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
        <el-icon :size="20">
          <Sunny v-if="isDark" />
          <Moon v-else />
        </el-icon>
      </button>
      <button class="tool-btn" @click="$emit('showGuide')" title="帮助">
        <el-icon :size="20">
          <QuestionFilled />
        </el-icon>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import {
  Document,
  VideoPlay,
  Clock,
  Link,
  Share,
  Folder,
  Setting,
  MagicStick,
  Sunny,
  Moon,
  QuestionFilled,
  Tools,
  Coin,
  PriceTag,
  Files
} from '@element-plus/icons-vue'

// Props
defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

// Emits
defineEmits(['toggleTheme', 'showGuide'])

// Router
const route = useRoute()

// Navigation items
const navItems = [
  { path: '/scripts', icon: Document, title: '脚本管理' },
  { path: '/executions', icon: VideoPlay, title: '执行记录' },
  { path: '/schedules', icon: Clock, title: '定时任务' },
  { path: '/webhooks', icon: Link, title: 'Webhook' },
  { path: '/workflows', icon: Share, title: '工作流' },
  { path: '/files', icon: Folder, title: '文件管理' },
  { path: '/environments', icon: Setting, title: '环境配置' },
  { path: '/global-variables', icon: Coin, title: '全局变量' },
  { path: '/tags', icon: PriceTag, title: '标签管理' },
  { path: '/backup', icon: Files, title: '备份管理' },
  { path: '/ai-settings', icon: Tools, title: '系统设置' },
  { path: '/ai-script-writer', icon: MagicStick, title: 'AI脚本助手' }
]

// Check if current route is active
const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.glass-sidebar {
  width: 48px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
}

/* Logo Area */
.logo-area {
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  width: 100%;
  display: flex;
  justify-content: center;
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: var(--el-color-primary);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-letter {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Arial', sans-serif;
}

/* Navigation Area */
.nav-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  padding: 0 8px;
}

.nav-area::-webkit-scrollbar {
  width: 4px;
}

.nav-area::-webkit-scrollbar-track {
  background: transparent;
}

.nav-area::-webkit-scrollbar-thumb {
  background: var(--el-border-color-lighter);
  border-radius: 2px;
}

.nav-item {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--el-text-color-secondary);
  text-decoration: none;
  transition: background 0.15s ease, color 0.15s ease;
  flex-shrink: 0;
}

.nav-item:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.nav-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

/* Tools Area */
.tools-area {
  padding-top: 10px;
  margin-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.tool-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: background 0.15s ease;
}

.tool-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

/* Responsive: Mobile Bottom Navigation */
@media (max-width: 768px) {
  .glass-sidebar {
    width: 100%;
    height: auto;
    margin: 0;
    border-radius: 0;
    border-left: none;
    border-right: none;
    border-bottom: none;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    flex-direction: row;
    padding: 8px 16px;
    z-index: 1000;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
  }

  .logo-area {
    display: none;
  }

  .nav-area {
    flex-direction: row;
    flex: 1;
    justify-content: center;
    padding: 0;
    border-bottom: none;
    margin-bottom: 0;
    gap: 4px;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .nav-item {
    width: 36px;
    height: 36px;
  }

  .tools-area {
    flex-direction: row;
    padding-top: 0;
    margin-top: 0;
    border-top: none;
    padding-left: 16px;
    gap: 4px;
  }

  .tool-btn {
    width: 36px;
    height: 36px;
  }
}
</style>