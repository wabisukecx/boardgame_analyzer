import streamlit as st
from ui.ui_components import load_css
from ui.pages.search_page import search_page
from ui.pages.details_page import details_page
from ui.pages.save_page import save_page
from ui.pages.compare_page import compare_page

def main():
    """BoardGameGeek APIツールのメインアプリケーションエントリポイント"""
    # ページ設定
    st.set_page_config(
        page_title="BoardGameGeek API ツール",
        page_icon="🎲",
        layout="wide"
    )

    # カスタムCSSをロード
    load_css()

    # サイドバーでアプリの機能を選択
    st.sidebar.title("機能")
    option = st.sidebar.radio(
        "操作を選んでください",
        ["ゲーム名で検索", "ゲームIDで詳細情報を取得", "YAMLでデータを保存", "ゲーム比較"]
    )

    # 選択された機能に基づいてページを表示
    if option == "ゲーム名で検索":
        search_page()
    elif option == "ゲームIDで詳細情報を取得":
        details_page()
    elif option == "YAMLでデータを保存":
        save_page()
    elif option == "ゲーム比較":
        compare_page()

    # フッター
    st.sidebar.markdown("---")
    st.sidebar.caption("BoardGameGeek API を使用したデータ収集ツール")

if __name__ == "__main__":
    main()