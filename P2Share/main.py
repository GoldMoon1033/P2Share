#!/usr/bin/env python3
"""
Bluetooth P2P File Sharing System - Main Application
A peer-to-peer file sharing system using Bluetooth with pybluez.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import time
from p2p_network import P2PBluetoothNetwork
from file_manager import FileManager
from peer_discovery import BluetoothPeerDiscovery

class BluetoothP2PFileShareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bluetooth P2P File Sharing System")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Initialize components
        self.network = P2PBluetoothNetwork()
        self.file_manager = FileManager()
        self.peer_discovery = BluetoothPeerDiscovery()
        
        # UI Variables
        self.status_var = tk.StringVar(value="Offline")
        self.bt_info_var = tk.StringVar(value="Bluetooth: Not detected")
        
        self.setup_ui()
        self.setup_callbacks()
        
        # Check Bluetooth and start discovery
        self.check_bluetooth_adapter()
        self.start_peer_discovery()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Bluetooth Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Service:").grid(row=0, column=0, sticky=tk.W)
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Button(status_frame, text="Start Server", 
                  command=self.toggle_server).grid(row=0, column=2, padx=(20, 0))
        
        bt_info_label = ttk.Label(status_frame, textvariable=self.bt_info_var)
        bt_info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Peers frame
        peers_frame = ttk.LabelFrame(main_frame, text="Available Bluetooth Peers", padding="5")
        peers_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        peers_frame.columnconfigure(0, weight=1)
        peers_frame.rowconfigure(1, weight=1)
        
        # Peers listbox with scrollbar
        peers_list_frame = ttk.Frame(peers_frame)
        peers_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        peers_list_frame.columnconfigure(0, weight=1)
        peers_list_frame.rowconfigure(0, weight=1)
        
        self.peers_listbox = tk.Listbox(peers_list_frame, height=8)
        self.peers_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        peers_scrollbar = ttk.Scrollbar(peers_list_frame, orient="vertical", 
                                       command=self.peers_listbox.yview)
        peers_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.peers_listbox.configure(yscrollcommand=peers_scrollbar.set)
        
        # Peer buttons
        peer_buttons_frame = ttk.Frame(peers_frame)
        peer_buttons_frame.grid(row=2, column=0, pady=(5, 0))
        
        ttk.Button(peer_buttons_frame, text="Scan for Peers", 
                  command=self.refresh_peers).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(peer_buttons_frame, text="Request File", 
                  command=self.request_file).pack(side=tk.LEFT)
        
        # Files frame
        files_frame = ttk.LabelFrame(main_frame, text="File Operations", padding="5")
        files_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(2, weight=1)
        
        # My files section
        ttk.Label(files_frame, text="My Shared Files:").grid(row=0, column=0, sticky=tk.W)
        
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        files_list_frame.columnconfigure(0, weight=1)
        
        self.my_files_listbox = tk.Listbox(files_list_frame, height=6)
        self.my_files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient="vertical",
                                       command=self.my_files_listbox.yview)
        files_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.my_files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        # File operation buttons
        file_buttons_frame = ttk.Frame(files_frame)
        file_buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(file_buttons_frame, text="Add File", 
                  command=self.add_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Remove File", 
                  command=self.remove_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Open Downloads", 
                  command=self.open_downloads).pack(side=tk.LEFT)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls
        log_controls_frame = ttk.Frame(log_frame)
        log_controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(log_controls_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.RIGHT)
    
    def setup_callbacks(self):
        """Setup network callbacks"""
        self.network.on_peer_connected = self.on_peer_connected
        self.network.on_peer_disconnected = self.on_peer_disconnected
        self.network.on_file_received = self.on_file_received
        self.network.on_message_received = self.log_message
        
        self.peer_discovery.on_peer_found = self.on_peer_found
        self.peer_discovery.on_peer_lost = self.on_peer_lost
    
    def check_bluetooth_adapter(self):
        """Check Bluetooth adapter status"""
        def check_thread():
            try:
                bt_info = self.peer_discovery.get_local_bluetooth_info()
                if bt_info:
                    info_text = f"Bluetooth: {bt_info['address']} ({bt_info['name']})"
                    if not bt_info.get('is_discoverable', False):
                        info_text += " - Make device discoverable for better connectivity"
                else:
                    info_text = "Bluetooth: Not available or disabled"
                
                self.root.after(0, lambda: self.bt_info_var.set(info_text))
                
            except Exception as e:
                error_text = f"Bluetooth: Error - {str(e)}"
                self.root.after(0, lambda: self.bt_info_var.set(error_text))
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def start_peer_discovery(self):
        """Start Bluetooth peer discovery service"""
        def discovery_thread():
            self.peer_discovery.start_discovery()
        
        threading.Thread(target=discovery_thread, daemon=True).start()
        self.log_message("Bluetooth peer discovery started")
    
    def toggle_server(self):
        """Toggle Bluetooth server on/off"""
        if self.network.is_running:
            self.network.stop_server()
            self.status_var.set("Offline")
            self.log_message("Bluetooth server stopped")
        else:
            def start_server_thread():
                port = self.network.start_server()
                if port:
                    self.root.after(0, lambda: self.status_var.set(f"Online - Port {port}"))
                    self.root.after(0, lambda: self.log_message(f"Bluetooth server started on port {port}"))
                else:
                    self.root.after(0, lambda: self.log_message("Failed to start Bluetooth server"))
            
            threading.Thread(target=start_server_thread, daemon=True).start()
    
    def refresh_peers(self):
        """Refresh the Bluetooth peers list"""
        self.peer_discovery.discover_peers()
        self.log_message("Scanning for Bluetooth peers...")
    
    def add_file(self):
        """Add a file to share"""
        file_path = filedialog.askopenfilename(
            title="Select File to Share",
            filetypes=[("All Files", "*.*")]
        )
        
        if file_path:
            if self.file_manager.add_shared_file(file_path):
                self.update_files_list()
                filename = file_path.split('/')[-1].split('\\')[-1]  # Cross-platform basename
                self.log_message(f"Added file: {filename}")
            else:
                messagebox.showerror("Error", "Failed to add file")
    
    def remove_file(self):
        """Remove a shared file"""
        selection = self.my_files_listbox.curselection()
        if selection:
            file_name = self.my_files_listbox.get(selection[0])
            if self.file_manager.remove_shared_file(file_name):
                self.update_files_list()
                self.log_message(f"Removed file: {file_name}")
    
    def open_downloads(self):
        """Open downloads directory"""
        import subprocess
        import os
        download_dir = self.file_manager.get_downloads_directory()
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(download_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', download_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open downloads folder: {e}")
    
    def request_file(self):
        """Request a file from a Bluetooth peer"""
        peer_selection = self.peers_listbox.curselection()
        if not peer_selection:
            messagebox.showwarning("Warning", "Please select a Bluetooth peer first")
            return
        
        peer_info_text = self.peers_listbox.get(peer_selection[0])
        # Extract address from display string "Name (Address)"
        try:
            if " (" in peer_info_text and ")" in peer_info_text:
                peer_address = peer_info_text.split(" (")[1].rstrip(")")
            else:
                peer_address = peer_info_text.split(" - ")[0]
        except:
            messagebox.showerror("Error", "Invalid peer information")
            return
        
        # Get available files from peer
        self.request_file_list(peer_address)
    
    def request_file_list(self, peer_address):
        """Request file list from Bluetooth peer"""
        def request_thread():
            files = self.network.get_peer_files(peer_address)
            if files:
                self.root.after(0, lambda: self.show_file_selection_dialog(files, peer_address))
            elif files is not None:
                self.root.after(0, lambda: messagebox.showinfo("Info", "Peer has no shared files"))
            else:
                self.root.after(0, lambda: self.log_message("Failed to connect to peer or get file list"))
        
        threading.Thread(target=request_thread, daemon=True).start()
        self.log_message(f"Requesting file list from {peer_address}")
    
    def show_file_selection_dialog(self, files, peer_address):
        """Show dialog to select file for download"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select File to Download")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text=f"Available files from {peer_address}:").pack(pady=10)
        
        # Files listbox
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        listbox = tk.Listbox(list_frame)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for file_info in files:
            size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] > 1024 * 1024 else file_info['size'] / 1024
            size_unit = "MB" if file_info['size'] > 1024 * 1024 else "KB"
            listbox.insert(tk.END, f"{file_info['name']} ({size_mb:.1f} {size_unit})")
        
        def download_selected():
            selection = listbox.curselection()
            if selection:
                file_info = files[selection[0]]
                dialog.destroy()
                self.download_file(peer_address, file_info['name'])
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Download", 
                  command=download_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Double-click to download
        listbox.bind('<Double-Button-1>', lambda e: download_selected())
    
    def download_file(self, peer_address, filename):
        """Download a file from Bluetooth peer"""
        save_path = filedialog.asksaveasfilename(
            title="Save File As",
            initialvalue=filename,
            defaultextension="",
            filetypes=[("All Files", "*.*")]
        )
        
        if save_path:
            def download_thread():
                success = self.network.request_file(peer_address, filename, save_path)
                if success:
                    self.root.after(0, lambda: self.log_message(f"Downloaded: {filename}"))
                else:
                    self.root.after(0, lambda: self.log_message(f"Failed to download: {filename}"))
            
            threading.Thread(target=download_thread, daemon=True).start()
            self.log_message(f"Downloading {filename} from {peer_address}")
    
    def update_files_list(self):
        """Update the files listbox"""
        self.my_files_listbox.delete(0, tk.END)
        for filename in self.file_manager.get_shared_files():
            self.my_files_listbox.insert(tk.END, filename)
    
    def update_peers_list(self):
        """Update the peers listbox"""
        self.peers_listbox.delete(0, tk.END)
        for peer in self.peer_discovery.get_peers():
            display_text = f"{peer['name']} ({peer['address']})"
            self.peers_listbox.insert(tk.END, display_text)
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)
    
    def on_peer_connected(self, peer_address, peer_port):
        """Handle Bluetooth peer connection"""
        self.root.after(0, lambda: self.log_message(f"Peer connected: {peer_address}"))
    
    def on_peer_disconnected(self, peer_address, peer_port):
        """Handle Bluetooth peer disconnection"""
        self.root.after(0, lambda: self.log_message(f"Peer disconnected: {peer_address}"))
    
    def on_file_received(self, filename, sender_address):
        """Handle file reception"""
        self.root.after(0, lambda: self.log_message(f"Received file: {filename} from {sender_address}"))
    
    def on_peer_found(self, peer_info):
        """Handle Bluetooth peer discovery"""
        self.root.after(0, self.update_peers_list)
        self.root.after(0, lambda: self.log_message(f"Found peer: {peer_info['name']} ({peer_info['address']})"))
    
    def on_peer_lost(self, peer_info):
        """Handle Bluetooth peer loss"""
        self.root.after(0, self.update_peers_list)
        self.root.after(0, lambda: self.log_message(f"Lost peer: {peer_info['name']} ({peer_info['address']})"))
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """Handle application closing"""
        self.network.stop_server()
        self.peer_discovery.stop_discovery()
        self.root.destroy()

def main():
    # Check if pybluez is available
    try:
        import bluetooth
    except ImportError:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        messagebox.showerror(
            "Missing Dependency",
            "This application requires pybluez.\n\n"
            "Install it using:\n"
            "pip install pybluez\n\n"
            "On Linux, you may also need:\n"
            "sudo apt-get install bluetooth libbluetooth-dev\n\n"
            "On Windows, you may need Microsoft Visual C++ Build Tools."
        )
        return
    
    root = tk.Tk()
    app = BluetoothP2PFileShareApp(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()