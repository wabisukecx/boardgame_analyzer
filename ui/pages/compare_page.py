import streamlit as st
import pandas as pd
from src.data.data_handler import load_all_game_data
from src.analysis.learning_curve import calculate_learning_curve
from ui.ui_components import compare_games_radar_chart

def compare_page():
    """複数ゲームを比較するページを表示"""
    st.header("複数ゲームの比較")
    
    # 保存済みのゲームデータを読み込む
    all_game_data = load_all_game_data()
    
    if not all_game_data:
        st.warning("保存済みのゲームデータがありません。まずはゲームを検索して保存してください。")
    else:
        # ゲームの選択オプションを作成
        game_options = []
        for game_id, game_data in all_game_data.items():
            # 日本語名を優先
            display_name = game_data.get('japanese_name', game_data.get('name', '名称不明'))
            game_options.append({"id": game_id, "name": display_name})
        
        # IDで並び替え
        game_options.sort(key=lambda x: x["id"])
        
        # 表示用の辞書を作成
        game_display_dict = {f"{g['id']} - {g['name']}": g["id"] for g in game_options}
        
        # マルチセレクト
        st.subheader("比較するゲームを選択してください")
        selected_game_keys = st.multiselect(
            "比較するゲーム (最大6つまで選択可能)", 
            options=list(game_display_dict.keys()),
            default=[]
        )
        
        if selected_game_keys:
            selected_game_ids = [game_display_dict[key] for key in selected_game_keys]
            
            # 選択されたゲームを最大6つまでに制限
            if len(selected_game_ids) > 6:
                st.warning("表示は最大6ゲームまでに制限されます。最初の6つを表示します。")
                selected_game_ids = selected_game_ids[:6]
            
            # 各ゲームのデータと学習曲線情報を取得
            games_data = []
            for game_id in selected_game_ids:
                game_data = all_game_data[game_id]
                
                # 学習曲線情報がある場合はそれを使用
                if 'learning_analysis' in game_data:
                    learning_curve = game_data['learning_analysis']
                # なければ計算する
                elif ('description' in game_data and 'mechanics' in game_data and 
                      'weight' in game_data):
                    learning_curve = calculate_learning_curve(game_data)
                else:
                    st.warning(f"{game_data.get('name', 'ID: '+game_id)} の学習曲線情報を取得できません。")
                    continue
                
                games_data.append((game_data, learning_curve))
            
            # 比較レーダーチャートを表示
            if games_data:
                st.subheader("ゲーム特性比較チャート")
                fig = compare_games_radar_chart(games_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # テーブル形式でも数値を表示
                st.subheader("数値比較")
                comparison_data = []
                for game_data, learning_curve in games_data:
                    game_name = game_data.get('japanese_name', game_data.get('name', '不明'))
                    comparison_data.append({
                        "ゲーム名": game_name,
                        "初期学習障壁": f"{learning_curve.get('initial_barrier', 0):.2f}",
                        "戦略的深さ": f"{learning_curve.get('strategic_depth', 0):.2f}",
                        "リプレイ性": f"{learning_curve.get('replayability', 0):.2f}",
                        "意思決定の深さ": f"{learning_curve.get('decision_points', 0):.2f}",
                        "プレイヤー相互作用": f"{learning_curve.get('interaction_complexity', 0):.2f}",
                        "ルールの複雑さ": f"{learning_curve.get('rules_complexity', 0):.2f}",
                        "BGG重み": f"{float(game_data.get('weight', 0)):.2f}"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)