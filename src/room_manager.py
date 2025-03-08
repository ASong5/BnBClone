import pygame
import socketio

class RoomManager:
    def __init__(self, sio):
        self.sio = sio
        self.room_confirmed = False
        self.current_room = None
        self.sio.on('room_created', self.on_room_created)
        self.sio.on('room_joined', self.on_room_joined)

    def on_room_created(self, data):
        print('on_room_created called with data:', data)
        if 'room_id' in data:
            print('Room created:', data['room_id'])
            self.current_room = data['room_id']
            self.room_confirmed = True
        else:
            print('Room creation failed. Server did not send room_id.')

    def on_room_joined(self, data):
        print('on_room_joined called with data:', data)
        if 'room_id' in data:
            print('Joined room:', data['room_id'])
            self.current_room = data['room_id']
            self.room_confirmed = True
        else:
            print('Joining room failed. Server did not send room_id.')

    def prompt_for_room(self):
        choice = input("Enter 'c' to create a room or 'j' to join a room: ").strip().lower()
        if choice == 'c':
            room_id = input("Enter room ID to create: ").strip()
            self.create_room(room_id)
        elif choice == 'j':
            room_id = input("Enter room ID to join: ").strip()
            self.join_room(room_id)
        else:
            print("Invalid choice. Please enter 'c' to create or 'j' to join.")

    def create_room(self, room_id):
        print('Creating room with ID:', room_id)
        self.sio.emit('create_room', {'room_id': room_id})

    def join_room(self, room_id):
        print('Joining room with ID:', room_id)
        self.sio.emit('join_room', {'room_id': room_id})

    def leave_room(self, room_id):
        print('Leaving room with ID:', room_id)
        self.sio.emit('leave_room', {'room_id': room_id})
        self.current_room = None
        self.room_confirmed = False
