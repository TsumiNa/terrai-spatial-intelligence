# TerrAI Spatial Intelligence

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

TerrAI はクリーンエネルギーと気候レジリエンス向けの空間意思決定 Demo です。公開 foundation data、追跡可能な拡張 evidence、scenario analysis を組み合わせ、地図と action queue で「どこを先に確認すべきか、なぜか、証拠は信頼できるか」を示します。

現在は横浜の斜面曝露と道路・施設レジリエンス、茂原の太陽光立地と module 横断分析を提供します。主要値から出典、式、model status、制約を確認でき、UI は中・日・英を即時切替できます。

## クイックスタート

[uv](https://docs.astral.sh/uv/) が必要です。DB と有料 data service は不要です。

```bash
uv run python -m terrai_spatial serve --port 4176
```

次を開きます。

- 展示 UI：`http://127.0.0.1:4176/`
- FastAPI 文書：`http://127.0.0.1:8000/docs`

最初の online 起動は自動取得可能な data を確認・補完し、欠落または古い派生結果を再構築します。完全 offline は `--offline` を追加します。

## 文書入口

- [製品・実行状態](docs/summary/2026-07-prototype-state.ja.md)
- [system architecture](docs/architecture/FRONTEND_BACKEND.ja.md)
- [FL → SL → AL concept](docs/architecture/FL_SL_AL_CONCEPT.ja.md)
- [接続済み data と license](docs/data/README.ja.md)
- [refactor plan](docs/refactor/fl-sl-al-platform/00-overview.ja.md)
- [開発・contribution](CONTRIBUTING.ja.md)

本 project は顧客対話と技術検証用 Prototype です。順位は screening と due diligence の入口であり、engineering、許認可、系統接続、投資判断を代替しません。
