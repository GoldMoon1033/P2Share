# 🔵 P2Share Bluetooth P2P File Sharing System

A peer-to-peer file sharing application using Bluetooth connectivity. Share files directly between computers via Bluetooth without requiring internet connectivity or external servers.

## ✨ Key Features

- **Bluetooth Communication** - Direct peer-to-peer communication via Bluetooth RFCOMM
- **Automatic Peer Discovery** - Finds other Bluetooth devices running the application
- **Simple GUI** - Clean interface built with tkinter
- **File Integrity** - SHA-256 hashing ensures safe file transfers
- **Cross-Platform** - Works on Windows, Linux, and macOS
- **No Internet Required** - Operates entirely over Bluetooth connections

## 🛠️ Core Components

- **main.py** - GUI application and user interaction handling
- **p2p_network.py** - Bluetooth socket communication and file transfer protocol
- **file_manager.py** - Shared files database and download management
- **peer_discovery.py** - Bluetooth device discovery and service detection

## 📋 Requirements

### Dependencies
- **Python 3.7+**
- **pybluez** - Python Bluetooth library

### System Requirements
- Bluetooth adapter (built-in or USB)
- Bluetooth drivers installed and enabled
- Sufficient permissions for Bluetooth access

## 🚀 Installation & Setup

### 1. Install Dependencies

**On Windows:**
```bash
pip install pybluez
```
*Note: May require Microsoft Visual C++ Build Tools*

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install bluetooth libbluetooth-dev
pip install pybluez
```

**On macOS:**
```bash
brew install bluetooth
pip install pybluez
```

### 2. Enable Bluetooth

Ensure Bluetooth is enabled on your system:
- **Windows**: Settings → Devices → Bluetooth & other devices
- **Linux**: `sudo systemctl start bluetooth`
- **macOS**: System Preferences → Bluetooth

### 3. Run the Application

```bash
python main.py
```

## 📖 How to Use

### Initial Setup
1. **Start the application** on both devices
2. **Enable Bluetooth server** by clicking "Start Server"
3. **Make devices discoverable** in your system Bluetooth settings
4. **Scan for peers** using the "Scan for Peers" button

### Sharing Files
1. **Add files** to share using "Add File" button
2. **Wait for peers** to appear in the peer list
3. **Other devices** can now request your shared files

### Downloading Files
1. **Select a peer** from the discovered peers list
2. **Click "Request File"** to see their available files
3. **Choose a file** and select download location
4. **File transfers** directly via Bluetooth connection

## 🔧 Technical Details

### Bluetooth Protocol
- **RFCOMM sockets** for reliable data transmission
- **Custom JSON protocol** for command communication
- **Service UUID**: `94f39d29-7d6d-437d-973b-fba39e49d4ee`
- **4KB chunks** for efficient Bluetooth file transfer

### File Transfer Process
1. **Service Discovery**: Client discovers P2P service on peer device
2. **Connection**: Establish RFCOMM connection to peer
3. **File List**: Request and receive list of available files
4. **File Request**: Request specific file download
5. **Transfer**: Receive file data in chunks with integrity verification

### Security & Reliability
- **File Integrity**: SHA-256 hash verification
- **Error Handling**: Automatic connection recovery and timeout management
- **Local Only**: No external network communication

## 🌐 Platform Compatibility

### Bluetooth Support
- **Windows 10+**: Full support with built-in Bluetooth stack
- **Linux**: Requires BlueZ Bluetooth stack (standard on most distributions)  
- **macOS 10.14+**: Native Bluetooth support

### Known Limitations
- **Range**: Limited to Bluetooth range (~10-30 feet depending on adapter)
- **Speed**: Transfer speeds limited by Bluetooth bandwidth (~1-3 MB/s)
- **Pairing**: Some systems may require device pairing before connection

## 🐛 Troubleshooting

### Common Issues

**"pybluez not found"**
- Install using platform-specific instructions above
- On Windows, ensure Visual C++ Build Tools are installed

**"Bluetooth adapter not found"**
- Verify Bluetooth adapter is connected and enabled
- Check device manager (Windows) or `hciconfig` (Linux)

**"No peers discovered"**
- Ensure both devices are running the application
- Check that Bluetooth is discoverable on both devices
- Try moving devices closer together

**"Connection failed"**
- Some systems require Bluetooth pairing before application connection
- Check firewall settings that might block Bluetooth
- Restart Bluetooth service if necessary

### Debug Information
The activity log shows:
- Bluetooth adapter status
- Peer discovery events  
- File transfer progress
- Connection errors

## ⚡ Performance

### Transfer Specifications
- **Speed**: 1-3 MB/s (depending on Bluetooth version)
- **Range**: 10-30 feet typical
- **File Size**: No artificial limits
- **Memory Usage**: ~10-20MB during operation

### Optimization
- Files transferred in 4KB chunks for Bluetooth efficiency
- Automatic connection management and cleanup
- Background peer discovery to minimize UI blocking

## 🔒 Security Considerations

### Data Protection
- **Local Communication**: All transfers occur directly between devices
- **File Verification**: SHA-256 hashing prevents corrupted transfers
- **No Cloud Storage**: Files never leave local devices

### Bluetooth Security
- Uses standard Bluetooth security protocols
- For sensitive files, consider pre-pairing devices
- Application doesn't implement additional encryption beyond Bluetooth stack

## 🤝 Contributing

This project demonstrates Bluetooth programming concepts with Python. Areas for improvement:

- **Enhanced UI**: Progress bars and transfer speed indicators
- **Encryption**: Additional file encryption layer
- **Resume**: Support for resuming interrupted transfers
- **Multiple Files**: Batch file transfer capabilities

## 📄 License

MIT License - Free to use for personal and educational projects.

---

**System Requirements**: Bluetooth adapter, Python 3.7+, pybluez library
**Tested Platforms**: Windows 10/11, Ubuntu 20.04+, macOS 11+
