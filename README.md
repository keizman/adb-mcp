# Android ADB MCP Server (Python)

A Model Context Protocol (MCP) server that enables AI assistants to interact with Android devices through the Android Debug Bridge (ADB). This server bridges the gap between AI capabilities and Android device management, allowing for seamless automation of Android development and testing operations.

**This is a Python implementation converted from the original JavaScript version, using `uv` for dependency management.**

## ⚙️ Quick Setup

### Using uv (Recommended)

1. Install the server using uv:
   ```bash
   uv add android-adb-mcp-server
   ```

2. Add the server to your MCP configuration file:
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

### Alternative: Direct Python execution

```json
{
  "mcpServers": {
    "android-adb": {
      "command": "python",
      "args": ["-m", "android_adb_mcp_server.main"],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### Configuration Locations

- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **Cline/Roo Code**: `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json` (macOS)
- For Windows/Linux, check the equivalent application support directories

After configuring, restart your AI assistant to load the new server configuration.

## 📋 Prerequisites

- **Python 3.10 or higher**
- **uv** (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **ADB (Android Debug Bridge)** must be installed and available in your system PATH
  - [Install ADB on Windows, macOS, or Linux](https://developer.android.com/tools/adb)
  - Verify installation by running `adb version` in your terminal
- For clipboard functionality:
  - **macOS**: `osascript` (built-in)
  - **Windows**: PowerShell (built-in)
  - **Linux**: `xclip` (install via `apt-get install xclip` or equivalent)

## 🚀 Features

- Connect to and manage multiple Android devices
- Execute shell commands on Android devices
- Install and uninstall applications
- Push and pull files between local system and Android devices
- Launch applications on Android devices
- Take screenshots and save them locally or copy to clipboard
- Smart device selection when multiple devices are connected

## 🛠️ Available Tools

| Tool | Description | Required Parameters | Optional Parameters |
|------|-------------|---------------------|---------------------|
| `adb_devices` | List connected devices | None | None |
| `adb_shell` | Execute shell commands | `command` | `device_id` |
| `adb_install` | Install APK files | `path` | `device_id` |
| `adb_uninstall` | Uninstall applications | `package_name` | `device_id` |
| `adb_list_packages` | List installed packages | None | `device_id`, `filter` |
| `adb_pull` | Pull files from device | `remote_path`, `local_path` | `device_id` |
| `adb_push` | Push files to device | `local_path`, `remote_path` | `device_id` |
| `launch_app` | Launch an application | `package_name` | `device_id` |
| `take_screenshot_and_save` | Take and save screenshot | `output_path` | `device_id`, `format` |
| `take_screenshot_and_copy_to_clipboard` | Take screenshot to clipboard | None | `device_id`, `format` |

### Device Management

The server intelligently handles device selection:
- If only one device is connected, it will be used automatically
- If multiple devices are connected, you must specify a `device_id` parameter
- If no devices are connected, an error will be returned

### Screenshot Path Resolution

When specifying the `output_path` for saving screenshots, the path is resolved as follows:
- Absolute paths are used as-is
- Paths starting with `~` are expanded to the user's home directory
- Relative paths are resolved relative to the user's home directory

This ensures that screenshots are saved to a location where the MCP server has write permissions.

## 🔍 Troubleshooting

### Common Issues

1. **"ADB is not available" error**
   - Ensure ADB is installed and in your system PATH
   - Verify by running `adb version` in your terminal

2. **"No Android devices connected" error**
   - Check if your device is properly connected with `adb devices`
   - Ensure USB debugging is enabled on your device
   - Try restarting ADB with `adb kill-server` followed by `adb start-server`

3. **"Multiple devices connected" error**
   - Specify the `device_id` parameter in your tool call
   - Get the list of available devices with the `adb_devices` tool

4. **Screenshot to clipboard not working**
   - Ensure the required platform-specific tools are installed

## 🔧 Alternative Installation Methods

### Option 1: Install from PyPI (when published)

```bash
# Install globally using pip
pip install android-adb-mcp-server

# Or install using uv
uv add android-adb-mcp-server
```

### Option 2: Manual Installation from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/landicefu/android-adb-mcp-server.git
   cd android-adb-mcp-server
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Test the installation:
   ```bash
   uv run python test_server.py
   ```

4. Configure with direct path:
   ```json
   {
     "mcpServers": {
       "android-adb": {
         "command": "uv",
         "args": ["run", "--directory", "/path/to/android-adb-mcp-server", "android-adb-mcp-server"],
         "env": {},
         "disabled": false,
         "alwaysAllow": []
       }
     }
   }
   ```

### Option 3: Development Mode

For development and testing:

```bash
# Run the server directly
uv run android-adb-mcp-server

# Or run the test suite
uv run python test_server.py
```

## 📄 License

This project is licensed under the ISC License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
