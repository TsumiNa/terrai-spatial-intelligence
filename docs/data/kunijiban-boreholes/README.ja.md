# KuniJiban ボーリング

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: user 提供の地域抽出として接続済み・オンデマンド
- 公開者/source system: 国土交通省、土木研究所、港湾空港技術研究所 / KuniJiban
- Dataset/API key: `kunijiban_borehole` / `kunijibanBoreholes`

## データの内容

- **形式と構造:** Apache Parquet 3 file。ボーリングごとの nested table、地層区間ごとの flat table、SPT 試験ごとの flat table です。`data/external/kunijiban_borehole/manifest.json` は asset、byte 数、SHA-256、timestamp、件数、provenance class を記録します。
- **coverage と CRS:** KuniJiban から user が抽出した地域 selection であり、全国完全 coverage ではありません。水平座標は WGS 84 経緯度（`EPSG:4326`）です。標高単位は m ですが、鉛直 datum は source 依存で未正規化です。港湾・河川 record は local datum の場合があります。提供 package は権威ある bounding box を定義していません。
- **粒度と量:** ボーリング 12,067、地層区間 122,693、SPT 観測 239,137。Parquet 3 asset の合計は 12,010,681 bytes です。
- **時点:** integration run は 2026-06-27 に完了し、`retrieved_at=2026-06-27T13:04:00+09:00` として記録します。公開者の単一 snapshot 日はなく、各ボーリングの調査時点は異なります。KuniJiban record は予告なく修正される場合があります。
- **主要 field と単位:** ボーリング ID、地域、source class、緯度/経度（decimal degree）、地盤標高（m）、総掘進長と地下水深（m）、地層下端深度（m）、日本語原文の地層名/記号、正規化 layer category、SPT 深度（m）、SPT N 値（打撃回数）。nested table は audit 用の source または synthetic XML も保持します。
- **Provenance:** 6,462 本は source JGS XML から parse、5,241 本は柱状図 PDF から VLM が再構成、364 本の PDF record は利用可能な地層を含みません。各 record の `data_source` を必ず保持し、VLM 抽出 field を source 観測として扱いません。
- **既知の gap:** 86 本は標高欠損、地下水位は 6,030 本で populated、364 record は layer 0 件です。調査目的、精度、legacy 試験の単位、標高 datum、鮮度は異なります。SPT N > 100 は review が必要で、報告最大値 794 は明らかな source outlier です。

## 出典

- [KuniJiban](https://www.kunijiban.pwri.go.jp/)
- [公式利用規約](https://www.kunijiban.pwri.go.jp/jp/terms.html)
- [公式利用上の留意点](https://www.kunijiban.pwri.go.jp/jp/attention.html)

本 package は project owner が interactive KuniJiban service から対象を絞って取得し提供したものです。KuniJiban は 2019 年に一括 download 機能を廃止しました。`Full_Pipeline_Run_Report.md` は integration run、field mapping、missing、VLM 由来 subset を記録します。抽出 script と upstream PDF/XML は本 repository にないため、現在の snapshot は source から自動再現できません。

## 本 project での利用

地下 Foundation Data Layer evidence として使用します。`GET /api/v1/catalog` は readiness とボーリング数を表示し、`GET /api/v1/datasets/kunijibanBoreholes` は audit manifest を返します。Parquet 3 file は `/api/v1/assets/external/kunijiban_borehole/` 以下からオンデマンド利用でき、exhibition bootstrap には読み込みません。

現在の FastAPI service は asset の catalog/配信だけを行い、Parquet row query は行いません。将来の SL model は source qualification 付きの layer/SPT から missing 地盤 parameter を推定できます。AL は `data_source`、調査時点制約、未解決の鉛直 datum を保持し、現在の site investigation として扱ってはなりません。

## License

KuniJiban 利用規約は、条件の範囲内で地盤情報の検索、download、閲覧、複製、改変、頒布、貸与、販売を許諾します。第三者へ提供する場合は KuniJiban の地盤情報であることを表示し、source 地盤情報に著作権を設定してはなりません。

## 商用利用時の注意

見える形で KuniJiban attribution と規約 link を保持してください。source XML record と VLM 抽出 PDF 再構成を明確に区別し、重要用途では model 抽出値を source と照合してください。KuniJiban は、地下水位/試験値が調査時点の値であること、調査ごとに精度が異なること、原本照合されていない場合があること、旧 data に非 SI 単位が含まれる可能性、予告なく修正される可能性を明示しています。本地域抽出だけを設計、施工、掘削、安全、規制判断に使用しないでください。抽出時 VLM に適用された別規約も確認が必要です。本 card は data governance summary であり法律助言ではありません。
