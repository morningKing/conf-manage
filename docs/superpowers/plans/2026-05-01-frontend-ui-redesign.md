# 前端UI渐变玻璃风格重设计实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将脚本管理系统前端从传统Element Plus风格转换为渐变玻璃风格，使用紫蓝渐变背景、紧凑侧边栏、边框玻璃卡片和圆润填充交互元素。

**Architecture:** 采用CSS变量驱动的设计系统，全局渐变背景铺满页面，侧边栏从200px改为55px紧凑图标式，所有卡片改为透明背景+发光边框样式，按钮改为圆角胶囊形状。

**Tech Stack:** Vue 3 + Element Plus + SCSS + CSS Variables

---

## 文件结构

### 新建文件
- `frontend/src/styles/glass-theme.scss` - 玻璃风格核心CSS变量和样式
- `frontend/src/components/GlassSidebar.vue` - 新的紧凑侧边栏组件
- `frontend/src/components/GlassCard.vue` - 玻璃卡片通用组件
- `frontend/src/components/GlassButton.vue` - 圆润按钮组件

### 修改文件
- `frontend/src/App.vue` - 重构整体布局，应用渐变背景
- `frontend/src/styles/variables.scss` - 添加玻璃风格变量
- `frontend/src/views/*.vue` - 各页面使用新样式组件

---

## Task 1: 创建玻璃风格核心CSS变量文件

**Files:**
- Create: `frontend/src/styles/glass-theme.scss`

- [ ] **Step 1: 创建glass-theme.scss文件**

```scss
// 玻璃风格核心变量和样式
// ================================

// 渐变颜色
$gradient-start: #667eea;
$gradient-end: #764ba2;

// 玻璃透明度层级
$glass-highlight: rgba(255, 255, 255, 0.25);
$glass-active: rgba(255, 255, 255, 0.15);
$glass-base: rgba(255, 255, 255, 0.10);
$glass-low: rgba(255, 255, 255, 0.05);
$glass-dark: rgba(30, 30, 50, 0.85);

// 边框颜色层级
$border-main: rgba(255, 255, 255, 0.35);
$border-secondary: rgba(255, 255, 255, 0.20);
$border-low: rgba(255, 255, 255, 0.10);
$border-gradient: rgba(102, 126, 234, 0.30);

// 圆角
$radius-lg: 12px;
$radius-md: 8px;
$radius-sm: 6px;
$radius-pill: 20px;

// 侧边栏尺寸
$sidebar-width: 55px;
$sidebar-icon-size: 32px;

// 文字颜色
$text-primary: #ffffff;
$text-secondary: rgba(255, 255, 255, 0.8);
$text-muted: rgba(255, 255, 255, 0.6);
$text-placeholder: rgba(255, 255, 255, 0.5);

// CSS变量导出
:root {
  // 渐变
  --gradient-start: #667eea;
  --gradient-end: #764ba2;
  
  // 玻璃层级
  --glass-highlight: rgba(255, 255, 255, 0.25);
  --glass-active: rgba(255, 255, 255, 0.15);
  --glass-base: rgba(255, 255, 255, 0.10);
  --glass-low: rgba(255, 255, 255, 0.05);
  --glass-dark: rgba(30, 30, 50, 0.85);
  
  // 边框
  --border-main: rgba(255, 255, 255, 0.35);
  --border-secondary: rgba(255, 255, 255, 0.20);
  --border-low: rgba(255, 255, 255, 0.10);
  
  // 圆角
  --radius-lg: 12px;
  --radius-md: 8px;
  --radius-sm: 6px;
  --radius-pill: 20px;
  
  // 侧边栏
  --sidebar-width: 55px;
  --sidebar-icon-size: 32px;
  
  // 文字
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.8);
  --text-muted: rgba(255, 255, 255, 0.6);
}

// 全局渐变背景
.glass-app {
  background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
  min-height: 100vh;
  color: var(--text-primary);
}

// 玻璃卡片样式
.glass-card {
  background: transparent;
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: 15px;
  transition: all 0.3s ease;
}

.glass-card:hover {
  border-color: var(--border-main);
  background: var(--glass-low);
}

// 深色玻璃卡片（用于代码编辑器等）
.glass-card-dark {
  background: var(--glass-dark);
  border: 1px solid var(--border-gradient);
  border-radius: var(--radius-lg);
}

// 玻璃按钮 - 主要
.glass-btn-primary {
  background: var(--glass-active);
  border: none;
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.glass-btn-primary:hover {
  background: var(--glass-highlight);
}

// 玻璃按钮 - 次要
.glass-btn-secondary {
  background: var(--glass-base);
  border: none;
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.glass-btn-secondary:hover {
  background: var(--glass-active);
}

// 玻璃按钮 - 小型
.glass-btn-sm {
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 10px;
}

// 玻璃输入框
.glass-input {
  background: var(--glass-active);
  border: none;
  border-radius: var(--radius-pill);
  padding: 10px 14px;
  color: var(--text-primary);
  outline: none;
  transition: background 0.2s ease;
}

.glass-input:focus {
  background: var(--glass-highlight);
}

.glass-input::placeholder {
  color: var(--text-placeholder);
}

// 玻璃侧边栏容器
.glass-sidebar {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 5px;
  gap: 8px;
}

// 侧边栏图标按钮
.glass-sidebar-icon {
  width: var(--sidebar-icon-size);
  height: var(--sidebar-icon-size);
  background: var(--glass-base);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
}

.glass-sidebar-icon:hover {
  background: var(--glass-active);
  color: var(--text-primary);
}

.glass-sidebar-icon.active {
  background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
  color: var(--text-primary);
}

// 玻璃顶部栏
.glass-header {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
}

// 玻璃状态栏
.glass-status-bar {
  background: transparent;
  border: 1px solid var(--border-low);
  border-radius: var(--radius-lg);
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
}

// 浅色模式变量
:root.light-mode {
  --gradient-start: #f0f4ff;
  --gradient-end: #e8e0f0;
  --glass-highlight: rgba(255, 255, 255, 0.9);
  --glass-active: rgba(255, 255, 255, 0.7);
  --glass-base: rgba(255, 255, 255, 0.5);
  --glass-low: rgba(255, 255, 255, 0.3);
  --glass-dark: rgba(255, 255, 255, 0.85);
  --border-main: rgba(102, 126, 234, 0.3);
  --border-secondary: rgba(102, 126, 234, 0.2);
  --border-low: rgba(102, 126, 234, 0.1);
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-muted: #999999;
  --text-placeholder: #aaaaaa;
}

// Element Plus组件覆盖样式
.glass-app .el-card {
  background: transparent;
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
}

.glass-app .el-button {
  border-radius: var(--radius-pill);
}

.glass-app .el-input__wrapper {
  background: var(--glass-active);
  border-radius: var(--radius-pill);
  box-shadow: none;
}

.glass-app .el-table {
  background: transparent;
  color: var(--text-primary);
}

.glass-app .el-table th,
.glass-app .el-table tr {
  background: transparent;
}

.glass-app .el-dialog {
  background: var(--glass-dark);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
}

// 响应式断点
@media (max-width: 1200px) {
  .glass-card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .glass-sidebar {
    width: 100%;
    height: auto;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    padding: 10px;
    gap: 5px;
    flex-direction: row;
    justify-content: space-around;
  }
  
  .glass-card-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 2: 验证文件创建成功**

Run: `ls -la frontend/src/styles/glass-theme.scss`
Expected: 文件存在，大小约3000字节

- [ ] **Step 3: 提交**

```bash
git add frontend/src/styles/glass-theme.scss
git commit -m "feat: add glass theme CSS variables and core styles"
```

---

## Task 2: 创建GlassSidebar紧凑侧边栏组件

**Files:**
- Create: `frontend/src/components/GlassSidebar.vue`

- [ ] **Step 1: 创建GlassSidebar.vue组件**

```vue
<template>
  <div class="glass-sidebar">
    <!-- Logo -->
    <div class="glass-sidebar-logo">
      <div class="logo-icon">
        <span>S</span>
      </div>
    </div>

    <!-- 导航图标 -->
    <div class="glass-sidebar-nav">
      <div
        v-for="item in navItems"
        :key="item.path"
        :class="['glass-sidebar-icon', { active: isActive(item.path) }]"
        @click="navigate(item.path)"
      >
        <el-icon :size="18">
          <component :is="item.icon" />
        </el-icon>
      </div>
    </div>

    <!-- 底部工具 -->
    <div class="glass-sidebar-tools">
      <div class="glass-sidebar-icon" @click="toggleTheme">
        <el-icon :size="18">
          <Sunny v-if="isDark" />
          <Moon v-else />
        </el-icon>
      </div>
      <div class="glass-sidebar-icon" @click="showGuide">
        <el-icon :size="18">
          <QuestionFilled />
        </el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Document, VideoPlay, Clock, Link, Share, Folder,
  Setting, MagicStick, Sunny, Moon, QuestionFilled
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  isDark: Boolean
})

const emit = defineEmits(['toggleTheme', 'showGuide'])

const navItems = [
  { path: '/scripts', icon: 'Document' },
  { path: '/executions', icon: 'VideoPlay' },
  { path: '/schedules', icon: 'Clock' },
  { path: '/webhooks', icon: 'Link' },
  { path: '/workflows', icon: 'Share' },
  { path: '/files', icon: 'Folder' },
  { path: '/environments', icon: 'Setting' },
  { path: '/ai-script-writer', icon: 'MagicStick' },
]

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const navigate = (path) => {
  router.push(path)
}

const toggleTheme = () => {
  emit('toggleTheme')
}

const showGuide = () => {
  emit('showGuide')
}
</script>

<style scoped>
.glass-sidebar {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  width: 55px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 5px;
  gap: 8px;
  height: calc(100vh - 30px);
  margin: 15px;
}

.glass-sidebar-logo {
  margin-bottom: 10px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.glass-sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  overflow-y: auto;
}

.glass-sidebar-icon {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.10);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255, 255, 255, 0.8);
}

.glass-sidebar-icon:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.glass-sidebar-icon.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.4), rgba(118, 75, 162, 0.4));
  color: white;
}

.glass-sidebar-tools {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

/* 响应式：移动端底部导航 */
@media (max-width: 768px) {
  .glass-sidebar {
    width: calc(100% - 20px);
    height: auto;
    position: fixed;
    bottom: 10px;
    left: 10px;
    right: 10px;
    border-radius: 12px;
    padding: 10px;
    gap: 5px;
    flex-direction: row;
    justify-content: space-around;
    align-items: center;
    margin: 0;
    z-index: 1000;
  }
  
  .glass-sidebar-nav {
    flex-direction: row;
    flex: none;
    gap: 5px;
  }
  
  .glass-sidebar-tools {
    flex-direction: row;
    margin-top: 0;
  }
  
  .glass-sidebar-logo {
    margin-bottom: 0;
  }
}
</style>
```

- [ ] **Step 2: 验证组件创建成功**

Run: `ls -la frontend/src/components/GlassSidebar.vue`
Expected: 文件存在

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/GlassSidebar.vue
git commit -m "feat: create GlassSidebar compact sidebar component"
```

---

## Task 3: 创建GlassCard玻璃卡片组件

**Files:**
- Create: `frontend/src/components/GlassCard.vue`

- [ ] **Step 1: 创建GlassCard.vue组件**

```vue
<template>
  <div :class="['glass-card', { 'glass-card-dark': dark, 'glass-card-hoverable': hoverable }]">
    <!-- 卡片头部 -->
    <div v-if="title || $slots.header" class="glass-card-header">
      <slot name="header">
        <span class="glass-card-title">{{ title }}</span>
      </slot>
      <div v-if="$slots.extra" class="glass-card-extra">
        <slot name="extra"></slot>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="glass-card-body">
      <slot></slot>
    </div>

    <!-- 卡片底部 -->
    <div v-if="$slots.footer" class="glass-card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  dark: Boolean,
  hoverable: Boolean
})
</script>

<style scoped>
.glass-card {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.20);
  border-radius: 12px;
  padding: 15px;
  transition: all 0.3s ease;
}

.glass-card-hoverable:hover {
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.05);
  cursor: pointer;
}

.glass-card-dark {
  background: rgba(30, 30, 50, 0.85);
  border: 1px solid rgba(102, 126, 234, 0.30);
}

.glass-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}

.glass-card-dark .glass-card-header {
  border-bottom-color: rgba(102, 126, 234, 0.20);
}

.glass-card-title {
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.glass-card-dark .glass-card-title {
  color: #a78bfa;
}

.glass-card-body {
  color: rgba(255, 255, 255, 0.9);
}

.glass-card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.10);
  display: flex;
  align-items: center;
  gap: 8px;
}

.glass-card-dark .glass-card-footer {
  border-top-color: rgba(102, 126, 234, 0.20);
}

.glass-card-extra {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
```

- [ ] **Step 2: 验证组件创建成功**

Run: `ls -la frontend/src/components/GlassCard.vue`

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/GlassCard.vue
git commit -m "feat: create GlassCard glass-style card component"
```

---

## Task 4: 创建GlassButton圆润按钮组件

**Files:**
- Create: `frontend/src/components/GlassButton.vue`

- [ ] **Step 1: 创建GlassButton.vue组件**

```vue
<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    @click="handleClick"
  >
    <el-icon v-if="icon" :size="size === 'small' ? 14 : 16">
      <component :is="icon" />
    </el-icon>
    <span v-if="label">{{ label }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  icon: String,
  type: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'success', 'warning', 'danger'].includes(v)
  },
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['small', 'default', 'large'].includes(v)
  },
  disabled: Boolean
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => [
  'glass-btn',
  `glass-btn-${props.type}`,
  `glass-btn-${props.size}`,
  { 'glass-btn-disabled': props.disabled }
])

const handleClick = (e) => {
  if (!props.disabled) {
    emit('click', e)
  }
}
</script>

<style scoped>
.glass-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  font-family: inherit;
}

.glass-btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 类型样式 */
.glass-btn-primary {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  color: white;
}

.glass-btn-primary:hover:not(.glass-btn-disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.glass-btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  color: rgba(255, 255, 255, 0.8);
}

.glass-btn-secondary:hover:not(.glass-btn-disabled) {
  background: rgba(255, 255, 255, 0.15);
}

.glass-btn-success {
  background: rgba(103, 194, 58, 0.2);
  border-radius: 20px;
  color: #67c23a;
}

.glass-btn-success:hover:not(.glass-btn-disabled) {
  background: rgba(103, 194, 58, 0.3);
}

.glass-btn-warning {
  background: rgba(230, 162, 60, 0.2);
  border-radius: 20px;
  color: #e6a23c;
}

.glass-btn-warning:hover:not(.glass-btn-disabled) {
  background: rgba(230, 162, 60, 0.3);
}

.glass-btn-danger {
  background: rgba(245, 108, 108, 0.2);
  border-radius: 20px;
  color: #f56c6c;
}

.glass-btn-danger:hover:not(.glass-btn-disabled) {
  background: rgba(245, 108, 108, 0.3);
}

/* 尺寸样式 */
.glass-btn-small {
  padding: 4px 10px;
  font-size: 10px;
  border-radius: 12px;
}

.glass-btn-default {
  padding: 8px 16px;
  font-size: 12px;
}

.glass-btn-large {
  padding: 10px 20px;
  font-size: 14px;
}
</style>
```

- [ ] **Step 2: 验证组件创建成功**

Run: `ls -la frontend/src/components/GlassButton.vue`

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/GlassButton.vue
git commit -m "feat: create GlassButton rounded pill-style button component"
```

---

## Task 5: 重构App.vue整体布局

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 重写App.vue模板部分**

将整个模板替换为新的玻璃风格布局，使用GlassSidebar组件和渐变背景。关键改动：
1. 最外层div添加`glass-app`类
2. 替换原有的`el-aside`为`GlassSidebar`组件
3. 内容区域使用玻璃卡片样式包裹
4. 移除原有的深色模式类切换逻辑，改为light-mode类

- [ ] **Step 2: 更新script部分**

```javascript
// 导入新组件
import GlassSidebar from '@/components/GlassSidebar.vue'
import GlassCard from '@/components/GlassCard.vue'
import GlassButton from '@/components/GlassButton.vue'
import '@/styles/glass-theme.scss'

// 更新toggleTheme方法
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  
  // 切换light-mode类
  if (isDark.value) {
    document.documentElement.classList.remove('light-mode')
  } else {
    document.documentElement.classList.add('light-mode')
  }
}
```

- [ ] **Step 3: 简化style部分**

移除原有的所有样式，只保留必要的全局覆盖和过渡动画。核心样式已由`glass-theme.scss`提供。

- [ ] **Step 4: 验证App.vue修改**

Run: `cd frontend && npm run dev`
Expected: 浏览器显示渐变背景和紧凑侧边栏

- [ ] **Step 5: 提交**

```bash
git add frontend/src/App.vue frontend/src/styles/glass-theme.scss
git commit -m "feat: refactor App.vue with glass-style layout"
```

---

## Task 6: 更新Scripts.vue页面样式

**Files:**
- Modify: `frontend/src/views/Scripts.vue`

- [ ] **Step 1: 替换el-card为glass-card**

将页面中的`<el-card>`替换为`<GlassCard>`组件，添加`hoverable`属性用于脚本卡片。

- [ ] **Step 2: 更新按钮样式**

将页面中的操作按钮（新建、编辑、执行、删除）改为使用`GlassButton`组件或添加玻璃按钮样式类。

- [ ] **Step 3: 更新脚本列表卡片样式**

脚本列表中的每个脚本项改为使用玻璃卡片样式：
- 透明背景
- 白色边框
- 圆角12px
- hover时边框变亮

- [ ] **Step 4: 验证页面样式**

Run: `curl -s http://localhost:5174/scripts`
Expected: 页面显示玻璃风格卡片

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Scripts.vue
git commit -m "feat: update Scripts.vue with glass-style components"
```

---

## Task 7: 更新Executions.vue页面样式

**Files:**
- Modify: `frontend/src/views/Executions.vue`

- [ ] **Step 1: 替换主卡片为GlassCard**

- [ ] **Step 2: 更新表格样式覆盖**

添加Element Plus表格的玻璃风格覆盖样式，使表格背景透明、边框淡化、文字白色。

- [ ] **Step 3: 更新执行状态标签样式**

执行状态标签（成功/失败/运行中）改为使用玻璃风格的圆角标签。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Executions.vue
git commit -m "feat: update Executions.vue with glass-style"
```

---

## Task 8: 更新其他页面样式

**Files:**
- Modify: `frontend/src/views/Schedules.vue`
- Modify: `frontend/src/views/Webhooks.vue`
- Modify: `frontend/src/views/Workflows.vue`
- Modify: `frontend/src/views/Files.vue`

- [ ] **Step 1: 批量更新Schedules.vue**

替换el-card为GlassCard，更新按钮样式。

- [ ] **Step 2: 批量更新Webhooks.vue**

替换卡片和按钮样式，添加玻璃风格表格覆盖。

- [ ] **Step 3: 批量更新Workflows.vue**

工作流编辑器需要特殊处理，保持Vue Flow功能但调整容器样式为玻璃风格。

- [ ] **Step 4: 批量更新Files.vue**

文件浏览器改为玻璃卡片样式。

- [ ] **Step 5: 提交所有页面更新**

```bash
git add frontend/src/views/Schedules.vue frontend/src/views/Webhooks.vue frontend/src/views/Workflows.vue frontend/src/views/Files.vue
git commit -m "feat: update remaining pages with glass-style"
```

---

## Task 9: 更新剩余页面和全局组件

**Files:**
- Modify: `frontend/src/views/Environments.vue`
- Modify: `frontend/src/views/GlobalVariables.vue`
- Modify: `frontend/src/views/Backup.vue`
- Modify: `frontend/src/views/AISettings.vue`
- Modify: `frontend/src/views/AIScriptWriter.vue`
- Modify: `frontend/src/components/CodeEditor.vue`

- [ ] **Step 1: 更新配置类页面**

Environments、GlobalVariables、Backup页面替换卡片样式。

- [ ] **Step 2: 更新AI相关页面**

AISettings和AIScriptWriter使用GlassCard和GlassButton。

- [ ] **Step 3: 更新CodeEditor组件**

代码编辑器使用深色玻璃卡片样式（`glass-card-dark`），保持编辑器功能不变。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/ frontend/src/components/CodeEditor.vue
git commit -m "feat: update remaining views and CodeEditor with glass-style"
```

---

## Task 10: 最终验证和主题切换测试

**Files:**
- Test: 整体前端应用

- [ ] **Step 1: 启动前端开发服务器**

Run: `cd frontend && npm run dev`

- [ ] **Step 2: 验证渐变背景显示**

在浏览器检查页面背景是否为紫蓝渐变(#667eea → #764ba2)。

- [ ] **Step 3: 验证侧边栏样式**

检查侧边栏是否为55px宽、图标式、玻璃边框样式。

- [ ] **Step 4: 验证主题切换功能**

点击主题切换按钮，验证浅色模式是否正常切换：
- 背景变为淡紫蓝渐变
- 文字变为深色
- 卡片变为白色半透明

- [ ] **Step 5: 验证响应式布局**

调整浏览器宽度，验证：
- >1200px: 3列卡片网格
- 768-1200px: 2列卡片网格
- <768px: 侧边栏移至底部，1列卡片

- [ ] **Step 6: 提交最终验证**

```bash
git add -A
git commit -m "feat: complete glass-style UI redesign with theme switching"
git push origin main
```

---

## 完成清单

- [ ] Task 1: 创建glass-theme.scss核心样式文件
- [ ] Task 2: 创建GlassSidebar紧凑侧边栏组件
- [ ] Task 3: 创建GlassCard玻璃卡片组件
- [ ] Task 4: 创建GlassButton圆润按钮组件
- [ ] Task 5: 重构App.vue整体布局
- [ ] Task 6: 更新Scripts.vue页面样式
- [ ] Task 7: 更新Executions.vue页面样式
- [ ] Task 8: 更新其他页面样式（Schedules/Webhooks/Workflows/Files）
- [ ] Task 9: 更新剩余页面和全局组件
- [ ] Task 10: 最终验证和主题切换测试