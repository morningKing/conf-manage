/**
 * Webhook管理API
 */
import request from './request'

/**
 * 获取Webhook列表
 */
export function getWebhooks(params) {
  return request({
    url: '/webhooks',
    method: 'get',
    params
  })
}

/**
 * 获取单个Webhook详情
 */
export function getWebhook(id) {
  return request({
    url: `/webhooks/${id}`,
    method: 'get'
  })
}

/**
 * 创建Webhook
 */
export function createWebhook(data) {
  return request({
    url: '/webhooks',
    method: 'post',
    data
  })
}

/**
 * 更新Webhook
 */
export function updateWebhook(id, data) {
  return request({
    url: `/webhooks/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除Webhook
 */
export function deleteWebhook(id) {
  return request({
    url: `/webhooks/${id}`,
    method: 'delete'
  })
}

/**
 * 重新生成Token
 */
export function regenerateWebhookToken(id) {
  return request({
    url: `/webhooks/${id}/regenerate-token`,
    method: 'post'
  })
}

/**
 * 启用/禁用Webhook
 */
export function toggleWebhook(id) {
  return request({
    url: `/webhooks/${id}/toggle`,
    method: 'post'
  })
}

/**
 * 获取Webhook调用日志
 */
export function getWebhookLogs(id, params) {
  return request({
    url: `/webhooks/${id}/logs`,
    method: 'get',
    params
  })
}

/**
 * 获取Webhook统计信息
 */
export function getWebhookStatistics(id) {
  return request({
    url: `/webhooks/${id}/statistics`,
    method: 'get'
  })
}

/**
 * 测试Webhook（发送HTTP请求到webhook endpoint）
 */
export function testWebhook(webhookKey, data, config = {}) {
  return request({
    url: `/webhook/${webhookKey}`,
    method: config.method || 'POST',
    data,
    headers: config.headers || {}
  })
}
