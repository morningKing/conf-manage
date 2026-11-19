import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 全局主题（专业后台风：紧凑密度 + 真实深色主题）
import './styles/theme.scss'

// jQuery 和 Luckysheet 已通过 index.html 中的 script 标签加载
// window.$, window.jQuery, window.luckysheet 已可用

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
