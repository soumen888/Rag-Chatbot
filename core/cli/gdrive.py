import sys
import os
from ragchat_core.services.google.auth import GoogleAuthManager
from ragchat_core.services.google.client import GoogleClient

def handle_drive_cli(args):
    """Handles Google Drive file listing, search, upload, and download."""
    if len(args) < 3:
        print("[!] Usage:")
        print("  ragchat drive <profile> list [--all] [--filter <docs|sheets|slides>]")
        print("  ragchat drive <profile> download <file_id> [output_path]")
        print("  ragchat drive <profile> upload <local_file_or_folder_path> [parent_folder_id]")
        sys.exit(1)

    profile_name = args[1]
    action = args[2].lower()

    try:
        creds = GoogleAuthManager().get_credentials(profile_name)
        client = GoogleClient(creds)
    except Exception as e:
        print(f"[!] Authentication failed for Google profile '{profile_name}': {e}")
        sys.exit(1)

    if action == 'list':
        filter_all = '--all' in args
        if filter_all:
            args.remove('--all')

        filter_ext = None
        if '--filter' in args:
            idx = args.index('--filter')
            if idx + 1 < len(args):
                filter_ext = args[idx + 1].lower().strip()
                args = args[:idx]

        query_parts = []
        if filter_ext in ['sheets', 'excel', 'xlsx', 'xls']:
            query_parts.append(
                "mimeType = 'application/vnd.google-apps.spreadsheet' or "
                "mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or "
                "name contains '.xls'"
            )
        elif filter_ext in ['docs', 'word', 'docx', 'doc']:
            query_parts.append(
                "mimeType = 'application/vnd.google-apps.document' or "
                "mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or "
                "name contains '.doc'"
            )
        elif filter_ext in ['slides', 'powerpoint', 'ppt', 'pptx']:
            query_parts.append(
                "mimeType = 'application/vnd.google-apps.presentation' or "
                "mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation' or "
                "name contains '.ppt'"
            )

        query = " and ".join(query_parts) if query_parts else None

        try:
            files = client.drive.list_drive_files(max_results=50, query=query, filter_media=not filter_all)
            if not files:
                print("[-] No files found matching your request.")
            else:
                header_str = f"Google Drive Search [Filter: {filter_ext}]" if filter_ext else "Google Drive Files"
                print(f"[+] {header_str}:")
                for f in files:
                    ftype = "File"
                    if f['mimeType'] == 'application/vnd.google-apps.folder':
                        ftype = "Folder"
                    elif f['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                        ftype = "Google Sheets"
                    elif f['mimeType'] == 'application/vnd.google-apps.document':
                        ftype = "Google Docs"
                    elif f['mimeType'] == 'application/vnd.google-apps.presentation':
                        ftype = "Google Slides"
                    print(f"  - [{ftype}] {f['name']} (ID: {f['id']})")
        except Exception as e:
            print(f"[!] Failed to list Google Drive files: {e}")
        sys.exit(0)

    elif action == 'download':
        if len(args) < 4:
            print("[!] Usage: ragchat drive <profile> download <file_id> [output_path]")
            sys.exit(1)
        file_id = args[3]
        
        try:
            meta = client.drive.service.files().get(fileId=file_id, fields="name").execute(num_retries=5)
            filename = meta.get("name", "downloaded_file")
        except Exception as e:
            print(f"[!] Failed to fetch file details for ID '{file_id}': {e}")
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
            client.drive.download_large_file_to_disk(file_id, output_path)
            print(f"[+] Download complete: {output_path}")
        except Exception as e:
            print(f"[!] Download failed: {e}")
            sys.exit(1)
        sys.exit(0)

    elif action == 'upload':
        if len(args) < 4:
            print("[!] Usage: ragchat drive <profile> upload <local_path> [parent_folder_id]")
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
                folder_meta = client.drive.create_drive_file(
                    os.path.basename(local_path), 
                    mime_type='application/vnd.google-apps.folder',
                    parent_id=parent_id
                )
                target_parent_id = folder_meta['id']
                print(f"[+] Created remote folder '{folder_meta['name']}' (ID: {target_parent_id})")
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
                            sub_folder = client.drive.create_drive_file(
                                part,
                                mime_type='application/vnd.google-apps.folder',
                                parent_id=current_parent
                            )
                            current_parent = sub_folder['id']
                        except Exception:
                            pass
                            
                print(f"[*] Uploading ({idx+1}/{len(files_to_upload)}): {os.path.basename(file_path)}")
                try:
                    client.drive.upload_large_file_from_disk(file_path, parent_id=current_parent)
                    success_count += 1
                except Exception as e:
                    print(f"[!] Failed to upload {os.path.basename(file_path)}: {e}")
            print(f"[+] Finished folder upload. Successfully uploaded {success_count}/{len(files_to_upload)} files.")
            sys.exit(0)
        else:
            print(f"[*] Uploading file: {local_path}...")
            try:
                res = client.drive.upload_large_file_from_disk(local_path, parent_id=parent_id)
                print(f"[+] Upload complete: {res.get('name')} (ID: {res.get('id')})")
            except Exception as e:
                print(f"[!] Upload failed: {e}")
                sys.exit(1)
            sys.exit(0)
    else:
        print(f"[!] Unknown action: '{action}'. Use: list, download, upload")
        sys.exit(1)
