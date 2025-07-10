#!/usr/bin/env python3
"""Android ADB MCP Server - Python implementation."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)
from PIL import Image


def check_adb_availability() -> bool:
    """Check if ADB is available in the system PATH."""
    try:
        subprocess.run(
            ["adb", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


async def execute_adb_command(command: str, device_id: Optional[str] = None) -> str:
    """Execute ADB command with proper error handling."""
    device_flag = f"-s {device_id} " if device_id else ""
    full_command = f"adb {device_flag}{command}"
    
    try:
        process = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            stderr_text = stderr.decode('utf-8').strip()
            if stderr_text and "Warning" not in stderr_text:
                raise Exception(f"ADB command failed: {stderr_text}")
        
        return stdout.decode('utf-8').strip()
    except Exception as e:
        raise Exception(f"ADB command failed: {str(e)}")


async def get_connected_devices() -> List[Dict[str, str]]:
    """Get list of connected devices."""
    output = await execute_adb_command("devices")
    lines = output.split('\n')[1:]  # Skip the first line (header)
    
    devices = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
            devices.append({"id": parts[0], "state": parts[1]})
    
    return devices


async def validate_device_id(device_id: Optional[str] = None) -> str:
    """Validate device ID or select the only connected device."""
    devices = await get_connected_devices()
    
    if not devices:
        raise Exception("No Android devices connected")
    
    if device_id:
        device = next((d for d in devices if d["id"] == device_id), None)
        if not device:
            raise Exception(f'Device with ID "{device_id}" not found')
        return device_id
    
    if len(devices) > 1:
        raise Exception("Multiple devices connected. Please specify a device ID")
    
    return devices[0]["id"]


def get_file_extension(format_name: str = "png") -> str:
    """Get file extension for image format."""
    return f".{format_name.lower()}"


def create_temp_file_path(format_name: str = "png") -> str:
    """Create a temporary file path."""
    extension = get_file_extension(format_name)
    return os.path.join(tempfile.gettempdir(), f"adb-screenshot-{int(asyncio.get_event_loop().time() * 1000)}{extension}")


def get_mime_type(format_name: str = "png") -> str:
    """Get MIME type for image format."""
    return f"image/{format_name.lower()}"


async def convert_image_format(input_path: str, output_path: str, format_name: str = "png") -> None:
    """Convert image to specified format using PIL."""
    try:
        normalized_format = format_name.lower()
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Use PIL to convert the image
        with Image.open(input_path) as img:
            # Convert format name for PIL
            pil_format = "JPEG" if normalized_format == "jpg" else normalized_format.upper()
            img.save(output_path, format=pil_format)
            
    except Exception as e:
        raise Exception(f"Failed to convert image: {str(e)}")


def resolve_path(file_path: str) -> str:
    """Resolve path to ensure it's absolute and writable."""
    path = Path(file_path)
    
    # If path is already absolute, return it
    if path.is_absolute():
        return str(path)
    
    # If path starts with ~, expand to user's home directory
    if str(path).startswith("~/") or str(path) == "~":
        return str(Path.home() / str(path)[2:])
    
    # For other relative paths, use the home directory as base
    return str(Path.home() / path)


async def is_directory_writable(dir_path: str) -> bool:
    """Check if a directory is writable."""
    try:
        # Ensure directory exists
        os.makedirs(dir_path, exist_ok=True)
        
        # Try to write a temporary file
        test_file = os.path.join(dir_path, f".write-test-{int(asyncio.get_event_loop().time() * 1000)}")
        with open(test_file, "w") as f:
            f.write("test")
        os.unlink(test_file)
        return True
    except Exception:
        return False


async def copy_image_to_clipboard(image_path: str, format_name: str = "png") -> None:
    """Copy image to clipboard (platform-specific)."""
    platform = sys.platform
    
    try:
        if platform == "darwin":
            # macOS
            cmd = f"osascript -e 'set the clipboard to (read (POSIX file \"{image_path}\") as TIFF picture)'"
            await asyncio.create_subprocess_shell(cmd, check=True)
        elif platform == "win32":
            # Windows
            cmd = f"powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{image_path}'))\""
            await asyncio.create_subprocess_shell(cmd, check=True)
        elif platform.startswith("linux"):
            # Linux (requires xclip)
            cmd = f"xclip -selection clipboard -t image/{format_name} -i \"{image_path}\""
            await asyncio.create_subprocess_shell(cmd, check=True)
        else:
            raise Exception(f"Clipboard operations not supported on platform: {platform}")
    except Exception as e:
        raise Exception(f"Failed to copy image to clipboard: {str(e)}")


class AndroidAdbServer:
    """Android ADB MCP Server implementation."""
    
    def __init__(self):
        """Initialize the server."""
        # Check if ADB is available
        if not check_adb_availability():
            print("ADB is not available. Please install Android SDK Platform Tools and add it to your PATH.", file=sys.stderr)
            sys.exit(1)
        
        self.server = Server("android-adb-server")
    
    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="adb_devices",
                description="Lists all connected Android devices and their connection status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="adb_shell",
                description="Executes shell commands on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target (if multiple devices are connected)",
                        },
                    },
                    "required": ["command"],
                },
            ),
            Tool(
                name="adb_install",
                description="Installs APK files on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to APK file or directory containing APK files",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="adb_uninstall",
                description="Uninstalls an application from a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to uninstall",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
            Tool(
                name="adb_list_packages",
                description="Lists all installed packages on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                        "filter": {
                            "type": "string",
                            "description": "Optional case-insensitive filter to search for specific packages",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="adb_pull",
                description="Pulls files from a connected Android device to the local system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remote_path": {
                            "type": "string",
                            "description": "Path to the file or directory on the device",
                        },
                        "local_path": {
                            "type": "string",
                            "description": "Path where to save the file(s) locally",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["remote_path", "local_path"],
                },
            ),
            Tool(
                name="adb_push",
                description="Pushes files from the local system to a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "local_path": {
                            "type": "string",
                            "description": "Path to the local file or directory",
                        },
                        "remote_path": {
                            "type": "string",
                            "description": "Path on the device where to push the file(s)",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["local_path", "remote_path"],
                },
            ),
            Tool(
                name="launch_app",
                description="Launches an application on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to launch",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
            Tool(
                name="take_screenshot_and_save",
                description="Takes a screenshot and saves it to the local system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output_path": {
                            "type": "string",
                            "description": "Path where to save the screenshot",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                        "format": {
                            "type": "string",
                            "description": "Image format (png, jpg, webp, etc.). Default is png",
                            "enum": ["png", "jpg", "jpeg", "webp", "bmp", "gif"],
                        },
                    },
                    "required": ["output_path"],
                },
            ),
            Tool(
                name="take_screenshot_and_copy_to_clipboard",
                description="Takes a screenshot and copies it to the clipboard",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                        "format": {
                            "type": "string",
                            "description": "Image format (png, jpg, webp, etc.). Default is png",
                            "enum": ["png", "jpg", "jpeg", "webp", "bmp", "gif"],
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="clear_app_data",
                description="Clears all data for a specific application on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to clear data for",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
            Tool(
                name="force_stop_app",
                description="Force stops a running application on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to force stop",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
            Tool(
                name="go_to_home",
                description="Navigates to the home screen on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="open_settings",
                description="Opens the Android Settings app on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="clear_cache_and_restart",
                description="Clears app data and automatically restarts the application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to clear and restart",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
            Tool(
                name="force_restart_app",
                description="Force stops and then restarts an application on a connected Android device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package_name": {
                            "type": "string",
                            "description": "Package name of the application to force restart",
                        },
                        "device_id": {
                            "type": "string",
                            "description": "Specific device ID to target",
                        },
                    },
                    "required": ["package_name"],
                },
            ),
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool with the given arguments."""
        try:
            if name == "adb_devices":
                return await self.handle_adb_devices()
            elif name == "adb_shell":
                return await self.handle_adb_shell(arguments)
            elif name == "adb_install":
                return await self.handle_adb_install(arguments)
            elif name == "adb_uninstall":
                return await self.handle_adb_uninstall(arguments)
            elif name == "adb_list_packages":
                return await self.handle_adb_list_packages(arguments)
            elif name == "adb_pull":
                return await self.handle_adb_pull(arguments)
            elif name == "adb_push":
                return await self.handle_adb_push(arguments)
            elif name == "launch_app":
                return await self.handle_launch_app(arguments)
            elif name == "take_screenshot_and_save":
                return await self.handle_take_screenshot_and_save(arguments)
            elif name == "take_screenshot_and_copy_to_clipboard":
                return await self.handle_take_screenshot_and_copy_to_clipboard(arguments)
            elif name == "clear_app_data":
                return await self.handle_clear_app_data(arguments)
            elif name == "force_stop_app":
                return await self.handle_force_stop_app(arguments)
            elif name == "go_to_home":
                return await self.handle_go_to_home(arguments)
            elif name == "open_settings":
                return await self.handle_open_settings(arguments)
            elif name == "clear_cache_and_restart":
                return await self.handle_clear_cache_and_restart(arguments)
            elif name == "force_restart_app":
                return await self.handle_force_restart_app(arguments)
            else:
                raise Exception(f"Unknown tool: {name}")
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_adb_devices(self) -> List[TextContent]:
        """Handle adb_devices tool call."""
        devices = await get_connected_devices()
        return [TextContent(type="text", text=json.dumps(devices, indent=2))]
    
    async def handle_adb_shell(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_shell tool call."""
        if not isinstance(args.get("command"), str):
            raise Exception("Invalid parameters: command is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command(f"shell {args['command']}", device_id)
        
        return [TextContent(type="text", text=output)]
    
    async def handle_adb_install(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_install tool call."""
        if not isinstance(args.get("path"), str):
            raise Exception("Invalid parameters: path is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        path = args["path"]
        
        # Check if path contains wildcards or is a directory
        is_multiple = "*" in path or (os.path.exists(path) and os.path.isdir(path))
        
        command = f"install-multiple {path}" if is_multiple else f"install {path}"
        output = await execute_adb_command(command, device_id)
        
        return [TextContent(type="text", text=output)]
    
    async def handle_adb_uninstall(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_uninstall tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command(f"uninstall {args['package_name']}", device_id)
        
        return [TextContent(type="text", text=output)]
    
    async def handle_adb_list_packages(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_list_packages tool call."""
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        filter_text = args.get("filter", "").lower() if args.get("filter") else None
        
        output = await execute_adb_command("shell pm list packages", device_id)
        
        # Parse the output to extract package names
        packages = [
            line.strip().replace("package:", "")
            for line in output.split("\n")
            if line.strip() and line.strip().startswith("package:")
        ]
        
        # Apply case-insensitive filter if provided
        if filter_text:
            packages = [pkg for pkg in packages if filter_text in pkg.lower()]
        
        return [TextContent(type="text", text=json.dumps(packages, indent=2))]
    
    async def handle_adb_pull(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_pull tool call."""
        if not isinstance(args.get("remote_path"), str) or not isinstance(args.get("local_path"), str):
            raise Exception("Invalid parameters: remote_path and local_path are required and must be strings")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        
        # Resolve the local path to ensure it's absolute and in a writable location
        resolved_local_path = resolve_path(args["local_path"])
        
        # Ensure the directory exists
        local_dir = os.path.dirname(resolved_local_path)
        try:
            os.makedirs(local_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create directory: {str(e)}")
        
        # Check if the directory is writable
        if not await is_directory_writable(local_dir):
            raise Exception(f"Directory is not writable: {local_dir}. Try using an absolute path or a path in your home directory.")
        
        try:
            output = await execute_adb_command(f'pull "{args["remote_path"]}" "{resolved_local_path}"', device_id)
            
            return [TextContent(type="text", text=f"File pulled successfully to: {resolved_local_path}\n{output}")]
        except Exception as e:
            raise Exception(f"Failed to pull file: {str(e)}. Try using an absolute path or a path in your home directory.")
    
    async def handle_adb_push(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle adb_push tool call."""
        if not isinstance(args.get("local_path"), str) or not isinstance(args.get("remote_path"), str):
            raise Exception("Invalid parameters: local_path and remote_path are required and must be strings")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        
        # Resolve the local path to ensure it's absolute
        resolved_local_path = resolve_path(args["local_path"])
        
        # Check if the local file exists
        if not os.path.exists(resolved_local_path):
            raise Exception(f"Local file does not exist: {resolved_local_path}")
        
        output = await execute_adb_command(f'push "{resolved_local_path}" "{args["remote_path"]}"', device_id)
        
        return [TextContent(type="text", text=output)]
    
    async def handle_launch_app(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle launch_app tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        
        try:
            # Try to launch the default activity
            output = await execute_adb_command(
                f"shell monkey -p {args['package_name']} -c android.intent.category.LAUNCHER 1",
                device_id
            )
            
            return [TextContent(type="text", text=f"App launched: {args['package_name']}\n{output}")]
        except Exception as e:
            # If the default activity launch fails, try to determine the main activity
            try:
                package_info = await execute_adb_command(
                    f'shell dumpsys package {args["package_name"]} | grep -A 1 "android.intent.action.MAIN"',
                    device_id
                )
                
                # Simple regex replacement - look for activity pattern
                import re
                activity_match = re.search(r'([a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', package_info)
                if activity_match:
                    activity = activity_match.group(1)
                    output = await execute_adb_command(f"shell am start -n {activity}", device_id)
                    
                    return [TextContent(type="text", text=f"App launched with activity: {activity}\n{output}")]
                
                raise Exception("Could not determine main activity")
            except Exception:
                raise Exception(f"Failed to launch app: {str(e)}")
    
    async def handle_take_screenshot_and_save(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle take_screenshot_and_save tool call."""
        if not isinstance(args.get("output_path"), str):
            raise Exception("Invalid parameters: output_path is required and must be a string")
        
        # Validate device ID if provided
        device_id = args.get("device_id")
        if device_id:
            await validate_device_id(device_id)
        
        # Resolve the output path to ensure it's absolute and in a writable location
        resolved_output_path = resolve_path(args["output_path"])
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(resolved_output_path)
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create directory: {str(e)}")
        
        # Check if the directory is writable
        if not await is_directory_writable(output_dir):
            raise Exception(f"Directory is not writable: {output_dir}. Try using an absolute path or a path in your home directory.")
        
        try:
            # Use the direct ADB command
            device_flag = f"-s {device_id} " if device_id else ""
            cmd = f"adb {device_flag}exec-out screencap -p > \"{resolved_output_path}\""
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception("Failed to take screenshot")
            
            # Convert to the desired format if not PNG
            format_name = args.get("format", "png").lower()
            if format_name != "png":
                temp_png_path = resolved_output_path
                format_output_path = resolved_output_path.replace(".png", get_file_extension(format_name))
                
                await convert_image_format(temp_png_path, format_output_path, format_name)
                
                # Remove the original PNG file
                os.unlink(temp_png_path)
                resolved_output_path = format_output_path
            
            return [TextContent(type="text", text=f"Screenshot saved to: {resolved_output_path} in {format_name} format")]
        except Exception as e:
            raise Exception(f"Failed to take screenshot: {str(e)}. Try using an absolute path or a path in your home directory.")
    
    async def handle_take_screenshot_and_copy_to_clipboard(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle take_screenshot_and_copy_to_clipboard tool call."""
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        format_name = args.get("format", "png").lower()
        temp_local_path = create_temp_file_path(format_name)
        
        try:
            # Take screenshot using the direct method
            device_flag = f"-s {device_id} " if device_id else ""
            temp_png_path = temp_local_path.replace(f".{format_name}", ".png")
            
            cmd = f"adb {device_flag}exec-out screencap -p > \"{temp_png_path}\""
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception("Failed to take screenshot")
            
            # Convert to desired format if not PNG
            if format_name != "png":
                await convert_image_format(temp_png_path, temp_local_path, format_name)
                os.unlink(temp_png_path)
            else:
                # If PNG, just rename the file
                os.rename(temp_png_path, temp_local_path)
            
            # Copy to clipboard
            await copy_image_to_clipboard(temp_local_path, format_name)
            
            return [TextContent(type="text", text=f"Screenshot copied to clipboard in {format_name} format")]
        except Exception as e:
            raise Exception(f"Failed to take screenshot: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_local_path):
                os.unlink(temp_local_path)
    
    async def handle_clear_app_data(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle clear_app_data tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command(f"shell pm clear {args['package_name']}", device_id)
        
        return [TextContent(type="text", text=f"App data cleared for {args['package_name']}\n{output}")]
    
    async def handle_force_stop_app(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle force_stop_app tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command(f"shell am force-stop {args['package_name']}", device_id)
        
        return [TextContent(type="text", text=f"App force stopped: {args['package_name']}\n{output}")]
    
    async def handle_go_to_home(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle go_to_home tool call."""
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command("shell input keyevent KEYCODE_HOME", device_id)
        
        return [TextContent(type="text", text=f"Navigated to home screen\n{output}")]
    
    async def handle_open_settings(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle open_settings tool call."""
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        output = await execute_adb_command("shell am start -a android.settings.SETTINGS", device_id)
        
        return [TextContent(type="text", text=f"Settings app opened\n{output}")]
    
    async def handle_clear_cache_and_restart(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle clear_cache_and_restart tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        package_name = args["package_name"]
        
        # Clear app data
        clear_output = await execute_adb_command(f"shell pm clear {package_name}", device_id)
        
        # Wait a bit before starting
        await asyncio.sleep(1)
        
        # Start the app
        try:
            start_output = await execute_adb_command(
                f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1",
                device_id
            )
        except Exception:
            # Fallback method if monkey fails
            try:
                package_info = await execute_adb_command(
                    f'shell dumpsys package {package_name} | grep -A 1 "android.intent.action.MAIN"',
                    device_id
                )
                import re
                activity_match = re.search(r'([a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', package_info)
                if activity_match:
                    activity = activity_match.group(1)
                    start_output = await execute_adb_command(f"shell am start -n {activity}", device_id)
                else:
                    start_output = "Could not determine main activity to restart"
            except Exception as e:
                start_output = f"Failed to restart app: {str(e)}"
        
        return [TextContent(type="text", text=f"App data cleared and restarted: {package_name}\nClear: {clear_output}\nStart: {start_output}")]
    
    async def handle_force_restart_app(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle force_restart_app tool call."""
        if not isinstance(args.get("package_name"), str):
            raise Exception("Invalid parameters: package_name is required and must be a string")
        
        device_id = await validate_device_id(args.get("device_id")) if args.get("device_id") else None
        package_name = args["package_name"]
        
        # Force stop the app
        stop_output = await execute_adb_command(f"shell am force-stop {package_name}", device_id)
        
        # Wait a bit before starting
        await asyncio.sleep(1)
        
        # Start the app
        try:
            start_output = await execute_adb_command(
                f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1",
                device_id
            )
        except Exception:
            # Fallback method if monkey fails
            try:
                package_info = await execute_adb_command(
                    f'shell dumpsys package {package_name} | grep -A 1 "android.intent.action.MAIN"',
                    device_id
                )
                import re
                activity_match = re.search(r'([a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', package_info)
                if activity_match:
                    activity = activity_match.group(1)
                    start_output = await execute_adb_command(f"shell am start -n {activity}", device_id)
                else:
                    start_output = "Could not determine main activity to restart"
            except Exception as e:
                start_output = f"Failed to restart app: {str(e)}"
        
        return [TextContent(type="text", text=f"App force restarted: {package_name}\nStop: {stop_output}\nStart: {start_output}")]
    
    async def run(self):
        """Run the server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.list_tools,
                self.call_tool,
            )


def main():
    """Main entry point."""
    server = AndroidAdbServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()