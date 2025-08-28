#!/usr/bin/env python3
"""
Bluetooth Peer Discovery Module
Handles Bluetooth device discovery and service detection using pybluez.
"""

import bluetooth
import threading
import time
from collections import defaultdict

class BluetoothPeerDiscovery:
    def __init__(self):
        self.is_running = False
        self.service_uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.service_name = "P2P File Share"
        self.peers = {}  # {address -> peer_info}
        self.last_seen = defaultdict(float)
        
        # Callbacks
        self.on_peer_found = None
        self.on_peer_lost = None
        
        # Threading
        self.discovery_thread = None
        self.cleanup_thread = None
    
    def start_discovery(self):
        """Start Bluetooth peer discovery service"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start discovery thread
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def stop_discovery(self):
        """Stop Bluetooth peer discovery service"""
        self.is_running = False
    
    def discover_peers(self):
        """Actively discover Bluetooth peers"""
        if not self.is_running:
            return
        
        # Trigger immediate discovery
        threading.Thread(target=self._perform_discovery, daemon=True).start()
    
    def get_peers(self):
        """Get list of discovered Bluetooth peers"""
        current_time = time.time()
        active_peers = []
        
        for address, peer_info in self.peers.items():
            # Return peers seen in last 120 seconds (Bluetooth discovery is slower)
            if current_time - self.last_seen[address] < 120:
                active_peers.append(peer_info)
        
        return active_peers
    
    def is_peer_alive(self, peer_address):
        """Check if a specific Bluetooth peer is still alive"""
        try:
            # Try to find the service
            services = bluetooth.find_service(uuid=self.service_uuid, address=peer_address)
            return len(services) > 0
        except:
            return False
    
    def _discovery_loop(self):
        """Main discovery loop"""
        while self.is_running:
            try:
                self._perform_discovery()
                time.sleep(45)  # Bluetooth discovery every 45 seconds (slower than WiFi)
            except Exception as e:
                print(f"Discovery loop error: {e}")
                time.sleep(10)
    
    def _perform_discovery(self):
        """Perform Bluetooth device discovery"""
        try:
            # Discover nearby Bluetooth devices
            nearby_devices = bluetooth.discover_devices(
                duration=8,  # 8 second discovery
                lookup_names=True,
                flush_cache=True
            )
            
            for address, name in nearby_devices:
                if not self.is_running:
                    break
                
                # Check if device has our P2P service
                threading.Thread(
                    target=self._check_peer_service,
                    args=(address, name),
                    daemon=True
                ).start()
                
        except bluetooth.BluetoothError as e:
            print(f"Bluetooth discovery error: {e}")
        except Exception as e:
            print(f"Discovery error: {e}")
    
    def _check_peer_service(self, address, name):
        """Check if a Bluetooth device has our P2P service"""
        try:
            services = bluetooth.find_service(
                uuid=self.service_uuid,
                address=address
            )
            
            if services:
                # Found P2P service on this device
                service = services[0]
                self._add_peer(address, name, service)
                
        except bluetooth.BluetoothError:
            # Device doesn't have our service or is unreachable
            pass
        except Exception as e:
            print(f"Service check error for {address}: {e}")
    
    def _cleanup_loop(self):
        """Periodically clean up old peers"""
        while self.is_running:
            try:
                current_time = time.time()
                peers_to_remove = []
                
                for address, last_seen_time in list(self.last_seen.items()):
                    if current_time - last_seen_time > 180:  # 3 minutes timeout for Bluetooth
                        peers_to_remove.append(address)
                
                for address in peers_to_remove:
                    if address in self.peers:
                        peer_info = self.peers[address]
                        del self.peers[address]
                        del self.last_seen[address]
                        
                        if self.on_peer_lost:
                            self.on_peer_lost(peer_info)
                
                time.sleep(20)  # Check every 20 seconds
            except Exception:
                break
    
    def _add_peer(self, address, name, service_info):
        """Add or update a Bluetooth peer"""
        current_time = time.time()
        is_new_peer = address not in self.peers
        
        peer_info = {
            'address': address,
            'name': name or f"Device-{address.replace(':', '')}",
            'port': service_info.get('port', 'Unknown'),
            'service_name': service_info.get('name', 'Unknown'),
            'first_seen': self.peers.get(address, {}).get('first_seen', current_time),
            'last_seen': current_time,
        }
        
        self.peers[address] = peer_info
        self.last_seen[address] = current_time
        
        if is_new_peer and self.on_peer_found:
            self.on_peer_found(peer_info)
    
    def get_local_bluetooth_info(self):
        """Get local Bluetooth adapter information"""
        try:
            local_address = bluetooth.read_local_bdaddr()[0]
            
            # Try to get adapter name
            try:
                import socket
                sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
                sock.bind((local_address, 0))
                adapter_name = bluetooth.lookup_name(local_address, timeout=5)
                sock.close()
            except:
                adapter_name = "Unknown"
            
            return {
                'address': local_address,
                'name': adapter_name,
                'is_discoverable': self._is_discoverable()
            }
        except Exception as e:
            print(f"Error getting Bluetooth info: {e}")
            return None
    
    def _is_discoverable(self):
        """Check if local Bluetooth is discoverable"""
        try:
            # This is a simplified check - actual implementation depends on system
            return True
        except:
            return False
    
    def make_discoverable(self):
        """Make local Bluetooth device discoverable"""
        try:
            # On most systems, this requires system-level commands
            # This is a placeholder - actual implementation varies by OS
            import subprocess
            
            # Linux example (requires bluetoothctl)
            try:
                subprocess.run(['bluetoothctl', 'discoverable', 'on'], 
                             check=False, capture_output=True)
                return True
            except:
                pass
            
            # Windows/macOS would require different approaches
            return False
        except:
            return False
    
    def get_discovery_status(self):
        """Get current discovery status information"""
        return {
            'is_running': self.is_running,
            'total_peers': len(self.peers),
            'active_peers': len(self.get_peers()),
            'local_info': self.get_local_bluetooth_info()
        }
    
    def refresh_peer_services(self):
        """Refresh service information for known peers"""
        def refresh_thread():
            for address in list(self.peers.keys()):
                if not self.is_running:
                    break
                
                try:
                    services = bluetooth.find_service(
                        uuid=self.service_uuid,
                        address=address
                    )
                    
                    if services:
                        # Update last seen time
                        self.last_seen[address] = time.time()
                    else:
                        # Service no longer available
                        if address in self.peers:
                            peer_info = self.peers[address]
                            del self.peers[address]
                            del self.last_seen[address]
                            
                            if self.on_peer_lost:
                                self.on_peer_lost(peer_info)
                                
                except Exception:
                    continue
        
        threading.Thread(target=refresh_thread, daemon=True).start()