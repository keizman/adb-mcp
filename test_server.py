#!/usr/bin/env python3
"""Test script for the Android ADB MCP Server."""

import asyncio
from src.android_adb_mcp_server.main import AndroidAdbServer


async def test_server():
    """Test the server initialization and tool listing."""
    try:
        server = AndroidAdbServer()
        print("✓ Server initialized successfully")
        
        # Test listing tools
        tools = await server.list_tools()
        print(f"✓ Tools listed successfully: {len(tools)} tools available")
        
        # Print tool names
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Main test function."""
    print("Testing Android ADB MCP Server...")
    print("=" * 50)
    
    success = asyncio.run(test_server())
    
    if success:
        print("\n✓ All tests passed!")
        print("\nTo run the server, use: uv run android-adb-mcp-server")
    else:
        print("\n✗ Tests failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())