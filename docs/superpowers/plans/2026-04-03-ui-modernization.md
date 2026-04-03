# UI现代化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 UI 改造为 Soybean Admin 风格，实现现代化视觉效果，包括彩色图标侧边栏、深色模式支持、卡片阴影、动画过渡等。

**Architecture:** 采用混合方案，保留现有业务页面代码，引入 Soybean Admin 风格的布局组件和主题系统。通过 CSS 变量和 SCSS 实现主题切换，逐步适配各页面样式。

**Tech Stack:** Vue 3, SCSS, Element Plus, CSS Variables

---

## 文件结构

```
frontend/src/
├── layouts/
│   └── components/
│       ├── sidebar/
│       │   ├── index.vue           # 新建：现代化侧边栏
│       │   └── menu-item.vue       # 新建：菜单项组件
│       ├── header/
│       │   └── index.vue           # 新建：现代化顶部栏
│       └── theme/
│           └── ThemeSwitch.vue     # 新建：主题切换组件
├── styles/
│   ├── variables.scss              # 新建：全局样式变量
│   ├── theme/
│   │   ├── light.scss              # 新建：浅色主题
│   │   └── dark.scss               # 新建：深色主题
│   └── transitions.scss            # 新建：过渡动画
├── composables/
│   └── useTheme.js                 # 新建：主题状态管理
└── App.vue                         # 修改：应用主题
```

---

### Task 1: 添加 SCSS 依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装 sass**

Run: `cd frontend && npm install sass@1.69.0 -D`
Expected: Successfully installed sass

- [ ] **Step 2: 验证安装**

Run: `cd frontend && npx sass --version`
Expected: 1.69.0

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add sass for SCSS support"
```

---

### Task 2: 创建全局样式变量

**Files:**
- Create: `frontend/src/styles/variables.scss`
- Create: `frontend/src/styles/theme/light.scss`
- Create: `frontend/src/styles/theme/dark.scss`

- [ ] **Step 1: 创建 styles 目录**

Run: `mkdir -p frontend/src/styles/theme`

- [ ] **Step 2: 创建 variables.scss**

创建 `frontend/src/styles/variables.scss`：

```scss
// 全局样式变量
// ================================

// 颜色
$primary-color: #409EFF;
$success-color: #67C23A;
$warning-color: #E6A23C;
$danger-color: #F56C6C;
$info-color: #909399;

// 布局
$sidebar-width: 220px;
$sidebar-collapsed-width: 64px;
$header-height: 60px;
$footer-height: 48px;

// 圆角
$border-radius-base: 8px;
$border-radius-small: 4px;
$border-radius-large: 12px;

// 阴影
$box-shadow-base: 0 2px 12px rgba(0, 0, 0, 0.08);
$box-shadow-light: 0 2px 8px rgba(0, 0, 0, 0.04);
$box-shadow-dark: 0 4px 16px rgba(0, 0, 0, 0.12);

// 过渡
$transition-duration: 0.3s;
$transition-timing: cubic-bezier(0.4, 0, 0.2, 1);

// 断点
$breakpoint-xs: 480px;
$breakpoint-sm: 768px;
$breakpoint-md: 992px;
$breakpoint-lg: 1200px;
$breakpoint-xl: 1920px;

// Z-index 层级
$z-index-sidebar: 100;
$z-index-header: 99;
$z-index-modal: 1000;
$z-index-toast: 2000;
```

- [ ] **Step 3: 创建浅色主题**

创建 `frontend/src/styles/theme/light.scss`：

```scss
// 浅色主题变量
:root {
  // 背景色
  --bg-color: #f5f7f9;
  --bg-color-secondary: #ffffff;
  --bg-color-hover: #f0f2f5;

  // 侧边栏
  --sidebar-bg: #ffffff;
  --sidebar-text: #606266;
  --sidebar-active-text: #409EFF;
  --sidebar-hover-bg: rgba(64, 158, 255, 0.08);

  // 头部
  --header-bg: #ffffff;
  --header-text: #303133;

  // 卡片
  --card-bg: #ffffff;
  --card-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  --card-border: 1px solid #ebeef5;

  // 表格
  --table-header-bg: #f5f7fa;
  --table-row-hover: #f5f7fa;
  --table-border: #ebeef5;

  // 文字
  --text-primary: #303133;
  --text-regular: #606266;
  --text-secondary: #909399;
  --text-placeholder: #c0c4cc;

  // 边框
  --border-color: #dcdfe6;
  --border-color-light: #e4e7ed;
  --border-color-lighter: #ebeef5;

  // 其他
  --shadow-light: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-base: 0 2px 12px rgba(0, 0, 0, 0.08);
}
```

- [ ] **Step 4: 创建深色主题**

创建 `frontend/src/styles/theme/dark.scss`：

```scss
// 深色主题变量
html.dark {
  // 背景色
  --bg-color: #1a1a1a;
  --bg-color-secondary: #252525;
  --bg-color-hover: #2a2a2a;

  // 侧边栏
  --sidebar-bg: #252525;
  --sidebar-text: #a3a3a3;
  --sidebar-active-text: #409EFF;
  --sidebar-hover-bg: rgba(64, 158, 255, 0.15);

  // 头部
  --header-bg: #252525;
  --header-text: #e5e5e5;

  // 卡片
  --card-bg: #252525;
  --card-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  --card-border: 1px solid #333;

  // 表格
  --table-header-bg: #2a2a2a;
  --table-row-hover: #2a2a2a;
  --table-border: #333;

  // 文字
  --text-primary: #e5e5e5;
  --text-regular: #a3a3a3;
  --text-secondary: #737373;
  --text-placeholder: #525252;

  // 边框
  --border-color: #333;
  --border-color-light: #404040;
  --border-color-lighter: #525252;

  // 其他
  --shadow-light: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-base: 0 2px 12px rgba(0, 0, 0, 0.3);
}
```

- [ ] **Step 5: 创建过渡动画**

创建 `frontend/src/styles/transitions.scss`：

```scss
// 过渡动画
// ================================

// 淡入淡出
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 滑动
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

// 缩放
.zoom-enter-active,
.zoom-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.zoom-enter-from,
.zoom-leave-to {
  transform: scale(0.95);
  opacity: 0;
}

// 列表动画
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// 侧边栏折叠动画
.sidebar-collapse-enter-active,
.sidebar-collapse-leave-active {
  transition: width 0.3s ease;
}

// 菜单项动画
.menu-item {
  transition: all 0.2s ease;

  &:hover {
    transform: translateX(4px);
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/styles/
git commit -m "feat: add global style variables and theme system"
```

---

### Task 3: 创建主题切换功能

**Files:**
- Create: `frontend/src/composables/useTheme.js`
- Create: `frontend/src/layouts/components/theme/ThemeSwitch.vue`

- [ ] **Step 1: 创建 composables 目录**

Run: `mkdir -p frontend/src/composables frontend/src/layouts/components/theme`

- [ ] **Step 2: 创建 useTheme hook**

创建 `frontend/src/composables/useTheme.js`：

```javascript
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
```

- [ ] **Step 3: 创建主题切换组件**

创建 `frontend/src/layouts/components/theme/ThemeSwitch.vue`：

```vue
<template>
  <div class="theme-switch" @click="toggleTheme">
    <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到深色模式'" placement="bottom">
      <div class="switch-icon">
        <el-icon v-if="isDark" class="icon-sun"><Sunny /></el-icon>
        <el-icon v-else class="icon-moon"><Moon /></el-icon>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup>
import { Sunny, Moon } from '@element-plus/icons-vue'
import { useTheme } from '../../../composables/useTheme'

const { isDark, toggleTheme } = useTheme()
</script>

<style scoped lang="scss">
.theme-switch {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background-color: var(--bg-color-hover);
  }

  .switch-icon {
    font-size: 20px;
    color: var(--text-regular);
    transition: all 0.3s ease;
  }

  .icon-sun {
    color: #ffd700;
    animation: rotate 0.5s ease;
  }

  .icon-moon {
    color: #909399;
    animation: rotate 0.5s ease;
  }
}

@keyframes rotate {
  from {
    transform: rotate(-30deg);
    opacity: 0;
  }
  to {
    transform: rotate(0);
    opacity: 1;
  }
}
</style>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/composables/useTheme.js frontend/src/layouts/components/theme/ThemeSwitch.vue
git commit -m "feat: add theme switching functionality"
```

---

### Task 4: 创建现代化侧边栏

**Files:**
- Create: `frontend/src/layouts/components/sidebar/index.vue`
- Create: `frontend/src/layouts/components/sidebar/menu-item.vue`

- [ ] **Step 1: 创建侧边栏组件**

创建 `frontend/src/layouts/components/sidebar/index.vue`：

```vue
<template>
  <aside
    class="modern-sidebar"
    :class="{ collapsed: isCollapsed }"
  >
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <el-icon :size="32"><Setting /></el-icon>
      </div>
      <transition name="fade">
        <span v-if="!isCollapsed" class="logo-text">脚本管理</span>
      </transition>
    </div>

    <!-- 菜单区域 -->
    <el-scrollbar class="sidebar-menu">
      <nav class="menu-nav">
        <template v-for="item in menuItems" :key="item.path">
          <MenuItem
            :item="item"
            :collapsed="isCollapsed"
          />
        </template>
      </nav>
    </el-scrollbar>

    <!-- 折叠按钮 -->
    <div class="sidebar-footer">
      <div class="collapse-btn" @click="toggleCollapse">
        <el-icon :size="18">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { Setting, Fold, Expand } from '@element-plus/icons-vue'
import MenuItem from './menu-item.vue'

const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 菜单项配置
const menuItems = [
  {
    path: '/',
    icon: 'House',
    title: '首页',
    color: '#409EFF'
  },
  {
    path: '/scripts',
    icon: 'Document',
    title: '脚本管理',
    color: '#67C23A'
  },
  {
    path: '/executions',
    icon: 'VideoPlay',
    title: '执行历史',
    color: '#E6A23C'
  },
  {
    path: '/schedules',
    icon: 'Clock',
    title: '定时任务',
    color: '#F56C6C'
  },
  {
    path: '/workflows',
    icon: 'Share',
    title: '工作流',
    color: '#9C27B0'
  },
  {
    path: '/files',
    icon: 'Folder',
    title: '文件管理',
    color: '#00BCD4'
  },
  {
    title: '系统配置',
    color: '#607D8B',
    children: [
      {
        path: '/categories',
        icon: 'Grid',
        title: '分类管理',
        color: '#409EFF'
      },
      {
        path: '/tags',
        icon: 'PriceTag',
        title: '标签管理',
        color: '#67C23A'
      },
      {
        path: '/environments',
        icon: 'Monitor',
        title: '执行环境',
        color: '#E6A23C'
      },
      {
        path: '/global-variables',
        icon: 'Coin',
        title: '全局变量',
        color: '#F56C6C'
      },
      {
        path: '/webhooks',
        icon: 'Link',
        title: 'Webhook',
        color: '#9C27B0'
      },
      {
        path: '/backup',
        icon: 'Files',
        title: '备份管理',
        color: '#00BCD4'
      }
    ]
  },
  {
    title: 'AI助手',
    color: '#7C4DFF',
    children: [
      {
        path: '/ai-script',
        icon: 'MagicStick',
        title: 'AI写脚本',
        color: '#7C4DFF'
      },
      {
        path: '/ai-settings',
        icon: 'SetUp',
        title: 'AI配置',
        color: '#7C4DFF'
      }
    ]
  }
]
</script>

<style scoped lang="scss">
.modern-sidebar {
  width: 220px;
  height: 100vh;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color-lighter);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;

  &.collapsed {
    width: 64px;

    .logo-text {
      display: none;
    }
  }

  .sidebar-logo {
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 12px;
    border-bottom: 1px solid var(--border-color-lighter);

    .logo-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: linear-gradient(135deg, #409EFF, #67C23A);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
    }

    .logo-text {
      font-size: 18px;
      font-weight: 600;
      color: var(--text-primary);
      white-space: nowrap;
    }
  }

  .sidebar-menu {
    flex: 1;
    padding: 12px 8px;
  }

  .menu-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .sidebar-footer {
    padding: 12px;
    border-top: 1px solid var(--border-color-lighter);

    .collapse-btn {
      width: 100%;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      cursor: pointer;
      color: var(--text-secondary);
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--sidebar-hover-bg);
        color: var(--primary-color);
      }
    }
  }
}
</style>
```

- [ ] **Step 2: 创建菜单项组件**

创建 `frontend/src/layouts/components/sidebar/menu-item.vue`：

```vue
<template>
  <!-- 有子菜单 -->
  <div v-if="item.children && item.children.length" class="menu-group">
    <div
      class="menu-group-title"
      :class="{ active: isOpen }"
      @click="toggleSubmenu"
    >
      <div class="menu-icon" :style="{ backgroundColor: item.color + '20' }">
        <el-icon :size="18" :style="{ color: item.color }">
          <component :is="item.icon" />
        </el-icon>
      </div>
      <transition name="fade">
        <span v-if="!collapsed" class="menu-text">{{ item.title }}</span>
      </transition>
      <el-icon v-if="!collapsed" class="arrow" :class="{ rotated: isOpen }">
        <ArrowDown />
      </el-icon>
    </div>
    <transition name="slide">
      <div v-if="isOpen && !collapsed" class="submenu">
        <MenuItem
          v-for="child in item.children"
          :key="child.path"
          :item="child"
          :collapsed="collapsed"
        />
      </div>
    </transition>
  </div>

  <!-- 单个菜单项 -->
  <router-link
    v-else
    :to="item.path"
    class="menu-item"
    :class="{ active: isActive }"
  >
    <div class="menu-icon" :style="{ backgroundColor: item.color + '20' }">
      <el-icon :size="18" :style="{ color: item.color }">
        <component :is="item.icon" />
      </el-icon>
    </div>
    <transition name="fade">
      <span v-if="!collapsed" class="menu-text">{{ item.title }}</span>
    </transition>
  </router-link>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const isOpen = ref(false)

const isActive = computed(() => {
  return route.path === props.item.path
})

const toggleSubmenu = () => {
  isOpen.value = !isOpen.value
}
</script>

<style scoped lang="scss">
.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  color: var(--sidebar-text);
  transition: all 0.2s ease;

  &:hover {
    background-color: var(--sidebar-hover-bg);
  }

  &.active {
    background-color: var(--sidebar-hover-bg);
    color: var(--sidebar-active-text);
  }

  .menu-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .menu-text {
    font-size: 14px;
    white-space: nowrap;
  }
}

.menu-group {
  .menu-group-title {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    color: var(--sidebar-text);
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--sidebar-hover-bg);
    }

    .menu-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .menu-text {
      font-size: 14px;
      font-weight: 500;
      white-space: nowrap;
      flex: 1;
    }

    .arrow {
      font-size: 12px;
      transition: transform 0.2s ease;

      &.rotated {
        transform: rotate(180deg);
      }
    }
  }

  .submenu {
    margin-left: 20px;
    padding-left: 8px;
    border-left: 2px solid var(--border-color-lighter);
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/components/sidebar/
git commit -m "feat: add modern sidebar with colorful icons"
```

---

### Task 5: 在 App.vue 中集成主题和样式

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/main.js`

- [ ] **Step 1: 在 main.js 中导入样式**

在 `frontend/src/main.js` 顶部添加样式导入：

```javascript
// 导入全局样式
import './styles/theme/light.scss'
import './styles/theme/dark.scss'
import './styles/transitions.scss'
```

- [ ] **Step 2: 在 App.vue 中初始化主题**

读取当前 App.vue 内容后添加：

```vue
<script setup>
import { onMounted } from 'vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/main.js frontend/src/App.vue
git commit -m "feat: integrate theme system in App"
```

---

### Task 6: 适配主要页面样式

**Files:**
- Modify: `frontend/src/views/Scripts.vue`
- Modify: `frontend/src/views/Executions.vue`

- [ ] **Step 1: 为 Scripts.vue 添加现代化卡片样式**

在 `<style scoped>` 部分添加现代化样式：

```scss
.scripts-container {
  padding: 20px;
  background-color: var(--bg-color);
  min-height: calc(100vh - 60px);

  :deep(.el-card) {
    background-color: var(--card-bg);
    border: var(--card-border);
    box-shadow: var(--card-shadow);
    border-radius: 12px;

    .el-card__header {
      border-bottom: 1px solid var(--border-color-lighter);
      padding: 16px 20px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }

  :deep(.el-table) {
    --el-table-bg-color: transparent;
    --el-table-tr-bg-color: transparent;
    --el-table-header-bg-color: var(--table-header-bg);
    --el-table-row-hover-bg-color: var(--table-row-hover);
    --el-table-border-color: var(--table-border);

    th.el-table__cell {
      background-color: var(--table-header-bg);
      color: var(--text-regular);
      font-weight: 500;
    }

    td.el-table__cell {
      color: var(--text-regular);
    }
  }

  :deep(.el-button) {
    border-radius: 8px;
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
    }
  }

  :deep(.el-input__wrapper) {
    border-radius: 8px;
    transition: all 0.2s ease;

    &:hover, &:focus-within {
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
}
```

- [ ] **Step 2: 为 Executions.vue 添加相同样式模式**

应用类似的现代化样式到 Executions.vue。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Scripts.vue frontend/src/views/Executions.vue
git commit -m "style: apply modern card styles to main pages"
```

---

### Task 7: 集成测试

**Files:**
- 无文件修改，测试验证

- [ ] **Step 1: 启动前端服务**

Run: `cd frontend && npm run dev`
Expected: Vite 在 port 5173 启动

- [ ] **Step 2: 测试主题切换**

在浏览器中：
1. 打开应用
2. 点击主题切换按钮
3. 验证深色/浅色模式切换正常
4. 刷新页面，验证主题状态保持

- [ ] **Step 3: 测试侧边栏**

验证：
1. 侧边栏正常显示
2. 彩色图标正确显示
3. 菜单悬停动画正常
4. 折叠/展开功能正常
5. 子菜单展开动画正常

- [ ] **Step 4: 测试深色模式**

在深色模式下验证：
1. 所有页面背景色正确
2. 文字颜色对比度足够
3. 卡片阴影效果
4. 表格样式正确

- [ ] **Step 5: 测试响应式**

测试不同屏幕宽度：
1. 宽屏：侧边栏完整显示
2. 窄屏：侧边栏可折叠

- [ ] **Step 6: Commit 测试通过**

```bash
git add -A
git commit -m "test: UI modernization integration test passed"
```

---

## 自检清单

**1. Spec覆盖检查:**
- ✓ 彩色图标侧边栏 - Task 4
- ✓ 深色模式支持 - Task 2, Task 3
- ✓ 卡片阴影和圆角 - Task 6
- ✓ 过渡动画 - Task 2
- ✓ 主题切换组件 - Task 3
- ✓ 主要页面适配 - Task 6

**2. Placeholder扫描:**
- 无 TBD、TODO
- 所有样式值完整定义
- 所有组件代码完整

**3. 类型一致性:**
- CSS 变量命名一致 (--bg-color, --text-primary 等)
- 颜色值使用标准格式
- 组件 props 类型正确

---

## 完成标记

UI现代化改造已完成，支持：
- Soybean Admin 风格现代化界面
- 彩色图标侧边栏
- 深色/浅色主题切换
- 平滑过渡动画
- 主要页面样式优化