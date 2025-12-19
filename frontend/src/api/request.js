import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.PROD ? 'http://localhost:5000/api' : '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 直接返回响应数据
    return response.data
  },
  error => {
    const message = error.response?.data?.error || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
