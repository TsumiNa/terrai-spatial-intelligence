# MLIT W05 河川データ評価

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## 決定

W05 は TerrAI に接続しません。repository には downloader、local output、API dataset key、自動 task、顧客向け河川 layer を残しません。

## データ内容

旧版は神奈川・千葉の2008年 JGD2000、概ね1:25,000の河川中心線・関連点を提供します。現在の MLIT FL pack の他 layer と比べて年代が古いデータです。

## 出典と条件

- [W05公式ページ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W05.html)
- 旧公式ページは明示的に**非商用**と表示しています。

## 除外理由

TerrAI は商用顧客 demo を前提とします。技術的に分離した local cache でも、製品利用できない layer への隠れた依存を招きます。資料だけを残すことで、shadow integration を作らず source 調査結果を維持します。

## 再検討方法

河川データを追加する前に、商用・再配布条件が明確な最新 source を選びます。範囲、形状、更新周期、水文属性、法的権威、道路レジリエンス・浸水・太陽光分析との互換性を比較し、通常の FL timestamp、provenance、文書、API review を経て接続します。削除した W05 task を既定で復活させません。
