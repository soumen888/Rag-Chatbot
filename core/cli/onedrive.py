import sys
from services.microsoft.auth import MicrosoftAuthManager
from services.microsoft.client import MicrosoftClient

def handle_onedrive_cli(args):
    """Handles Microsoft OneDrive file listing and search."""
    if len(args) < 3:
        print("[!] Usage:")
        print("  ragchat onedrive <profile> list")
        print("  ragchat onedrive <profile> list <folder_path>")
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
                files = client.onedrive.search_onedrive_files(query=target_extensions[0])
            else:
                files = client.onedrive.list_onedrive_files(folder_path=folder_path)
                
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
                    header_str = f"OneDrive Files Search [Filter: {', '.join(target_extensions)}]" if filter_ext else f"OneDrive Files ({folder_path or 'Root'})"
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
    else:
        print(f"[!] Unknown action: '{action}'. Use: list")
        sys.exit(1)
