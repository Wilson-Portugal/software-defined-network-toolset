import bluetooth
import time
import struct
from micropython import const

# BLE Event constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# Flags for building raw advertising data bytes
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)

# Exact matching 128-bit IDs for the web browser handshake
SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F333-E0A9-E50E24DCCA9E")
CHAR_UUID    = bluetooth.UUID("6E400002-B5A3-F333-E0A9-E50E24DCCA9E")

class ESP32_BLE_Echo:
    def __init__(self, name="ESP32-Echo"):
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        
        # Register our Service and Characteristic
        char = (CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY,)
        service = (SERVICE_UUID, (char,),)
        ((self.char_handle,),) = self.ble.gatts_register_services((service,))
        
        self.connections = set()
        print("BLE initialized successfully.")
        self.advertise()

    def advertise(self):
        # 1. PRIMARY ADV DATA: Must contain Flags and Service UUID so the filter hits
        adv_payload = bytearray()
        adv_payload += struct.pack("BB", 2, _ADV_TYPE_FLAGS) + b"\x06"
        
        uuid_bytes = bytes(SERVICE_UUID)
        adv_payload += struct.pack("BB", len(uuid_bytes) + 1, _ADV_TYPE_UUID128_COMPLETE) + uuid_bytes
        
        # 2. SCAN RESPONSE DATA: Move the device name here to prevent -18 memory overflow
        resp_payload = bytearray()
        resp_payload += struct.pack("BB", len(self.name) + 1, _ADV_TYPE_NAME) + self.name.encode("utf-8")
        
        # Fire up the radio broadcasting with both buffers assigned (Interval: 100ms)
        self.ble.gap_advertise(100000, adv_data=adv_payload, resp_data=resp_payload)
        print("Radio transmitting: Payload split successfully. Advertising active!")

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
            print(f"\n--- Chromebook Connected: Handle [{conn_handle}] ---")
            
            # Send an immediate greeting right after the channel opens
            greeting = "Hello from ESP32! How are you?"
            self.ble.gatts_notify(conn_handle, self.char_handle, greeting.encode('utf-8'))
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self.connections:
                self.connections.remove(conn_handle)
            print(f"\n--- Chromebook Disconnected: Handle [{conn_handle}] ---")
            self.advertise()
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self.char_handle:
                received = self.ble.gatts_read(self.char_handle)
                print(f"Received text data: {received.decode('utf-8')}")
                #self.ble.gatts_notify(conn_handle, self.char_handle, received)
                
                # 1. Echo the exact string back
                self.ble.gatts_notify(conn_handle, self.char_handle, received)
                
                # 2. If they said hello, fire our custom greeting right after!
                if decoded_msg.lower() == "hello":
                    reply = "Hello from ESP32! How are you?"
                    time.sleep_ms(100) # Tiny pause to let the web terminal process the first packet
                    self.ble.gatts_notify(conn_handle, self.char_handle, reply.encode('utf-8'))

# Start up the loop execution hook
print("Starting up BLE service loop...")
ble_echo = ESP32_BLE_Echo()
