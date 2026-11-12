# picow

Raspberry Pi Pico W で電子部品を動かすためのコードと手順。部品ごとにディレクトリを分け、その中にプロジェクトを置く。

## 部品とプロジェクト

| 部品 | プロジェクト |
|---|---|
| [st7735](st7735/)：1.8 インチ TFT 液晶 | [project1](st7735/project1/)：表示デモ<br>[project2](st7735/project2/)：PC 画面のミラー表示 |
| [lcd1602](lcd1602/)：I2C 接続の 16 文字 × 2 行の液晶 | [project1](lcd1602/project1/)：Wi-Fi で時刻を合わせる時計<br>[project2](lcd1602/project2/)：OpenWeatherMap の天気表示 |

初めての場合は、このページの「[Pico W の準備](#pico-w-の準備)」を済ませてから、部品のディレクトリの README で配線し、プロジェクトの README の手順で動かす。

## ディレクトリ構成

README は階層ごとに役割を分けている。

```
picow/
├── README.md          # Pico W 共通の準備（このファイル）
├── images/            # このファイルの図
├── st7735/
│   ├── README.md      # ST7735 液晶の部品と配線
│   ├── images/        # 配線図
│   ├── project1/      # 表示デモ
│   │   └── README.md  # プロジェクトの使い方
│   └── project2/      # PC 画面のミラー表示
│       └── README.md
└── lcd1602/           # I2C LCD1602 液晶（構成は st7735/ と同じ）
```

## Pico W の準備

どの部品を使う場合でも共通の手順。1 から 2 は、初めて使うときに 1 回だけ行う。

### 1. Thonny をインストールする

Thonny は、Pico W にプログラムを書き込んで実行するためのエディタである。[thonny.org](https://thonny.org/) からダウンロードしてインストールする。画面写真付きの手順は、SunFounder Kepler Kit の解説「[1.2 Thonny IDE をインストール](https://docs.sunfounder.com/projects/kepler-kit/ja/latest/pyproject/python_start/install_thonny.html)」にある。

### 2. Pico W に MicroPython を書き込む

1. Thonny を開く。
2. Pico W の BOOTSEL ボタン（USB 端子の近くにある白いボタン）を押しながら、USB ケーブルで PC につなぐ。PC に RPI-RP2 という名前のドライブが現れたら、ボタンを離す。
3. Thonny の右下（下の図の①）をクリックし、「MicroPython をインストール」を選ぶ。
4. 「MicroPython のバリアント」で Pico W 用（Pico W / Pico WH）を選び、「インストール」を押す。終わったら画面を閉じる。

画面写真付きの手順は、「[1.3 Raspberry Pi Pico に MicroPython をインストール](https://docs.sunfounder.com/projects/kepler-kit/ja/latest/pyproject/python_start/install_micropython_to_pico.html)」にある。

### 3. Thonny の使い方

![Thonny の画面で操作する場所（簡略図）](images/thonny.svg)

| 番号 | 場所 | 使い方 |
|---|---|---|
| ① | 右下 | 接続先を選ぶ。Pico W をつないだら「MicroPython (Raspberry Pi Pico)」を選ぶ |
| ② | 開く | PC にある `.py` ファイルを開く |
| ③ | 実行（緑） | 開いているファイルを Pico W で実行する（F5） |
| ④ | 停止（赤） | 実行を止める |
| ⑤ | 保存 | 開いているファイルを保存する |

Pico W に保存するには、「ファイル」→「名前を付けて保存」で保存先に「Raspberry Pi Pico」を選ぶ。`main.py` という名前で保存したファイルは、Pico W の電源を入れるたびに自動で実行される。

### 4. ブレッドボードに Pico W を差す

![ブレッドボードの内部のつながり](images/breadboard.svg)

ブレッドボードは、縦に並んだ 5 つの穴が中でつながっている。中央の溝で上下は分かれる。Pico W を中央の溝をまたぐように差すと、各ピンが別々の縦の列につながる。その列の空いた穴にワイヤーを差せば、そのピンにつながる。

このリポジトリの配線図と配線表は、どれも次の向きと番号で書いている。

- Pico W は、USB 端子を左、部品面（チップやボタンがある面）を上にして差す。
- ピンは物理ピン番号（1〜40）で示す。配線図では、Pico W の基板の内側に各ピンの番号を書いている。番号とピンの名前の対応は「[Pico W のピン](#pico-w-のピン)」にまとめた。

配線は、USB ケーブルを抜いた状態で行う。

## Pico W のピン

![Pico W のピンの物理ピン番号と名前](images/pinout.svg)

USB 端子を左、部品面を上にすると、物理ピン番号は下側の列が左から 1〜20、上側の列が右から 21〜40 と並ぶ。プログラムでは物理ピン番号ではなく GP の後の番号を使う。例えば、9 番ピン（GP6）は `Pin(6)` と書く。

次の表は、USB 側から順に、同じ縦の列に並ぶ下側と上側のピンを並べたものである。

| 下側の番号 | 名前 | 機能 | 上側の番号 | 名前 | 機能 |
|---|---|---|---|---|---|
| 1 | GP0 | I2C0 SDA、SPI0 RX | 40 | VBUS | USB から受け取った 5 V |
| 2 | GP1 | I2C0 SCL、SPI0 CSn | 39 | VSYS | Pico W の電源の入力（1.8〜5.5 V） |
| 3 | GND | グラウンド（0 V） | 38 | GND | グラウンド（0 V） |
| 4 | GP2 | I2C1 SDA、SPI0 SCK | 37 | 3V3_EN | GND につなぐと 3.3 V の電源が止まる |
| 5 | GP3 | I2C1 SCL、SPI0 TX | 36 | 3V3(OUT) | 3.3 V の出力。部品の電源に使う |
| 6 | GP4 | I2C0 SDA、SPI0 RX | 35 | ADC_VREF | ADC の基準電圧 |
| 7 | GP5 | I2C0 SCL、SPI0 CSn | 34 | GP28 | I2C0 SDA、SPI1 RX、ADC2 |
| 8 | GND | グラウンド（0 V） | 33 | AGND | ADC 用のグラウンド |
| 9 | GP6 | I2C1 SDA、SPI0 SCK | 32 | GP27 | I2C1 SCL、SPI1 TX、ADC1 |
| 10 | GP7 | I2C1 SCL、SPI0 TX | 31 | GP26 | I2C1 SDA、SPI1 SCK、ADC0 |
| 11 | GP8 | I2C0 SDA、SPI1 RX | 30 | RUN | GND につなぐと Pico W がリセットされる |
| 12 | GP9 | I2C0 SCL、SPI1 CSn | 29 | GP22 | I2C1 SDA、SPI0 SCK |
| 13 | GND | グラウンド（0 V） | 28 | GND | グラウンド（0 V） |
| 14 | GP10 | I2C1 SDA、SPI1 SCK | 27 | GP21 | I2C0 SCL、SPI0 CSn |
| 15 | GP11 | I2C1 SCL、SPI1 TX | 26 | GP20 | I2C0 SDA、SPI0 RX |
| 16 | GP12 | I2C0 SDA、SPI1 RX | 25 | GP19 | I2C1 SCL、SPI0 TX |
| 17 | GP13 | I2C0 SCL、SPI1 CSn | 24 | GP18 | I2C1 SDA、SPI0 SCK |
| 18 | GND | グラウンド（0 V） | 23 | GND | グラウンド（0 V） |
| 19 | GP14 | I2C1 SDA、SPI1 SCK | 22 | GP17 | I2C0 SCL、SPI0 CSn |
| 20 | GP15 | I2C1 SCL、SPI1 TX | 21 | GP16 | I2C0 SDA、SPI0 RX |

- I2C と SPI は、表の組み合わせのピンでだけ使える。例えば `I2C(1, ...)` の SDA には、「I2C1 SDA」と書いたピン（GP2、GP6、GP10 など）を使う。
- SPI の TX は、部品側の SDA（MOSI）につなぐピンである。
- UART などのほかの機能は、公式のピン配置図（[Pico W Pinout](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf)）にある。各ピンの役割の説明は、キットの解説の [Pico W のページ](https://docs.sunfounder.com/projects/kepler-kit/ja/latest/introduction_to_pico_w.html) にもある。
