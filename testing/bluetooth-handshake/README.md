OK, how about a proof of concept that an HTML page with a form and with JavaScript can talk to and ESP32 and just say "hello" and get a "how are you?" back?

That is the perfect first brick. A simple, clean, bidirectional echo test lets us verify that the Bluetooth link works, the Web Bluetooth API can find the ESP32, and the data can flow back and forth before we layer on any complex Wi-Fi scanning or GPS math.

To do this, we need to create two pieces: the **ESP32 MicroPython script** and a **single local HTML/JavaScript file** that you can open right on your Chromebook or phone.

---

## 1. The ESP32 MicroPython Side (`main.py`)

MicroPython handles BLE using raw byte values and **UUIDs** (Universally Unique Identifiers) to define services and characteristics. Think of a Service as a folder, and a Characteristic as a file inside it that we can read and write to.

For this test, we will create a custom Service with one Characteristic that allows **Write** (for the phone to say "hello") and **Notify** (for the ESP32 to instantly shout "how are you?" back).

Here is the MicroPython code. You can load this onto your ESP32-S3 using Thonny (via USB for now, since we're setting up Bluetooth!).

```python
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

```

---

## 2. The Phone / Chromebook Side (`index.html`)

Because Web Bluetooth security is strict, the browser requires a **direct physical user interaction** (like clicking a button) to trigger the Bluetooth connection window.

Save this code below as a local file named `index.html` on your Chromebook. You don't need a web server to test this locally; you can just double-click the file to open it in Chrome!

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLE Echo Proof of Concept</title>
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 500px; margin: auto; line-height: 1.5; }
        button { padding: 10px 15px; font-size: 16px; margin: 5px 0; width: 100%; cursor: pointer; }
        input[type="text"] { width: 100%; padding: 8px; box-sizing: border-box; font-size: 16px; }
        .log { background: #f0f0f0; border: 1px solid #ccc; padding: 10px; height: 150px; overflow-y: auto; font-family: monospace; font-size: 14px; margin-top: 15px; }
        .status { font-weight: bold; color: #d32f2f; }
        .connected { color: #388e3c; }
    </style>
</head>
<body>

    <h2>BLE Echo Node Test</h2>
    <p>Connection Status: <span id="status" class="status">Disconnected</span></p>

    <button id="connectBtn">Connect to ESP32</button>
    
    <hr>

    <form id="echoForm" onsubmit="return false;">
        <label for="msgInput">Send Message to Node:</label>
        <input type="text" id="msgInput" value="hello" disabled>
        <button id="sendBtn" disabled>Send to ESP32</button>
    </form>

    <h3>Data Terminal Log:</h3>
    <div id="log" class="log"></div>

    <script>
        // Must match the exact UUID strings used in the MicroPython code
        const SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
        const CHAR_UUID    = "6e400002-b5a3-f393-e0a9-e50e24dcca9e";

        let bleDevice = null;
        let echoCharacteristic = null;

        const connectBtn = document.getElementById('connectBtn');
        const sendBtn = document.getElementById('sendBtn');
        const msgInput = document.getElementById('msgInput');
        const statusSpan = document.getElementById('status');
        const logDiv = document.getElementById('log');

        function log(message) {
            logDiv.innerHTML += `[${new Date().toLocaleTimeString()}] ${message}<br>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        // 1. Connect to the ESP32 Device
        connectBtn.addEventListener('click', async () => {
            log("Requesting Bluetooth devices...");
            try {
                // Look for devices broadcasting our specific custom service
                bleDevice = await navigator.bluetooth.requestDevice({
                    filters: [{ services: [SERVICE_UUID] }]
                });

                log(`Found device: ${bleDevice.name}. Connecting to GATT Server...`);
                statusSpan.textContent = "Connecting...";
                
                const server = await bleDevice.gatt.connect();
                log("GATT Server connected. Fetching Service...");
                
                const service = await server.getPrimaryService(SERVICE_UUID);
                log("Service found. Fetching Characteristic...");
                
                echoCharacteristic = await service.getCharacteristic(CHAR_UUID);
                log("Characteristic ready!");

                // Start listening for notifications (the ESP32 replying)
                await echoCharacteristic.startNotifications();
                echoCharacteristic.addEventListener('characteristicvaluechanged', handleNotifications);
                
                // Update UI state
                statusSpan.textContent = "Connected";
                statusSpan.className = "status connected";
                msgInput.disabled = false;
                sendBtn.disabled = false;
                connectBtn.disabled = true;

                bleDevice.addEventListener('gattserverdisconnected', onDisconnected);

            } catch (error) {
                log(`Error: ${error}`);
                statusSpan.textContent = "Disconnected";
                statusSpan.className = "status";
            }
        });

        // 2. Handle incoming data notifications from the ESP32
        function handleNotifications(event) {
            let value = event.target.value;
            let decoder = new TextDecoder('utf-8');
            let text = decoder.decode(value);
            log(`<b>Received from ESP32:</b> ${text}`);
        }

        // 3. Send text to the ESP32
        sendBtn.addEventListener('click', async () => {
            if (!echoCharacteristic) return;
            let text = msgInput.value;
            log(`Sending: "${text}"`);
            
            let encoder = new TextEncoder('utf-8');
            let data = encoder.encode(text);
            
            try {
                // Write data to the characteristic slot on the ESP32
                await echoCharacteristic.writeValue(data);
                log("Write complete.");
            } catch (error) {
                log(`Write Error: ${error}`);
            }
        });

        function onDisconnected() {
            log("Device disconnected.");
            statusSpan.textContent = "Disconnected";
            statusSpan.className = "status";
            msgInput.disabled = true;
            sendBtn.disabled = true;
            connectBtn.disabled = false;
        }
    </script>
</body>
</html>

```

---

## How to Test Your Proof of Concept

1. Run the MicroPython script on your ESP32 through Thonny. Watch the Thonny shell pane—it should print `Advertising BLE Echo Service...`.
2. Open `index.html` in Chrome on your Chromebook or Android phone.
3. Click the **Connect to ESP32** button. A native browser window will pop up scanning for Bluetooth devices.
4. Select **ESP32-Echo-Node** and click Pair.
5. Once the UI status flips to green and reads **Connected**, type `hello` in the text box and hit **Send**.
6. Check your browser's log container—you should see the confirmation of the write, followed immediately by a fresh incoming notification from the ESP32 reading: `Received from ESP32: how are you?`.

How does this setup look to start with? Let me know what your Thonny console and browser console say once you give this handshake a spin!
