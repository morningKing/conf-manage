/**
 * SSE 连接生命周期封装
 *
 * 统一"关闭旧连接 → 建立新连接 → 消息分发 → 卸载清理"的模式，
 * 替代各视图内散落的裸 EventSource 管理。
 */
import { ref } from 'vue'

export function useEventSource() {
  const source = ref(null)
  const connected = ref(false)

  const disconnect = () => {
    if (source.value) {
      source.value.close()
      source.value = null
    }
    connected.value = false
  }

  /**
   * 建立连接（自动关闭旧连接）
   * @param {string} url SSE 端点
   * @param {object} handlers { onMessage, onError, onOpen }
   */
  const connect = (url, { onMessage, onError, onOpen } = {}) => {
    disconnect()
    const es = new EventSource(url)
    source.value = es
    es.onmessage = (event) => onMessage && onMessage(event)
    es.onerror = (event) => onError && onError(event)
    es.onopen = () => {
      connected.value = true
      if (onOpen) onOpen()
    }
    return es
  }

  return { connect, disconnect, source, connected }
}
