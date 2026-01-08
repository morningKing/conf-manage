/**
 * 备份管理 API
 */
import request from './request'

/**
 * 导出数据库
 */
export function exportDatabase() {
  return request({
    url: '/backup/database-export',
    method: 'post'
  })
}

/**
 * 创建系统备份
 * @param {Object} data 备份配置
 * @param {string} data.backup_name 备份名称（可选）
 * @param {boolean} data.include_logs 是否包含日志
 * @param {boolean} data.include_execution_spaces 是否包含执行空间
 */
export function createSystemBackup(data) {
  return request({
    url: '/backup/system-backup',
    method: 'post',
    data
  })
}

/**
 * 获取备份列表
 */
export function getBackupList() {
  return request({
    url: '/backup/list',
    method: 'get'
  })
}

/**
 * 下载备份文件
 * @param {string} filename 文件名
 */
export function downloadBackup(filename) {
  return `${import.meta.env.VITE_API_BASE_URL}/backup/download/${filename}`
}

/**
 * 删除备份文件
 * @param {string} filename 文件名
 */
export function deleteBackup(filename) {
  return request({
    url: `/backup/${filename}`,
    method: 'delete'
  })
}

/**
 * 清理旧备份
 * @param {number} keep_days 保留天数
 */
export function cleanOldBackups(keep_days) {
  return request({
    url: '/backup/clean',
    method: 'post',
    data: { keep_days }
  })
}

/**
 * 获取数据库信息
 */
export function getDatabaseInfo() {
  return request({
    url: '/backup/database-info',
    method: 'get'
  })
}
