# PC の画面を USB で受け取って ST7735 に表示する（Pico W に main.py として保存）
from machine import Pin, SPI
import micropython
import sys
import time

W, H = 160, 128  # 横向き

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
cmd(0x36, b"\xA0")  # 横向き。上下が逆さなら b"\x60" にする
cmd(0x2A, bytes([0, 0, 0, W - 1]))
cmd(0x2B, bytes([0, 0, 0, H - 1]))
cmd(0x29)  # Display On

buf = bytearray(W * H * 2)
mv = memoryview(buf)
cmd(0x2C, buf)  # 受信前の画面を黒で消す

rx = sys.stdin.buffer
tx = sys.stdout.buffer
while True:
    if rx.read(1) != b"F":  # ここで待っている間は Thonny の停止（Ctrl-C）が効く
        continue
    micropython.kbd_intr(-1)  # 画像データ中の 0x03 を Ctrl-C と誤認しないため
    tx.write(b"K")
    n = 0
    # shortcut: 1 コマの途中で PC 側が止まるとここで固まる（USB の挿し直しで戻る）。頻発するならタイムアウトを入れる
    while n < len(buf):
        n += rx.readinto(mv[n:])
    micropython.kbd_intr(3)
    cmd(0x2C, buf)
