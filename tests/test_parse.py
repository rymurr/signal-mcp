import asyncio

from signal_mcp.main import _parse_receive_output


recv = """
Envelope from: “Bob Sagat” +11234567890 (device: 4) to +15551234567
Timestamp: 1744185564802 (2025-04-09T07:59:24.802Z)
Server timestamps: received: 1744185564847 (2025-04-09T07:59:24.847Z) delivered: 1744185565739 (2025-04-09T07:59:25.739Z)
Sent by unidentified/sealed sender
Received a receipt message
  When: 1744185564802 (2025-04-09T07:59:24.802Z)
  Is read receipt
  Timestamps:
  - 1744185570322 (2025-04-09T07:59:30.322Z)

Envelope from: “Bob Sagat” +11234567890 (device: 4) to +15551234567
Timestamp: 1744185565138 (2025-04-09T07:59:25.138Z)
Server timestamps: received: 1744185565194 (2025-04-09T07:59:25.194Z) delivered: 1744185565739 (2025-04-09T07:59:25.739Z)
Sent by unidentified/sealed sender
Received a typing message
  Action: STARTED
  Timestamp: 1744185565138 (2025-04-09T07:59:25.138Z)

Envelope from: “Bob Sagat” +11234567890 (device: 4) to +15551234567
Timestamp: 1744185565192 (2025-04-09T07:59:25.192Z)
Server timestamps: received: 1744185565302 (2025-04-09T07:59:25.302Z) delivered: 1744185565740 (2025-04-09T07:59:25.740Z)
Sent by unidentified/sealed sender
Received a receipt message
  When: 1744185565192 (2025-04-09T07:59:25.192Z)
  Is delivery receipt
  Timestamps:
  - 1744185570322 (2025-04-09T07:59:30.322Z)

Envelope from: “Bob Sagat” +11234567890 (device: 4) to +15551234567
Timestamp: 1744185565466 (2025-04-09T07:59:25.466Z)
Server timestamps: received: 1744185565586 (2025-04-09T07:59:25.586Z) delivered: 1744185565740 (2025-04-09T07:59:25.740Z)
Sent by unidentified/sealed sender
Message timestamp: 1744185565466 (2025-04-09T07:59:25.466Z)
Body: yo
With profile key

Envelope from: “Bob Sagat” +11234567890 (device: 3) to +15551234567
Timestamp: 1744185572206 (2025-04-09T07:59:32.206Z)
Server timestamps: received: 1744185566038 (2025-04-09T07:59:26.038Z) delivered: 1744185566039 (2025-04-09T07:59:26.039Z)
Sent by unidentified/sealed sender
Received a receipt message
  When: 1744185572206 (2025-04-09T07:59:32.206Z)
  Is delivery receipt
  Timestamps:
  - 1744185570322 (2025-04-09T07:59:30.322Z)

Envelope from: “Bob Sagat” +11234567890 (device: 1) to +15551234567
Timestamp: 1744185569713 (2025-04-09T07:59:29.713Z)
Server timestamps: received: 1744185567862 (2025-04-09T07:59:27.862Z) delivered: 1744185567863 (2025-04-09T07:59:27.863Z)
Sent by unidentified/sealed sender
Received a receipt message
  When: 1744185569713 (2025-04-09T07:59:29.713Z)
  Is delivery receipt
  Timestamps:
  - 1744185570322 (2025-04-09T07:59:30.322Z)
"""


def test_parse_direct_message():
    expected_result = ("yo", "+11234567890", None)

    result = asyncio.run(_parse_receive_output(recv))

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
