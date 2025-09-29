from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

rooms_users = {}  # { room_code: { sid: username } }

def current_time_str():
    return datetime.now().strftime('%H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    join_room(room)

    if room not in rooms_users:
        rooms_users[room] = {}
    rooms_users[room][request.sid] = username

    emit('joined', {'room': room, 'num_users': len(rooms_users[room]), 'users': list(rooms_users[room].values())})

    timestamp = current_time_str()
    emit('message', {
        'msg': f"{username} has joined the room.",
        'username': "System",
        'timestamp': timestamp
    }, room=room)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data['sdp'], room=data['room'], include_self=False)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data['sdp'], room=data['room'], include_self=False)

@socketio.on('candidate')
def handle_candidate(data):
    emit('candidate', data['candidate'], room=data['room'], include_self=False)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    msg = data['msg']
    timestamp = data.get('timestamp', current_time_str())
    emit('message', {'msg': msg, 'username': username, 'timestamp': timestamp}, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    sid = request.sid

    leave_room(room)
    if room in rooms_users and sid in rooms_users[room]:
        rooms_users[room].pop(sid)
        if len(rooms_users[room]) == 0:
            rooms_users.pop(room)

    timestamp = current_time_str()
    emit('message', {
        'msg': f"{username} has left the room.",
        'username': "System",
        'timestamp': timestamp
    }, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    found_room = None
    username = None
    for room, users in rooms_users.items():
        if sid in users:
            username = users.pop(sid)
            found_room = room
            if len(users) == 0:
                rooms_users.pop(room)
            break

    if found_room and username:
        timestamp = current_time_str()
        emit('message', {
            'msg': f"{username} has left the room.",
            'username': "System",
            'timestamp': timestamp
        }, room=found_room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
