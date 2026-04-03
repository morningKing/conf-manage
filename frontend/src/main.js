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

// 导入 Luckysheet CSS
import 'luckysheet/dist/plugins/css/pluginsCss.css'
import 'luckysheet/dist/plugins/plugins.css'
import 'luckysheet/dist/css/luckysheet.css'

// 导入 jQuery 并挂载到全局 window（Luckysheet 依赖）
import jquery from 'jquery'
window.jQuery = window.$ = jquery

// 导入 jQuery mousewheel 插件
import 'jquery-mousewheel'

// 导入 Luckysheet
import luckysheet from 'luckysheet'
window.luckysheet = luckysheet

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
