import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 导入全局样式
import './styles/theme/light.scss'
import './styles/theme/dark.scss'
import './styles/transitions.scss'

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
