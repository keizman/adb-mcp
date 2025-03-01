#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { exec, execSync } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const execAsync = promisify(exec);

// Check if ADB is available
function checkAdbAvailability(): boolean {
  try {
    execSync('adb version', { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

// Execute ADB command with proper error handling
async function executeAdbCommand(
  command: string,
  deviceId?: string
): Promise<string> {
  const deviceFlag = deviceId ? `-s ${deviceId} ` : '';
  const fullCommand = `adb ${deviceFlag}${command}`;
  
  try {
    const { stdout, stderr } = await execAsync(fullCommand);
    if (stderr && !stderr.includes('Warning')) {
      throw new Error(stderr);
    }
    return stdout.trim();
  } catch (error) {
    if (error instanceof Error) {
      throw new McpError(
        ErrorCode.InternalError,
        `ADB command failed: ${error.message}`
      );
    }
    throw error;
  }
}

// Get list of connected devices
async function getConnectedDevices(): Promise<{ id: string; state: string }[]> {
  const output = await executeAdbCommand('devices');
  const lines = output.split('\n').slice(1); // Skip the first line (header)
  
  const devices = lines
    .map(line => {
      const [id, state] = line.trim().split(/\s+/);
      return id && state ? { id, state } : null;
    })
    .filter((device): device is { id: string; state: string } => device !== null);
  
  return devices;
}

// Validate device ID or select the only connected device
async function validateDeviceId(deviceId?: string): Promise<string> {
  const devices = await getConnectedDevices();
  
  if (devices.length === 0) {
    throw new McpError(
      ErrorCode.InternalError,
      'No Android devices connected'
    );
  }
  
  if (deviceId) {
    const device = devices.find(d => d.id === deviceId);
    if (!device) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Device with ID "${deviceId}" not found`
      );
    }
    return deviceId;
  }
  
  if (devices.length > 1) {
    throw new McpError(
      ErrorCode.InvalidParams,
      'Multiple devices connected. Please specify a device ID'
    );
  }
  
  return devices[0].id;
}

// Create a temporary file path
function createTempFilePath(extension: string): string {
  return path.join(os.tmpdir(), `adb-screenshot-${Date.now()}${extension}`);
}

// Copy image to clipboard based on platform
async function copyImageToClipboard(imagePath: string): Promise<void> {
  const platform = os.platform();
  
  try {
    if (platform === 'darwin') {
      // macOS
      await execAsync(`osascript -e 'set the clipboard to (read (POSIX file "${imagePath}") as JPEG picture)'`);
    } else if (platform === 'win32') {
      // Windows
      await execAsync(`powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('${imagePath}'))"`);
    } else if (platform === 'linux') {
      // Linux
      await execAsync(`xclip -selection clipboard -t image/png -i "${imagePath}"`);
    } else {
      throw new Error(`Unsupported platform: ${platform}`);
    }
  } catch (error) {
    if (error instanceof Error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to copy image to clipboard: ${error.message}`
      );
    }
    throw error;
  }
}

class AndroidAdbServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'android-adb-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Check if ADB is available
    if (!checkAdbAvailability()) {
      console.error('ADB is not available. Please install ADB and add it to your PATH.');
      process.exit(1);
    }

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'adb_devices',
          description: 'Lists all connected Android devices and their connection status',
          inputSchema: {
            type: 'object',
            properties: {},
            required: [],
          },
        },
        {
          name: 'adb_shell',
          description: 'Executes shell commands on a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              command: {
                type: 'string',
                description: 'The shell command to execute',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target (if multiple devices are connected)',
              },
            },
            required: ['command'],
          },
        },
        {
          name: 'adb_install',
          description: 'Installs APK files on a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              path: {
                type: 'string',
                description: 'Path to APK file or directory containing APK files',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['path'],
          },
        },
        {
          name: 'adb_uninstall',
          description: 'Uninstalls an application from a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              package_name: {
                type: 'string',
                description: 'Package name of the application to uninstall',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['package_name'],
          },
        },
        {
          name: 'adb_list_packages',
          description: 'Lists all installed packages on a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
              filter: {
                type: 'string',
                description: 'Optional case-insensitive filter to search for specific packages',
              },
            },
            required: [],
          },
        },
        {
          name: 'adb_pull',
          description: 'Pulls files from a connected Android device to the local system',
          inputSchema: {
            type: 'object',
            properties: {
              remote_path: {
                type: 'string',
                description: 'Path to the file or directory on the device',
              },
              local_path: {
                type: 'string',
                description: 'Path where to save the file(s) locally',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['remote_path', 'local_path'],
          },
        },
        {
          name: 'adb_push',
          description: 'Pushes files from the local system to a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              local_path: {
                type: 'string',
                description: 'Path to the local file or directory',
              },
              remote_path: {
                type: 'string',
                description: 'Path on the device where to push the file(s)',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['local_path', 'remote_path'],
          },
        },
        {
          name: 'launch_app',
          description: 'Launches an application on a connected Android device',
          inputSchema: {
            type: 'object',
            properties: {
              package_name: {
                type: 'string',
                description: 'Package name of the application to launch',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['package_name'],
          },
        },
        {
          name: 'take_screenshot_and_save',
          description: 'Takes a screenshot and saves it to the local system',
          inputSchema: {
            type: 'object',
            properties: {
              output_path: {
                type: 'string',
                description: 'Path where to save the screenshot',
              },
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: ['output_path'],
          },
        },
        {
          name: 'take_screenshot_and_copy_to_clipboard',
          description: 'Takes a screenshot and copies it to the clipboard',
          inputSchema: {
            type: 'object',
            properties: {
              device_id: {
                type: 'string',
                description: 'Specific device ID to target',
              },
            },
            required: [],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'adb_devices':
          return this.handleAdbDevices();
        case 'adb_shell':
          return this.handleAdbShell(args);
        case 'adb_install':
          return this.handleAdbInstall(args);
        case 'adb_uninstall':
          return this.handleAdbUninstall(args);
        case 'adb_list_packages':
          return this.handleAdbListPackages(args);
        case 'adb_pull':
          return this.handleAdbPull(args);
        case 'adb_push':
          return this.handleAdbPush(args);
        case 'launch_app':
          return this.handleLaunchApp(args);
        case 'take_screenshot_and_save':
          return this.handleTakeScreenshotAndSave(args);
        case 'take_screenshot_and_copy_to_clipboard':
          return this.handleTakeScreenshotAndCopyToClipboard(args);
        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${name}`
          );
      }
    });
  }

  private async handleAdbDevices() {
    const devices = await getConnectedDevices();
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(devices, null, 2),
        },
      ],
    };
  }

  private async handleAdbShell(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.command !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: command is required and must be a string'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const output = await executeAdbCommand(`shell ${args.command}`, deviceId);
    
    return {
      content: [
        {
          type: 'text',
          text: output,
        },
      ],
    };
  }

  private async handleAdbInstall(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.path !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: path is required and must be a string'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const path = args.path;

    // Check if path contains wildcards or is a directory
    const isMultiple = path.includes('*') || 
                       (fs.existsSync(path) && fs.statSync(path).isDirectory());

    let command = isMultiple ? `install-multiple ${path}` : `install ${path}`;
    const output = await executeAdbCommand(command, deviceId);
    
    return {
      content: [
        {
          type: 'text',
          text: output,
        },
      ],
    };
  }

  private async handleAdbUninstall(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.package_name !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: package_name is required and must be a string'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const output = await executeAdbCommand(`uninstall ${args.package_name}`, deviceId);
    
    return {
      content: [
        {
          type: 'text',
          text: output,
        },
      ],
    };
  }

  private async handleAdbListPackages(args: any) {
    if (typeof args !== 'object' && args !== null) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: expected an object'
      );
    }

    const deviceId = args?.device_id ? await validateDeviceId(args.device_id) : undefined;
    const filter = args?.filter ? String(args.filter).toLowerCase() : undefined;
    const output = await executeAdbCommand('shell pm list packages', deviceId);
    
    // Parse the output to extract package names
    let packages = output
      .split('\n')
      .map(line => line.trim().replace('package:', ''))
      .filter(Boolean);
    
    // Apply case-insensitive filter if provided
    if (filter) {
      packages = packages.filter(pkg => pkg.toLowerCase().includes(filter));
    }
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(packages, null, 2),
        },
      ],
    };
  }

  private async handleAdbPull(args: any) {
    if (
      typeof args !== 'object' || 
      args === null || 
      typeof args.remote_path !== 'string' || 
      typeof args.local_path !== 'string'
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: remote_path and local_path are required and must be strings'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const output = await executeAdbCommand(
      `pull "${args.remote_path}" "${args.local_path}"`, 
      deviceId
    );
    
    return {
      content: [
        {
          type: 'text',
          text: output,
        },
      ],
    };
  }

  private async handleAdbPush(args: any) {
    if (
      typeof args !== 'object' || 
      args === null || 
      typeof args.local_path !== 'string' || 
      typeof args.remote_path !== 'string'
    ) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: local_path and remote_path are required and must be strings'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const output = await executeAdbCommand(
      `push "${args.local_path}" "${args.remote_path}"`, 
      deviceId
    );
    
    return {
      content: [
        {
          type: 'text',
          text: output,
        },
      ],
    };
  }

  private async handleLaunchApp(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.package_name !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: package_name is required and must be a string'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    
    try {
      // Try to launch the default activity
      const output = await executeAdbCommand(
        `shell monkey -p ${args.package_name} -c android.intent.category.LAUNCHER 1`, 
        deviceId
      );
      
      return {
        content: [
          {
            type: 'text',
            text: `App launched: ${args.package_name}\n${output}`,
          },
        ],
      };
    } catch (error) {
      // If the default activity launch fails, try to determine the main activity
      try {
        const packageInfo = await executeAdbCommand(
          `shell dumpsys package ${args.package_name} | grep -A 1 "android.intent.action.MAIN"`,
          deviceId
        );
        
        const activityMatch = packageInfo.match(/([a-zA-Z0-9_.]+\/[a-zA-Z0-9_.]+)/);
        if (activityMatch) {
          const activity = activityMatch[1];
          const output = await executeAdbCommand(
            `shell am start -n ${activity}`,
            deviceId
          );
          
          return {
            content: [
              {
                type: 'text',
                text: `App launched with activity: ${activity}\n${output}`,
              },
            ],
          };
        }
        
        throw new Error('Could not determine main activity');
      } catch (activityError) {
        if (error instanceof Error) {
          throw new McpError(
            ErrorCode.InternalError,
            `Failed to launch app: ${error.message}`
          );
        }
        throw error;
      }
    }
  }

  private async handleTakeScreenshotAndSave(args: any) {
    if (typeof args !== 'object' || args === null || typeof args.output_path !== 'string') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: output_path is required and must be a string'
      );
    }

    const deviceId = args.device_id ? await validateDeviceId(args.device_id) : undefined;
    const tempDevicePath = '/sdcard/screenshot.png';
    const tempLocalPath = createTempFilePath('.png');
    
    try {
      // Take screenshot on device
      await executeAdbCommand(`shell screencap -p ${tempDevicePath}`, deviceId);
      
      // Pull screenshot to local temp file
      await executeAdbCommand(`pull ${tempDevicePath} ${tempLocalPath}`, deviceId);
      
      // Clean up device temp file
      await executeAdbCommand(`shell rm ${tempDevicePath}`, deviceId);
      
      // Ensure output directory exists
      const outputDir = path.dirname(args.output_path);
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      // Move temp file to output path
      fs.copyFileSync(tempLocalPath, args.output_path);
      
      return {
        content: [
          {
            type: 'text',
            text: `Screenshot saved to: ${args.output_path}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof Error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to take screenshot: ${error.message}`
        );
      }
      throw error;
    } finally {
      // Clean up local temp file
      if (fs.existsSync(tempLocalPath)) {
        fs.unlinkSync(tempLocalPath);
      }
    }
  }

  private async handleTakeScreenshotAndCopyToClipboard(args: any) {
    if (typeof args !== 'object' && args !== null) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Invalid parameters: expected an object'
      );
    }

    const deviceId = args?.device_id ? await validateDeviceId(args.device_id) : undefined;
    const tempDevicePath = '/sdcard/screenshot.png';
    const tempLocalPath = createTempFilePath('.png');
    
    try {
      // Take screenshot on device
      await executeAdbCommand(`shell screencap -p ${tempDevicePath}`, deviceId);
      
      // Pull screenshot to local temp file
      await executeAdbCommand(`pull ${tempDevicePath} ${tempLocalPath}`, deviceId);
      
      // Clean up device temp file
      await executeAdbCommand(`shell rm ${tempDevicePath}`, deviceId);
      
      // Copy to clipboard
      await copyImageToClipboard(tempLocalPath);
      
      return {
        content: [
          {
            type: 'text',
            text: 'Screenshot copied to clipboard',
          },
        ],
      };
    } catch (error) {
      if (error instanceof Error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to take screenshot: ${error.message}`
        );
      }
      throw error;
    } finally {
      // Clean up local temp file
      if (fs.existsSync(tempLocalPath)) {
        fs.unlinkSync(tempLocalPath);
      }
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Android ADB MCP server running on stdio');
  }
}

const server = new AndroidAdbServer();
server.run().catch(console.error);