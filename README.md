# picow

Raspberry Pi Pico W で電子部品を動かすためのコードと手順。部品ごとにディレクトリを分け、その中にプロジェクトを置く。

## 部品とプロジェクト

| 部品 | プロジェクト |
|---|---|
| [st7735](st7735/)：1.8 インチ TFT 液晶 | [project1](st7735/project1/)：表示デモ<br>[project2](st7735/project2/)：PC 画面のミラー表示 |

## ディレクトリ構成

README は階層ごとに役割を分けている。

```
picow/
├── README.md          # Pico W 共通の準備（このファイル）
└── st7735/
    ├── README.md      # ST7735 液晶の部品と配線
    ├── project1/      # 表示デモ
    │   └── README.md  # プロジェクトの使い方
    └── project2/      # PC 画面のミラー表示
        └── README.md
```
