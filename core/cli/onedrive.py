import sys
import os
from ragchat_core.services.microsoft.auth import MicrosoftAuthManager
from ragchat_core.services.microsoft.client import MicrosoftClient

def handle_onedrive_cli(args):
    """Handles Microsoft OneDrive file listing, search, upload, and download."""
    if len(args) < 3:
        print("[!] Usage:")
        print("  ragchat onedrive <profile> list [--all] [folder_path]")
        print("  ragchat onedrive <profile> list [--all] --filter <excel|word|powerpoint>")
        print("  ragchat onedrive <profile> download <item_id> [output_path]")
        print("  ragchat onedrive <profile> upload <local_file_or_folder_path> [parent_folder_id]")
        sys.exit(1)

    profile_name = args[1]
    action = args[2].lower()
    
    try:
        token = MicrosoftAuthManager().get_token(profile_name)
        client = MicrosoftClient(token)
    except Exception as e:
        print(f"[!] Authentication failed for Microsoft profile '{profile_name}': {e}")
        sys.exit(1)

    if action == 'list':
        filter_all = '--all' in args
        if filter_all:
            args.remove('--all')

        filter_ext = None
        if '--filter' in args:
            idx = args.index('--filter')
            if idx + 1 < len(args):
                filter_ext = args[idx + 1].lower().strip('.')
                args = args[:idx]
        
        target_extensions = [filter_ext] if filter_ext else []
        if filter_ext in ['excel', 'xlsx', 'xls', 'sheets']:
            target_extensions = ['xlsx', 'xls', 'xlsm']
        elif filter_ext in ['word', 'doc', 'docx', 'docs']:
            target_extensions = ['docx', 'doc', 'docm']
        elif filter_ext in ['powerpoint', 'ppt', 'pptx', 'slides']:
            target_extensions = ['pptx', 'ppt']
            
        folder_path = args[3] if len(args) > 3 else None
        try:
            if filter_ext:
                print(f"[*] Searching recursively for {target_extensions} files...")
                files = client.onedrive.search_onedrive_files(query=target_extensions[0], filter_media=not filter_all)
            else:
                files = client.onedrive.list_onedrive_files(folder_path=folder_path, filter_media=not filter_all)
                
            if not files:
                print("[-] No files found matching your request.")
            else:
                filtered_files = []
                for f in files:
                    if "folder" in f:
                        if not filter_ext:
                            filtered_files.append(f)
                    else:
                        if filter_ext:
                            matches_any = any(f['name'].lower().endswith(f".{ext}") for ext in target_extensions)
                            if matches_any:
                                filtered_files.append(f)
                        else:
                            filtered_files.append(f)
                             
                if not filtered_files:
                    print(f"[-] No files matching filter '{filter_ext}' found.")
                else:
                    header_str = f"OneDrive Files Search [Filter: {filter_ext}]" if filter_ext else f"OneDrive Files ({folder_path or 'Root'})"
                    print(f"[+] {header_str}:")
                    for f in filtered_files:
                        ftype = "Folder" if "folder" in f else "File"
                        parent_path = f.get("parentReference", {}).get("path", "")
                        if parent_path.startswith("/drive/root:"):
                            rel_dir = parent_path.split("/drive/root:")[-1]
                            print(f"  - [{ftype}] {rel_dir}/{f['name']} (ID: {f['id']})")
                        else:
                            print(f"  - [{ftype}] {f['name']} (ID: {f['id']})")
        except Exception as e:
            print(f"[!] Failed to list OneDrive files: {e}")
        sys.exit(0)

    elif action == 'download':
        if len(args) < 4:
            print("[!] Usage: ragchat onedrive <profile> download <item_id> [output_path]")
            sys.exit(1)
        item_id = args[3]
        
        try:
            meta_url = f"{client.onedrive.base_url}/me/drive/items/{item_id}"
            meta_response = client.onedrive.session.get(meta_url)
            meta_response.raise_for_status()
            filename = meta_response.json().get("name", "downloaded_file")
        except Exception as e:
            print(f"[!] Failed to fetch file details for ID '{item_id}': {e}")
            sys.exit(1)

        output_path = args[4] if len(args) > 4 else None
        if not output_path:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop", "ragchat_downloads")
            os.makedirs(desktop_dir, exist_ok=True)
            output_path = os.path.join(desktop_dir, filename)
        else:
            output_path = os.path.abspath(os.path.expanduser(output_path.strip("'\"")))
            if os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
                
        print(f"[*] Downloading file to: {output_path}...")
        try:
            client.onedrive.download_onedrive_file_to_disk(item_id, output_path)
            print(f"[+] Download complete: {output_path}")
        except Exception as e:
            print(f"[!] Download failed: {e}")
            sys.exit(1)
        sys.exit(0)

    elif action == 'upload':
        if len(args) < 4:
            print("[!] Usage: ragchat onedrive <profile> upload <local_path> [parent_folder_id]")
            sys.exit(1)
            
        raw_local_path = args[3]
        local_path = os.path.abspath(os.path.expanduser(raw_local_path.strip("'\"")))
        parent_id = args[4] if len(args) > 4 else None
        
        if not os.path.exists(local_path):
            print(f"[!] Local path does not exist: {local_path}")
            sys.exit(1)
            
        def get_files_to_upload(dir_path, max_files=500):
            file_list = []
            ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv'}
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if d not in ignored_dirs]
                for file in files:
                    if file.startswith('.') or file in ['Thumbs.db']:
                        continue
                    full_path = os.path.join(root, file)
                    file_list.append(full_path)
                    if len(file_list) >= max_files:
                        print(f"[!] Hit safety folder limit of {max_files} files.")
                        return file_list
            return file_list

        if os.path.isdir(local_path):
            files_to_upload = get_files_to_upload(local_path)
            print(f"[*] Found {len(files_to_upload)} files to upload recursively from folder.")
            confirm = input("Confirm upload? (y/n, default y): ").strip().lower()
            if confirm in ['n', 'no']:
                print("[-] Upload aborted.")
                sys.exit(0)
                
            try:
                if parent_id:
                    folder_url = f"{client.onedrive.base_url}/me/drive/items/{parent_id}/children"
                else:
                    folder_url = f"{client.onedrive.base_url}/me/drive/root/children"
                
                body = {
                    "name": os.path.basename(local_path),
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
                folder_resp = client.onedrive.session.post(folder_url, json=body)
                folder_resp.raise_for_status()
                target_parent_id = folder_resp.json()['id']
                print(f"[+] Created remote folder '{folder_resp.json()['name']}' (ID: {target_parent_id})")
            except Exception as e:
                print(f"[!] Failed to create remote folder: {e}")
                sys.exit(1)

            success_count = 0
            for idx, file_path in enumerate(files_to_upload):
                rel_dir = os.path.relpath(os.path.dirname(file_path), local_path)
                current_parent = target_parent_id
                if rel_dir != ".":
                    parts = rel_dir.split(os.sep)
                    for part in parts:
                        try:
                            sub_folder_url = f"{client.onedrive.base_url}/me/drive/items/{current_parent}/children"
                            sub_body = {
                                "name": part,
                                "folder": {},
                                "@microsoft.graph.conflictBehavior": "fail"
                            }
                            sub_resp = client.onedrive.session.post(sub_folder_url, json=sub_body)
                            if sub_resp.status_code == 201:
                                current_parent = sub_resp.json()['id']
                            else:
                                list_resp = client.onedrive.session.get(sub_folder_url)
                                for item in list_resp.json().get("value", []):
                                    if item["name"] == part and "folder" in item:
                                        current_parent = item["id"]
                                        break
                        except Exception:
                            pass
                            
                print(f"[*] Uploading ({idx+1}/{len(files_to_upload)}): {os.path.basename(file_path)}")
                try:
                    client.onedrive.upload_large_file_from_disk(file_path, parent_id=current_parent)
                    success_count += 1
                except Exception as e:
                    print(f"[!] Failed to upload {os.path.basename(file_path)}: {e}")
            print(f"[+] Finished folder upload. Successfully uploaded {success_count}/{len(files_to_upload)} files.")
            sys.exit(0)
        else:
            print(f"[*] Uploading file: {local_path}...")
            try:
                res = client.onedrive.upload_large_file_from_disk(local_path, parent_id=parent_id)
                print(f"[+] Upload complete: {res.get('name')} (ID: {res.get('id')})")
            except Exception as e:
                print(f"[!] Upload failed: {e}")
                sys.exit(1)
            sys.exit(0)
    else:
        print(f"[!] Unknown action: '{action}'. Use: list, download, upload")
        sys.exit(1)
