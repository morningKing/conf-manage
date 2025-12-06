<template>
  <div class="loading-container" :class="{ fullscreen }">
    <div class="loading-content">
      <div class="spinner-wrapper">
        <div class="spinner">
          <div v-for="i in 12" :key="i" class="spinner-blade"></div>
        </div>
      </div>
      <p v-if="text" class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '加载中...'
  },
  fullscreen: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.loading-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.dark-mode .loading-container.fullscreen {
  background: rgba(0, 0, 0, 0.9);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.spinner-wrapper {
  position: relative;
}

.spinner {
  position: relative;
  width: 40px;
  height: 40px;
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

.spinner-blade {
  position: absolute;
  left: 50%;
  top: 0;
  width: 3px;
  height: 40%;
  background: #409EFF;
  border-radius: 3px;
  transform-origin: center 100%;
  opacity: 0;
  animation: fade 1.5s linear infinite;
}

.spinner-blade:nth-child(1) {
  transform: rotate(0deg);
  animation-delay: 0s;
}

.spinner-blade:nth-child(2) {
  transform: rotate(30deg);
  animation-delay: 0.125s;
}

.spinner-blade:nth-child(3) {
  transform: rotate(60deg);
  animation-delay: 0.25s;
}

.spinner-blade:nth-child(4) {
  transform: rotate(90deg);
  animation-delay: 0.375s;
}

.spinner-blade:nth-child(5) {
  transform: rotate(120deg);
  animation-delay: 0.5s;
}

.spinner-blade:nth-child(6) {
  transform: rotate(150deg);
  animation-delay: 0.625s;
}

.spinner-blade:nth-child(7) {
  transform: rotate(180deg);
  animation-delay: 0.75s;
}

.spinner-blade:nth-child(8) {
  transform: rotate(210deg);
  animation-delay: 0.875s;
}

.spinner-blade:nth-child(9) {
  transform: rotate(240deg);
  animation-delay: 1s;
}

.spinner-blade:nth-child(10) {
  transform: rotate(270deg);
  animation-delay: 1.125s;
}

.spinner-blade:nth-child(11) {
  transform: rotate(300deg);
  animation-delay: 1.25s;
}

.spinner-blade:nth-child(12) {
  transform: rotate(330deg);
  animation-delay: 1.375s;
}

@keyframes fade {
  0% {
    opacity: 0.85;
  }
  50% {
    opacity: 0.25;
  }
  100% {
    opacity: 0.25;
  }
}

.loading-text {
  color: #409EFF;
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}
</style>
