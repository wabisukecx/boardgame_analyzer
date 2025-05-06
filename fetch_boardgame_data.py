#!/usr/bin/env python3
"""
リモートのRaspberry PiからBoardgame Analyzerのデータを取得するスクリプト
PC側にあってRaspberry Piにないファイルを同期する機能も提供
"""

import os
import posixpath
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
    parser.add_argument('--no-upload', action='store_true', default=False, help='アップロード処理をスキップ')
    
    return parser.parse_args()

def get_local_yaml_files(directory):
    """指定されたディレクトリ内のすべてのYAMLファイル名を取得"""
    if not os.path.exists(directory):
        return []
    
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    yaml_files.extend(glob.glob(os.path.join(directory, "*.yml")))
    
    return [os.path.basename(f) for f in yaml_files]

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

def get_remote_yaml_files(ssh, remote_path):
    """リモートディレクトリ内のYAMLファイル名リストを取得"""
    try:
        # ディレクトリの存在確認
        stdin, stdout, stderr = ssh.exec_command(f'[ -d "{remote_path}" ] && echo "exists" || echo "not exists"')
        if stdout.read().decode().strip() != "exists":
            print(f"リモートディレクトリが見つかりません: {remote_path}")
            return []
        
        # findコマンドでファイル名を取得
        stdin, stdout, stderr = ssh.exec_command(
            f'find {remote_path} -type f \\( -name "*.yaml" -o -name "*.yml" \\) -printf "%f\\n" 2>/dev/null')
        
        files = stdout.read().decode().strip().split('\n')
        # 空文字列があれば除去
        files = [f for f in files if f]
        
        # デバッグ出力: 見つかったファイル数と一部のファイル名
        print(f"リモート側で{len(files)}個のYAMLファイルを検出しました")
        return files
    
    except Exception as e:
        print(f"リモートファイル一覧の取得エラー: {e}")
        return []

def upload_files(ssh, local_path, remote_path, file_names):
    """指定されたファイルをアップロード（デバッグ強化版）"""
    if not file_names:
        print(f"アップロードするファイルはありません: {local_path}")
        return True
    
    print(f"{len(file_names)}個のファイルをアップロードします: {', '.join(file_names[:5])}...")
    if len(file_names) > 5:
        print(f"...および他{len(file_names)-5}個のファイル")
    
    # アップロード処理
    sftp = ssh.open_sftp()
    upload_success = 0
    upload_fail = 0
    
    try:
        # リモートディレクトリが存在するか確認（デバッグ出力追加）
        try:
            sftp.stat(remote_path)
            print(f"リモートディレクトリが存在します: {remote_path}")
        except FileNotFoundError:
            # リモートディレクトリが存在しない場合は作成
            print(f"リモートディレクトリを作成します: {remote_path}")
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
            stderr_content = stderr.read().decode().strip()
            if stderr_content:
                print(f"リモートディレクトリ作成エラー: {stderr_content}")
                return False
            else:
                print(f"リモートディレクトリを作成しました: {remote_path}")
        
        # リモートディレクトリの内容を確認（デバッグ）
        stdin, stdout, stderr = ssh.exec_command(f'ls -la {remote_path}')
        print(f"リモートディレクトリの内容: \n{stdout.read().decode()}")
        
        # 各ファイルをアップロード
        for i, filename in enumerate(file_names):
            local_file = os.path.join(local_path, filename)
            remote_file = posixpath.join(remote_path, filename)
            
            try:
                print(f"アップロード中 ({i+1}/{len(file_names)}): {filename}")
                print(f"  ローカル: {local_file}")
                print(f"  リモート: {remote_file}")
                
                sftp.put(local_file, remote_file)
                
                # アップロードの成功を確認（ファイルの存在チェック）
                try:
                    sftp.stat(remote_file)
                    print(f"  ✓ アップロード成功: {filename}")
                    upload_success += 1
                except FileNotFoundError:
                    print(f"  ✗ アップロード後のファイル確認失敗: {remote_file}")
                    upload_fail += 1
                    
            except Exception as e:
                print(f"  ✗ ファイル {filename} のアップロード中にエラー: {e}")
                upload_fail += 1
        
        print(f"アップロード完了: 成功={upload_success}, 失敗={upload_fail}")
        
        # アップロード後のリモートディレクトリの内容を確認（デバッグ）
        stdin, stdout, stderr = ssh.exec_command(f'ls -la {remote_path}')
        print(f"アップロード後のリモートディレクトリの内容: \n{stdout.read().decode()}")
        
        return upload_fail == 0
        
    except Exception as e:
        print(f"ファイルアップロード処理全体でエラー: {e}")
        return False
        
    finally:
        sftp.close()

def upload_files(ssh, local_path, remote_path, file_names):
    """指定されたファイルをアップロード"""
    if not file_names:
        print(f"アップロードするファイルはありません: {local_path}")
        return True
    
    print(f"{len(file_names)}個のファイルをアップロードします...")
    
    # アップロード処理
    sftp = ssh.open_sftp()
    try:
        # リモートディレクトリが存在するか確認
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            # リモートディレクトリが存在しない場合は作成
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
            stderr_content = stderr.read().decode().strip()
            if stderr_content:
                print(f"リモートディレクトリ作成エラー: {stderr_content}")
                return False
        
        # 各ファイルをアップロード
        for i, filename in enumerate(file_names):
            local_file = os.path.join(local_path, filename)
            remote_file = posixpath.join(remote_path, filename)
            
            print(f"アップロード中 ({i+1}/{len(file_names)}): {filename}")
            sftp.put(local_file, remote_file)
        
        print(f"{len(file_names)}個のファイルをアップロードしました: {remote_path}")
        return True
        
    except Exception as e:
        print(f"ファイルアップロードエラー: {e}")
        return False
        
    finally:
        sftp.close()

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
        
        # .ymlファイルも検索
        stdin, stdout, stderr = ssh.exec_command(f'find {remote_path} -name "*.yml" -type f')
        yml_files = stdout.read().decode().strip().split('\n')
        
        all_files = files + yml_files
        # 空文字列があれば除去
        all_files = [f for f in all_files if f]
        
        if not all_files:
            print(f"ディレクトリ内にYAMLファイルが見つかりませんでした: {remote_path}")
            return False
        
        # 各ファイルをダウンロード
        for i, remote_file in enumerate(all_files):
            if not remote_file:  # 空行をスキップ
                continue
                
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_path, filename)
            
            print(f"ダウンロード中 ({i+1}/{len(all_files)}): {filename}")
            sftp.get(remote_file, local_file)
        
        print(f"{len(all_files)}個のファイルをダウンロードしました: {local_path}")
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
        
        # リモートのパスを設定
        remote_game_data_path = f"{home_dir}/boardgame_analyzer/game_data"
        remote_config_path = f"{home_dir}/boardgame_analyzer/config"
        
        # アップロード処理（no-uploadフラグがセットされていない場合）
        if not args.no_upload:
            print("\nPC側にあってラズパイ側にないファイルをアップロードします...")
            
            # ローカルとリモートのファイル一覧を取得
            local_game_files = get_local_yaml_files(game_data_dir)
            remote_game_files = get_remote_yaml_files(ssh, remote_game_data_path)
            
            # リモートに存在しないファイルを特定
            missing_game_files = [f for f in local_game_files if f not in remote_game_files]
            
            # ゲームデータファイルのアップロード
            upload_files(ssh, game_data_dir, remote_game_data_path, missing_game_files)
            
            # 設定ファイルの処理
            if args.config:
                local_config_files = get_local_yaml_files(config_dir)
                remote_config_files = get_remote_yaml_files(ssh, remote_config_path)
                
                # リモートに存在しないファイルを特定
                missing_config_files = [f for f in local_config_files if f not in remote_config_files]
                
                # 設定ファイルのアップロード
                upload_files(ssh, config_dir, remote_config_path, missing_config_files)
        
        # ローカルディレクトリのYAMLファイルを削除
        print("\nローカルディレクトリのYAMLファイルを削除しています...")
        clean_local_yaml_files(game_data_dir)
        if args.config:
            clean_local_yaml_files(config_dir)
        
        # 現在のゲームデータをダウンロード
        print(f"\nゲームデータをダウンロードしています... ({remote_game_data_path})")
        download_directory(ssh, remote_game_data_path, game_data_dir)
        
        # 設定ファイルも取得する場合
        if args.config:
            print(f"\n設定ファイルをダウンロードしています... ({remote_config_path})")
            download_directory(ssh, remote_config_path, config_dir)
        
        print("\nデータ同期が完了しました")
        print(f"ゲームデータの保存先: {os.path.abspath(game_data_dir)}")
        if args.config:
            print(f"設定ファイルの保存先: {os.path.abspath(config_dir)}")
    
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    main()