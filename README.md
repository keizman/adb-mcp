# Android ADB MCP Server

This MCP server provides tools for interacting with Android devices through the Android Debug Bridge (ADB). It enables AI assistants to perform common Android development and testing operations.

## Features

- List connected Android devices
- Execute shell commands on Android devices
- Install and uninstall applications
- List installed packages
- Pull and push files between the device and local system
- Launch applications
- Take screenshots and save them or copy to clipboard

## Installation

```bash
npm install -g @landicefu/android-adb-mcp-server
```

## Requirements

- Node.js 14 or later
- Android SDK Platform Tools (adb) installed and in your PATH

## Usage

### Taking Screenshots

The server provides two tools for taking screenshots:

1. `take_screenshot_and_save`: Takes a screenshot and saves it to the local system
2. `take_screenshot_and_copy_to_clipboard`: Takes a screenshot and copies it to the clipboard

#### Path Resolution

When specifying the `output_path` for saving screenshots, the path is resolved as follows:

- Absolute paths are used as-is
- Paths starting with `~` are expanded to the user's home directory
- Relative paths are resolved relative to the user's home directory

This ensures that screenshots are saved to a location where the MCP server has write permissions.

#### Example

```javascript
// Save screenshot to the user's home directory
await use_mcp_tool({
  server_name: "android-adb",
  tool_name: "take_screenshot_and_save",
  arguments: {
    output_path: "~/screenshot.png"
  }
});

// Save screenshot to an absolute path
await use_mcp_tool({
  server_name: "android-adb",
  tool_name: "take_screenshot_and_save",
  arguments: {
    output_path: "/Users/username/Documents/screenshot.png"
  }
});
```

## License

ISC
