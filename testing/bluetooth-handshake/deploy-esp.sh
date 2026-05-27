#!/bin/bash

CREDENTIALS="cat production-credentials.txt | grep -v '^#' | head -n 1"
ESP_IP=`echo $CREDENTIALS | cut -d '|' -f 1`
ESP_PORT=`echo $CREDENTIALS | cut -d '|' -f 2`
ESP_PASS=`echo $CREDENTIALS | cut -d '|' -f 3`
WEBREPL_CLI="$HOME/webrepl/webrepl_cli.py"
LOCAL_DIR="/mnt/chromeos/MyFiles/software-defined-network-toolset/testing/bluetooth-handshake"
LOCAL_FILE="$LOCAL_DIR/python/main.py"

echo "Deploying main.py to ESP32 over Wi-Fi ($ESP_IP)..."
python3 "$WEBREPL_CLI" -p "$ESP_PASS" "$LOCAL_FILE" "$ESP_IP:$ESP_PORT:/main.py"

echo "Deployment asset transferred. Run ./reset-esp.sh to execute."