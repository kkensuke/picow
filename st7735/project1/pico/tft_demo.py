# Raspberry Pi Pico W + 1.8 インチ ST7735 (128x160) 表示デモ（MicroPython）
from machine import Pin, SPI
import framebuf
import time

W, H = 128, 160
X0, Y0 = 0, 0  # 画面の端に 1〜2 px のノイズが出る基板では 2, 1 にする

spi = SPI(0, baudrate=15000000, sck=Pin(18), mosi=Pin(19))  # ST7735 の書き込み上限が約 15 MHz のため
cs = Pin(17, Pin.OUT, value=1)
dc = Pin(20, Pin.OUT, value=0)
rst = Pin(21, Pin.OUT, value=1)


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
cmd(0x36, b"\xC0")  # 赤と青が入れ替わって見える場合は b"\xC8" にする
cmd(0x29)  # Display On

buf = bytearray(W * H * 2)
fb = framebuf.FrameBuffer(buf, W, H, framebuf.RGB565)


def show():
    cmd(0x2A, bytes([0, X0, 0, X0 + W - 1]))
    cmd(0x2B, bytes([0, Y0, 0, Y0 + H - 1]))
    cmd(0x2C, buf)


def rgb(r, g, b):
    c = (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3
    return (c & 0xFF) << 8 | c >> 8  # framebuf はリトルエンディアンで格納し、ST7735 はビッグエンディアンで受け取るため


assert rgb(255, 0, 0) == 0x00F8

x, y, dx, dy = 10, 40, 2, 3
while True:
    fb.fill(rgb(0, 0, 64))
    fb.text("Hello Pico W", 16, 8, rgb(255, 255, 255))
    fb.fill_rect(x, y, 20, 20, rgb(255, 0, 0))
    show()
    x += dx
    y += dy
    if not 0 <= x <= W - 20:
        dx = -dx
    if not 20 <= y <= H - 20:
        dy = -dy
