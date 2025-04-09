#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp",
# ]
# ///
from mcp.server.fastmcp import FastMCP
from typing import Optional, Tuple, Dict, Union, Any
import asyncio
import subprocess
import shlex
import argparse
from dataclasses import dataclass
import logging

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(name="signal-cli")
logger.info("Initialized FastMCP server for signal-cli")


@dataclass
class SignalConfig:
    """Configuration for Signal CLI."""

    user_id: str = ""  # The user's Signal phone number
    transport: str = "sse"


@dataclass
class MessageResponse:
    """Structured result for received messages."""

    message: Optional[str] = None
    sender_id: Optional[str] = None
    group_name: Optional[str] = None
    error: Optional[str] = None


class SignalError(Exception):
    """Base exception for Signal-related errors."""

    pass


class SignalCLIError(SignalError):
    """Exception raised when signal-cli command fails."""

    pass


SuccessResponse = Dict[str, str]
ErrorResponse = Dict[str, str]

# Global config instance
config = SignalConfig()


async def _run_signal_cli(cmd: str) -> Tuple[str, str, int | None]:
    """Helper method to run a signal-cli command."""
    logger.debug(f"Executing signal-cli command: {cmd}")
    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        stdout_str, stderr_str = stdout.decode(), stderr.decode()

        if process.returncode != 0:
            logger.warning(
                f"signal-cli command failed with return code {process.returncode}"
            )
            logger.warning(f"stderr: {stderr_str}")
        else:
            logger.debug("signal-cli command completed successfully")

        return stdout_str, stderr_str, process.returncode

    except Exception as e:
        logger.error(f"Error running signal-cli command: {str(e)}", exc_info=True)
        raise SignalCLIError(f"Failed to run signal-cli: {str(e)}")


async def _get_group_id(group_name: str) -> Optional[str]:
    """Get the group name for a given group name."""
    logger.info(f"Looking up group with name: {group_name}")

    list_cmd = f"signal-cli -u {shlex.quote(config.user_id)} listGroups"
    stdout, stderr, return_code = await _run_signal_cli(list_cmd)

    if return_code != 0:
        logger.error(f"Error listing groups: {stderr}")
        return None

    # Parse the output to find the group name
    for line in stdout.split("\n"):
        if "Name: " in line and group_name in line:
            logger.info(f"Found group: {group_name}")
            return group_name

    logger.error(f"Could not find group with name: {group_name}")
    return None


async def _send_message(message: str, target: str, is_group: bool = False) -> bool:
    """Send a message to either a user or group."""
    target_type = "group" if is_group else "user"
    logger.info(f"Sending message to {target_type}: {target}")

    flag = "-g" if is_group else ""
    cmd = f"signal-cli -u {shlex.quote(config.user_id)} send {flag} {shlex.quote(target)} -m {shlex.quote(message)}"

    try:
        _, stderr, return_code = await _run_signal_cli(cmd)

        if return_code == 0:
            logger.info(f"Successfully sent message to {target_type}: {target}")
            return True
        else:
            logger.error(f"Error sending message to {target_type}: {stderr}")
            return False
    except SignalCLIError as e:
        logger.error(f"Failed to send message to {target_type}: {str(e)}")
        return False


async def _parse_receive_output(
    stdout: str,
) -> Optional[MessageResponse]:
    """Parse the output of signal-cli receive command."""
    logger.debug("Parsing received message output")

    lines = stdout.split("\n")

    # Process each envelope section separately
    current_envelope: Dict[str, Any] = {}
    current_sender: Optional[str] = None

    for i, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        if line.startswith("Envelope from:"):
            # Start of a new envelope block
            current_envelope = {}

            # Extract phone number using a straightforward approach
            # Format: Envelope from: "Bob Sagat" +11234567890 (device: 4) to +15551234567
            parts = line.split("+")
            if len(parts) > 1:
                # Get the phone number part
                phone_part = parts[1].split()[0]
                current_sender = "+" + phone_part
                current_envelope["sender"] = current_sender
                logger.debug(f"Found sender: {current_sender}")

        elif line.startswith("Body:"):
            # Found a message body
            if current_envelope:
                message_body = line[5:].strip()
                current_envelope["message"] = message_body
                current_envelope["has_body"] = True
                logger.debug(f"Found message body: {message_body}")

                # If we have a valid message with body, return it
                if current_envelope.get("has_body") and "sender" in current_envelope:
                    sender = current_envelope["sender"]
                    msg = current_envelope["message"]
                    group = current_envelope.get("group")

                    if isinstance(sender, str) and isinstance(msg, str):
                        logger.info(
                            f"Successfully parsed message from {sender}"
                            + (f" in group {group}" if group else "")
                        )
                        return MessageResponse(
                            message=msg, sender_id=sender, group_name=group
                        )

        elif line.startswith("Group info:"):
            if current_envelope:
                current_envelope["in_group"] = True

        elif (
            line.startswith("Name:")
            and current_envelope
            and current_envelope.get("in_group")
        ):
            group_name = line[5:].strip()
            current_envelope["group"] = group_name
            logger.debug(f"Found group name: {group_name}")

    logger.warning("Failed to parse message from output")
    return None


@mcp.tool()
async def send_message_to_user(
    message: str, user_id: str
) -> Union[SuccessResponse, ErrorResponse]:
    """Send a message to a specific user using signal-cli."""
    logger.info(f"Tool called: send_message_to_user for user {user_id}")

    try:
        success = await _send_message(message, user_id, is_group=False)
        if success:
            logger.info(f"Successfully sent message to user {user_id}")
            return {"message": "Message sent successfully"}
        logger.error(f"Failed to send message to user {user_id}")
        return {"error": "Failed to send message"}
    except Exception as e:
        logger.error(f"Error in send_message_to_user: {str(e)}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def send_message_to_group(
    message: str, group_id: str
) -> Union[SuccessResponse, ErrorResponse]:
    """Send a message to a group using signal-cli."""
    logger.info(f"Tool called: send_message_to_group for group {group_id}")

    try:
        group_name = await _get_group_id(group_id)
        if not group_name:
            logger.error(f"Could not find group: {group_id}")
            return {"error": f"Could not find group: {group_id}"}

        success = await _send_message(message, group_name, is_group=True)
        if success:
            logger.info(f"Successfully sent message to group {group_id}")
            return {"message": "Message sent successfully"}
        logger.error(f"Failed to send message to group {group_id}")
        return {"error": "Failed to send message"}
    except Exception as e:
        logger.error(f"Error in send_message_to_group: {str(e)}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def receive_message(timeout: float) -> MessageResponse:
    """Wait for and receive a message using signal-cli."""
    logger.info(f"Tool called: receive_message with timeout {timeout}s")

    try:
        cmd = f"signal-cli -u {shlex.quote(config.user_id)} receive --timeout {int(timeout)}"

        stdout, stderr, return_code = await _run_signal_cli(cmd)

        if return_code != 0:
            if "timeout" in stderr.lower():
                logger.info("Receive timeout reached with no messages")
                return MessageResponse()
            else:
                logger.error(f"Error receiving message: {stderr}")
                return MessageResponse(error=f"Failed to receive message: {stderr}")

        if not stdout.strip():
            logger.info("No message received within timeout")
            return MessageResponse()

        result = await _parse_receive_output(stdout)
        if result:
            logger.info(
                f"Successfully received message from {result.sender_id}"
                + (f" in group {result.group_name}" if result.group_name else "")
            )
            return result
        else:
            logger.error("Received message but couldn't parse the output format")
            return MessageResponse(error="Failed to parse message output")

    except Exception as e:
        logger.error(f"Error in receive_message: {str(e)}", exc_info=True)
        return MessageResponse(error=str(e))


def initialize_server() -> SignalConfig:
    """Initialize the Signal server with configuration."""
    logger.info("Initializing Signal server")

    parser = argparse.ArgumentParser(description="Run the Signal MCP server")
    parser.add_argument(
        "--user-id", required=True, help="Signal phone number for the user"
    )
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport to use for communication with the client. (default: sse)",
    )

    args = parser.parse_args()
    logger.info(f"Parsed arguments: user_id={args.user_id}, transport={args.transport}")

    # Set global config
    config.user_id = args.user_id
    config.transport = args.transport

    logger.info(f"Initialized Signal server for user: {config.user_id}")
    return config


def run_mcp_server():
    """Run the MCP server in the current event loop."""
    config = initialize_server()

    transport = config.transport
    logger.info(f"Starting MCP server with transport: {transport}")

    return transport


def main():
    """Main function to run the Signal MCP server."""
    logger.info("Starting Signal MCP server")
    try:
        transport = run_mcp_server()
        mcp.run(transport)
    except Exception as e:
        logger.error(f"Error running Signal MCP server: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Signal MCP server shutting down")


if __name__ == "__main__":
    main()
