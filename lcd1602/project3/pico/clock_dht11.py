# Wi-Fi で時刻を合わせ、日本時間の日付と時刻、DHT11 で測った室内の温度と湿度を、I2C LCD1602 に表示する（MicroPython）
from machine import I2C, Pin
import network
import ntptime
import time

from dht import DHT11, InvalidPulseCount
from lcd1602 import LCD
import config

JST = 9 * 3600  # NTP で合わせた時刻は UTC のため、9 時間（秒）足す
WEEK = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
WIFI_ERRORS = {
    network.STAT_WRONG_PASSWORD: "Wrong password",
    network.STAT_NO_AP_FOUND: "SSID not found",
    network.STAT_CONNECT_FAIL: "Connect failed",
}
SENSOR_INTERVAL = 5  # DHT11 は 1 秒に 1 回までしか測れないため、5 秒ごとに測る
SENSOR_TIMEOUT = 60  # この秒数のあいだ測れなければ、古い値の代わりに「--」を表示する
DEG_C = "\x00"  # 自作文字「℃」（CGRAM の 0 番）
PERCENT = "\x01"  # 自作文字「%」（CGRAM の 1 番）。文字 ROM の「%」より丸を大きくした
GLYPHS = (  # 自作文字の形。1 行 5 ビットで、1 の点が光る
    (0b11100, 0b10100, 0b11100, 0b01110, 0b10001, 0b10000, 0b10001, 0b01110),  # ℃
    (0b11100, 0b10101, 0b11110, 0b00100, 0b01111, 0b10101, 0b00111, 0b00000),  # %
)

lcd = LCD(I2C(1, sda=Pin(6), scl=Pin(7), freq=100000))  # 液晶の基板の I2C チップ PCF8574 の上限が 100 kHz のため
sensor = DHT11(Pin(16, Pin.IN))
for n, rows in enumerate(GLYPHS):
    lcd.send_command(0x40 | (n << 3))  # CGRAM（自作文字を記憶する場所）の n 番の文字を書き込み先にする
    for row in rows:
        lcd.send_data(row)


def show(line1, line2):
    lcd.write(0, 0, "{:<16}".format(line1[:16]))  # 前の表示が残らないよう、16 文字まで空白で埋める
    lcd.write(0, 1, "{:<16}".format(line2[:16]))


def connect():
    network.country("JP")  # 日本で使える Wi-Fi のチャンネル（12、13）にもつなぐため
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # 省電力をオフにする。オンのままだと、iPhone のテザリングに接続できないことがある
    wlan.connect(config.SSID, config.PASSWORD)
    for _ in range(20):  # 最大 20 秒待つ
        if wlan.isconnected() or wlan.status() < 0:
            break
        time.sleep(1)
    if not wlan.isconnected():
        raise OSError(WIFI_ERRORS.get(wlan.status(), "Timeout"))  # 20 秒たっても接続中のまま
    return wlan.ifconfig()[0]


def measure():
    sensor.measure()  # 失敗すると 5 回まで測り直し、それでも失敗すると InvalidPulseCount を出す
    return round(sensor.temperature), round(sensor.humidity)


def lines(t, th):
    temp, hum = ("{:2d}".format(th[0]), "{:2d}".format(th[1])) if th else ("--", "--")
    return (
        "'{:02d}-{:02d}-{:02d} {} {}{}".format(t[0] % 100, t[1], t[2], WEEK[t[6]], temp, DEG_C),
        " {:02d}:{:02d}:{:02d}    {}{}".format(t[3], t[4], t[5], hum, PERCENT),  # 湿度の数字を、温度と同じ 14〜15 文字目にそろえる
    )


assert lines(time.gmtime(1794420000 + JST), (22, 45)) == ("'26-11-12 Th 22\x00", " 03:00:00    45\x01")  # UTC の 11 月 11 日 18 時は、日本時間では翌日
assert lines(time.gmtime(1794420000 + JST), (5, 45))[0] == "'26-11-12 Th  5\x00"
assert lines(time.gmtime(1794420000 + JST), None) == ("'26-11-12 Th --\x00", " 03:00:00    --\x01")

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

th = None  # 最後に測れた温度と湿度
synced = last = time.time()
measured_at = read_at = 0
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
    if now - read_at >= SENSOR_INTERVAL:
        read_at = now
        try:
            th, measured_at = measure(), now
        except InvalidPulseCount:
            if now - measured_at >= SENSOR_TIMEOUT:
                th = None  # 測れない状態が続いたら、古い値を出し続けない
    show(*lines(time.gmtime(now + JST), th))
