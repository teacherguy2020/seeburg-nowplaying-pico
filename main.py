import network
import time
from secrets import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Connecting to Wi-Fi...")
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 15

while not wlan.isconnected() and timeout > 0:
    print(".", end="")
    time.sleep(1)
    timeout -= 1

print()

if wlan.isconnected():
    print("Connected!")
    print("IP address:", wlan.ifconfig()[0])
else:
    print("Wi-Fi connection failed.")