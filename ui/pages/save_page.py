import streamlit as st
from src.data.data_handler import save_game_data_to_yaml

def save_page():
    """ゲームデータをYAML形式で保存するページを表示"""
    st.header("ゲームデータをYAML形式で保存")
    
    # 保存するゲームIDの選択
    game_ids = []
    if 'game_data' in st.session_state and st.session_state.game_data:
        game_ids = list(st.session_state.game_data.keys())
        selected_game_id = st.selectbox(
            "保存するゲームデータを選択してください", 
            game_ids,
            format_func=lambda x: f"{x}_{st.session_state.game_data[x].get('japanese_name', st.session_state.game_data[x].get('name', '名称不明'))}"
        )
        
        # 選択したゲームのデータを表示
        if selected_game_id:
            game_data = st.session_state.game_data[selected_game_id]
            
            # ゲーム名と基本情報を表示（日本語名があれば表示）
            game_name = game_data.get('name', '名称不明')
            japanese_name = game_data.get('japanese_name', '')
            
            if japanese_name:
                st.markdown(f"## {japanese_name}")
                st.markdown(f"**英語名:** {game_name}")
            else:
                st.markdown(f"## {game_name}")
            
            st.markdown(f"**ゲームID:** {selected_game_id}")
            
            # ゲームサムネイルを表示（ある場合）
            if 'thumbnail_url' in game_data:
                st.image(game_data['thumbnail_url'], caption=japanese_name or game_name)
            
            if 'year_published' in game_data:
                st.markdown(f"**発行年:** {game_data['year_published']}")
            
            # ファイル名の指定欄をボタンの前に配置
            display_name = japanese_name or game_name
            placeholder_filename = f"{selected_game_id}_{display_name}.yaml"
            # 特殊文字を置換（セミコロンも追加）
            placeholder_filename = placeholder_filename.replace(" ", "_").replace(
                "/", "_").replace("\\", "_").replace(":", "_").replace(";", "_")
            
            custom_filename = st.text_input(
                "保存するファイル名 (空白の場合はplaceholderの名前を使用)", 
                value="", 
                placeholder=placeholder_filename
            )
            
            # 保存ボタン
            if st.button("選択したゲームデータをYAMLに保存", type="primary"):
                success, file_path, error_msg = save_game_data_to_yaml(
                    game_data, custom_filename
                )
                
                if success:
                    st.success(f"ゲームデータをYAMLファイルに保存しました: {file_path}")
                else:
                    st.error(f"ファイル保存エラー: {error_msg}")
                    st.error("特殊文字（:;など）を含むゲーム名があると保存に失敗する場合があります。")
    else:
        st.info("保存可能なゲームデータがありません。まずゲームを検索して詳細情報を取得してください。")