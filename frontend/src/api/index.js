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
export const cleanScriptVersions = (id, data) => request.delete(`/scripts/${id}/versions/clean`, { data })
export const cleanScriptExecutions = (id, data) => request.delete(`/scripts/${id}/executions/clean`, { data })
export const moveScript = (id, data) => request.post(`/scripts/${id}/move`, data)

// 执行历史
export const getExecutions = (params) => request.get('/executions', { params })
export const getExecution = (id) => request.get(`/executions/${id}`)
export const getExecutionLogs = (id) => request.get(`/executions/${id}/logs`)
export const deleteExecution = (id) => request.delete(`/executions/${id}`)
export const cancelExecution = (id) => request.post(`/executions/${id}/cancel`)
export const getExecutionFiles = (id) => request.get(`/executions/${id}/files`)
export const getExecutionFile = (id, filePath, download = false) => `/api/executions/${id}/files/${filePath}?download=${download}`
export const previewExecutionFile = (id, filePath) => request.get(`/executions/${id}/files/${filePath}`)

// 批量管理
export const batchManageExecutions = (data) => request.post('/executions/batch', data)
export const getExecutionsStatistics = () => request.get('/executions/statistics')

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

// 文件夹管理（脚本文件夹）
export const getFolderTree = () => request.get('/folders/tree')
export const getFolderContents = (id) => request.get(`/folders/${id}/contents`)
export const getRootContents = () => request.get('/folders/root/contents')
export const createScriptFolder = (data) => request.post('/folders', data)
export const updateFolder = (id, data) => request.put(`/folders/${id}`, data)
export const deleteScriptFolder = (id) => request.delete(`/folders/${id}`)
export const moveFolder = (id, data) => request.post(`/folders/${id}/move`, data)
export const getFolderPath = (id) => request.get(`/folders/${id}/path`)

// 标签管理
export const getTags = () => request.get('/tags')
export const createTag = (data) => request.post('/tags', data)
export const updateTag = (id, data) => request.put(`/tags/${id}`, data)
export const deleteTag = (id) => request.delete(`/tags/${id}`)

// 工作流管理
export const getWorkflows = () => request.get('/workflows')
export const getWorkflow = (id) => request.get(`/workflows/${id}`)
export const createWorkflow = (data) => request.post('/workflows', data)
export const updateWorkflow = (id, data) => request.put(`/workflows/${id}`, data)
export const deleteWorkflow = (id) => request.delete(`/workflows/${id}`)
export const executeWorkflow = (id, params) => request.post(`/workflows/${id}/execute`, { params })
export const toggleWorkflow = (id) => request.post(`/workflows/${id}/toggle`)
export const cancelWorkflowExecution = (id) => request.post(`/workflow-executions/${id}/cancel`)
export const deleteWorkflowExecution = (id) => request.delete(`/workflow-executions/${id}`)

// 选择会话管理（批量操作支持1000条）
export const createSelectionSession = () => request.post('/executions/selection/create')
export const getSelectionSession = (sessionId) => request.get(`/executions/selection/${sessionId}`)
export const addToSelection = (sessionId, executionIds) => request.post(`/executions/selection/${sessionId}/add`, { execution_ids: executionIds })
export const removeFromSelection = (sessionId, executionIds) => request.post(`/executions/selection/${sessionId}/remove`, { execution_ids: executionIds })
export const clearSelection = (sessionId) => request.post(`/executions/selection/${sessionId}/clear`)
export const deleteSelectionBatch = (sessionId) => request.post(`/executions/selection/${sessionId}/delete`)

// 重新执行
export const reExecuteScript = (executionId) => request.post(`/executions/${executionId}/re-execute`)

// Excel 文件操作
export const getExcelFile = (executionId, filePath) =>
  request.get(`/executions/${executionId}/files/${encodeURIComponent(filePath)}?excel=true`)

export const saveExcelFile = (executionId, filePath, data) =>
  request.post(`/executions/${executionId}/files/${encodeURIComponent(filePath)}?excel=true`, data)

// 系统清理管理
export const getCleanupStats = () => request.get('/system/cleanup/stats')
export const executeCleanup = () => request.post('/system/cleanup')
export const getCleanupConfig = () => request.get('/system/cleanup/config')
export const updateCleanupConfig = (data) => request.put('/system/cleanup/config', data)

// 定时任务白名单
export const toggleSchedulePreserve = (id) => request.post(`/schedules/${id}/preserve`)
export const batchToggleSchedulePreserve = (data) => request.post('/schedules/batch/preserve', data)

