# BoardGame Analyzer

BoardGameGeek (BGG) APIを使用してボードゲーム情報を検索、分析、保存するためのStreamlitアプリケーションです。

## 概要

このアプリケーションは、BoardGameGeek APIを通じてボードゲームのデータを取得し、ゲームの複雑さ、学習曲線、メカニクスなどを分析するためのツールです。日本語UIで設計されており、ボードゲーム愛好家やボードゲームの情報を整理したい方に最適です。

デモはStreamlit Community Cloudで確認できます。（YAMLデータ保存はできますが、ローカルPCには保存されません）

https://boardgameanalyzer-gsmlbaspmgvf3arxttip4f.streamlit.app/

## 主な機能

- **ゲーム名での検索**: 名前を使ってBGGからボードゲームを検索
- **ゲームIDによる詳細情報取得**: ゲームIDを使用して詳細なゲーム情報を取得
- **保存済みゲームの選択**: 保存したゲームデータをドロップダウンから簡単に選択
- **データ分析**: ゲームの複雑さ、学習曲線、リプレイ性などを自動分析
- **YAMLデータ保存**: 取得したゲーム情報をYAML形式でローカルに保存
- **日本語名対応**: 日本語名があるゲームは日本語表示に対応
- **ラーニングカーブ分析**: ゲームの学習しやすさやマスターに必要な時間の推定
- **データ比較機能**: 既存データと新規取得データの自動比較
- **カテゴリ分析**: ゲームカテゴリに基づく複雑さの評価
- **ランキング分析**: BGGランキング種別と順位に基づく評価

## インストール方法

1. このリポジトリをクローンまたはダウンロードします

```bash
git clone https://github.com/yourusername/boardgame-analyzer.git
cd boardgame-analyzer
```

2. 必要なライブラリをインストールします

```bash
pip install -r requirements.txt
```

または個別にインストールする場合:

```bash
pip install streamlit pandas requests pyyaml deepdiff
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
5. 検索結果が表示され、各ゲームのゲームID、ゲーム名、発行年が表示されます

### ゲームIDで詳細情報を取得

1. サイドバーから「ゲームIDで詳細情報を取得」を選択
2. 手動入力または保存済みYAMLファイルから選択
3. 「詳細情報を取得」ボタンをクリック
4. 詳細情報が表示され、以下の情報を確認できます：
   - 基本情報（ゲーム名、発行年、平均評価）
   - プレイ人数情報（最適人数、対応人数）
   - 推奨年齢・プレイ時間
   - ゲームの複雑さ
   - ラーニングカーブ分析
   - ゲーム説明文
   - メカニクス、カテゴリ、ランキング、デザイナー、パブリッシャー情報

### YAMLでデータを保存

1. サイドバーから「YAMLでデータを保存」を選択
2. 保存したいゲームをドロップダウンリストから選択
3. ファイル名を入力（空白の場合は自動生成）
4. 「選択したゲームデータをYAMLに保存」ボタンをクリック
5. 保存が成功すると確認メッセージが表示されます

### データ比較機能

保存済みのゲームデータと新しく取得したデータを自動的に比較し、変更があった場合は詳細な変更内容を表示します。この機能により、時間経過によるゲームデータの変化（評価の更新、メカニクスの追加/削除など）を追跡できます。

## 学習曲線分析システム

このアプリは独自のアルゴリズムを使用してボードゲームの学習曲線を分析します。以下の要素を考慮して分析が行われます：

### 分析に使用する要素

- **メカニクスの複雑さと数**: 各ゲームメカニクスに複雑さスコアを割り当て、総合的な複雑さを計算
- **BGGでの重さ評価（Weight）**: コミュニティによって評価された複雑さの指標
- **カテゴリの複雑さ**: 各ゲームカテゴリに割り当てられた複雑さに基づく評価
- **ランキング情報**: BGGでの種別ごとのランキングと順位に基づく評価
- **ランキング種別の複雑さ**: 各ランキング種別（戦略ゲーム、ファミリーゲームなど）の特性に基づく複雑さ
- **リプレイ性**: ゲームの再プレイ価値

### 分析結果の指標

分析結果には以下の指標が含まれます：

- **初期学習の障壁（1〜5）**: ゲームを始めるための難易度
- **戦略の深さ（1〜5）**: ゲームの戦略的側面の複雑さと深さ
- **意思決定ポイント（1〜5）**: ゲーム中の意思決定の複雑さと多様性
- **プレイヤー相互作用（1〜5）**: プレイヤー間の相互作用の複雑さ
- **ルールの複雑さ（1〜5）**: ルールの難解さの評価
- **カテゴリに基づく複雑さ（1〜5）**: ゲームカテゴリから算出された複雑さ
- **ランキングに基づく複雑さ（1〜5）**: BGGランキングから算出された複雑さ
- **学習曲線タイプ**: 学習難易度の推移パターン（緩やか、中程度、急など）
- **リプレイ性（1〜5）**: ゲームを繰り返し遊ぶ価値と多様性
- **マスター時間**: ゲームをマスターするのにかかる時間の推定（短い、中程度、長いなど）
- **対象プレイヤータイプ**: どのようなプレイヤーに適しているか（初心者、熟練者など）

### 複雑さデータのカスタマイズ

本アプリは、以下の3つのYAMLファイルを使用して複雑さの評価を行います：

1. **mechanics_data.yaml**: メカニクス（ゲームの仕組み）ごとの複雑さ
2. **categories_data.yaml**: カテゴリ（ゲームのテーマや種類）ごとの複雑さ
3. **rank_complexity.yaml**: ランキング種別ごとの複雑さ

これらのファイルは手動で編集できるため、実際のゲーム体験に基づいてカスタマイズすることで、より正確な分析が可能になります。初回起動時に基本データが自動生成され、新しいメカニクスやカテゴリが見つかると自動的に追加されます。

## 複雑さデータファイルの使い方と注意点

本アプリは3つのYAMLファイル（`mechanics_data.yaml`、`categories_data.yaml`、`rank_complexity.yaml`）を使用して、ボードゲームの複雑さを評価します。これらのファイルを適切に管理することで、より正確な分析結果を得ることができます。

### ファイルの役割

- **mechanics_data.yaml**: ゲームのメカニクス（ルールの仕組み）ごとの複雑さを定義
- **categories_data.yaml**: ゲームのカテゴリ（テーマや種類）ごとの複雑さを定義
- **rank_complexity.yaml**: BGGのランキング種別（戦略ゲーム、ファミリーゲームなど）ごとの複雑さを定義

### 編集時の注意点

1. **エンコーディング**: 
   - すべてのYAMLファイルは必ず **UTF-8** エンコーディングで保存してください
   - 他のエンコーディング（Shift-JISなど）で保存すると読み込みエラーが発生します

2. **コメント**: 
   - コメントは英語で記述することを推奨します（`# Strategy Games (Complex)`）
   - 日本語コメントを使用する場合は、エディタで明示的にUTF-8で保存してください

3. **書式**: 
   - 各行は `メカニクス名: 数値 # コメント` の形式で記述します
   - 数値は1.0～5.0の範囲内にしてください（小数点第一位まで）

4. **複雑さの基準**:
   - 1.0～1.5: 非常に簡単（子供向け、サイコロを振って進むなど）
   - 1.6～2.0: 簡単（ビンゴ、記憶、レースなど）
   - 2.1～2.5: やや簡単（運試し、トラック移動など）
   - 2.6～3.0: 中程度（協力ゲーム、エリア移動など）
   - 3.1～3.5: やや複雑（アクションポイント、交渉など）
   - 3.6～4.0: 複雑（エリアコントロール、デッキ構築など）
   - 4.1～5.0: 非常に複雑（エンジン構築、ワーカープレイスメントなど）

### ファイルの自動生成と更新

1. アプリ初回起動時、YAMLファイルが存在しない場合は初期データが自動生成されます
2. BGGから未知のメカニクス/カテゴリ/ランキング種別が見つかると、デフォルト値で自動追加されます
3. 自動追加されたアイテムは、適切な複雑さ値に手動で更新することをお勧めします

### カスタマイズの方法

1. YAMLファイルをテキストエディタで開きます（必ずUTF-8対応エディタを使用）
2. 複雑さの値を実際のゲーム体験に基づいて調整します
3. 変更を保存し、アプリを再起動します

複雑さデータをカスタマイズすることで、分析結果がより正確になり、自分の感覚により近い評価が得られるようになります。

## 分析結果の指標の計算方法

本アプリで計算される各指標の算出方法は以下の通りです：

### 初期学習の障壁

初期学習の障壁は、ゲームを始めるための難易度を表し、以下の要素から計算されます：

- メカニクスの平均複雑さ（60%の重み）
- BGGの複雑さ評価（20%の重み）
- カテゴリとランキングからの複雑さ推定（20%の重み）
- メカニクスの数による補正（メカニクスが多いほど難易度が上がる）

### 戦略の深さ

戦略の深さは、ゲームの戦略的側面の複雑さと深さを表し、以下の要素から計算されます：

- BGGの複雑さ評価（30%の重み）
- 意思決定ポイント（30%の重み）
- ルールの複雑さ（20%の重み）
- プレイヤー相互作用の複雑性（20%の重み）
- 長期的な戦略性の存在（ボーナスポイント）

### 意思決定ポイント

意思決定ポイントは、ゲーム中のプレイヤーの選択肢と決断の複雑さを表し、以下の要素から計算されます：

- メカニクス分類の評価（高/中/低の意思決定を必要とするメカニクス）
- 戦略的決断が多いメカニクス（ワーカープレイスメント、エンジン構築など）の数
- 中程度の決断が必要なメカニクス（タイル配置、オークションなど）の数
- 簡単な決断のみのメカニクス（ダイスロール、レースなど）の数
- メカニクスの多様性による追加ボーナス

### プレイヤー相互作用

プレイヤー相互作用の複雑さは、プレイヤー間の駆け引きや影響の度合いを表し、以下の要素から計算されます：

- カテゴリ分類の評価（高/中/低の相互作用を持つカテゴリ）
- 高い相互作用のカテゴリ（交渉、対戦型、取引など）の数
- 中程度の相互作用のカテゴリ（エリアコントロール、経済、オークションなど）の数
- 低い相互作用のカテゴリ（パズル、ソロゲーム、教育など）の数

### ルールの複雑さ

ルールの複雑さは、ゲームルールの難解さを表し、以下の要素から計算されます：

- メカニクスの平均複雑さ
- メカニクスの数による補正係数
- 推奨年齢からの複雑さ推定
- BGGの複雑さ評価（Weight）
- これらの要素の加重平均

### カテゴリに基づく複雑さ

カテゴリに基づく複雑さは、ゲームの種類やテーマによる複雑さを表し、以下の要素から計算されます：

- 各カテゴリの複雑さスコア（categories_data.yamlに定義）の平均
- カテゴリの数による補正（多様なカテゴリのゲームはより複雑と評価）
- 例）「戦略」「文明」「経済」などのカテゴリは高得点、「子供向け」「パーティー」などは低得点

### ランキングに基づく複雑さ

ランキングに基づく複雑さは、BGGのランキング情報から導き出される複雑さを表し、以下の要素から計算されます：

- ランキング種別ごとの基準複雑さ（rank_complexity.yamlに定義）
- ランキング順位からの評価（上位ほど高評価、対数スケールで計算）
- ランキング種別の重み付け（「戦略ゲーム」は高い重み、「ファミリーゲーム」は低い重み）
- 種別と順位を考慮した複合評価（例：戦略ゲームの上位は高い複雑さ、パーティーゲームの上位は低い複雑さ）

### 学習曲線タイプ

学習曲線タイプは、初期障壁と戦略深度の組み合わせに基づいて以下のタイプに分類されます：

- **緩やか**: 初期障壁が低く、すぐに遊べるようになるゲーム
- **中程度**: 中程度の初期障壁があるゲーム
- **急**: 初期障壁が高く、始めるのに時間がかかるゲーム
- **初期は急だが戦略は浅い**: 最初は難しいが、戦略的深さはそれほどないゲーム
- **初期は急だが中程度の複雑さ**: 最初は難しいが、中程度の戦略的深さを持つゲーム
- **中程度の障壁で深い戦略性**: 中程度の学習曲線で、深い戦略を持つゲーム
- **習得は簡単だが深い戦略性**: 始めるのは簡単だが、戦略的に深いゲーム

### リプレイ性

リプレイ性は、ゲームを繰り返し遊ぶ価値と多様性を表し、以下の要素から計算されます：

- 基本スコア（2.0）をベースに調整
- メカニクスの多様性（最大0.7ポイント）
- リプレイ性を高めるメカニクスの評価（最大0.8ポイント）
  - 「Variable Set-up」「Modular Board」「Variable Player Powers」などのメカニクスは高評価
- カテゴリの多様性（最大0.4ポイント）
- ランキングからの補正（最大0.6ポイント）
- 長期的な人気による補正（発行から長い期間が経過しているゲームは評価が高い）

### マスター時間

マスターにかかる時間は、ゲームを完全に理解し熟達するのに必要な時間を推定し、以下の基準で計算されます：

- 戦略的深さが4.3以上で、メカニクスが6つ以上の場合：「中〜長い」（基本習得後は上達しやすい）
- 戦略的深さが4.3以上で、メカニクスが5つ以下の場合：「長い」（マスターに長時間必要）
- 戦略的深さが3.2～4.3の場合：「中程度」
- 戦略的深さが3.2未満の場合：「短い」

### 対象プレイヤータイプ

対象プレイヤータイプは、初期障壁、戦略深度、リプレイ性などの指標に基づいて以下のタイプに分類されます：

- **初心者**: 初期障壁が3.0未満、戦略的深さが3.5未満のゲーム
- **カジュアルプレイヤー**: 初期障壁が4.0未満、戦略的深さが4.5未満のゲーム
- **熟練プレイヤー**: 戦略的深さが3.0以上のゲーム
- **ハードコアゲーマー**: 初期障壁が3.0より高く、戦略的深さが3.5より高いゲーム
- **システムマスター**: メカニクスが5つ以上で、戦略的深さが3.5より高いゲーム
- **戦略家**: 戦略的深さが3.8より高いゲーム
- **リプレイヤー**: リプレイ性が3.8以上のゲーム
- **トレンドフォロワー**: BGGランキングが1000位以内のゲーム
- **クラシック愛好家**: 2000年以前に発行されたゲーム

これらの指標を組み合わせることで、ボードゲームの特性を多角的に分析し、プレイヤーに適したゲーム選びの参考情報を提供します。

## データ保存形式

ゲームデータはYAML形式で保存され、以下の情報が含まれます：

- 基本情報（ゲーム名、英語名、日本語名、発行年など）
- 詳細情報（プレイ人数、推奨年齢、プレイ時間など）
- メカニクスとカテゴリ
- デザイナーとパブリッシャー
- 評価情報（平均評価、複雑さ評価、ランキング）
- ラーニングカーブ分析結果

保存されたデータは `game_data` ディレクトリに格納され、ファイル名は `ゲームID_ゲーム名.yaml` の形式になります。

## API制限と最適化

- BGG APIへのリクエストはレート制限され、キャッシュされます
- リクエスト間の待機時間を自動調整して429エラーを回避
- データはTTL（Time To Live）キャッシュでローカルに保存され、効率的なAPI利用を実現

## ファイル構成

- `app.py` - メインアプリケーション（Streamlit UI）
- `bgg_api.py` - BoardGameGeek APIとの通信を行う関数
- `data_handler.py` - データ保存・変換を扱う関数
- `learning_curve.py` - 学習曲線分析のロジック
- `mechanic_complexity.py` - メカニクスの複雑さ評価を扱う関数
- `category_complexity.py` - カテゴリの複雑さ評価を扱う関数
- `rank_complexity.py` - ランキング種別の複雑さ評価を扱う関数
- `ui_components.py` - UIコンポーネント関数
- `rate_limiter.py` - API呼び出しのレート制限と再試行機能
- `strategic_depth.py` - 戦略深度計算の改善機能
- `mechanics_data.yaml` - メカニクスの複雑さデータ
- `categories_data.yaml` - カテゴリの複雑さデータ
- `rank_complexity.yaml` - ランキング種別の複雑さデータ
- `requirements.txt` - 必要なパッケージのリスト

## 注意事項

- BoardGameGeek APIの使用には制限があり、短時間に多数のリクエストを送ると一時的にブロックされる場合があります
- 初回起動時に各YAMLファイルが存在しない場合は自動的に初期データが作成されます
- ゲーム名に特殊文字（:;など）が含まれていると、ファイル保存に失敗する場合があります
- このツールは学習曲線分析アルゴリズムが主観的要素を含み、絶対的な評価ではありません
- 大量のゲームデータを取得する場合は、API制限に配慮してください

## ライセンス

このプロジェクトはオープンソースであり、自由に使用・改変できます。

## 謝辞

- このアプリケーションはBoardGameGeek APIを使用しています。BoardGameGeekに感謝します。
- ボードゲームのメカニクス複雑さデータを提供してくれたボードゲームコミュニティに感謝します。
