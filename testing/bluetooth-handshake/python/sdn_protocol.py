import time
import machine

# Pre-allocate a fixed 32-byte response tray once in memory at boot.
# This ensures we never fragment RAM when responding to BLE commands.
_response_buffer = bytearray(32)

def process_command(opcode: int) -> bytearray:
    """
    Accepts a raw numeric opcode, executes the corresponding system task,
    and returns a sliced view of our static memory buffer.
    """
    
    # Command 0x01: Ping Status
    if opcode == 0x01:
        # Load "PONG" into the start of the buffer
        _response_buffer[0:4] = b"PONG"
        # Return a zero-allocation slice of exactly those 4 bytes
        return memoryview(_response_buffer)[0:4]
        
    # Command 0x02: Query Uptime
    elif opcode == 0x02:
        # Get internal CPU milliseconds since boot
        uptime_ms = time.ticks_ms()
        uptime_str = str(uptime_ms).encode('utf-8')
        length = len(uptime_str)
        
        _response_buffer[0:length] = uptime_str
        return memoryview(_response_buffer)[0:length]
        
    # Command 0x03: Identify Node
    elif opcode == 0x03:
        # For now, a distinct static identity layout
        identity = b"NODE-ESP32-SGN01"
        length = len(identity)
        
        _response_buffer[0:length] = identity
        return memoryview(_response_buffer)[0:length]
        
    # Unknown Command Fallback
    else:
        _response_buffer[0:5] = b"ERROR"
        return memoryview(_response_buffer)[0:5]
