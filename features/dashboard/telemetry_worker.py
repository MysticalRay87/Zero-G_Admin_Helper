import json, os, socket, threading, time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

import socket
import threading
import time

class TelemetryWorker:
    def __init__(self, ip, port, password):
        self.ip = ip
        self.port = port
        self.password = password
        self.command_queue = []
        self.running = False
        self.socket = None
        config_path = "data/server_config.json"

    def check_config_file():
        if os.path.exists(config_path):
            print("[DEBUG] Config found.")
            try:
                with open(config_path, 'r') as file:
                    config_data = json.load(file)
                    target_ip = config_data.get("server_ip", "")
                    target_port = int(config_data.get("telnet_port", 0))
                    telnet_password = config_data.get("auth_token", "")
                    print(f"PARSING CREDENTIALS: IP={target_ip}, Port={target_port}")
            except (json.JSONDecodeError, ValueError):
                print("[CRITICAL ERROR] server_config.json contains unparseable format.")
        else:
            print("[DEBUG] Config not found, defaulting to localhost.")

    check_config_file()

    def connect(self):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout=5)
            print("[DEBUG] Connected to the server.")
            self.authenticate()
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")

    def authenticate(self):
        # Transmit authentication credentials
        self.socket.sendall(f"{self.password}\r\n".encode('utf-8'))
        response = self.socket.recv(1024).decode('utf-8')
        if "Login successful" in response:
            print("[DEBUG] Authentication successful.")
            self.running = True
        else:
            print("[ERROR] Authentication failed.")

    def listener(self):
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    print(f"[RECEIVED] {data.strip()}")
                else:
                    print("[DEBUG] Connection closed by server.")
                    self.running = False
            except Exception as e:
                print(f"[ERROR] Listener error: {e}")
                self.running = False

    def command_sender(self):
        while self.running:
            if self.command_queue:
                command = self.command_queue.pop(0)
                self.socket.sendall(f"{command}\r\n".encode('utf-8'))
                time.sleep(0.5)  # Mandatory input buffer delay
            else:
                time.sleep(1)
            self.keep_alive()

    def keep_alive(self):
        try:
            self.socket.sendall(b"\r\n")
            print("[DEBUG] Sent keep-alive pulse.")
        except Exception as e:
            print(f"[ERROR] Keep-alive error: {e}")
            self.running = False

    def send_command(self, command):
        self.command_queue.append(command)
        print(f"[QUEUED] Command added to queue: {command}")

    def run(self):
        self.connect()
        if self.running:
            listener_thread = threading.Thread(target=self.listener)
            sender_thread = threading.Thread(target=self.command_sender)
            listener_thread.start()
            sender_thread.start()

    def close(self):
        self.running = False
        if self.socket:
            self.socket.close()
            print("[DEBUG] Socket closed.")