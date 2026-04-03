/**
 * 主题状态管理
 */
import { ref, watch } from 'vue'

const THEME_KEY = 'app-theme'

// 响应式主题状态
const isDark = ref(false)

// 初始化主题
const initTheme = () => {
  // 从 localStorage 读取
  const savedTheme = localStorage.getItem(THEME_KEY)

  if (savedTheme) {
    isDark.value = savedTheme === 'dark'
  } else {
    // 检测系统主题
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  applyTheme()
}

// 应用主题
const applyTheme = () => {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 切换主题
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
  applyTheme()
}

// 设置主题
const setTheme = (dark) => {
  isDark.value = dark
  localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light')
  applyTheme()
}

// 监听系统主题变化
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem(THEME_KEY)) {
      isDark.value = e.matches
      applyTheme()
    }
  })
}

export function useTheme() {
  return {
    isDark,
    initTheme,
    toggleTheme,
    setTheme
  }
}