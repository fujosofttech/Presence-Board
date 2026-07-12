import { ref, onUnmounted } from 'vue'

export function usePresenceSSE(
  onPresenceUpdated: (data: any) => void,
  onConnected?: (isReconnect: boolean) => void
) {
  const isConnected = ref(false)
  const error = ref<any>(null)
  let eventSource: EventSource | null = null
  let reconnectTimeout: number | null = null
  let reconnectDelay = 1000 // 初期再接続遅延（1秒）
  const maxReconnectDelay = 30000 // 最大30秒
  let hasConnectedOnce = false

  const connect = () => {
    if (eventSource) {
      eventSource.close()
    }

    eventSource = new EventSource('/api/v1/events/stream/')
    
    eventSource.onopen = () => {
      isConnected.value = true
      error.value = null
      reconnectDelay = 1000 // 接続成功時に遅延をリセット
      if (onConnected) {
        onConnected(hasConnectedOnce)
      }
      hasConnectedOnce = true
    }

    eventSource.addEventListener('presence_updated', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        onPresenceUpdated(data)
      } catch (e) {
        console.error('Failed to parse SSE payload:', e)
      }
    })

    eventSource.onerror = (err) => {
      isConnected.value = false
      error.value = err
      console.warn(`SSE connection error. Attempting reconnect in ${reconnectDelay}ms...`, err)
      
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }

      // 指数バックオフによる再接続
      reconnectTimeout = window.setTimeout(() => {
        reconnectDelay = Math.min(reconnectDelay * 2, maxReconnectDelay)
        connect()
      }, reconnectDelay)
    }
  }

  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    error,
    connect,
    disconnect,
  }
}
