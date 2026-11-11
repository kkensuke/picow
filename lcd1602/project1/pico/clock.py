# Wi-Fi で時刻を合わせ、I2C LCD1602 に日本時間の日付と時刻を表示する（MicroPython）
from machine import I2C, Pin
import network
import ntptime
import time

from lcd1602 import LCD
import config

JST = 9 * 3600  # NTP で合わせた時刻は UTC のため、9 時間（秒）足す
WEEK = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WIFI_ERRORS = {
    network.STAT_WRONG_PASSWORD: "Wrong password",
    network.STAT_NO_AP_FOUND: "SSID not found",
    network.STAT_CONNECT_FAIL: "Connect failed",
}

lcd = LCD(I2C(1, sda=Pin(26), scl=Pin(27), freq=100000))  # 液晶の基板の I2C チップ PCF8574 の上限が 100 kHz のため


def show(line1, line2):
    lcd.write(0, 0, "{:<16}".format(line1[:16]))  # 前の表示が残らないよう、16 文字まで空白で埋める
    lcd.write(0, 1, "{:<16}".format(line2[:16]))


def connect():
    network.country("JP")  # 日本で使える Wi-Fi のチャンネル（12、13）にもつなぐため
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.SSID, config.PASSWORD)
    for _ in range(20):  # 最大 20 秒待つ
        if wlan.isconnected() or wlan.status() < 0:
            break
        time.sleep(1)
    if not wlan.isconnected():
        raise OSError(WIFI_ERRORS.get(wlan.status(), "Timeout"))  # 20 秒たっても接続中のまま
    return wlan.ifconfig()[0]


def lines(t):
    return "{}-{:02d}-{:02d} {}".format(t[0], t[1], t[2], WEEK[t[6]]), "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])


assert lines(time.gmtime(1794420000 + JST)) == ("2026-11-12 Thu", "03:00:00")  # UTC の 11 月 11 日 18 時が、日本時間では翌日になる

show("Wi-Fi...", config.SSID)
try:
    ip = connect()
except OSError as e:
    show("Wi-Fi failed", str(e))
    raise
show("IP address", ip)
time.sleep(3)

show("NTP...", "")
for _ in range(5):  # NTP の応答（UDP）は届かないことがあるため、数回試す
    try:
        ntptime.settime()
        break
    except OSError:
        time.sleep(1)
else:
    show("NTP failed", "")
    raise OSError("NTP で時刻を合わせられません")

synced = last = time.time()
while True:
    now = time.time()
    if now == last:
        time.sleep_ms(50)
        continue
    last = now
    if now - synced >= 3600:  # Pico W の時計は少しずつずれるため、1 時間ごとに合わせ直す
        synced = now
        try:
            ntptime.settime()
        except OSError:
            pass  # 失敗しても Pico W の時計で表示を続け、1 時間後にやり直す
    show(*lines(time.gmtime(now + JST)))
