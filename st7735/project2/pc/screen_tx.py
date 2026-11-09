# /// script
# dependencies = ["mss", "pillow", "pyserial", "numpy"]
# ///
# PC の画面を縮小して Pico W に USB で送る（実行: uv run screen_tx.py）
import sys

import mss
import numpy as np
import serial
from PIL import Image
from serial.tools import list_ports

W, H = 160, 128


def to_rgb565(img):
    a = np.asarray(img, dtype=np.uint16)
    c = (a[..., 0] >> 3) << 11 | (a[..., 1] >> 2) << 5 | a[..., 2] >> 3
    return c.astype(">u2").tobytes()  # ST7735 はビッグエンディアンで受け取るため


assert to_rgb565(Image.new("RGB", (1, 1), (255, 0, 0))) == b"\xf8\x00"

ports = [p.device for p in list_ports.comports() if p.vid == 0x2E8A]  # 0x2E8A は Raspberry Pi の USB ベンダー ID
if not ports:
    sys.exit("Pico W が見つかりません。USB ケーブルを確認してください。")
try:
    ser = serial.Serial(ports[0], timeout=2)
except serial.SerialException:
    sys.exit("Pico W に接続できません。Thonny を閉じてから実行してください。")
ser.reset_input_buffer()

with mss.mss() as sct:
    monitor = sct.monitors[1]  # メインの画面
    while True:
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
        img.thumbnail((W, H))  # 縦横比を保って縮小する
        frame = Image.new("RGB", (W, H))
        frame.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
        ser.write(b"F")
        if ser.read(1) != b"K":
            sys.exit("Pico W から応答がありません。main.py を保存して USB を挿し直してください。")
        ser.write(to_rgb565(frame))
