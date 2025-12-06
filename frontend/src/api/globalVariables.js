/**
 * 全局变量管理API
 */
import request from './request'

/**
 * 获取全局变量列表
 */
export function getGlobalVariables(showEncrypted = false) {
  return request({
    url: '/global-variables',
    method: 'get',
    params: { show_encrypted: showEncrypted }
  })
}

/**
 * 获取单个全局变量详情
 */
export function getGlobalVariable(id, showEncrypted = false) {
  return request({
    url: `/global-variables/${id}`,
    method: 'get',
    params: { show_encrypted: showEncrypted }
  })
}

/**
 * 创建全局变量
 */
export function createGlobalVariable(data) {
  return request({
    url: '/global-variables',
    method: 'post',
    data
  })
}

/**
 * 更新全局变量
 */
export function updateGlobalVariable(id, data) {
  return request({
    url: `/global-variables/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除全局变量
 */
export function deleteGlobalVariable(id) {
  return request({
    url: `/global-variables/${id}`,
    method: 'delete'
  })
}

/**
 * 获取全局变量字典
 */
export function getGlobalVariablesDict() {
  return request({
    url: '/global-variables/dict',
    method: 'get'
  })
}
