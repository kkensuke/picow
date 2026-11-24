# Wi-Fi で時刻を合わせ、日本時間の日付と時刻、DHT11 で測った室内の温度と湿度、BMP180 で測った気圧、気象庁の今日の天気予報を、I2C LCD2004 に表示する（MicroPython）
from machine import I2C, Pin
import gc
import network
import ntptime
import requests
import struct
import time

from dht import DHT11, InvalidPulseCount
from lcd1602 import LCD
import config

JST = 9 * 3600  # NTP で合わせた時刻は UTC のため、9 時間（秒）足す
WEEK = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WIFI_ERRORS = {
    network.STAT_WRONG_PASSWORD: "Wrong password",
    network.STAT_NO_AP_FOUND: "SSID not found",
    network.STAT_CONNECT_FAIL: "Connect failed",
}
SENSOR_INTERVAL = 5  # DHT11 は 1 秒に 1 回までしか測れないため、5 秒ごとに測る
SENSOR_TIMEOUT = 60  # この秒数のあいだ測れなければ、古い値の代わりに「--」を表示する
DEG_C = "\x00"  # 自作文字「℃」（CGRAM の 0 番）
PERCENT = "\x01"  # 自作文字「%」（CGRAM の 1 番）。文字 ROM の「%」より丸を大きくした
UMBRELLA = "\x02"  # 自作文字の傘（CGRAM の 2 番）。降水確率の印
GLYPHS = (  # 自作文字の形。1 行 5 ビットで、1 の点が光る
    (0b11100, 0b10100, 0b11100, 0b01110, 0b10001, 0b10000, 0b10001, 0b01110),  # ℃
    (0b11100, 0b10101, 0b11110, 0b00100, 0b01111, 0b10101, 0b00111, 0b00000),  # %
    (0b01110, 0b11111, 0b11111, 0b10101, 0b00100, 0b00100, 0b10100, 0b01100),  # 傘
)
ROW_ADDR = (0x00, 0x40, 0x14, 0x54)  # 液晶の各行の左端の文字の番地（DDRAM アドレス）
BMP180 = 0x77  # BMP180 の I2C アドレス
OSS = 3  # 気圧の測り方（0〜3）。3 は 8 回測った平均で、1 回に最大 25.5 ms かかる
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json".format(config.JMA_OFFICE)
FORECAST_INTERVAL = 1800  # 気象庁は 5、11、17 時に予報を発表するため、30 分ごとに取り直す
WEATHER = {"1": "Sunny", "2": "Cloudy", "3": "Rain", "4": "Snow"}  # 天気コードの 1 桁目（晴れ、くもり、雨、雪）

lcd = LCD(I2C(1, sda=Pin(6), scl=Pin(7), freq=100000))  # 液晶の基板の I2C チップ PCF8574 の上限が 100 kHz のため
bmp = I2C(0, sda=Pin(4), scl=Pin(5))  # 液晶の基板が 5 V に引き上げている線を避け、別の I2C にする
sensor = DHT11(Pin(16, Pin.IN))
for n, rows in enumerate(GLYPHS):
    lcd.send_command(0x40 | (n << 3))  # CGRAM（自作文字を記憶する場所）の n 番の文字を書き込み先にする
    for row in rows:
        lcd.send_data(row)
shown = [None] * 4  # 液晶に今表示している各行の文字列


def show(*lines):
    lines += ("",) * (4 - len(lines))  # 指定しなかった行は空白にする
    for row, line in enumerate(lines):
        line = "{:<20}".format(" " + line[:19])  # 左端を 1 文字あけ、前の表示が残らないよう 20 文字まで空白で埋める
        if line != shown[row]:  # 1 文字の書き込みに約 5 ms かかるため、変わった行だけ書き直す
            lcd.send_command(0x80 | ROW_ADDR[row])  # キットの write() は 16 × 2 文字の範囲にしか書けないため、番地を直接指定する
            for c in line:
                lcd.send_data(ord(c))
            shown[row] = line


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


def bmp180_read(cmd, size, wait_ms):
    bmp.writeto_mem(BMP180, 0xF4, bytes([cmd]))  # 測定を始める
    time.sleep_ms(wait_ms)
    return int.from_bytes(bmp.readfrom_mem(BMP180, 0xF6, size), "big")


def pascal(cal, ut, up, oss):
    # BMP180 の温度の生の値 ut と気圧の生の値 up から、気圧（Pa）を計算する。手順は BMP180 のデータシートの 3.5 節のとおり
    ac1, ac2, ac3, ac4, ac5, ac6, b1, b2, mb, mc, md = cal
    x1 = (ut - ac6) * ac5 >> 15
    b6 = x1 + (mc << 11) // (x1 + md) - 4000  # 温度で補正するための値
    x3 = (b2 * (b6 * b6 >> 12) >> 11) + (ac2 * b6 >> 11)
    b3 = (((ac1 * 4 + x3) << oss) + 2) >> 2
    x3 = ((ac3 * b6 >> 13) + (b1 * (b6 * b6 >> 12) >> 16) + 2) >> 2
    b4 = ac4 * (x3 + 32768) >> 15
    p = (up - b3) * (50000 >> oss) * 2 // b4
    return p + ((((p >> 8) * (p >> 8) * 3038 >> 16) + (-7357 * p >> 16) + 3791) >> 4)


def pressure():
    ut = bmp180_read(0x2E, 2, 5)  # 温度の生の値。気圧の補正に使う
    up = bmp180_read(0x34 | (OSS << 6), 3, 26) >> (8 - OSS)
    return pascal(CAL, ut, up, OSS)


def area(series):
    for a in series["areas"]:
        if a["area"]["code"] == config.JMA_AREA:
            return a
    raise ValueError("JMA_AREA {} not found".format(config.JMA_AREA))  # 一次細分区域のコードが、府県予報区の中にない


def forecast():
    # shortcut: 取得中の数秒間は時計の表示が止まる。気になる場合は、asyncio などで表示と取得を分ける
    gc.collect()  # TLS の通信と JSON の読み込みに、まとまったメモリが要るため
    r = requests.get(FORECAST_URL, timeout=10)
    try:
        if r.status_code != 200:
            raise OSError("HTTP {}".format(r.status_code))  # 府県予報区のコードが違うと 404 になる
        series = r.json()[0]["timeSeries"]  # 0 番は明後日までの予報（1 番は週間予報）
    finally:
        r.close()
    weather = {t[:10]: c for t, c in zip(series[0]["timeDefines"], area(series[0])["weatherCodes"])}  # 「2026-11-12」などの日付 → 天気コード
    pops = {t[:13]: p for t, p in zip(series[1]["timeDefines"], area(series[1])["pops"])}  # 「2026-11-12T06」などの 6 時間の始まり → 降水確率（%）
    return weather, pops


def lines(t, th, pa, fc):
    today = "{}-{:02d}-{:02d}".format(t[0], t[1], t[2])
    weather, pops = fc or ({}, {})
    temp, hum = ("{:2d}".format(th[0]), "{:2d}".format(th[1])) if th else ("--", "--")
    return (
        "{} {}  {}{}".format(today, WEEK[t[6]], temp, DEG_C),
        "{:02d}:{:02d}:{:02d} {}     {}{}".format((t[3] - 1) % 12 + 1, t[4], t[5], "AM" if t[3] < 12 else "PM", hum, PERCENT),  # 12 時間制。0 時と 12 時は 12 と表示する
        "{:<6}{:>10}hPa".format(WEATHER.get((weather.get(today) or "-")[0], "--"), "{:.1f}".format(pa / 100) if pa else "--"),
        "{} {}{}".format(UMBRELLA, "".join("{:>4}".format(pops.get("{}T{:02d}".format(today, h)) or "--") for h in (0, 6, 12, 18)), PERCENT),  # 今日の 0、6、12、18 時からの 6 時間
    )


assert pascal((408, -72, -14383, 32741, 32757, 23153, 6190, 4, -32768, -8711, 2868), 27898, 23843, 0) == 69964  # データシートの計算例
T = time.gmtime(1794420000 + JST)  # 2026-11-12（木）03:00:00
FC = ({"2026-11-12": "300", "2026-11-13": "101"}, {"2026-11-12T06": "100", "2026-11-12T12": "90", "2026-11-12T18": "", "2026-11-13T00": "10"})
assert lines(T, (22, 45), 101320, FC) == ("2026-11-12 Thu  22\x00", "03:00:00 AM     45\x01", "Rain      1013.2hPa", "\x02   -- 100  90  --\x01")
assert lines(T, (5, 45), 99870, FC)[0::2] == ("2026-11-12 Thu   5\x00", "Rain       998.7hPa")
assert lines(T, None, None, None) == ("2026-11-12 Thu  --\x00", "03:00:00 AM     --\x01", "--            --hPa", "\x02   --  --  --  --\x01")
assert [lines(time.gmtime(1794420000 + JST + h * 3600), None, None, None)[1][:11] for h in (-3, 9, 12)] == ["12:00:00 AM", "12:00:00 PM", "03:00:00 PM"]

try:
    CAL = struct.unpack(">hhhHHHhhhhh", bmp.readfrom_mem(BMP180, 0xAA, 22))  # 工場で BMP180 ごとに書き込まれた補正の係数
except OSError:
    show("BMP180 not found")
    raise

show("Wi-Fi...", config.SSID)
try:
    ip = connect()
except OSError as e:
    show("Wi-Fi failed", str(e))
    raise
show("IP address", ip)
time.sleep(3)

show("NTP...")
for _ in range(5):  # NTP の応答（UDP）は届かないことがあるため、数回試す
    try:
        ntptime.settime()
        break
    except OSError:
        time.sleep(1)
else:
    show("NTP failed")
    raise OSError("NTP で時刻を合わせられません")

th = pa = fc = None  # 最後に測れた温度と湿度、気圧と、最後に取れた天気予報
synced = last = time.time()
th_at = pa_at = read_at = forecast_at = 0
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
            th, th_at = measure(), now
        except InvalidPulseCount:
            if now - th_at >= SENSOR_TIMEOUT:
                th = None  # 測れない状態が続いたら、古い値を出し続けない
        try:
            pa, pa_at = pressure(), now
        except OSError:  # 配線がゆるむと、I2C の通信が失敗する
            if now - pa_at >= SENSOR_TIMEOUT:
                pa = None
    if now - forecast_at >= FORECAST_INTERVAL:
        forecast_at = now
        try:
            fc = forecast()
        except Exception as e:  # 通信の失敗や、地域のコードの間違い。前の予報を使い続ける
            print("forecast:", repr(e))  # Thonny の「シェル」に原因を表示する
    show(*lines(time.gmtime(now + JST), th, pa, fc))
