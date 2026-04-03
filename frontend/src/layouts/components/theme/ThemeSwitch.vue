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