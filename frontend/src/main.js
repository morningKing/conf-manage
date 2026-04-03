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

// 导入 jQuery 并挂载到 window（Luckysheet 依赖）
import $ from 'jquery'
window.$ = window.jQuery = $

// 导入 jQuery mousewheel 插件（Luckysheet 依赖）
import 'jquery-mousewheel'

// 导入 Luckysheet CSS
import 'luckysheet/dist/plugins/css/pluginsCss.css'
import 'luckysheet/dist/plugins/plugins.css'
import 'luckysheet/dist/css/luckysheet.css'

// 动态导入 Luckysheet 并挂载到 window
import('luckysheet').then((module) => {
  // Vite会将UMD转换为ES模块，需要手动挂载到window
  if (module && module.default) {
    window.luckysheet = module.default
  } else if (module) {
    window.luckysheet = module
  }
  console.log('Luckysheet loaded:', window.luckysheet ? 'success' : 'failed')
}).catch(err => {
  console.error('Failed to load Luckysheet:', err)
})

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
