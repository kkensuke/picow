# Wi-Fi で時刻を合わせる時計

Raspberry Pi Pico W を Wi-Fi につなぎ、インターネットの時刻（NTP）で内蔵の時計を合わせて、I2C LCD1602 に日本時間の日付と時刻を表示する。起動時には、Wi-Fi のルーターから割り当てられた Pico W の IP アドレスを 3 秒間表示する。

## 準備

初めての場合は、先に次の 3 つを済ませる。

1. [Pico W の準備](../../README.md#pico-w-の準備)：Thonny のインストールと MicroPython の書き込み
2. [LCD1602 の配線](../README.md#配線)と[ライブラリの保存](../README.md#ライブラリを保存する)
3. 2.4 GHz の Wi-Fi の名前（SSID）とパスワードを調べる。Pico W は 5 GHz の Wi-Fi にはつながらない

## ファイル構成

```
project1/
├── README.md
└── pico/
    ├── clock.py    # Pico W で実行するスクリプト
    └── config.py   # Wi-Fi の名前とパスワード（Pico W に保存してから書き換える）
```

## 使い方

### 初回だけ：Wi-Fi の設定を Pico W に保存する

1. Pico W を USB で PC につなぎ、Thonny を開く。
2. Thonny の右下で「MicroPython (Raspberry Pi Pico)」を選ぶ。
3. `pico/config.py` を開き、書き換える前に「ファイル」→「名前を付けて保存」で「Raspberry Pi Pico」を選び、`config.py` という名前で保存する。
4. タブの名前が `[ config.py ]` のように角かっこ付きになり、Pico W 上のファイルを開いた状態になる。ここで `SSID` と `PASSWORD` の値を書き換え、保存する（Ctrl+S）。

PC 側の `config.py` はリポジトリに含まれる。パスワードを書き込むと、誤ってコミットして公開するおそれがあるため、Pico W 上のファイルだけを書き換える。

### 毎回：時計を動かす

1. Thonny で `pico/clock.py` を開き、実行ボタン（F5）を押す。
2. 液晶の表示は、次の順に変わる。

   | 1 行目 | 2 行目 | 状態 |
   |---|---|---|
   | `Wi-Fi...` | Wi-Fi の名前 | Wi-Fi に接続している（最大 20 秒） |
   | `IP address` | `192.168.10.23` など | 接続できた。Pico W の IP アドレスを 3 秒間表示する |
   | `NTP...` | （なし） | NTP サーバーから時刻を受け取っている |
   | `2026-11-12 Thu` | `03:06:12` | 時計。1 秒ごとに更新する |

3. 止めるときは停止ボタンを押す。

PC につながず、電源を入れるだけで動かしたい場合は、`clock.py` を「ファイル」→「名前を付けて保存」で「Raspberry Pi Pico」を選び、`main.py` という名前で保存する。この場合も、`lcd1602.py` と `config.py` は Pico W に保存しておく。

## 表示がおかしいとき

| 液晶の表示・症状 | 確認すること |
|---|---|
| `Wi-Fi failed` と `Wrong password` | Pico W に保存した `config.py` のパスワード |
| `Wi-Fi failed` と `SSID not found` | Wi-Fi の名前のつづり（大文字と小文字も区別する）と、Wi-Fi が 2.4 GHz かどうか。iPhone のテザリングは、「互換性を優先」をオンにすると 2.4 GHz になる |
| `Wi-Fi failed` と `Timeout` または `Connect failed` | ルーターとの距離。ユーザー名とパスワードでログインする Wi-Fi（大学の eduroam など）には、このスクリプトではつながらない |
| `NTP failed` | Wi-Fi がインターネットにつながっているか。NTP（UDP の 123 番ポート）の通信を止めているネットワークでは、時刻を合わせられない |
| 何も表示されない、`ImportError` が出る | 部品の README の「[表示されないとき](../README.md#表示されないとき)」 |

## 仕組み

- `ntptime.settime()` は、NTP サーバー（`pool.ntp.org`）から受け取った時刻を、Pico W の内蔵の時計に UTC で書き込む。`clock.py` は、その時刻に 9 時間（`JST`）足して日本時間を表示する。
- 内蔵の時計は少しずつずれるため、1 時間ごとに NTP で合わせ直す。合わせ直しに失敗しても、内蔵の時計で表示を続ける。
- 時刻を合わせるときに 1 秒未満を切り捨てるため、表示は最大で 1 秒ほど遅れる。
- 日本以外で使う場合は、`clock.py` の `JST` を UTC からのずれ（秒）に、`network.country("JP")` をその国の 2 文字の国名コードに変える。
