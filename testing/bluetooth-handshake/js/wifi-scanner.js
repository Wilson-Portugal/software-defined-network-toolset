// wifi-scanner.js
async function handleIncomingTelemetry(rawBleData) {
    try {
        // 1. Capture GPS Point A (The current location right now)
        const gpsStart = await getAccurateLocation();
        
        log(`Processing batch transmission...`);

        const telemetryPayload = {
            scan_initiated: gpsStart.time,
            start_coordinates: { lat: gpsStart.lat, lon: gpsStart.lon },
            end_coordinates: null, // We will fill this in next
            networks: []
        };

        // 2. Parse the raw BLE payload (Assuming format: BSSID,RSSI,ESSID|...)
        const records = rawBleData.split('|');
        records.forEach(record => {
            const fields = record.split(',');
            if (fields.length >= 2) {
                telemetryPayload.networks.push({
                    bssid: fields[0],
                    rssi: parseInt(fields[1]),
                    essid: fields[2] || "[Hidden]"
                });
            }
        });

        // 3. Capture GPS Point B (The final location vector point)
        const gpsEnd = await getAccurateLocation();
        telemetryPayload.end_coordinates = { lat: gpsEnd.lat, lon: gpsEnd.lon };

        // 4. Queue it or send it off!
        log(`Logged node with ${telemetryPayload.networks.length} routers across a vector of ${gpsStart.lat} to ${gpsEnd.lat}`);
        
        // TODO: postToWilsonPortugal(telemetryPayload);

    } catch (err) {
        log(`Telemetry capture error: ${err}`);
    }
}