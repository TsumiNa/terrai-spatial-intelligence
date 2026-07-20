# MLIT W05 River Dataset Evaluation

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## Decision

W05 is not integrated into TerrAI. The repository contains no downloader, local output, API dataset key, automatic task, or customer-facing river layer.

## What the dataset contains

The legacy release provides 2008 JGD2000 river centreline and related point data at approximately 1:25,000 for Kanagawa and Chiba. Its source vintage is materially older than the other MLIT layers in the current FL pack.

## Source and terms

- [W05 official page](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W05.html)
- The official legacy page explicitly marks the dataset **non-commercial**.

## Why it was excluded

TerrAI is being prepared as a commercial customer demonstration. A technically separate local cache would still encourage accidental dependence on a layer that cannot support the intended product use. Documentation-only retention keeps the sourcing knowledge without creating a shadow integration.

## Reconsideration path

Before adding river data, identify a current source whose commercial and redistribution rights are explicit. Then compare coverage, geometry, update cadence, hydrological attributes, legal authority and compatibility with road-resilience, flood and solar-site analyses. The future source should enter the normal FL timestamp, provenance, documentation and API review—not revive the removed W05 task by default.
