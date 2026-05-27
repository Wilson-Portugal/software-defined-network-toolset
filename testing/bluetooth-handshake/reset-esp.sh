#!/bin/bash

ESP_IP="192.168.1.105"
ESP_PORT="8266"
ESP_PASS="coelho123"
WEBREPL_CLI="$HOME/webrepl/webrepl_cli.py"

echo "Transmitting clean hardware restart sequence to $ESP_IP..."

# Pipe a 1ms deep sleep command into the interactive REPL 
python3 "$WEBREPL_CLI" -p "$ESP_PASS" <(echo -e "import machine\nmachine.deepsleep(1)\n") "$ESP_IP:$ESP_PORT:"

echo "Reset sequence completed."