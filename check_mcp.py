import asyncio
import os
import mcp
from mcp.client.stdio import StdioServerParameters
from mcp import ClientSession
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def main():
    # Configure the stdio client
    server_params = StdioServerParameters(
        command="python",
        args=[
            "signal_mcp/main.py",
            "--user-id",
            os.environ["SENDER_NUMBER"],
            "--transport",
            "stdio",
        ],
    )
    async with mcp.stdio_client(server_params) as transport:
        stdio, write = transport
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            # List available tools
            response = await session.list_tools()
            print(response.tools)

            # Call a tool to send a message
            send_result = await session.call_tool(
                "send_message_to_user",
                {
                    "message": "Hello from MCP stdio client!",
                    "user_id": os.environ["RECEIVER_NUMBER"],
                },
            )
            print(f"Send result: {send_result}")

            # Receive a message with timeout
            print("Waiting for message...")
            receive_result = await session.call_tool(
                "receive_message",
                {"timeout": 10},  # 5 second timeout
            )

            print(f"Receive result: {receive_result}")

            # Check if we received a message (might be None if timeout)
            if isinstance(receive_result, tuple) and len(receive_result) >= 2:
                message, sender, group = receive_result
                if message and sender:
                    print(f"Received message from {sender}: {message}")
                    if group:
                        print(f"In group: {group}")


if __name__ == "__main__":
    asyncio.run(main())
