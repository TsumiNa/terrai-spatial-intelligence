# GSI 指定緊急避難場所・指定避難所データ

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：全国 base として接続済み
- 自治体：横浜市（`14100`）
- Source 更新日：2026-01-16（GSI 公開履歴）
- Access：直接無料 download。account、API key、Earth Engine、有料 service は不要

## データの内容

- **配布** — GSI は自治体別に、指定避難所（`14100_1`）と指定緊急避難場所（`14100_2`）の CSV / GeoJSON、および機械可読の公開履歴 CSV を提供します。
- **データ量** — 現在の正規化 snapshot は指定避難所 459 件、指定緊急避難場所 1,796 件です。
- **粒度** — 指定避難所は通常 1 施設 1 record です。指定緊急避難場所は同じ学校の校舎・体育館が複数 record になるため、集約せずに 1,796 個の独立 site と解釈してはいけません。
- **災害種別** — 指定緊急避難場所は洪水、崖崩れ・土石流・地滑り、高潮、地震、津波、大規模火災、内水氾濫、火山現象への指定可否を持ちます。
- **時刻 metadata** — normalizer は GSI 公開履歴から `source_updated_at` を取得し、UTC の `retrieved_at` を dataset metadata と全 feature に書きます。両者は audit 上の意味が異なるため、単一の「最新日」に統合しません。

## 出典

- [GSI 公開・download page](https://hinanmap.gsi.go.jp/hinanjocp/hinanbasho/koukaidate.html)
- [指定避難所 GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_1.geojson)
- [指定緊急避難場所 GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_2.geojson)
- [自治体別公開履歴](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/publicHistoryCSV/publicHistoryListData.csv)

## 本 project での利用

GSI 指定避難所を施設レジリエンス view の全国 FL base とします。横浜市地域防災拠点は一致施設の検証と地方説明の追加に使い、不一致の横浜 record は明示的に label した地方補足として残します。GSI 指定緊急避難場所の校舎等は施設名で集約して災害種別の証拠を追加しますが、指定避難所へ読み替えません。

正規化 FL artifact は `data/external/gsi_evacuation/yokohama_evacuation.geojson`、metadata は同じ directory にあります。照合済み AL 証拠は `data/yokohama/official_facility_resilience.geojson`、raw 正規化 dataset は backend の `gsiEvacuation` key から取得できます。

直接更新する command：

```bash
uv run python -m terrai_spatial data update --only gsi_evacuation
```

file が不足し network が許可されている場合、startup もこの task を自動実行します。

## License

GSI は、別記がない限り [国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html) と公共データ利用規約 1.0 を適用します。通常は出典表示が必要で、編集・加工を明示し、第三者権利は利用者が確認します。

## 商用利用時の注意

自治体が災害対策基本法に基づき登録した情報ですが、GSI は未掲載や旧情報の可能性を注意喚起しています。指定緊急避難場所は災害種別ごとの概念で、指定避難所とは異なります。緊急案内、顧客納品、運用判断の前に、最新指定、開設条件、収容力、accessibility、詳細 hazard を横浜市へ確認してください。この注意を downstream user にも伝え、TerrAI の resilience、roof、PV、access proxy を GSI field と表示してはいけません。

