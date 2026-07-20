# NASA POWER 日射 climatology data

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続・cache 済み
- 変数：`ALLSKY_SFC_SW_DWN`
- 気候期間：2001–2020

## 出典

NASA POWER Climatology API：https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

## 本 project での利用

茂原の長期地域日射背景を提供し、現在の年平均 GHI は約1,378 kWh/m²です。cell 別発電量 model には入れず、設備、影、方位、温度、loss model の代替ではありません。

## License

NASA data は一般に米国著作権の対象外ですが、product 固有 notice を確認し適切に credit します。NASA mark を無許可使用したり endorsement を示唆してはいけません。

## 商用利用時の注意

商用 report は変数、climatology 期間、空間 scale、取得日を明示します。気候平均は案件 P50/P90 発電予測や融資保証ではありません。細時間系列を接続する場合は単位、missing、bias を再検証してください。
