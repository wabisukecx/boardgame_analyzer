import streamlit as st
from src.api.bgg_api import search_games
from src.data.data_handler import search_results_to_dataframe

def search_page():
    """ゲーム名で検索するページを表示"""
    st.header("ゲーム名で検索")
    
    # 検索パラメータ入力欄
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("検索するゲーム名を入力してください")
    with col2:
        exact = st.checkbox("完全一致検索", value=False)
    
    # 検索ボタン
    if st.button("検索", type="primary"):
        if query:
            results = search_games(query, exact)
            
            if results:
                st.success(f"検索結果: {len(results)}件見つかりました")
                
                # DataFrameに変換して表示
                df = search_results_to_dataframe(results)
                st.dataframe(df, use_container_width=True)
                
                # 詳細情報へのリンクを追加
                st.info("詳細情報を表示するには「ゲームIDで詳細情報を取得」機能を使用してください。")
                
                # セッションステートに結果を保存
                st.session_state.search_results = results
            else:
                st.warning("検索結果がありません")
        else:
            st.error("検索するゲーム名を入力してください")