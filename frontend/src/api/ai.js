/**
 * AI 相关 API（配置管理 + 脚本生成/改进/解释 + 预览执行）
 */
import request from './request'

// ===== AI 配置 =====
export const getAIConfigs = () => request.get('/ai-configs')
export const createAIConfig = (data) => request.post('/ai-configs', data)
export const updateAIConfig = (id, data) => request.put(`/ai-configs/${id}`, data)
export const deleteAIConfig = (id) => request.delete(`/ai-configs/${id}`)
export const activateAIConfig = (id) => request.post(`/ai-configs/${id}/activate`)

// ===== AI 脚本能力 =====
export const generateScript = (prompt) => request.post('/ai/generate-script', { prompt })

export const improveScript = (script, improvementRequest) =>
  request.post('/ai/improve-script', { script, request: improvementRequest })

export const explainScript = (script) => request.post('/ai/explain-script', { script })

/**
 * 预览执行：支持 JSON（无文件）与 FormData（含文件）两种载荷
 * @param {object|FormData} payload { code, params } 或构造好的 FormData
 */
export const previewExecute = (payload) => request.post('/ai/preview-execute', payload)
