#!/usr/bin/env python3
"""
Script to fetch BoardGame Analyzer data from remote Raspberry Pi
Also provides functionality to synchronize files that exist on PC but not on Raspberry Pi
"""

import os
import posixpath
import argparse
import paramiko
import glob
from pathlib import Path

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Fetch BoardGame Analyzer data from Raspberry Pi')
    parser.add_argument('--host', type=str, default='192.168.50.192', help='Raspberry Pi IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port number')
    parser.add_argument('--username', type=str, default='pi', help='Username')
    parser.add_argument('--key-file', type=str, default=None, help='Private key file path')
    parser.add_argument('--password', type=str, default=None, help='Password (not recommended for security)')
    parser.add_argument('--config', action='store_true', default=True, help='Also fetch configuration files (enabled by default)')
    parser.add_argument('--no-upload', action='store_true', default=False, help='Skip upload process')
    
    return parser.parse_args()

def get_local_yaml_files(directory):
    """Get all YAML filenames in the specified directory"""
    if not os.path.exists(directory):
        return []
    
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    yaml_files.extend(glob.glob(os.path.join(directory, "*.yml")))
    
    return [os.path.basename(f) for f in yaml_files]

def clean_local_yaml_files(directory):
    """Delete all YAML files in the specified directory"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return
    
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    yaml_files.extend(glob.glob(os.path.join(directory, "*.yml")))
    
    if yaml_files:
        print(f"Deleting {len(yaml_files)} YAML files in {directory}")
        for file in yaml_files:
            os.remove(file)
        print(f"Deleted all YAML files in {directory}")

def connect_ssh(host, port, username, key_file=None, password=None):
    """Connect via SSH"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_file:
            ssh.connect(host, port=port, username=username, key_filename=key_file)
        else:
            ssh.connect(host, port=port, username=username, password=password)
        return ssh
    except Exception as e:
        print(f"SSH connection error: {e}")
        return None

def get_remote_yaml_files(ssh, remote_path):
    """Get list of YAML filenames from remote directory"""
    try:
        # Check if directory exists
        stdin, stdout, stderr = ssh.exec_command(f'[ -d "{remote_path}" ] && echo "exists" || echo "not exists"')
        if stdout.read().decode().strip() != "exists":
            print(f"Remote directory not found: {remote_path}")
            return []
        
        # Get filenames using find command
        stdin, stdout, stderr = ssh.exec_command(
            f'find {remote_path} -type f \\( -name "*.yaml" -o -name "*.yml" \\) -printf "%f\\n" 2>/dev/null')
        
        files = stdout.read().decode().strip().split('\n')
        # Remove empty strings
        files = [f for f in files if f]
        
        # Debug output: show number of files found and some filenames
        print(f"Detected {len(files)} YAML files on remote side")
        return files
    
    except Exception as e:
        print(f"Error getting remote file list: {e}")
        return []

def upload_files(ssh, local_path, remote_path, file_names):
    """Upload specified files (debug enhanced version)"""
    if not file_names:
        print(f"No files to upload: {local_path}")
        return True
    
    print(f"Uploading {len(file_names)} files: {', '.join(file_names[:5])}...")
    if len(file_names) > 5:
        print(f"...and {len(file_names)-5} more files")
    
    # Upload process
    sftp = ssh.open_sftp()
    upload_success = 0
    upload_fail = 0
    
    try:
        # Check if remote directory exists (with debug output)
        try:
            sftp.stat(remote_path)
            print(f"Remote directory exists: {remote_path}")
        except FileNotFoundError:
            # Create remote directory if it doesn't exist
            print(f"Creating remote directory: {remote_path}")
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
            stderr_content = stderr.read().decode().strip()
            if stderr_content:
                print(f"Remote directory creation error: {stderr_content}")
                return False
            else:
                print(f"Created remote directory: {remote_path}")
        
        # Check remote directory contents (debug)
        stdin, stdout, stderr = ssh.exec_command(f'ls -la {remote_path}')
        print(f"Remote directory contents: \n{stdout.read().decode()}")
        
        # Upload each file
        for i, filename in enumerate(file_names):
            local_file = os.path.join(local_path, filename)
            remote_file = posixpath.join(remote_path, filename)
            
            try:
                print(f"Uploading ({i+1}/{len(file_names)}): {filename}")
                print(f"  Local: {local_file}")
                print(f"  Remote: {remote_file}")
                
                sftp.put(local_file, remote_file)
                
                # Verify successful upload (check file existence)
                try:
                    sftp.stat(remote_file)
                    print(f"  ✓ Upload successful: {filename}")
                    upload_success += 1
                except FileNotFoundError:
                    print(f"  ✗ Upload file verification failed: {remote_file}")
                    upload_fail += 1
                    
            except Exception as e:
                print(f"  ✗ Error uploading file {filename}: {e}")
                upload_fail += 1
        
        print(f"Upload complete: Success={upload_success}, Failed={upload_fail}")
        
        # Check remote directory contents after upload (debug)
        stdin, stdout, stderr = ssh.exec_command(f'ls -la {remote_path}')
        print(f"Remote directory contents after upload: \n{stdout.read().decode()}")
        
        return upload_fail == 0
        
    except Exception as e:
        print(f"Overall file upload process error: {e}")
        return False
        
    finally:
        sftp.close()

def upload_files(ssh, local_path, remote_path, file_names):
    """Upload specified files"""
    if not file_names:
        print(f"No files to upload: {local_path}")
        return True
    
    print(f"Uploading {len(file_names)} files...")
    
    # Upload process
    sftp = ssh.open_sftp()
    try:
        # Check if remote directory exists
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            # Create remote directory if it doesn't exist
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_path}')
            stderr_content = stderr.read().decode().strip()
            if stderr_content:
                print(f"Remote directory creation error: {stderr_content}")
                return False
        
        # Upload each file
        for i, filename in enumerate(file_names):
            local_file = os.path.join(local_path, filename)
            remote_file = posixpath.join(remote_path, filename)
            
            print(f"Uploading ({i+1}/{len(file_names)}): {filename}")
            sftp.put(local_file, remote_file)
        
        print(f"Uploaded {len(file_names)} files to: {remote_path}")
        return True
        
    except Exception as e:
        print(f"File upload error: {e}")
        return False
        
    finally:
        sftp.close()

def download_directory(ssh, remote_path, local_path):
    """Download entire directory"""
    sftp = ssh.open_sftp()
    
    try:
        # Check if remote directory exists
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            print(f"Remote directory not found: {remote_path}")
            return False
        
        # Create local directory
        os.makedirs(local_path, exist_ok=True)
        
        # List files in remote directory
        stdin, stdout, stderr = ssh.exec_command(f'find {remote_path} -name "*.yaml" -type f')
        files = stdout.read().decode().strip().split('\n')
        
        # Also search for .yml files
        stdin, stdout, stderr = ssh.exec_command(f'find {remote_path} -name "*.yml" -type f')
        yml_files = stdout.read().decode().strip().split('\n')
        
        all_files = files + yml_files
        # Remove empty strings
        all_files = [f for f in all_files if f]
        
        if not all_files:
            print(f"No YAML files found in directory: {remote_path}")
            return False
        
        # Download each file
        for i, remote_file in enumerate(all_files):
            if not remote_file:  # Skip empty lines
                continue
                
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_path, filename)
            
            print(f"Downloading ({i+1}/{len(all_files)}): {filename}")
            sftp.get(remote_file, local_file)
        
        print(f"Downloaded {len(all_files)} files to: {local_path}")
        return True
    
    except Exception as e:
        print(f"Directory download error: {e}")
        return False
    
    finally:
        sftp.close()

def main():
    """Main process"""
    args = parse_arguments()
    
    # Get script path at same level
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Set local save destination directories
    game_data_dir = script_dir / "game_data"
    config_dir = script_dir / "config"
    
    # Check if SSH authentication is specified
    if not args.password and not args.key_file:
        password = input(f"Enter password for {args.username}@{args.host}: ")
        args.password = password
    
    # SSH connection
    ssh = connect_ssh(
        args.host, 
        args.port, 
        args.username, 
        args.key_file, 
        args.password
    )
    
    if not ssh:
        print("SSH connection failed")
        return
    
    try:
        # Get home directory path
        stdin, stdout, stderr = ssh.exec_command('echo $HOME')
        home_dir = stdout.read().decode().strip()
        
        # Set remote paths
        remote_game_data_path = f"{home_dir}/boardgame_analyzer/game_data"
        remote_config_path = f"{home_dir}/boardgame_analyzer/config"
        
        # Upload process (if no-upload flag is not set)
        if not args.no_upload:
            print("\nUploading files that exist on PC but not on Raspberry Pi...")
            
            # Get file lists from local and remote
            local_game_files = get_local_yaml_files(game_data_dir)
            remote_game_files = get_remote_yaml_files(ssh, remote_game_data_path)
            
            # Identify files that don't exist on remote
            missing_game_files = [f for f in local_game_files if f not in remote_game_files]
            
            # Upload game data files
            upload_files(ssh, game_data_dir, remote_game_data_path, missing_game_files)
            
            # Process configuration files
            if args.config:
                local_config_files = get_local_yaml_files(config_dir)
                remote_config_files = get_remote_yaml_files(ssh, remote_config_path)
                
                # Identify files that don't exist on remote
                missing_config_files = [f for f in local_config_files if f not in remote_config_files]
                
                # Upload configuration files
                upload_files(ssh, config_dir, remote_config_path, missing_config_files)
        
        # Delete YAML files in local directories
        print("\nDeleting YAML files in local directories...")
        clean_local_yaml_files(game_data_dir)
        if args.config:
            clean_local_yaml_files(config_dir)
        
        # Download current game data
        print(f"\nDownloading game data... ({remote_game_data_path})")
        download_directory(ssh, remote_game_data_path, game_data_dir)
        
        # Also fetch configuration files if specified
        if args.config:
            print(f"\nDownloading configuration files... ({remote_config_path})")
            download_directory(ssh, remote_config_path, config_dir)
        
        print("\nData synchronization completed")
        print(f"Game data saved to: {os.path.abspath(game_data_dir)}")
        if args.config:
            print(f"Configuration files saved to: {os.path.abspath(config_dir)}")
    
    except Exception as e:
        print(f"Error occurred during processing: {e}")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    main()