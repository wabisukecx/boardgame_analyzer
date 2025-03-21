# BoardGame Analyzer

BoardGameGeek (BGG) APIを使用してボードゲーム情報を検索、分析、保存するためのStreamlitアプリケーションです。新たに類似性検索機能を追加し、ゲーム間の関連性を分析できるようになりました。

## 概要

このアプリケーションは、BoardGameGeek APIを通じてボードゲームのデータを取得し、ゲームの複雑さ、学習曲線、メカニクスなどを分析するためのツールです。日本語UIで設計されており、ボードゲーム愛好家やボードゲームの情報を整理したい方に最適です。さらに、事前計算された埋め込みモデルを使用して類似したゲームを検索・分析することができます。

デモはStreamlit Community Cloudで確認できます。（YAMLデータ保存はできますが、ローカルPCには保存されません）
<https://boardgameanalyzer-gsmlbaspmgvf3arxttip4f.streamlit.app/>

## 主な機能

- ゲーム名での検索: 名前を使ってBGGからボードゲームを検索
- ゲームIDによる詳細情報取得: ゲームIDを使用して詳細なゲーム情報を取得
- 保存済みゲームの選択: 保存したゲームデータをドロップダウンから簡単に選択
- データ分析: ゲームの複雑さ、学習曲線、リプレイ性などを自動分析
- YAMLデータ保存: 取得したゲーム情報をYAML形式でローカルに保存
- 日本語名対応: 日本語名があるゲームは日本語表示に対応
- ラーニングカーブ分析: ゲームの学習しやすさやマスターに必要な時間の推定
- データ比較機能: 既存データと新規取得データの自動比較
- カテゴリ分析: ゲームカテゴリに基づく複雑さの評価
- ランキング分析: BGGランキング種別と順位に基づく評価
- 戦略深度評価: 意思決定の質と重みに基づく戦略性の分析
- プレイヤー相互作用分析: ゲームにおけるプレイヤー間の相互作用の評価
- ゲーム比較機能: 複数のゲームを選択し、レーダーチャートと数値比較で分析
- **類似性検索機能**: 事前計算された埋め込みモデルを使用して類似ゲームを検索・分析

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
pip install streamlit pandas requests pyyaml deepdiff plotly
```

類似性検索機能を使用する場合は、追加で以下のライブラリが必要です:

```bash
pip install voyageai scikit-learn tqdm python-dotenv
```

## 使用方法

ターミナルでアプリケーションを実行します

```bash
streamlit run app.py
```

ブラウザで自動的に開かれるアプリケーションにアクセスします（通常は <http://localhost:8501>）

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

### ゲーム比較機能

1. サイドバーから「ゲーム比較」を選択
2. 比較したいゲームを複数選択（最大6つまで）
3. 選択したゲームの特性がレーダーチャートで視覚化されます
4. 数値比較テーブルで詳細な数値を確認できます

この機能により、複数のゲームの戦略的深さ、初期学習障壁、リプレイ性、意思決定の深さ、プレイヤー相互作用、ルールの複雑さを一目で比較できます。

### 類似性検索機能（新機能）

1. サイドバーから「類似性検索」を選択
2. 検索の設定を調整（表示する類似ゲーム数、類似度閾値）
3. カテゴリやメカニクスでフィルタリングするには「検索フィルターを設定」を展開
4. フィルタリング結果から検索の基準となるゲームを選択
5. 「類似ゲームを検索」ボタンをクリック
6. 結果は以下のタブで表示されます：
   - 類似ゲーム一覧：類似度スコアと類似の理由を含むゲーム情報
   - 類似度ヒートマップ：ゲーム間の類似関係を視覚化
   - データ分析：最も類似度が高いゲームのリスト、カテゴリとメカニクスの分布分析

### データ比較機能

保存済みのゲームデータと新しく取得したデータを自動的に比較し、変更があった場合は詳細な変更内容を表示します。この機能により、時間経過によるゲームデータの変化（評価の更新、メカニクスの追加/削除など）を追跡できます。

## 学習曲線分析システム

このアプリは独自のアルゴリズムを使用してボードゲームの学習曲線を分析します。以下の要素を考慮して分析が行われます：

### 分析に使用する要素

- メカニクスの複雑さと数: 各ゲームメカニクスに複雑さスコアを割り当て、総合的な複雑さを計算
- BGGでの重さ評価（Weight）: コミュニティによって評価された複雑さの指標
- カテゴリの複雑さ: 各ゲームカテゴリに割り当てられた複雑さに基づく評価
- ランキング情報: BGGでの種別ごとのランキングと順位に基づく評価
- ランキング種別の複雑さ: 各ランキング種別（戦略ゲーム、ファミリーゲームなど）の特性に基づく複雑さ
- リプレイ性: ゲームの再プレイ価値
- メカニクスの戦略的価値: 各メカニクスが持つ戦略的深度への貢献度
- プレイヤー相互作用値: メカニクスとカテゴリが促進するプレイヤー間の相互作用の度合い
- プレイ時間: ゲームのプレイ時間に基づく戦略深度と複雑さの修正

### 分析結果の指標

分析結果には以下の指標が含まれます：

- 初期学習の障壁（1〜5）: ゲームを始めるための難易度
- 戦略の深さ（1〜5）: ゲームの戦略的側面の複雑さと深さ
- 意思決定ポイント（1〜5）: ゲーム中の意思決定の複雑さと多様性
- プレイヤー相互作用（1〜5）: プレイヤー間の相互作用の複雑さ
- ルールの複雑さ（1〜5）: ルールの難解さの評価
- カテゴリに基づく複雑さ（1〜5）: ゲームカテゴリから算出された複雑さ
- ランキングに基づく複雑さ（1〜5）: BGGランキングから算出された複雑さ
- 学習曲線タイプ: 学習難易度の推移パターン（緩やか、中程度、急など）
- リプレイ性（1〜5）: ゲームを繰り返し遊ぶ価値と多様性
- マスター時間: ゲームをマスターするのにかかる時間の推定（短い、中程度、長いなど）
- 対象プレイヤータイプ: どのようなプレイヤーに適しているか（初心者、熟練者など）

## 複雑さデータのカスタマイズ

本アプリは、以下の3つのYAMLファイルを使用して複雑さの評価を行います：

- mechanics_data.yaml: メカニクス（ゲームの仕組み）ごとの複雑さ、戦略的価値、相互作用値
- categories_data.yaml: カテゴリ（ゲームのテーマや種類）ごとの複雑さ、戦略的価値、相互作用値
- rank_complexity.yaml: ランキング種別ごとの複雑さ、戦略的価値、相互作用値

これらのファイルは手動で編集できるため、実際のゲーム体験に基づいてカスタマイズすることで、より正確な分析が可能になります。初回起動時に基本データが自動生成され、新しいメカニクスやカテゴリが見つかると自動的に追加されます。

### 複雑さデータファイルの使い方と注意点

本アプリは上記のYAMLファイルを使用して、ボードゲームの複雑さを評価します。これらのファイルを適切に管理することで、より正確な分析結果を得ることができます。

#### ファイルの役割

- mechanics_data.yaml: ゲームのメカニクス（ルールの仕組み）ごとの複雑さ、戦略的価値、相互作用値を定義
- categories_data.yaml: ゲームのカテゴリ（テーマや種類）ごとの複雑さ、戦略的価値、相互作用値を定義
- rank_complexity.yaml: BGGのランキング種別（戦略ゲーム、ファミリーゲームなど）ごとの複雑さ、戦略的価値、相互作用値を定義

#### 編集時の注意点

- すべてのYAMLファイルは必ず UTF-8 エンコーディングで保存してください
- 他のエンコーディング（Shift-JISなど）で保存すると読み込みエラーが発生します
  
**書式:**

- 各項目はYAML形式で、複雑さ、戦略的価値、相互作用値をそれぞれ定義します
- 数値は1.0～5.0の範囲内にしてください（小数点第一位まで）

**複雑さの基準:**

- 1.0～1.5: 非常に簡単（子供向け、サイコロを振って進むなど）
- 1.6～2.0: 簡単（ビンゴ、記憶、レースなど）
- 2.1～2.5: やや簡単（運試し、トラック移動など）
- 2.6～3.0: 中程度（協力ゲーム、エリア移動など）
- 3.1～3.5: やや複雑（アクションポイント、交渉など）
- 3.6～4.0: 複雑（エリアコントロール、デッキ構築など）
- 4.1～5.0: 非常に複雑（エンジン構築、ワーカープレイスメントなど）

#### ファイルの自動生成と更新

- アプリ初回起動時、YAMLファイルが存在しない場合は初期データが自動生成されます
- BGGから未知のメカニクス/カテゴリ/ランキング種別が見つかると、デフォルト値で自動追加されます
- 自動追加されたアイテムは、適切な複雑さ値に手動で更新することをお勧めします

#### カスタマイズの方法

1. YAMLファイルをテキストエディタで開きます（必ずUTF-8対応エディタを使用）
2. 複雑さ、戦略的価値、相互作用値を実際のゲーム体験に基づいて調整します
3. 変更を保存し、アプリを再起動します

複雑さデータをカスタマイズすることで、分析結果がより正確になり、自分の感覚により近い評価が得られるようになります。

## 類似性検索システム（新機能）

本アプリの類似性検索機能は、事前計算された埋め込みモデルを使用してボードゲーム間の類似性を分析します。この機能により、あるゲームに似た特性を持つ他のゲームを発見できます。

### 類似性検索の仕組み

1. 埋め込みモデル生成: ゲームの情報（名前、説明、カテゴリ、メカニクスなど）をAIモデルによって埋め込みモデル（多次元ベクトル）に変換
2. 類似度計算: コサイン類似度を使用してゲーム間の類似性を測定
3. 検索: 選択したゲームと最も類似度が高いゲームを検索
4. 分析: 類似の理由や特徴を分析して表示

### 埋め込みモデルの生成

類似性検索を使用するには、事前にエンベディングデータファイル（game_embeddings.pkl）を用意する必要があります。このファイルが提供されている場合は、そのまま使用できます。自分で埋め込みモデルを生成する必要はありません。

もし自分で埋め込みモデルを生成したい場合は、Voyage AIのAPIを使用します。Voyage AIの利用には以下が必要です：

- Voyage AIのユーザー登録（https://www.voyageai.com/）
- API利用のための支払い設定（高速で埋め込みモデルを生成するため）

generate_embedding_model.pyスクリプトを使用して、YAMLファイルから保存されたゲームデータの埋め込みモデルを生成できます：

```bash
# Voyage AIのAPIキーを設定
export VOYAGE_API_KEY="your_api_key_here"

# 埋め込みモデルを生成
python generate_embedding_model.py --data_path "game_data/*.yaml" --output "game_embeddings.pkl"
```

### 類似性検索の解析機能

類似性検索では以下の分析が可能です：

1. 類似ゲームの一覧表示: 類似度スコアと類似の理由を表示
2. 類似度ヒートマップ: 選択したゲームとその類似ゲーム間の類似度を視覚化
3. カテゴリ分布: 類似ゲームのカテゴリ分布を円グラフで表示
4. メカニクス分布: 類似ゲームに使用されているメカニクスの頻度を棒グラフで表示
5. 類似ゲームランキング: 類似度に基づくゲームのランキングを表示

この機能を使用すると、以下のことが可能になります：
- 気に入ったゲームに似たゲームを発見
- 複数のゲーム間の関連性を視覚的に理解
- 特定のカテゴリやメカニクスに基づいてゲームを探索
- ゲームコレクションを多様化する参考情報を得る

## 戦略的価値と相互作用の分析

各メカニクスとカテゴリには以下の値が定義されています：

**複雑さ (complexity)**: ルールや概念の複雑さ（1.0～5.0）
**戦略的価値 (strategic_value)**: 戦略的深さへの貢献度（1.0～5.0）
**相互作用値 (interaction_value)**: プレイヤー間の相互作用の程度（1.0～5.0）

例えば、mechanics_data.yamlでは以下のように定義されています：

```yaml
Engine Building:
  complexity: 4.7
  strategic_value: 5.0
  interaction_value: 2.0
  description: 戦略的に非常に深いが、相互作用は比較的少ない
```

これらの値は、ゲームの戦略深度と相互作用の複雑さをより精密に計算するために使用されます。

### 分析アルゴリズムの改良点

最新版では、以下の分析アルゴリズムの改良が行われています：

**戦略深度計算の精緻化：**

- 上位メカニクスの重み付けを調整し、多様なメカニクスの組み合わせをより適切に評価
- プレイ時間に基づく戦略的深さの調整（長時間ゲームの戦略性を適切に評価）

**相互作用複雑性の計算改善：**

- カテゴリとメカニクスの重み付けバランスを最適化（60:40）
- プレイヤー数に基づく修正係数の調整

**リプレイ性評価の向上：**

- ランキング情報と発行年に基づく長期的人気の考慮
- 特定のリプレイ性を高めるメカニクスへの重み付け調整

## ディレクトリ構成

```bash
boardgame-analyzer/
├── app.py                         # メインアプリケーション
├── requirements.txt               # 必要なパッケージのリスト
├── generate_embedding_model.py    # 埋め込みモデル生成スクリプト（新機能）
├── config/                        # 設定ファイル
│   ├── mechanics_data.yaml        # メカニクスの複雑さ、戦略的価値、相互作用値データ
│   ├── categories_data.yaml       # カテゴリの複雑さ、戦略的価値、相互作用値データ
│   └── rank_complexity.yaml       # ランキング種別の複雑さ、戦略的価値、相互作用値データ
├── game_data/                     # 保存されたゲームデータ
│   └── [ゲームID]_[ゲーム名].yaml  # 各ゲームのデータファイル
├── src/                           # ソースコード
│   ├── api/                       # API関連
│   │   ├── bgg_api.py             # BoardGameGeek API関連の関数
│   │   └── rate_limiter.py        # APIレート制限と再試行機能
│   ├── data/                      # データ処理
│   │   └── data_handler.py        # データ保存・変換関数
│   └── analysis/                  # 分析関連
│       ├── learning_curve.py      # 学習曲線分析ロジック
│       ├── game_analyzer.py       # ゲーム分析サマリー生成
│       ├── mechanic_complexity.py # メカニクスの複雑さ評価
│       ├── category_complexity.py # カテゴリの複雑さ評価
│       ├── rank_complexity.py     # ランキング種別の複雑さ評価
│       ├── strategic_depth.py     # 戦略深度計算機能
│       └── similarity.py          # 類似性検索機能（新機能）
└── ui/                            # UI関連
    ├── ui_components.py           # UIコンポーネント関数
    └── pages/                     # ページコンポーネント
        ├── __init__.py            # パッケージ初期化
        ├── search_page.py         # 検索ページ機能
        ├── details_page.py        # 詳細情報ページ機能
        ├── save_page.py           # 保存ページ機能
        └── compare_page.py        # 比較ページ機能
```

## モジュール化の利点

アプリケーションのコードを複数のモジュールに分割することで、以下の利点があります：

1. **可読性の向上**: 各ファイルが特定の機能に集中し、コードが整理されています
2. **保守性の向上**: 修正が必要な場合、関連する機能のファイルだけを編集すればよくなります
3. **拡張性の向上**: 新機能の追加が容易になります
4. **再利用性の向上**: モジュール化されたコードは他のプロジェクトでも再利用しやすくなります
5. **コラボレーションの改善**: 複数の開発者が異なるモジュールを同時に開発できます

## API制限と最適化

- BGG APIへのリクエストはレート制限され、キャッシュされます
- リクエスト間の待機時間を自動調整して429エラーを回避
- TTL（Time To Live）キャッシュによる効率的なAPI利用を実現
- エラー発生時の自動再試行機能により信頼性を向上
- ジッター（ばらつき）を追加したリクエスト間隔で集中アクセスを回避

## 注意事項

- BoardGameGeek APIの使用には制限があり、短時間に多数のリクエストを送ると一時的にブロックされる場合があります
- 初回起動時に各YAMLファイルが存在しない場合は自動的に初期データが作成されます
- ゲーム名に特殊文字（:;など）が含まれていると、ファイル保存に失敗する場合があります
- このツールは学習曲線分析アルゴリズムが主観的要素を含み、絶対的な評価ではありません
- 類似性検索機能を使用するには、事前にエンベディングデータファイル（game_embeddings.pkl）が必要です
- 自分で埋め込みモデルを生成する場合は、Voyage AIのユーザー登録と支払い設定が必要です

## ライセンス

このプロジェクトはオープンソースであり、自由に使用・改変できます。

## 謝辞

このアプリケーションはBoardGameGeek APIを使用しています。BoardGameGeekに感謝します。また、類似性検索機能はVoyage AIのエンベディングAPIを使用しています。
