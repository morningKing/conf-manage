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
        <template v-for="item in menuItems" :key="item.path || item.title">
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
        color: var(--sidebar-active-text);
      }
    }
  }
}
</style>