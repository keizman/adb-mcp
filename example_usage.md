# Example Usage

This document provides examples of how to use the Android ADB MCP Server.

## Starting the Server

```bash
# Using uv (recommended)
uv run android-adb-mcp-server

# Or using Python directly
python -m android_adb_mcp_server.main
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
      "args": ["run", "android-adb-mcp-server"],
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
      "args": ["run", "android-adb-mcp-server"],
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