<template>
  <div class="table-skeleton">
    <el-skeleton :rows="rows" animated>
      <template #template>
        <div class="skeleton-header">
          <el-skeleton-item variant="text" style="width: 30%" />
          <el-skeleton-item variant="text" style="width: 20%" />
        </div>
        <div v-for="i in rows" :key="i" class="skeleton-row">
          <el-skeleton-item variant="text" style="width: 40%" />
          <el-skeleton-item variant="text" style="width: 30%" />
          <el-skeleton-item variant="text" style="width: 20%" />
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
defineProps({
  rows: {
    type: Number,
    default: 5
  }
})
</script>

<style scoped>
.table-skeleton {
  padding: 20px;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.skeleton-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  padding: 10px 0;
}
</style>
