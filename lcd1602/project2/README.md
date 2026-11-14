# OpenWeatherMap の天気表示

Raspberry Pi Pico W を Wi-Fi につなぎ、天気予報サービス OpenWeatherMap から指定した地点の現在の天気を受け取って、I2C LCD1602 に表示する。表示は 10 分ごとに更新する。SunFounder Kepler Kit の例 `iot/4_weather.py` を元にしている（[キットの例との違い](#キットの例との違い)）。

## 準備

初めての場合は、先に次の 5 つを済ませる。

1. [Pico W の準備](../../README.md#pico-w-の準備)：Thonny のインストールと MicroPython の書き込み
2. [LCD1602 の配線](../README.md#配線)と[ライブラリの保存](../README.md#ライブラリを保存する)
3. 2.4 GHz の Wi-Fi の名前（SSID）とパスワードを調べる。Pico W は 5 GHz の Wi-Fi にはつながらない
4. OpenWeatherMap の API キー（32 文字の英数字）を取る
   1. [OpenWeatherMap のアカウント登録ページ](https://home.openweathermap.org/users/sign_up)で、無料のアカウントを作る。
   2. 届いた確認のメールを開いて登録を終えたら、[API キーのページ](https://home.openweathermap.org/api_keys)に表示される API キーを控える。

   作ったばかりの API キーは、使えるようになるまで時間がかかることがある。10 分ごとの取得は 1 日 144 回で、無料プランの上限より十分少ない。
5. 天気を表示する地点の緯度と経度を調べる。Google マップで地点を右クリックすると、メニューのいちばん上に `35.68123, 139.76712` のように緯度と経度が表示され、クリックするとコピーできる

## ファイル構成

```
project2/
├── README.md
└── pico/
    ├── weather.py  # Pico W で実行するスクリプト
    └── config.py   # Wi-Fi、API キー、地点の設定（Pico W に保存してから書き換える）
```

## 使い方

### 初回だけ：設定を Pico W に保存する

1. Pico W を USB で PC につなぎ、Thonny を開く。
2. Thonny の右下で「MicroPython (Raspberry Pi Pico)」を選ぶ。
3. `pico/config.py` を開き、書き換える前に「ファイル」→「名前を付けて保存」で「Raspberry Pi Pico」を選び、`config.py` という名前で保存する。[project1](../project1/) の `config.py` を保存済みでも、API キーと地点の項目が増えているので上書きする。
4. タブの名前が `[ config.py ]` のように角かっこ付きになり、Pico W 上のファイルを開いた状態になる。ここで次の値を書き換え、保存する（Ctrl+S）。

   | 項目 | 書く値 |
   |---|---|
   | `SSID`、`PASSWORD` | Wi-Fi の名前とパスワード |
   | `API_KEY` | OpenWeatherMap の API キー |
   | `LAT`、`LON` | 地点の緯度と経度。引用符を付けず、数値で書く（例：`LAT = 35.681`） |

リポジトリの `pico/config.py` は書き換えず、Pico W に保存した `config.py` だけにパスワードと API キーを書き込む。リポジトリのファイルに書き込むと、誤ってコミットしたときにパスワードや API キーが公開されてしまう。

### 毎回：天気を表示する

1. Thonny で `pico/weather.py` を開き、実行ボタン（F5）を押す。
2. 液晶の表示は、次の順に変わる。

   | 1 行目 | 2 行目 | 状態 |
   |---|---|---|
   | `Wi-Fi...` | Wi-Fi の名前 | Wi-Fi に接続している（最大 20 秒） |
   | `IP address` | `192.168.10.23` など | 接続できた。Pico W の IP アドレスを 3 秒間表示する |
   | `Weather...` | （なし） | OpenWeatherMap から天気を受け取っている |
   | `09:40 Clouds` | `12.3°C 65%` | 天気。10 分ごとに更新する |

3. 止めるときは停止ボタンを押す。

PC につながず、電源を入れるだけで動かしたい場合は、`weather.py` を「ファイル」→「名前を付けて保存」で「Raspberry Pi Pico」を選び、`main.py` という名前で保存する。この場合も、`lcd1602.py` と `config.py` は Pico W に保存しておく。

## 表示の見方

| 位置 | 内容 |
|---|---|
| 1 行目の時刻 | OpenWeatherMap がそのデータを計算した時刻（地点の現地時刻）。今の時刻ではなく、10 分以上前のこともある |
| 1 行目の英単語 | 天気の分類。`Clear`（晴れ）、`Clouds`（くもり）、`Rain`（雨）、`Drizzle`（霧雨）、`Snow`（雪）、`Thunderstorm`（雷雨）、`Mist` や `Fog`（霧）など。16 文字を超える部分は表示しない |
| 2 行目 | 気温（°C）と湿度（%） |

気温の単位の「°」は、液晶の文字 ROM（文字の形を記録したメモリ）にある、形の似た文字（文字コード 0xDF）で代用している。

## 表示がおかしいとき

| 液晶の表示・症状 | 確認すること |
|---|---|
| `Wi-Fi failed` | 起動時に Wi-Fi につながらない。project1 の「[表示がおかしいとき](../project1/README.md#表示がおかしいとき)」と同じ |
| `API error 401` と `Invalid API key.` | API キーのつづり。作ったばかりのキーなら、有効になるまで待つ。10 分ごとに自動でやり直す |
| `API error 400` | `LAT` と `LON` の値。緯度は −90〜90、経度は −180〜180 の数値で書く |
| `API error 429` | 取得回数が無料プランの上限を超えた。同じ API キーをほかのプログラムでも使っていないか |
| `Network error` と数字や `ETIMEDOUT` | 通信の失敗。Wi-Fi がインターネットにつながっているか。10 分後に自動でやり直す |
| `Network error` と `Wrong password` など | 途中で Wi-Fi が切れ、つなぎ直せなかった。10 分後に自動でやり直す |
| 「°」の位置に別の記号が出る | 液晶の文字 ROM の種類による。`weather.py` の `\xdf` を消すと、単位は `C` だけになる |
| 何も表示されない、`ImportError` が出る | 部品の README の「[表示されないとき](../README.md#表示されないとき)」 |

## キットの例との違い

キットの `iot/4_weather.py` は、今のキットのライブラリでは動かない箇所などがあるため、次のように変えた。

| 項目 | キットの例 | このプロジェクト |
|---|---|---|
| 液晶の初期化 | `LCD()`。今の `lcd1602.py` は I2C を引数に取るため、エラーで止まる | `LCD(I2C(...))` |
| 地点の指定 | 都市名（`q=shenzhen`）。OpenWeatherMap は、都市名での指定を非推奨にしている | 緯度と経度 |
| 時刻 | NTP で合わせた UTC の「時」に時差を足すだけなので、日本では `32:10` のように 24 時を超えることがある | データの時刻（`dt`）を現地時刻に直す。NTP は使わない |
| 「°C」 | `°` をそのまま送るため、液晶では別の文字になる | 文字コード 0xDF の文字で代用する |
| 更新の間隔 | 30 秒 | 10 分（OpenWeatherMap の推奨） |
| 失敗したとき | 通信に失敗すると、エラーで止まる | 液晶に原因を表示し、10 分後にやり直す |
| Wi-Fi の設定 | `secrets.py` | `config.py` |
