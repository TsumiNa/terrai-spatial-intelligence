# NASA POWER 日射 climatology data

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続・cache 済み
- 変数：`ALLSKY_SFC_SW_DWN`
- 気候期間：2001–2020

## データの内容

- **形式** — NASA POWER Climatology API が返す JSON を `data/mobara/solar_summary.json` にキャッシュしたもの。ラスタのダウンロードではなく地点クエリです。
- **変数** — `ALLSKY_SFC_SW_DWN`：全天日射のうち地表下向き短波放射、すなわち全天日射量（GHI）。
- **単位とキャッシュ値** — API の単位は kWh/m²/日。キャッシュには `daily_ghi_kwh_m2` = 3.7747、`annual_ghi_kwh_m2` = 1,378、および 12 か月分の `monthly_ghi` を保持します。
- **対象期間** — 2001–2020 年の平年値（20 年平均）であり、特定年の値ではありません。
- **空間粒度** — POWER は概ね緯度 0.5° × 経度 0.625° の全球再解析グリッドを提供します。1 グリッドセルが茂原のデモ範囲全体を覆うため、敷地内で値は変化しません。
- **データ量** — 地点 1 か所のクエリ結果。月別 12 値と年平均 1 値。
- **既知の欠測と留意点** — 単一グリッドセルには敷地内変動が無く、候補セル間の区別には使えません。平年値は P50/P90 の発電量推定ではなく、陰影・地形・方位・温度・汚損・機器損失を含みません。

## 出典

NASA POWER Climatology API：https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

## 本 project での利用

茂原の長期地域日射背景を提供し、現在の年平均 GHI は約1,378 kWh/m²です。cell 別発電量 model には入れず、設備、影、方位、温度、loss model の代替ではありません。

## License

NASA data は一般に米国著作権の対象外ですが、product 固有 notice を確認し適切に credit します。NASA mark を無許可使用したり endorsement を示唆してはいけません。

## 商用利用時の注意

商用 report は変数、climatology 期間、空間 scale、取得日を明示します。気候平均は案件 P50/P90 発電予測や融資保証ではありません。細時間系列を接続する場合は単位、missing、bias を再検証してください。
