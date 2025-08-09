# ZYNAPSE CLI with Firebase Integration

## 🚀 Complete Setup Guide

### Prerequisites
- Python 3.8+
- Firebase Project
- Gemini AI API Key

### 📦 Installation

1. **Install Python Dependencies:**
```bash
pip install google-genai firebase-admin
```

2. **Clone/Download the ZYNAPSE Files:**
- `zynapse_firebase.py` - Main Python application
- `zynapse_web_controller.html` - Web interface
- `firebase-service-account.json` - Firebase credentials (you need to create this)

### 🔥 Firebase Setup

#### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Name your project (e.g., "zynapse-cli")
4. Enable Google Analytics (optional)
5. Create project

#### Step 2: Setup Firestore Database
1. In your Firebase project, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select a location
5. Click "Done"

#### Step 3: Setup Realtime Database
1. Go to "Realtime Database"
2. Click "Create Database"
3. Choose "Start in test mode"
4. Select a location
5. Click "Done"

#### Step 4: Get Service Account Key
1. Go to "Project Settings" (gear icon)
2. Go to "Service accounts" tab
3. Click "Generate new private key"
4. Save the JSON file as `firebase-service-account.json` in your project folder

#### Step 5: Get Web Config
1. In "Project Settings", go to "General" tab
2. Scroll down to "Your apps"
3. Click "Web app" (</>) icon
4. Register your app with a name
5. Copy the Firebase config object

### 📝 Configuration Files

#### 1. Firebase Service Account (`firebase-service-account.json`)
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project-id.iam.gserviceaccount.com"
}
```

#### 2. Update Web Interface Config
Edit `zynapse_web_controller.html` and replace the `firebaseConfig` object:

```javascript
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project-id.firebaseapp.com",
    databaseURL: "https://your-project-id-default-rtdb.firebaseio.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456"
};
```

#### 3. Update Python Script
Edit `zynapse_firebase.py` and set your Gemini API key:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### 🛡️ Security Rules (Important!)

#### Firestore Rules (`firestore.rules`)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write to zynapse collections
    match /zynapse_devices/{document} {
      allow read, write: if true;
    }
    match /zynapse_sessions/{document} {
      allow read, write: if true;
    }
    match /zynapse_exports/{document} {
      allow read, write: if true;
    }
    match /zynapse_test/{document} {
      allow read, write: if true;
    }
  }
}
```

#### Realtime Database Rules
```json
{
  "rules": {
    "zynapse_commands": {
      ".read": true,
      ".write": true
    },
    "zynapse_results": {
      ".read": true,
      ".write": true
    }
  }
}
```

⚠️ **Security Warning:** These rules allow public access. For production, implement proper authentication and authorization.

### 🚀 Running ZYNAPSE CLI

1. **Start the Python Application:**
```bash
python zynapse_firebase.py
```

2. **Open Web Interface:**
- Double-click `zynapse_web_controller.html` to open in browser
- Or serve it via a web server for better HTTPS support

### 📱 Usage Guide

#### Local Commands (Python CLI)
```bash
ZYNAPSE[device_id] > list files in current directory
ZYNAPSE[device_id] > show system information
ZYNAPSE[device_id] > help
ZYNAPSE[device_id] > stats
ZYNAPSE[device_id] > firebase
```

#### Remote Commands (Web Interface)
1. Open the web interface
2. Wait for your device to appear in "Available Devices"
3. Click on your device to select it
4. Type natural language commands
5. Click "Send Command" or press Ctrl+Enter
6. View real-time results

### 🎯 Available Commands

#### System Information
- `show system information`
- `check memory usage`
- `list running processes`
- `show disk usage`

#### File Operations
- `list files in current directory`
- `create folder called test`
- `copy file.txt to backup.txt`
- `find large files`

#### Application Control
- `open calculator`
- `open notepad`
- `start chrome`
- `close all chrome windows`

#### Network Operations
- `ping google.com`
- `check internet connection`
- `show network adapters`
- `display IP configuration`

#### Advanced Operations
- `backup documents folder`
- `clean temporary files`
- `restart computer in 5 minutes`
- `show event logs`

### 🔧 Troubleshooting

#### Common Issues

1. **Firebase Connection Failed**
   - Check `firebase-service-account.json` exists and is valid
   - Verify Firebase project settings
   - Ensure Firestore and Realtime Database are enabled

2. **Web Interface Not Loading**
   - Check Firebase config in HTML file
   - Open browser developer console for errors
   - Ensure internet connection for Firebase CDN

3. **Commands Not Executing**
   - Check device is online in web interface
   - Verify PowerShell execution policy
   - Check Python CLI logs for errors

4. **Gemini API Errors**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure internet connection

#### Debugging Commands
```bash
# Check Firebase connection
ZYNAPSE[device_id] > firebase

# View detailed logs
ZYNAPSE[device_id] > stats

# Export session data
ZYNAPSE[device_id] > export
```

### 📊 Data Structure

#### Firebase Collections

**Firestore:**
- `zynapse_devices/` - Device status and configuration
- `zynapse_sessions/` - Command execution history
- `zynapse_exports/` - Exported session data
- `zynapse_test/` - Connection testing

**Realtime Database:**
- `zynapse_commands/` - Pending and active commands
- `zynapse_results/` - Command execution results

### 🔒 Security Considerations

1. **API Keys:** Store securely, never commit to public repos
2. **Firebase Rules:** Implement proper authentication for production
3. **Network:** Use HTTPS for web interface in production
4. **Commands:** Review safety levels before dangerous operations
5. **Logging:** Be aware that all commands are logged to Firebase

### 📈 Performance Tips

1. **Device Limits:** Each device can handle one command at a time
2. **Timeout:** Adjust timeout based on expected command duration
3. **Results:** Large outputs are stored in Firebase, consider pagination
4. **Network:** Stable internet connection required for real-time features

### 🆘 Support

If you encounter issues:

1. Check the browser console (F12) for JavaScript errors
2. Check Python application logs
3. Verify Firebase project configuration
4. Test with simple commands first
5. Check network connectivity

### 📝 Example Session

```bash
# Start Python CLI
python zynapse_firebase.py

# Output:
🚀 Initializing ZYNAPSE CLI with Firebase...
✅ Firebase initialized successfully!
👂 Firebase command listener started
🚀 ZYNAPSE CLI with Firebase - Ready!
Device ID: abc123ef
Model: gemini-2.0-flash-exp
Safety: ON
Timeout: 60s
Firebase: Connected

# Send command from web interface
# Command appears in CLI:
📨 Received Firebase command: show system information

# Result sent back to web interface automatically
```

### 🎉 Congratulations!

You now have a fully functional AI-powered remote PowerShell controller with:
- ✅ Web-based command interface
- ✅ Real-time command execution
- ✅ Firebase synchronization
- ✅ AI-powered code generation
- ✅ Safety mechanisms
- ✅ Comprehensive logging

Enjoy using ZYNAPSE CLI! 🚀