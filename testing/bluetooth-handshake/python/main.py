import bluetooth
import time
import struct
from micropython import const
import sdn_protocol

# BLE Event constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)

SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F333-E0A9-E50E24DCCA9E")
CHAR_UUID    = bluetooth.UUID("6E400002-B5A3-F333-E0A9-E50E24DCCA9E")

class ESP32_BLE_System:
    def __init__(self, name="ESP32-Echo"):
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        
        char = (CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY,)
        service = (SERVICE_UUID, (char,),)
        ((self.char_handle,),) = self.ble.gatts_register_services((service,))
        
        self.connections = set()
        print("BLE Node initialized.")
        self.advertise()

    def advertise(self):
        adv_payload = bytearray()
        adv_payload += struct.pack("BB", 2, _ADV_TYPE_FLAGS) + b"\x06"
        uuid_bytes = bytes(SERVICE_UUID)
        adv_payload += struct.pack("BB", len(uuid_bytes) + 1, _ADV_TYPE_UUID128_COMPLETE) + uuid_bytes
        
        resp_payload = bytearray()
        resp_payload += struct.pack("BB", len(self.name) + 1, _ADV_TYPE_NAME) + self.name.encode("utf-8")
        
        self.ble.gap_advertise(100000, adv_data=adv_payload, resp_data=resp_payload)
        print("Advertising active!")

    def ble_irq_handler(event, data):
        # This event code triggers when a central device (your PWA) writes data to us
        if event == 3:  # 3 corresponds to the low-level _IRQ_WRITE flag
            conn_handle, value_handle = data
            
            # Read the raw incoming bytes from the hardware buffer
            raw_rx_data = ble.gatts_read(value_handle)
            
            if len(raw_rx_data) > 0:
                # 1. Extract the very first byte as our integer opcode (e.g., 0x01, 0x02)
                opcode = raw_rx_data[0]
                
                print("Received Dashboard Command Opcode: 0x{:02X}".format(opcode))
                
                # 2. Delegate the heavy lifting to our specialized worker module.
                # response_view will capture the direct zero-allocation memory pointer window.
                response_view = sdn_protocol.process_command(opcode)
                
                # 3. Write the response back to the BLE hardware characteristic
                ble.gatts_write(value_handle, response_view)
                
                # 4. Notify the connected PWA that data is ready to be read
                ble.gatts_notify(conn_handle, value_handle)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
            print(f"\n--- Client Connected: [{conn_handle}] ---")
            self.ble.gatts_notify(conn_handle, self.char_handle, b"Node Pipeline Active")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self.connections:
                self.connections.remove(conn_handle)
            print(f"\n--- Client Disconnected ---")
            self.advertise()
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self.char_handle:
                raw_data = self.ble.gatts_read(self.char_handle)
                if not raw_data:
                    return

                # Check packet structure length to differentiate binary vs text strings
                if len(raw_data) == 1:
                    opcode = raw_data[0]
                    print(f"Processing Opcode: 0x{opcode:02X}")
                    
                    if opcode == 0x01:
                        reply = "STATUS_OK: PONG"
                    elif opcode == 0x02:
                        reply = f"UPTIME: {time.ticks_ms()} ms"
                    elif opcode == 0x03:
                        reply = "NODE_ID: SDN-TOOLSET-ESP32"
                    else:
                        reply = f"ERROR: Unknown Opcode 0x{opcode:02X}"
                        
                    self.ble.gatts_notify(conn_handle, self.char_handle, reply.encode('utf-8'))
                
                else:
                    # Fallback path for multi-byte traditional text messages
                    try:
                        decoded_msg = raw_data.decode('utf-8')
                        print(f"Received text message: {decoded_msg}")
                        
                        # Echo original payload back out 
                        self.ble.gatts_notify(conn_handle, self.char_handle, raw_data)
                        
                        if decoded_msg.strip().lower() == "hello":
                            time.sleep_ms(100)
                            self.ble.gatts_notify(conn_handle, self.char_handle, b"Hello from ESP32! How are you?")
                    except Exception as e:
                        print(f"Data parse exception: {e}")

print("Starting up BLE system framework...")
system_node = ESP32_BLE_System()
