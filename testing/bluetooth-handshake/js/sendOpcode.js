async function sendOpcode(hexValue) {
    if (!echoCharacteristic) {
        log("Error: Cannot send command. No active BLE connection.");
        return;
    }

    try {
        log(`[TX] Sending Opcode: 0x${hexValue.toString(16).toUpperCase().padStart(2, '0')}`);
        
        // Create a 1-byte raw binary buffer container
        const buffer = new Uint8Array([hexValue]);
        
        // Write the binary buffer directly to the ESP32 characteristic
        await echoCharacteristic.writeValue(buffer);
        
        log("Write complete. Waiting for node notification...");
    } catch (error) {
        log("Error sending opcode: " + error);
    }
}