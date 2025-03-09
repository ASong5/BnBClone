import socketio
import eventlet
import eventlet.wsgi
from flask import Flask
from game_state import GameState

sio = socketio.Server()
app = Flask(__name__)

# Dictionary to hold the game state for each room
rooms = {}


class Player:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.pressed_keys = []


@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # Remove player from room
    for room_id, game_state in rooms.items():
        if sid in game_state.players:
            del game_state.players[sid]
            sio.emit("player_left", {"player_id": sid}, room=room_id)
            break


@sio.event
def create_room(sid, data):
    print(f"Create room request from {sid} with data: {data}")
    room_id = data["room_id"]
    if room_id not in rooms:
        rooms[room_id] = GameState()
        sio.enter_room(sid, room_id)
        sio.emit("room_created", {"room_id": room_id}, room=sid)
        join_room(sid, data)  # Automatically join the room after creating it
    else:
        sio.emit("error", {"message": "Room already exists"}, room=sid)


@sio.event
def join_room(sid, data):
    print(f"Join room request from {sid} with data: {data}")
    room_id = data["room_id"]
    if room_id in rooms:
        sio.enter_room(sid, room_id)
        rooms[room_id].players[sid] = Player(sid, 0, 0)  # Initial position
        sio.emit("room_joined", {"room_id": room_id}, room=sid)
        sio.emit("player_joined", {"player_id": sid}, room=room_id)
        # Send the current state of all players in the room to the new player
        game_state = [
            {"player_id": pid, "pressed_keys": [], "x": p.x, "y": p.y}
            for pid, p in rooms[room_id].players.items()
        ]
        sio.emit("update_game_state", {"players": game_state}, room=room_id)
    else:
        sio.emit("error", {"message": "Room does not exist"}, room=sid)


@sio.event
def player_action(sid, data):
    print(f"Player action from {sid} with data: {data}")
    room_id = data["room_id"]
    pressed_keys = data.get("pressed_keys", [])
    print(sid, pressed_keys)
    x = data.get("x", 0)
    y = data.get("y", 0)
    rooms[room_id].players[sid].x = x
    rooms[room_id].players[sid].y = y
    if room_id in rooms and sid in rooms[room_id].players:
        # Broadcast the state of all players in the room
        game_state = [
            {"player_id": pid, "pressed_keys": pressed_keys, "x": x, "y": y}
            for pid, p in rooms[room_id].players.items()
        ]
        sio.emit("update_game_state", {"players": game_state}, room=room_id, skip_sid=sid)


if __name__ == "__main__":
    app = socketio.WSGIApp(sio, app)
    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
