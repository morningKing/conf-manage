"""
Excel WebSocket handlers for real-time collaboration
"""
import logging
from flask_socketio import emit, join_room, leave_room
from . import socketio

logger = logging.getLogger(__name__)

# Store user sessions with their colors
# Structure: { sid: { 'room': str, 'user_id': str, 'color': str } }
user_sessions = {}

# Colors for cursor/selection highlighting
CURSOR_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
    '#BB8FCE', '#85C1E9', '#F8B500', '#00CED1'
]
color_index = 0


def get_next_color():
    """Get next available cursor color"""
    global color_index
    color = CURSOR_COLORS[color_index % len(CURSOR_COLORS)]
    color_index += 1
    return color


@socketio.on('connect', namespace='/excel')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to Excel namespace')
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect', namespace='/excel')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request
    sid = request.sid

    if sid in user_sessions:
        session = user_sessions[sid]
        room = session.get('room')
        user_id = session.get('user_id')

        if room:
            # Notify others in the room
            emit('user_left', {
                'user_id': user_id,
                'message': f'User {user_id} left'
            }, room=room, include_self=False)

            # Leave the room
            leave_room(room)

        # Clean up session
        del user_sessions[sid]
        logger.info(f'User {user_id} disconnected from room {room}')


@socketio.on('join', namespace='/excel')
def handle_join(data):
    """
    Handle user joining an Excel file room

    Expected data: {
        'file_id': str,
        'user_id': str,
        'user_name': str (optional)
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')
    user_name = data.get('user_name', user_id)

    if not file_id or not user_id:
        emit('error', {'message': 'file_id and user_id are required'})
        return

    room = f'excel_{file_id}'
    sid = request.sid

    # Assign a color to this user
    color = get_next_color()

    # Store session info
    user_sessions[sid] = {
        'room': room,
        'file_id': file_id,
        'user_id': user_id,
        'user_name': user_name,
        'color': color
    }

    # Join the room
    join_room(room)

    # Notify the user they've joined
    emit('joined', {
        'room': room,
        'file_id': file_id,
        'user_id': user_id,
        'color': color,
        'message': f'Successfully joined {room}'
    })

    # Notify others in the room
    emit('user_joined', {
        'user_id': user_id,
        'user_name': user_name,
        'color': color,
        'message': f'{user_name} joined the document'
    }, room=room, include_self=False)

    logger.info(f'User {user_id} joined room {room}')


@socketio.on('leave', namespace='/excel')
def handle_leave(data):
    """
    Handle user leaving an Excel file room

    Expected data: {
        'file_id': str,
        'user_id': str
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')

    room = f'excel_{file_id}'
    sid = request.sid

    # Notify others in the room
    emit('user_left', {
        'user_id': user_id,
        'message': f'User {user_id} left'
    }, room=room, include_self=False)

    # Leave the room
    leave_room(room)

    # Clean up session
    if sid in user_sessions:
        del user_sessions[sid]

    logger.info(f'User {user_id} left room {room}')


@socketio.on('edit', namespace='/excel')
def handle_edit(data):
    """
    Handle cell edit event

    Expected data: {
        'file_id': str,
        'user_id': str,
        'sheet': str,
        'cell': str,       # e.g., 'A1'
        'value': any,
        'previous_value': any (optional)
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')
    sheet = data.get('sheet')
    cell = data.get('cell')
    value = data.get('value')

    if not all([file_id, user_id, sheet, cell]):
        emit('error', {'message': 'file_id, user_id, sheet, and cell are required'})
        return

    room = f'excel_{file_id}'
    sid = request.sid

    # Get user color
    session = user_sessions.get(sid, {})
    color = session.get('color', '#000000')

    # Broadcast the edit to all other users in the room
    emit('cell_update', {
        'user_id': user_id,
        'sheet': sheet,
        'cell': cell,
        'value': value,
        'color': color,
        'timestamp': __import__('time').time()
    }, room=room, include_self=False)

    logger.debug(f'User {user_id} edited {sheet}!{cell} in {room}')


@socketio.on('cursor_move', namespace='/excel')
def handle_cursor_move(data):
    """
    Handle cursor movement for real-time collaboration

    Expected data: {
        'file_id': str,
        'user_id': str,
        'sheet': str,
        'cell': str,       # e.g., 'B2'
        'selection': {      # optional, for range selection
            'start': str,
            'end': str
        }
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')
    sheet = data.get('sheet')
    cell = data.get('cell')

    if not all([file_id, user_id, sheet, cell]):
        return  # Silently ignore incomplete cursor data

    room = f'excel_{file_id}'
    sid = request.sid

    # Get user info
    session = user_sessions.get(sid, {})
    color = session.get('color', '#000000')
    user_name = session.get('user_name', user_id)

    # Broadcast cursor position to others
    emit('cursor_update', {
        'user_id': user_id,
        'user_name': user_name,
        'sheet': sheet,
        'cell': cell,
        'color': color,
        'selection': data.get('selection')
    }, room=room, include_self=False)


@socketio.on('save_complete', namespace='/excel')
def handle_save_complete(data):
    """
    Handle save notification

    Expected data: {
        'file_id': str,
        'user_id': str,
        'version': int (optional)
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')

    if not file_id or not user_id:
        return

    room = f'excel_{file_id}'

    # Notify all users in the room about the save
    emit('file_saved', {
        'user_id': user_id,
        'file_id': file_id,
        'version': data.get('version'),
        'message': f'Document saved by user {user_id}',
        'timestamp': __import__('time').time()
    }, room=room)


@socketio.on('selection_change', namespace='/excel')
def handle_selection_change(data):
    """
    Handle selection range change

    Expected data: {
        'file_id': str,
        'user_id': str,
        'sheet': str,
        'selection': {
            'start': str,   # e.g., 'A1'
            'end': str      # e.g., 'C5'
        }
    }
    """
    from flask import request

    file_id = data.get('file_id')
    user_id = data.get('user_id')
    sheet = data.get('sheet')
    selection = data.get('selection')

    if not all([file_id, user_id, sheet, selection]):
        return

    room = f'excel_{file_id}'
    sid = request.sid

    # Get user info
    session = user_sessions.get(sid, {})
    color = session.get('color', '#000000')
    user_name = session.get('user_name', user_id)

    # Broadcast selection to others
    emit('selection_update', {
        'user_id': user_id,
        'user_name': user_name,
        'sheet': sheet,
        'selection': selection,
        'color': color
    }, room=room, include_self=False)


@socketio.on_error('/excel')
def error_handler(e):
    """Handle errors in the Excel namespace"""
    logger.error(f'WebSocket error in /excel namespace: {e}')
    emit('error', {'message': str(e)})