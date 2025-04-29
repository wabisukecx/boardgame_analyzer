#!/usr/bin/env python3
"""
リモートのRaspberry PiからBoardgame Analyzerのデータを取得するスクリプト
"""

import os
import sys
import argparse
import paramiko
import glob
from pathlib import Path

def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description='Raspberry PiからBoardgame Analyzerのデータを取得')
    parser.add_argument('--host', type=str, default='192.168.50.192', help='Raspberry PiのIPアドレス')
    parser.add_argument('--port', type=int, default=22, help='SSHポート番号')
    parser.add_argument('--username', type=str, default='pi', help='ユーザー名')
    parser.add_argument('--key-file', type=str, default=None, help='秘密鍵ファイルのパス')
    parser.add_argument('--password', type=str, default=None, help='パスワード（セキュリティ上、非推奨）')
    parser.add_argument('--config', action='store_true', default=True, help='設定ファイルも取得（デフォルトで有効）')
    
    return parser.parse_args()

def clean_local_yaml_files(directory):
    """指定されたディレクトリ内のすべてのYAMLファイルを削除"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return
    
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    yaml_files.extend(glob.glob(os.path.join(directory, "*.yml")))
    
    if yaml_files:
        print(f"{directory}内の{len(yaml_files)}個のYAMLファイルを削除しています")
        for file in yaml_files:
            os.remove(file)
        print(f"{directory}内のYAMLファイルをすべて削除しました")

def connect_ssh(host, port, username, key_file=None, password=None):
    """SSHで接続"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_file:
            ssh.connect(host, port=port, username=username, key_filename=key_file)
        else:
            ssh.connect(host, port=port, username=username, password=password)
        return ssh
    except Exception as e:
        print(f"SSH接続エラー: {e}")
        return None

def download_directory(ssh, remote_path, local_path):
    """ディレクトリ全体をダウンロード"""
    sftp = ssh.open_sftp()
    
    try:
        # リモートディレクトリが存在するか確認
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            print(f"リモートディレクトリが見つかりません: {remote_path}")
            return False
        
        # ローカルディレクトリを作成
        os.makedirs(local_path, exist_ok=True)
        
        # リモートディレクトリ内のファイルを列挙
        stdin, stdout, stderr = ssh.exec_command(f'find {remote_path} -name "*.yaml" -type f')
        files = stdout.read().decode().strip().split('\n')
        
        if not files or files[0] == '':
            print(f"ディレクトリ内にYAMLファイルが見つかりませんでした: {remote_path}")
            return False
        
        # 各ファイルをダウンロード
        for i, remote_file in enumerate(files):
            if not remote_file:  # 空行をスキップ
                continue
                
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_path, filename)
            
            print(f"ダウンロード中 ({i+1}/{len(files)}): {filename}")
            sftp.get(remote_file, local_file)
        
        print(f"{len(files)}個のファイルをダウンロードしました: {local_path}")
        return True
    
    except Exception as e:
        print(f"ディレクトリのダウンロードエラー: {e}")
        return False
    
    finally:
        sftp.close()

def main():
    """メイン処理"""
    args = parse_arguments()
    
    # スクリプトと同じ階層のパスを取得
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # ローカルの保存先ディレクトリを設定
    game_data_dir = script_dir / "game_data"
    config_dir = script_dir / "config"
    
    # ローカルディレクトリのYAMLファイルを削除
    print("ローカルディレクトリのYAMLファイルを削除しています...")
    clean_local_yaml_files(game_data_dir)
    if args.config:
        clean_local_yaml_files(config_dir)
    
    # SSHの認証情報が指定されているか確認
    if not args.password and not args.key_file:
        password = input(f"{args.username}@{args.host}のパスワードを入力してください: ")
        args.password = password
    
    # SSH接続
    ssh = connect_ssh(
        args.host, 
        args.port, 
        args.username, 
        args.key_file, 
        args.password
    )
    
    if not ssh:
        print("SSH接続に失敗しました")
        return
    
    try:
        # ホームディレクトリのパスを取得
        stdin, stdout, stderr = ssh.exec_command('echo $HOME')
        home_dir = stdout.read().decode().strip()
        
        # 現在のゲームデータをダウンロード
        remote_game_data_path = f"{home_dir}/boardgame_analyzer/game_data"
        print(f"\nゲームデータをダウンロードしています... ({remote_game_data_path})")
        download_directory(ssh, remote_game_data_path, game_data_dir)
        
        # 設定ファイルも取得する場合
        if args.config:
            remote_config_path = f"{home_dir}/boardgame_analyzer/config"
            print(f"\n設定ファイルをダウンロードしています... ({remote_config_path})")
            download_directory(ssh, remote_config_path, config_dir)
        
        print("\nデータ取得が完了しました")
        print(f"ゲームデータの保存先: {os.path.abspath(game_data_dir)}")
        if args.config:
            print(f"設定ファイルの保存先: {os.path.abspath(config_dir)}")
    
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    main()