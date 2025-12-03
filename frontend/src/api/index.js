import request from './request'

// 脚本管理
export const getScripts = (params) => request.get('/scripts', { params })
export const getScript = (id) => request.get(`/scripts/${id}`)
export const createScript = (data) => request.post('/scripts', data)
export const updateScript = (id, data) => request.put(`/scripts/${id}`, data)
export const deleteScript = (id) => request.delete(`/scripts/${id}`)
export const getScriptVersions = (id) => request.get(`/scripts/${id}/versions`)
export const rollbackScript = (id, version) => request.post(`/scripts/${id}/rollback/${version}`)
export const executeScript = (id, params) => request.post(`/scripts/${id}/execute`, { params })
export const executeScriptWithFiles = (id, formData) => request.post(`/scripts/${id}/execute`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const toggleScriptFavorite = (id) => request.post(`/scripts/${id}/favorite`)

// 执行历史
export const getExecutions = (params) => request.get('/executions', { params })
export const getExecution = (id) => request.get(`/executions/${id}`)
export const getExecutionLogs = (id) => request.get(`/executions/${id}/logs`)
export const deleteExecution = (id) => request.delete(`/executions/${id}`)
export const cancelExecution = (id) => request.post(`/executions/${id}/cancel`)

// 定时任务
export const getSchedules = () => request.get('/schedules')
export const getSchedule = (id) => request.get(`/schedules/${id}`)
export const createSchedule = (data) => request.post('/schedules', data)
export const updateSchedule = (id, data) => request.put(`/schedules/${id}`, data)
export const deleteSchedule = (id) => request.delete(`/schedules/${id}`)
export const toggleSchedule = (id) => request.post(`/schedules/${id}/toggle`)
export const runScheduleNow = (id) => request.post(`/schedules/${id}/run`)

// 文件管理
export const getFiles = (path) => request.get('/files', { params: { path } })
export const uploadFile = (formData) => request.post('/files/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const downloadFile = (path) => `/api/files/download?path=${encodeURIComponent(path)}`
export const deleteFile = (path) => request.delete('/files/delete', { params: { path } })
export const createFolder = (data) => request.post('/files/create-folder', data)
export const updateFile = (data) => request.put('/files/update', data)

// 执行环境管理
export const getEnvironments = () => request.get('/environments')
export const getEnvironment = (id) => request.get(`/environments/${id}`)
export const createEnvironment = (data) => request.post('/environments', data)
export const updateEnvironment = (id, data) => request.put(`/environments/${id}`, data)
export const deleteEnvironment = (id) => request.delete(`/environments/${id}`)
export const setDefaultEnvironment = (id) => request.post(`/environments/${id}/set-default`)
export const detectEnvironment = (data) => request.post('/environments/detect', data)

// 分类管理
export const getCategories = () => request.get('/categories')
export const createCategory = (data) => request.post('/categories', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}`)

// 标签管理
export const getTags = () => request.get('/tags')
export const createTag = (data) => request.post('/tags', data)
export const updateTag = (id, data) => request.put(`/tags/${id}`, data)
export const deleteTag = (id) => request.delete(`/tags/${id}`)

