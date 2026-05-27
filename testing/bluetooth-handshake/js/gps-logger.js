// gps-logger.js
async function getAccurateLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject("Geolocation not supported");
        }
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    alt: position.coords.altitude,
                    time: new Date().toISOString()
                });
            },
            (error) => reject(error),
            { enableHighAccuracy: true, timeout: 5000 }
        );
    });
}