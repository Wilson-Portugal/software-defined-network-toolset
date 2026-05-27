// A clean, compact function to merge telemetry states
async function captureTelemetryNode(rawBleData) {
    // 1. Get high-accuracy mobile GPS coordinates
    navigator.geolocation.getCurrentPosition((position) => {
        const gps = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            alt: position.coords.altitude
        };
        
        // 2. Pair the GPS coordinates with the current true system time
        const logNode = {
            timestamp: new Date().toISOString(),
            coordinates: gps,
            networks: [] // We will parse the raw BLE string array straight into here
        };

        // 3. Split the incoming ESP32 transmission payload
        const routers = rawBleData.split('|');
        routers.forEach(router => {
            const [mac, rssi] = router.split(',');
            if(mac) {
                logNode.networks.push({ bssid: mac, signal: parseInt(rssi) });
            }
        });

        // 4. Send the completed object to a hidden local cache array or storage frame
        saveToTelemetryLog(logNode);
        log(`Captured node at ${gps.lat}, ${gps.lon} with ${logNode.networks.length} routers.`);
    });
}
