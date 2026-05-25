import bluetooth
import time
from micropython import const

# BLE Event constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# Define our Unique IDs (UUIDs) for the Service and Characteristic
# You can generate random ones, but we'll use these fixed ones for our test
SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
CHAR_UUID    = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

class ESP32_BLE_Echo:
    def __init__(self, name="ESP32-Echo-Node"):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        
        # Register our Service and Characteristic
        # 'flags': bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY allows two-way traffic
        char = (CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY,)
        service = (SERVICE_UUID, (char,),)
        
        # Returns handles used to read/write memory values
        ((self.char_handle,),) = self.ble.gatts_register_services((service,))
        
        self.connections = set()
        self.name = name
        self.advertise()

    def _irq(self, event, data):
        # Track connections
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
            print(f"Connected to client! Handle: {conn_handle}")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self.connections:
                self.connections.remove(conn_handle)
            print(f"Disconnected. Handle: {conn_handle}")
            self.advertise() # Start advertising again so we can reconnect
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self.char_handle:
                # Read what the client wrote into the characteristic data slot
                received_bytes = self.ble.gatts_read(self.char_handle)
                received_text = received_bytes.decode('utf-8').strip()
                print(f"Received from Phone: {received_text}")
                
                # If they say "hello", we reply "how are you?"
                if received_text.lower() == "hello":
                    self.send_reply("how are you?")

    def send_reply(self, text):
        print(f"Replying: {text}")
        # Write to our local characteristic memory first
        self.ble.gatts_write(self.char_handle, text.encode('utf-8'))
        # Notify all connected clients that the data has changed
        for conn_handle in self.connections:
            self.ble.gatts_notify(conn_handle, self.char_handle)

    def advertise(self):
        print("Advertising BLE Echo Service...")
        # Payload helper to broadcast the device name
        payload = bytearray(b'\x02\x01\x06') # General discoverable mode
        payload += bytearray([len(self.name) + 1, 0x09]) + self.name.encode('utf-8')
        self.ble.gap_advertise(100000, payload)

# Boot up the server
echo_node = ESP32_BLE_Echo()

# Keep script alive
while True:
    time.sleep(1)

