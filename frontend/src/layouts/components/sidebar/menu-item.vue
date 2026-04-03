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
          <component :is="getIcon(item.icon)" />
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
        <component :is="getIcon(item.icon)" />
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
import { ArrowDown, House, Document, VideoPlay, Clock, Share, Folder, Grid, PriceTag, Monitor, Coin, Link, Files, MagicStick, SetUp } from '@element-plus/icons-vue'

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

// 图标映射
const iconMap = {
  House,
  Document,
  VideoPlay,
  Clock,
  Share,
  Folder,
  Grid,
  PriceTag,
  Monitor,
  Coin,
  Link,
  Files,
  MagicStick,
  SetUp
}

const getIcon = (iconName) => {
  return iconMap[iconName] || Document
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