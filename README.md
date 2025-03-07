# BoardGame Analyzer

BoardGameGeek (BGG) APIを使用してボードゲーム情報を検索、分析、保存するためのStreamlitアプリケーションです。

## 概要

このアプリケーションは、BoardGameGeek APIを通じてボードゲームのデータを取得し、ゲームの複雑さ、学習曲線、メカニクスなどを分析するためのツールです。日本語UIで設計されており、ボードゲーム愛好家やボードゲームの情報を整理したい方に最適です。

## 主な機能

- **ゲーム名での検索**: 名前を使ってBGGからボードゲームを検索
- **ゲームIDによる詳細情報取得**: ゲームIDを使用して詳細なゲーム情報を取得
- **データ分析**: ゲームの複雑さ、学習曲線、リプレイ性などを自動分析
- **YAMLデータ保存**: 取得したゲーム情報をYAML形式でローカルに保存
- **日本語名対応**: 日本語名があるゲームは日本語表示に対応

## インストール方法

1. このリポジトリをクローンまたはダウンロードします
2. 必要なライブラリをインストールします

```bash
pip install streamlit pandas requests pyyaml
```

## 使用方法

1. ターミナルでアプリケーションを実行します

```bash
streamlit run app.py
```

2. ブラウザで自動的に開かれるアプリケーションにアクセスします（通常は http://localhost:8501）

## アプリの使い方

### ゲーム名で検索

1. サイドバーから「ゲーム名で検索」を選択
2. 検索したいゲーム名を入力
3. 完全一致検索を行いたい場合はチェックボックスをオン
4. 「検索」ボタンをクリック

### ゲームIDで詳細情報を取得

1. サイドバーから「ゲームIDで詳細情報を取得」を選択
2. BGGのゲームIDを入力
3. 「詳細情報を取得」ボタンをクリック
4. 詳細情報が表示され、タブで分類された追加情報を閲覧できます

### YAMLでデータを保存

1. サイドバーから「YAMLでデータを保存」を選択
2. 保存したいゲームを選択
3. ファイル名を入力（空白の場合は自動生成）
4. 「選択したゲームデータをYAMLに保存」ボタンをクリック

## 学習曲線分析について

このアプリは以下の要素を考慮してボードゲームの学習曲線を分析します：

- メカニクスの複雑さと数
- BGGでの重さ評価（Weight）
- 推奨年齢
- ランキング情報
- リプレイ性

分析結果には以下が含まれます：

- 初期学習の障壁
- 戦略の深さ
- 学習曲線タイプ
- リプレイ性
- 対象プレイヤータイプ

### 評価指標の計算方法

#### 初期学習の障壁

初期学習の障壁は、ゲームを始めるための難易度を表し、以下の要素から計算されます：

- メカニクスの平均複雑さ（60%の重み）
- BGGの複雑さ評価（20%の重み）
- 推奨年齢からの複雑さ推定（20%の重み）
- メカニクスの数による補正（メカニクスが多いほど難易度が上がる）

#### 戦略の深さ

戦略の深さは、ゲームの戦略的側面の複雑さと深さを表し、以下の要素から計算されます：

- BGGの複雑さ評価（70%の重み）
- メカニクスの数に基づく要素（30%の重み）
- ゲームの人気順位（ランキング）による補正（人気ゲームは戦略的深さが評価されている傾向）

#### 学習曲線タイプ

学習曲線タイプは、ゲームの学習難易度の推移を表し、以下のロジックで決定されます：

- 初期障壁の値に基づいて基本タイプを決定（緩やか、中程度、急）
- メカニクス数と戦略的深さに基づいて、理解後の上達しやすさを考慮したタイプに調整
- 最終的に5つのタイプ（緩やか、中程度、急、初期は急だが習得後は上達しやすい、中程度で習得後は上達しやすい）に分類

#### リプレイ性

リプレイ性は、ゲームを繰り返し遊ぶ価値と多様性を表し、以下の要素から計算されます：

- 基本スコア（2.0）をベースに調整
- メカニクスの多様性（メカニクス数に基づく加算、最大0.7ポイント）
- 特定のリプレイ性が高いメカニクスの有無に基づく評価（最大0.8ポイント）
- カテゴリの多様性（カテゴリ数に基づく加算、最大0.4ポイント）
- ランキングによるボーナス（人気ゲームほど高いボーナス、最大0.6ポイント）
- 発行年からの長寿命係数（長期間人気を保っているゲームほど高いボーナス）

#### 対象プレイヤータイプ

対象プレイヤータイプは、どのようなプレイヤーにゲームが適しているかを表し、以下の条件で決定されます：

- 初心者向け：初期障壁が低く（<2.6）、戦略的深さも浅い（<3.7）
- カジュアルプレイヤー向け：初期障壁が中程度以下（<3.7）で、戦略的深さもそれほど高くない（<4.3）
- 熟練プレイヤー向け：戦略的深さが高い（>3.7）
- ハードコアゲーマー向け：初期障壁が高く（>3.7）、戦略的深さも高い（>4.3）
- システムマスター向け：メカニクスが多く（>=5）、戦略的深さが高い（>4.0）
- リプレイヤー向け：リプレイ性が高い（>=4.0）
- トレンドフォロワー向け：高ランキング（<=300）のゲーム
- クラシック愛好家向け：発行から10年以上経過したゲーム

## ファイル構成

- `app.py` - メインアプリケーション（Streamlit UI）
- `bgg_api.py` - BoardGameGeek APIとの通信を行う関数
- `data_handler.py` - データ保存・変換を扱う関数
- `learning_curve.py` - 学習曲線分析のロジック
- `mechanic_complexity.py` - メカニクスの複雑さ評価を扱う関数
- `ui_components.py` - UIコンポーネント関数
- `mechanics_data.yaml` - メカニクスの複雑さデータ

## 注意事項

- BoardGameGeek APIの使用には制限があり、短時間に多数のリクエストを送ると一時的にブロックされる場合があります
- 初回起動時に `mechanics_data.yaml` が存在しない場合は自動的に初期データが作成されます

## ライセンス

このプロジェクトはオープンソースであり、自由に使用・改変できます。

## 謝辞

- このアプリケーションはBoardGameGeek APIを使用しています。BoardGameGeekに感謝します。
