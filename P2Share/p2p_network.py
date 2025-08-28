#!/usr/bin/env python3
"""
P2P Bluetooth Network Module
Handles Bluetooth socket communication between peers using pybluez.
"""

import bluetooth
import threading
import json
import os
import hashlib
import time
from file_manager import FileManager

class P2PBluetoothNetwork:
    def __init__(self):
        self.server_socket = None
        self.is_running = False
        self.service_uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.service_name = "P2P File Share"
        self.connections = []
        self.file_manager = FileManager()
        
        # Callbacks
        self.on_peer_connected = None
        self.on_peer_disconnected = None
        self.on_file_received = None
        self.on_message_received = None
    
    def start_server(self):
        """Start the Bluetooth P2P server"""
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)
            
            port = self.server_socket.getsockname()[1]
            
            # Advertise service
            bluetooth.advertise_service(
                self.server_socket,
                self.service_name,
                service_id=self.service_uuid,
                service_classes=[self.service_uuid, bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )
            
            self.is_running = True
            
            # Start server thread
            threading.Thread(target=self._server_loop, daemon=True).start()
            
            self._log(f"Bluetooth server started on port {port}")
            return port
            
        except Exception as e:
            self._log(f"Failed to start Bluetooth server: {e}")
            return None
    
    def stop_server(self):
        """Stop the Bluetooth P2P server"""
        self.is_running = False
        
        # Close all connections
        for conn in self.connections.copy():
            try:
                conn.close()
            except:
                pass
        self.connections.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                bluetooth.stop_advertising(self.server_socket)
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
    
    def _server_loop(self):
        """Main server loop to accept Bluetooth connections"""
        while self.is_running:
            try:
                client_socket, client_info = self.server_socket.accept()
                self.connections.append(client_socket)
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_info),
                    daemon=True
                )
                client_thread.start()
                
                if self.on_peer_connected:
                    self.on_peer_connected(client_info[0], str(client_info[1]))
                    
            except bluetooth.BluetoothError:
                if self.is_running:
                    self._log("Bluetooth server error")
                break
            except Exception as e:
                if self.is_running:
                    self._log(f"Server loop error: {e}")
                break
    
    def _handle_client(self, client_socket, client_info):
        """Handle individual Bluetooth client connection"""
        try:
            while self.is_running:
                # Receive message length first
                length_data = self._receive_exact(client_socket, 4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, 'big')
                if message_length > 1024 * 1024:  # 1MB limit for messages
                    break
                
                # Receive actual message
                message_data = self._receive_exact(client_socket, message_length)
                if not message_data:
                    break
                
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    self._process_message(client_socket, client_info, message)
                except json.JSONDecodeError:
                    self._log(f"Invalid JSON from {client_info[0]}")
                    
        except bluetooth.BluetoothError as e:
            self._log(f"Bluetooth client handler error: {e}")
        except Exception as e:
            self._log(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
                if client_socket in self.connections:
                    self.connections.remove(client_socket)
                if self.on_peer_disconnected:
                    self.on_peer_disconnected(client_info[0], str(client_info[1]))
            except:
                pass
    
    def _process_message(self, client_socket, client_info, message):
        """Process received message"""
        msg_type = message.get('type')
        
        if msg_type == 'file_list_request':
            self._handle_file_list_request(client_socket)
        elif msg_type == 'file_request':
            self._handle_file_request(client_socket, message)
        elif msg_type == 'ping':
            self._send_message(client_socket, {'type': 'pong'})
        else:
            self._log(f"Unknown message type: {msg_type}")
    
    def _handle_file_list_request(self, client_socket):
        """Handle request for shared files list"""
        files = []
        for filename in self.file_manager.get_shared_files():
            file_path = self.file_manager.get_file_path(filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                files.append({
                    'name': filename,
                    'size': file_size,
                    'hash': self._get_file_hash(file_path)
                })
        
        response = {
            'type': 'file_list_response',
            'files': files
        }
        self._send_message(client_socket, response)
    
    def _handle_file_request(self, client_socket, message):
        """Handle file download request"""
        filename = message.get('filename')
        if not filename:
            return
        
        file_path = self.file_manager.get_file_path(filename)
        if not os.path.exists(file_path):
            error_response = {
                'type': 'file_response',
                'success': False,
                'error': 'File not found'
            }
            self._send_message(client_socket, error_response)
            return
        
        # Send file info first
        file_size = os.path.getsize(file_path)
        file_response = {
            'type': 'file_response',
            'success': True,
            'filename': filename,
            'size': file_size
        }
        self._send_message(client_socket, file_response)
        
        # Send file data in chunks
        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(4096)  # 4KB chunks for Bluetooth
                    if not chunk:
                        break
                    client_socket.send(chunk)
        except Exception as e:
            self._log(f"Error sending file {filename}: {e}")
    
    def get_peer_files(self, peer_address):
        """Get list of files from a Bluetooth peer"""
        try:
            client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            client_socket.settimeout(15)
            
            # Find service port
            services = bluetooth.find_service(uuid=self.service_uuid, address=peer_address)
            if not services:
                self._log(f"P2P service not found on {peer_address}")
                return None
            
            port = services[0]["port"]
            client_socket.connect((peer_address, port))
            
            # Request file list
            request = {'type': 'file_list_request'}
            if not self._send_message(client_socket, request):
                return None
            
            # Receive response
            response = self._receive_message(client_socket)
            client_socket.close()
            
            if response and response.get('type') == 'file_list_response':
                return response.get('files', [])
                
        except bluetooth.BluetoothError as e:
            self._log(f"Bluetooth error getting files from {peer_address}: {e}")
        except Exception as e:
            self._log(f"Failed to get files from {peer_address}: {e}")
        
        return None
    
    def request_file(self, peer_address, filename, save_path):
        """Request and download a file from a Bluetooth peer"""
        try:
            client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            client_socket.settimeout(60)
            
            # Find service port
            services = bluetooth.find_service(uuid=self.service_uuid, address=peer_address)
            if not services:
                self._log(f"P2P service not found on {peer_address}")
                return False
            
            port = services[0]["port"]
            client_socket.connect((peer_address, port))
            
            # Request file
            request = {
                'type': 'file_request',
                'filename': filename
            }
            if not self._send_message(client_socket, request):
                client_socket.close()
                return False
            
            # Receive response
            response = self._receive_message(client_socket)
            if not response or not response.get('success'):
                error = response.get('error', 'Unknown error') if response else 'No response'
                self._log(f"File request failed: {error}")
                client_socket.close()
                return False
            
            file_size = response.get('size', 0)
            
            # Receive file data
            with open(save_path, 'wb') as file:
                bytes_received = 0
                while bytes_received < file_size:
                    remaining = min(4096, file_size - bytes_received)
                    chunk = client_socket.recv(remaining)
                    if not chunk:
                        break
                    file.write(chunk)
                    bytes_received += len(chunk)
            
            client_socket.close()
            
            if bytes_received == file_size:
                if self.on_file_received:
                    self.on_file_received(filename, peer_address)
                return True
            else:
                self._log(f"Incomplete file transfer: {bytes_received}/{file_size}")
                return False
                    
        except bluetooth.BluetoothError as e:
            self._log(f"Bluetooth error downloading {filename}: {e}")
        except Exception as e:
            self._log(f"Failed to download {filename} from {peer_address}: {e}")
        
        return False
    
    def ping_peer(self, peer_address):
        """Ping a Bluetooth peer to check if it's alive"""
        try:
            client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            client_socket.settimeout(5)
            
            # Find service port
            services = bluetooth.find_service(uuid=self.service_uuid, address=peer_address)
            if not services:
                return False
            
            port = services[0]["port"]
            client_socket.connect((peer_address, port))
            
            # Send ping
            ping_msg = {'type': 'ping'}
            if not self._send_message(client_socket, ping_msg):
                client_socket.close()
                return False
            
            # Wait for pong
            response = self._receive_message(client_socket)
            client_socket.close()
            
            return response and response.get('type') == 'pong'
                
        except:
            return False
    
    def _send_message(self, sock, message):
        """Send JSON message with length prefix"""
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = len(message_data)
            
            # Send length first (4 bytes, big endian)
            sock.send(message_length.to_bytes(4, 'big'))
            # Send message
            sock.send(message_data)
            return True
        except Exception as e:
            self._log(f"Failed to send message: {e}")
            return False
    
    def _receive_message(self, sock):
        """Receive JSON message with length prefix"""
        try:
            # Receive length first
            length_data = self._receive_exact(sock, 4)
            if not length_data:
                return None
            
            message_length = int.from_bytes(length_data, 'big')
            if message_length > 1024 * 1024:  # 1MB limit
                return None
            
            # Receive message
            message_data = self._receive_exact(sock, message_length)
            if not message_data:
                return None
            
            return json.loads(message_data.decode('utf-8'))
        except Exception as e:
            self._log(f"Failed to receive message: {e}")
            return None
    
    def _receive_exact(self, sock, num_bytes):
        """Receive exact number of bytes"""
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _get_file_hash(self, file_path):
        """Get SHA-256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""
    
    def _log(self, message):
        """Log message via callback"""
        if self.on_message_received:
            self.on_message_received(message)