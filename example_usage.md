# Example Usage

This document provides examples of how to use the Android ADB MCP Server.

## Starting the Server

```bash
# Method 1: Using Python module (Recommended)
uv run python -m android_adb_mcp_server.main

# Method 2: Using direct script path
uv run python src/android_adb_mcp_server/main.py

# Method 3: Using wrapper script
uv run python run_server.py

# Method 4: Without uv (if dependencies are installed)
python run_server.py
```

## Testing the Server

Run the test script to verify everything is working:

```bash
uv run python test_server.py
```

## MCP Configuration Examples

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "android-adb": {
      "command": "uv",
      "args": ["run", "python", "-m", "android_adb_mcp_server.main"],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### Cline/Roo Code Configuration

Add to `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "android-adb": {
      "command": "uv",
      "args": ["run", "python", "-m", "android_adb_mcp_server.main"],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

## Available Tools

The server provides the following tools:

1. **adb_devices** - List connected devices
2. **adb_shell** - Execute shell commands
3. **adb_install** - Install APK files
4. **adb_uninstall** - Uninstall applications
5. **adb_list_packages** - List installed packages
6. **adb_pull** - Pull files from device
7. **adb_push** - Push files to device
8. **launch_app** - Launch applications
9. **take_screenshot_and_save** - Take and save screenshots
10. **take_screenshot_and_copy_to_clipboard** - Take screenshots to clipboard
11. **clear_app_data** - Clear all application data
12. **force_stop_app** - Force stop running applications
13. **go_to_home** - Navigate to home screen
14. **open_settings** - Open Android Settings app
15. **clear_cache_and_restart** - Clear app data and restart
16. **force_restart_app** - Force stop and restart applications

## Common Use Cases

### Check Connected Devices
Ask the AI assistant: "List all connected Android devices"

### Install an APK
Ask the AI assistant: "Install the APK file at /path/to/app.apk"

### Take a Screenshot
Ask the AI assistant: "Take a screenshot and save it to ~/Desktop/screenshot.png"

### Execute Shell Commands
Ask the AI assistant: "Execute the command 'ls -la' on the Android device"

### List Installed Apps
Ask the AI assistant: "List all installed apps that contain 'chrome' in the name"

### Clear App Data
Ask the AI assistant: "Clear all data for com.example.app"

### Force Stop an App
Ask the AI assistant: "Force stop the app com.example.app"

### Navigate to Home Screen
Ask the AI assistant: "Go to the home screen"

### Open Settings
Ask the AI assistant: "Open the Android settings app"

### Clear Cache and Restart App
Ask the AI assistant: "Clear cache and restart com.example.app"

### Force Restart an App
Ask the AI assistant: "Force restart the app com.example.app"

## Troubleshooting

### ADB Not Found
Make sure ADB is installed and available in your PATH:
```bash
adb version
```

### No Devices Connected
Check if devices are connected and have USB debugging enabled:
```bash
adb devices
```

### Permission Issues
Make sure your Android device has USB debugging enabled and you've accepted the debug authorization prompt.