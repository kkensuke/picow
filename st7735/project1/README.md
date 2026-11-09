# ST7735 表示デモ

Raspberry Pi Pico W に 1.8 インチの ST7735 液晶（128×160 ピクセル）をつなぎ、表示を確認するためのデモ。紺色の背景に白い文字を表示し、赤い四角を跳ね回らせる。

## ファイル構成

```
project1/
├── README.md
└── pico/
    └── tft_demo.py    # Pico W で実行するスクリプト
```

## 必要なもの

- Raspberry Pi Pico W（MicroPython を書き込んだもの）
- 1.8 インチ SPI 液晶モジュール（ドライバ IC：ST7735、128×160 ピクセル）
- ブレッドボード
- ジャンパーワイヤー（オス‐メス）8 本
- Thonny をインストールした PC

MicroPython の書き込み方は、SunFounder Kepler Kit の解説「[1.3 Raspberry Pi Pico に MicroPython をインストール](https://docs.sunfounder.com/projects/kepler-kit/ja/latest/pyproject/python_start/install_micropython_to_pico.html)」を参照する。

## 配線

Pico W は USB 端子を左、部品面を上にして、ブレッドボード中央の溝をまたぐように差す。表の「順番」は、Pico W の上側のピンを USB 側から数えた番号である。

| 液晶のピン | Pico W のピン | 物理ピン番号 | 順番 |
|---|---|---|---|
| VCC | 3V3(OUT) | 36 | 5 |
| GND | GND | 23 | 18 |
| CS | GP17 | 22 | 19 |
| RESET | GP21 | 27 | 14 |
| A0 | GP20 | 26 | 15 |
| SDA | GP19 | 25 | 16 |
| SCK | GP18 | 24 | 17 |
| LED | 3V3(OUT) | 36 | 5 |

VCC と LED はどちらも 3V3(OUT) につなぐ。同じ列の空いた穴に 1 本ずつ差す。液晶のピン名は、液晶の裏の右端に印刷されている。

## 使い方

1. Pico W を USB で PC につなぎ、Thonny を開く。
2. Thonny の右下で「MicroPython (Raspberry Pi Pico)」を選ぶ。
3. `pico/tft_demo.py` を開き、実行ボタン（F5）を押す。
4. 止めるときは停止ボタンを押す。

PC につながず、電源を入れるだけで動かしたい場合は、「ファイル」→「名前を付けて保存」で「Raspberry Pi Pico」を選び、`main.py` という名前で保存する。

## 表示がおかしいとき

| 症状 | 対処 |
|---|---|
| 赤い四角が青く見える | `tft_demo.py` の `b"\xC0"` を `b"\xC8"` に変える |
| 画面の端に 1〜2 px のノイズが出る | `X0, Y0 = 0, 0` を `2, 1` に変える |
| 画面が真っ白のまま | CS・RESET・A0・SDA・SCK の配線を確認する |
| 画面がまったく光らない | VCC・GND・LED の配線を確認する |
| 実行すると画面全体が暗くなり、停止すると明るくなる | 配線がずれている。LED の線が 3V3(OUT) 以外の列に入っている可能性が高い |
