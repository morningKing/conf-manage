<template>
  <div id="app">
    <el-container style="height: 100vh">
      <el-aside width="200px" style="background-color: #304156">
        <div class="logo">
          <h2 style="color: #fff; text-align: center; padding: 20px 0">脚本管理</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/scripts">
            <el-icon><Document /></el-icon>
            <span>脚本管理</span>
          </el-menu-item>
          <el-menu-item index="/executions">
            <el-icon><VideoPlay /></el-icon>
            <span>执行历史</span>
          </el-menu-item>
          <el-menu-item index="/schedules">
            <el-icon><Clock /></el-icon>
            <span>定时任务</span>
          </el-menu-item>
          <el-menu-item index="/categories">
            <el-icon><Menu /></el-icon>
            <span>分类管理</span>
          </el-menu-item>
          <el-menu-item index="/tags">
            <el-icon><CollectionTag /></el-icon>
            <span>标签管理</span>
          </el-menu-item>
          <el-menu-item index="/environments">
            <el-icon><Setting /></el-icon>
            <span>执行环境</span>
          </el-menu-item>
          <el-menu-item index="/files">
            <el-icon><Folder /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header style="background-color: #fff; box-shadow: 0 1px 4px rgba(0,21,41,.08)">
          <div style="line-height: 60px; font-size: 20px; font-weight: bold">
            脚本工具管理系统
          </div>
        </el-header>

        <el-main style="background-color: #f0f2f5">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
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
}

.el-main {
  padding: 20px;
}
</style>
