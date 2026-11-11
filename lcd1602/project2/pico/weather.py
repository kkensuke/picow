# OpenWeatherMap の現在の天気を、I2C LCD1602 に表示する（MicroPython）
# SunFounder Kepler Kit の iot/4_weather.py を元に、LCD の初期化などを直したもの
from machine import I2C, Pin
import network
import requests
import time

from lcd1602 import LCD
import config

URL = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
INTERVAL = 600  # OpenWeatherMap は、同じ地点の取得を 10 分に 1 回までにするよう勧めているため
WIFI_ERRORS = {
    network.STAT_WRONG_PASSWORD: "Wrong password",
    network.STAT_NO_AP_FOUND: "SSID not found",
    network.STAT_CONNECT_FAIL: "Connect failed",
}

lcd = LCD(I2C(1, sda=Pin(26), scl=Pin(27), freq=100000))  # 液晶の基板の I2C チップ PCF8574 の上限が 100 kHz のため
network.country("JP")  # 日本で使える Wi-Fi のチャンネル（12、13）にもつなぐため
wlan = network.WLAN(network.STA_IF)
wlan.active(True)


def show(line1, line2):
    lcd.write(0, 0, "{:<16}".format(line1[:16]))  # 前の表示が残らないよう、16 文字まで空白で埋める
    lcd.write(0, 1, "{:<16}".format(line2[:16]))


def connect():
    if wlan.isconnected():
        return
    wlan.connect(config.SSID, config.PASSWORD)
    for _ in range(20):  # 最大 20 秒待つ
        if wlan.isconnected() or wlan.status() < 0:
            break
        time.sleep(1)
    if not wlan.isconnected():
        raise OSError(WIFI_ERRORS.get(wlan.status(), "Timeout"))  # 20 秒たっても接続中のまま


def lines(data):
    t = time.gmtime(data["dt"] + data["timezone"])  # dt はデータの時刻（UTC）、timezone はその地点の UTC からのずれ（秒）
    return (
        "{:02d}:{:02d} {}".format(t[3], t[4], data["weather"][0]["main"]),
        "{:.1f}\xdfC {}%".format(data["main"]["temp"], data["main"]["humidity"]),  # 0xDF は液晶の文字 ROM で「°」に見える文字
    )


assert lines({"dt": 1659663579, "timezone": 28800, "weather": [{"main": "Clouds"}], "main": {"temp": 27.3, "humidity": 91}}) == (
    "09:39 Clouds",
    "27.3\xdfC 91%",
)

show("Wi-Fi...", config.SSID)
try:
    connect()
except OSError as e:
    show("Wi-Fi failed", str(e))
    raise
show("IP address", wlan.ifconfig()[0])
time.sleep(3)

show("Weather...", "")
while True:
    try:
        connect()  # Wi-Fi が切れていたら、つなぎ直す
        r = requests.get(URL.format(config.LAT, config.LON, config.API_KEY), timeout=10)
        data = r.json()
        if r.status_code == 200:
            show(*lines(data))
        else:
            show("API error {}".format(r.status_code), data.get("message", ""))
    except (OSError, ValueError) as e:  # ValueError は、サーバーの障害などで応答が JSON でなかったとき
        show("Network error", str(e))
    time.sleep(INTERVAL)
