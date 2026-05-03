/**
 * Excel WebSocket client for real-time collaboration
 */
import { io } from 'socket.io-client'

class ExcelSocket {
  constructor() {
    this.socket = null
    this.roomId = null
    this.userId = null
    this.callbacks = {}
    this.connected = false
  }

  /**
   * Connect to WebSocket server
   * @param {string} fileId - File ID or path
   * @param {string} userName - User display name
   */
  connect(fileId, userName) {
    if (this.socket) {
      this.disconnect()
    }

    // Connect to /excel namespace
    this.socket = io('/excel', {
      transports: ['websocket', 'polling'],
      path: '/socket.io'
    })

    this.socket.on('connect', () => {
      console.log('[ExcelSocket] Connected')
      this.connected = true
      this.userId = this.socket.id
      this.joinRoom(fileId, userName)
    })

    this.socket.on('connected', (data) => {
      console.log('[ExcelSocket] Server acknowledged connection:', data)
    })

    this.socket.on('joined', (data) => {
      console.log('[ExcelSocket] Joined room:', data.room)
      this.roomId = data.room
      this.trigger('joined', data)
    })

    this.socket.on('user_joined', (data) => {
      console.log('[ExcelSocket] User joined:', data.user_name)
      this.trigger('user_joined', data)
    })

    this.socket.on('user_left', (data) => {
      console.log('[ExcelSocket] User left:', data.user_id)
      this.trigger('user_left', data)
    })

    this.socket.on('cell_update', (data) => {
      this.trigger('cell_update', data)
    })

    this.socket.on('cursor_update', (data) => {
      this.trigger('cursor_update', data)
    })

    this.socket.on('file_saved', (data) => {
      console.log('[ExcelSocket] File saved:', data)
      this.trigger('file_saved', data)
    })

    this.socket.on('selection_update', (data) => {
      this.trigger('selection_update', data)
    })

    this.socket.on('error', (data) => {
      console.error('[ExcelSocket] Error:', data.message)
      this.trigger('error', data)
    })

    this.socket.on('disconnect', () => {
      console.log('[ExcelSocket] Disconnected')
      this.connected = false
      this.trigger('disconnect')
    })

    this.socket.on('connect_error', (error) => {
      console.error('[ExcelSocket] Connection error:', error)
      this.trigger('error', { message: error.message || 'Connection failed' })
    })
  }

  /**
   * Join an Excel file room
   * @param {string} fileId - File ID
   * @param {string} userName - User name
   */
  joinRoom(fileId, userName) {
    if (!this.socket || !this.connected) {
      console.warn('[ExcelSocket] Not connected, cannot join room')
      return
    }

    this.socket.emit('join', {
      file_id: fileId,
      user_id: this.userId,
      user_name: userName
    })
  }

  /**
   * Leave the current room
   * @param {string} fileId - File ID
   */
  leaveRoom(fileId) {
    if (!this.socket) return

    this.socket.emit('leave', {
      file_id: fileId,
      user_id: this.userId
    })
  }

  /**
   * Send cell edit operation
   * @param {string} fileId - File ID
   * @param {string} sheet - Sheet name
   * @param {string} cell - Cell reference (e.g., 'A1')
   * @param {any} value - New cell value
   */
  sendEdit(fileId, sheet, cell, value) {
    if (!this.socket || !this.connected) return

    this.socket.emit('edit', {
      file_id: fileId,
      user_id: this.userId,
      sheet: sheet,
      cell: cell,
      value: value
    })
  }

  /**
   * Send cursor position
   * @param {string} fileId - File ID
   * @param {string} sheet - Sheet name
   * @param {string} cell - Current cell (e.g., 'B2')
   * @param {object} selection - Optional selection range {start, end}
   */
  sendCursor(fileId, sheet, cell, selection = null) {
    if (!this.socket || !this.connected) return

    this.socket.emit('cursor_move', {
      file_id: fileId,
      user_id: this.userId,
      sheet: sheet,
      cell: cell,
      selection: selection
    })
  }

  /**
   * Send selection range change
   * @param {string} fileId - File ID
   * @param {string} sheet - Sheet name
   * @param {object} selection - Selection range {start, end}
   */
  sendSelection(fileId, sheet, selection) {
    if (!this.socket || !this.connected) return

    this.socket.emit('selection_change', {
      file_id: fileId,
      user_id: this.userId,
      sheet: sheet,
      selection: selection
    })
  }

  /**
   * Notify other users that file was saved
   * @param {string} fileId - File ID
   */
  notifySaved(fileId) {
    if (!this.socket || !this.connected) return

    this.socket.emit('save_complete', {
      file_id: fileId,
      user_id: this.userId
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
      this.roomId = null
      this.userId = null
    }
  }

  /**
   * Register event callback
   * @param {string} event - Event name
   * @param {function} callback - Callback function
   */
  on(event, callback) {
    this.callbacks[event] = callback
  }

  /**
   * Remove event callback
   * @param {string} event - Event name
   */
  off(event) {
    delete this.callbacks[event]
  }

  /**
   * Trigger event callback
   * @param {string} event - Event name
   * @param {any} data - Event data
   */
  trigger(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event](data)
    }
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  isConnected() {
    return this.connected && this.socket !== null
  }
}

// Export singleton instance
export default new ExcelSocket()