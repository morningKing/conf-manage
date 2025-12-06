import request from './request'

// ========== 工作流管理 ==========

/**
 * 获取工作流列表
 */
export const getWorkflows = () => request.get('/workflows')

/**
 * 获取工作流详情
 */
export const getWorkflow = (id) => request.get(`/workflows/${id}`)

/**
 * 创建工作流
 */
export const createWorkflow = (data) => request.post('/workflows', data)

/**
 * 更新工作流
 */
export const updateWorkflow = (id, data) => request.put(`/workflows/${id}`, data)

/**
 * 删除工作流
 */
export const deleteWorkflow = (id) => request.delete(`/workflows/${id}`)

/**
 * 执行工作流
 */
export const executeWorkflow = (id, params) => request.post(`/workflows/${id}/execute`, { params })

/**
 * 启用/禁用工作流
 */
export const toggleWorkflow = (id) => request.post(`/workflows/${id}/toggle`)

// ========== 工作流执行历史 ==========

/**
 * 获取工作流执行历史
 */
export const getWorkflowExecutions = (params) => request.get('/workflow-executions', { params })

/**
 * 获取工作流执行详情
 */
export const getWorkflowExecution = (id) => request.get(`/workflow-executions/${id}`)

/**
 * 取消工作流执行
 */
export const cancelWorkflowExecution = (id) => request.post(`/workflow-executions/${id}/cancel`)

// ========== 工作流模板 ==========

/**
 * 获取工作流模板列表
 */
export const getWorkflowTemplates = (params) => request.get('/workflow-templates', { params })

/**
 * 获取工作流模板详情
 */
export const getWorkflowTemplate = (id) => request.get(`/workflow-templates/${id}`)

/**
 * 创建工作流模板
 */
export const createWorkflowTemplate = (data) => request.post('/workflow-templates', data)

/**
 * 更新工作流模板
 */
export const updateWorkflowTemplate = (id, data) => request.put(`/workflow-templates/${id}`, data)

/**
 * 删除工作流模板
 */
export const deleteWorkflowTemplate = (id) => request.delete(`/workflow-templates/${id}`)

/**
 * 使用模板创建工作流
 */
export const useWorkflowTemplate = (id, data) => request.post(`/workflow-templates/${id}/use`, data)

/**
 * 获取模板分类列表
 */
export const getTemplateCategories = () => request.get('/workflow-templates/categories')
