# picow

Raspberry Pi Pico W で電子部品を動かすためのコードと手順。部品ごとにディレクトリを分け、その中にプロジェクトを置く。

## 部品とプロジェクト

| 部品 | プロジェクト |
|---|---|
| [st7735](st7735/)：1.8 インチ TFT 液晶 | [project1](st7735/project1/)：表示デモ<br>[project2](st7735/project2/)：PC 画面のミラー表示 |

初めての場合は、このページの「[Pico W の準備](#pico-w-の準備)」を済ませてから、部品のディレクトリの README で配線し、プロジェクトの README の手順で動かす。

## ディレクトリ構成

README は階層ごとに役割を分けている。

```
picow/
├── README.md          # Pico W 共通の準備（このファイル）
├── images/            # このファイルの図
└── st7735/
    ├── README.md      # ST7735 液晶の部品と配線
    ├── images/        # 配線図
    ├── project1/      # 表示デモ
    │   └── README.md  # プロジェクトの使い方
    └── project2/      # PC 画面のミラー表示
        └── README.md
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

このリポジトリの配線図と配線表は、どれも次の向きと数え方で書いている。

- Pico W は、USB 端子を左、部品面（チップやボタンがある面）を上にして差す。
- ピンは、上側の列を USB 側から 1, 2, 3 … と数える。この「順番」n のピンは、物理ピン番号 41 − n に当たる（順番 1 が物理ピン番号 40 の VBUS）。

各ピンの名前と機能は、公式のピン配置図（[Pico W Pinout](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf)）で確かめられる。

配線は、USB ケーブルを抜いた状態で行う。
