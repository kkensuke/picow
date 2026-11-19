# Wi-Fi で時刻を合わせ、日本時間の日付と時刻、DHT11 で測った室内の温度と湿度を、ST7735 に表示する（MicroPython）
from machine import Pin, SPI
import framebuf
import network
import ntptime
import time

from dht import DHT11, InvalidPulseCount
import config

W, H = 160, 128  # 横向き
X0, Y0 = 0, 0  # 画面の端に 1〜2 px のノイズが出る基板では 1, 2 にする
JST = 9 * 3600  # NTP で合わせた時刻は UTC のため、9 時間（秒）足す
WEEK = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
WIFI_ERRORS = {
    network.STAT_WRONG_PASSWORD: "Wrong password",
    network.STAT_NO_AP_FOUND: "SSID not found",
    network.STAT_CONNECT_FAIL: "Connect failed",
}
SENSOR_INTERVAL = 5  # DHT11 は 1 秒に 1 回までしか測れないため、5 秒ごとに測る
SENSOR_TIMEOUT = 60  # この秒数のあいだ測れなければ、古い値の代わりに「--」を表示する
SEGMENTS = {  # 数字の形。7 本の棒（上、右上、右下、下、左下、左上、中央）のうち光らせるものを、ビット 0〜6 で表す。「1」は digits() で描く
    "0": 0x3F, "2": 0x5B, "3": 0x4F, "4": 0x66, "5": 0x6D,
    "6": 0x7D, "7": 0x07, "8": 0x7F, "9": 0x6F, "-": 0x40, " ": 0x00,
}

spi = SPI(0, baudrate=15000000, sck=Pin(18), mosi=Pin(19))  # ST7735 の書き込み上限が約 15 MHz のため
cs = Pin(17, Pin.OUT, value=1)
dc = Pin(20, Pin.OUT, value=0)
rst = Pin(21, Pin.OUT, value=1)
sensor = DHT11(Pin(22, Pin.IN))


def cmd(c, data=b""):
    cs(0)
    dc(0)
    spi.write(bytes([c]))
    if data:
        dc(1)
        spi.write(data)
    cs(1)


rst(0)
time.sleep_ms(50)
rst(1)
time.sleep_ms(150)
cmd(0x11)  # Sleep Out
time.sleep_ms(150)
cmd(0x3A, b"\x05")  # 16 ビットカラー
cmd(0x36, b"\xA0")  # 横向き。上下が逆さなら b"\x60" にする
cmd(0x2A, bytes([0, X0, 0, X0 + W - 1]))
cmd(0x2B, bytes([0, Y0, 0, Y0 + H - 1]))
cmd(0x29)  # Display On

buf = bytearray(W * H * 2)
fb = framebuf.FrameBuffer(buf, W, H, framebuf.RGB565)


def rgb(r, g, b):
    c = (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3
    return (c & 0xFF) << 8 | c >> 8  # framebuf はリトルエンディアンで格納し、ST7735 はビッグエンディアンで受け取るため


WHITE = rgb(255, 255, 255)
GRAY = rgb(130, 134, 140)
DARK = rgb(44, 46, 50)
ORANGE = rgb(255, 160, 72)
BLUE = rgb(96, 184, 255)


def digits(s, x, y, w, h, t, gap, c):
    m = (h - t) // 2  # 中央の棒の上端
    bars = ((0, 0, w, t), (w - t, 0, t, m + t), (w - t, m, t, h - m), (0, h - t, w, t), (0, m, t, h - m), (0, 0, t, m + t), (0, m, w, t))
    for ch in s:
        if ch == "1":  # 右の 2 本で描くと左が大きく空くため、真ん中の縦棒と左上の短い横棒で描く
            fb.fill_rect(x + (w - t) // 2, y, t, h, c)
            fb.fill_rect(x + (w - t) // 2 - w // 4, y, w // 4, t, c)
        else:
            for i, (bx, by, bw, bh) in enumerate(bars):
                if SEGMENTS[ch] >> i & 1:
                    fb.fill_rect(x + bx, y + by, bw, bh, c)
        x += w + gap


def show(line1, line2):
    fb.fill(0)
    fb.text(line1[:16], 15, 52, WHITE)
    fb.text(line2[:16], 15, 68, GRAY)
    cmd(0x2C, buf)


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


def texts(t, th):
    temp, hum = ("{:2d}".format(th[0]), "{:2d}".format(th[1])) if th else ("--", "--")
    return "{}-{:02d}-{:02d}".format(t[0], t[1], t[2]), WEEK[t[6]], "{:02d}".format(t[3]), "{:02d}".format(t[4]), temp, hum


def show_clock(t, th):
    date, week, hour, minute, temp, hum = texts(t, th)
    fb.fill(0)
    fb.text(date, 15, 10, GRAY)
    fb.text(week, 121, 10, GRAY)  # 右端を、時刻の右端（x = 145）にそろえる
    digits(hour, 15, 27, 26, 48, 4, 6, WHITE)
    fb.fill_rect(78, 41, 4, 4, WHITE)  # 時と分の間の「:」
    fb.fill_rect(78, 57, 4, 4, WHITE)
    digits(minute, 87, 27, 26, 48, 4, 6, WHITE)
    fb.fill_rect(15, 87, 130, 2, DARK)  # 秒の進み。1 分で左端から右端まで伸びる
    fb.fill_rect(15, 87, 130 * t[5] // 59, 2, GRAY)
    digits(temp, 15, 99, 12, 20, 3, 4, ORANGE)
    fb.rect(47, 99, 4, 4, ORANGE)  # 「°」
    fb.text("C", 53, 99, ORANGE)
    digits(hum, 107, 99, 12, 20, 3, 4, BLUE)
    fb.line(143, 99, 138, 104, BLUE)  # 「%」の斜線。fb.text() の「%」と同じ形
    fb.line(143, 100, 138, 105, BLUE)
    fb.rect(137, 99, 3, 3, BLUE)  # 「%」の丸。fb.text() の 2×2 の点を、中が空いた 3×3 の輪にする
    fb.rect(142, 104, 3, 3, BLUE)
    cmd(0x2C, buf)


assert texts(time.gmtime(1794420000 + JST), (22, 45)) == ("2026-11-12", "THU", "03", "00", "22", "45")  # UTC の 11 月 11 日 18 時は、日本時間では翌日
assert texts(time.gmtime(1794420000 + JST), (5, 45))[4] == " 5"
assert texts(time.gmtime(1794420000 + JST), None)[4:] == ("--", "--")

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
    show_clock(time.gmtime(now + JST), th)
