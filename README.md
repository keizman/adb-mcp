# Android ADB MCP Server

A powerful Model Context Protocol (MCP) server that enables AI assistants to interact with Android devices through the Android Debug Bridge (ADB). This server bridges the gap between AI capabilities and Android device management, allowing for seamless automation of common Android development and testing operations.

## 🚀 Features

- Connect to and manage multiple Android devices
- Execute shell commands on Android devices
- Install and uninstall applications
- Push and pull files between local system and Android devices
- Launch applications on Android devices
- Take screenshots and save them locally or copy to clipboard
- Smart device selection when multiple devices are connected

## 📋 Prerequisites

- **ADB (Android Debug Bridge)** must be installed and available in your system PATH
  - [Install ADB on Windows, macOS, or Linux](https://developer.android.com/tools/adb)
  - Verify installation by running `adb version` in your terminal
- For the clipboard functionality, platform-specific tools are required:
  - **macOS**: `osascript` (built-in)
  - **Windows**: PowerShell (built-in)
  - **Linux**: `xclip` (install via `apt-get install xclip` or equivalent)
- Node.js 14.x or higher

## 🔧 Installation

### Option 1: Install from npm (Recommended)

```bash
# Install globally
npm install -g @landicefu/android-adb-mcp-server

# Or install locally in your project
npm install @landicefu/android-adb-mcp-server
```

### Option 2: Run directly with npx (No compilation needed)

You can use npx to run the package without installing it globally:

```bash
# Run directly with npx
npx @landicefu/android-adb-mcp-server

# Or if you've installed it locally
npx @landicefu/android-adb-mcp-server
```

### Option 3: Manual Installation from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/landicefu/android-adb-mcp-server.git
   cd android-adb-mcp-server
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the server:
   ```bash
   npm run build
   ```

## ⚙️ Configuration

Add the server to your MCP configuration file:

### For Cline, Roo Code and Claude Desktop

Edit the corresponding configuration file, for example, `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent on other platforms:

```json
{
  "mcpServers": {
    "android-adb": {
      "command": "npx",
      "args": ["-y", "@landicefu/android-adb-mcp-server"],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### Using node directly with source files

If you prefer to run with node directly on the source files:

```json
{
  "mcpServers": {
    "android-adb": {
      "command": "node",
      "args": ["/path/to/@landicefu/android-adb-mcp-server/src/index.js"],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

After configuring, restart your AI assistant to load the new server configuration.

## 📱 Device Management

The server intelligently handles device selection:

- If only one device is connected, it will be used automatically
- If multiple devices are connected, you must specify a `device_id` parameter
- If no devices are connected, an error will be returned

You can get the list of connected devices using the `adb_devices` tool.

## 🛠️ Available Tools

### 1. adb_devices

Lists all connected Android devices and their connection status.

- **Parameters**: None
- **Returns**: List of device IDs and their states (device, offline, unauthorized)

**Example**:
```javascript
{
  "name": "adb_devices",
  "arguments": {}
}
```

### 2. adb_shell

Executes shell commands on a connected Android device.

- **Parameters**:
  - `command` (required): The shell command to execute
  - `device_id` (optional): Specific device ID to target (if multiple devices are connected)
- **Returns**: Command output

**Example**:
```javascript
{
  "name": "adb_shell",
  "arguments": {
    "command": "ls /sdcard",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 3. adb_install

Installs APK files on a connected Android device.

- **Parameters**:
  - `path` (required): Path to APK file or directory containing APK files
  - `device_id` (optional): Specific device ID to target
- **Returns**: Installation result
- **Note**: Automatically uses `adb install-multiple` for directories or multiple APK files

**Example**:
```javascript
{
  "name": "adb_install",
  "arguments": {
    "path": "/path/to/app.apk",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 4. adb_uninstall

Uninstalls an application from a connected Android device.

- **Parameters**:
  - `package_name` (required): Package name of the application to uninstall
  - `device_id` (optional): Specific device ID to target
- **Returns**: Uninstallation result

**Example**:
```javascript
{
  "name": "adb_uninstall",
  "arguments": {
    "package_name": "com.example.app",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 5. adb_list_packages

Lists all installed packages on a connected Android device.

- **Parameters**:
  - `device_id` (optional): Specific device ID to target
- **Returns**: List of installed package names

**Example**:
```javascript
{
  "name": "adb_list_packages",
  "arguments": {
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 6. adb_pull

Pulls files from a connected Android device to the local system.

- **Parameters**:
  - `remote_path` (required): Path to the file or directory on the device
  - `local_path` (required): Path where to save the file(s) locally
  - `device_id` (optional): Specific device ID to target
- **Returns**: Operation result

**Example**:
```javascript
{
  "name": "adb_pull",
  "arguments": {
    "remote_path": "/sdcard/Download/file.txt",
    "local_path": "/path/to/save/file.txt",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 7. adb_push

Pushes files from the local system to a connected Android device.

- **Parameters**:
  - `local_path` (required): Path to the local file or directory
  - `remote_path` (required): Path on the device where to push the file(s)
  - `device_id` (optional): Specific device ID to target
- **Returns**: Operation result

**Example**:
```javascript
{
  "name": "adb_push",
  "arguments": {
    "local_path": "/path/to/file.txt",
    "remote_path": "/sdcard/Download/file.txt",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 8. launch_app

Launches an application on a connected Android device.

- **Parameters**:
  - `package_name` (required): Package name of the application to launch
  - `device_id` (optional): Specific device ID to target
- **Returns**: Launch result
- **Note**: Automatically attempts to find the main activity if the default launch fails

**Example**:
```javascript
{
  "name": "launch_app",
  "arguments": {
    "package_name": "com.example.app",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 9. take_screenshot_and_save

Takes a screenshot and saves it to the local system.

- **Parameters**:
  - `output_path` (required): Path where to save the screenshot
  - `device_id` (optional): Specific device ID to target
- **Returns**: Path to the saved screenshot

**Example**:
```javascript
{
  "name": "take_screenshot_and_save",
  "arguments": {
    "output_path": "/path/to/save/screenshot.png",
    "device_id": "emulator-5554"  // Optional
  }
}
```

### 10. take_screenshot_and_copy_to_clipboard

Takes a screenshot and copies it to the clipboard.

- **Parameters**:
  - `device_id` (optional): Specific device ID to target
- **Returns**: Success/failure status

**Example**:
```javascript
{
  "name": "take_screenshot_and_copy_to_clipboard",
  "arguments": {
    "device_id": "emulator-5554"  // Optional
  }
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"ADB is not available" error**
   - Ensure ADB is installed and in your system PATH
   - Verify by running `adb version` in your terminal
   - If using a custom ADB path, make sure it's correct

2. **"No Android devices connected" error**
   - Check if your device is properly connected with `adb devices`
   - Ensure USB debugging is enabled on your device
   - Try restarting ADB with `adb kill-server` followed by `adb start-server`

3. **"Multiple devices connected" error**
   - Specify the `device_id` parameter in your tool call
   - Get the list of available devices with the `adb_devices` tool

4. **Screenshot to clipboard not working**
   - Ensure the required platform-specific tools are installed:
     - macOS: `osascript` (built-in)
     - Windows: PowerShell (built-in)
     - Linux: `xclip` (install via package manager)

### Debugging

If you encounter issues, you can run the server manually to see error messages:

```bash
npm start
```

## 📦 Publishing to npm

If you want to publish your own version of this package to npm, follow these steps:

1. Make sure you have an npm account. If not, create one at [npmjs.com](https://www.npmjs.com/signup)

2. Log in to npm from the command line:
   ```bash
   npm login
   ```

3. Update the package.json with your information:
   - The package name is set to `@landicefu/android-adb-mcp-server`
   - Update the `version` following semantic versioning
   - The author field is set to "Landice Fu <landice.fu@gmail.com>"
   - The repository, bugs, and homepage URLs are set to your GitHub repository

4. Prepare the package for publishing:
   ```bash
   npm run build
   ```

5. Publish the package:
   ```bash
   npm publish
   ```

   Since you're publishing a scoped package (@landicefu/android-adb-mcp-server):
   ```bash
   npm publish --access public
   ```

6. To update the package later, increment the version number in package.json and run:
   ```bash
   npm publish
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the ISC License - see the LICENSE file for details.