import sys
from ragchat_core.services.google.auth import GoogleAuthManager
from ragchat_core.services.google.client import GoogleClient

def handle_drive_cli(args):
    """Handles Google Drive file searching and listing."""
    if len(args) < 3:
        print("[!] Usage:")
        print("  ragchat drive <profile> list")
        print("  ragchat drive <profile> list --filter <docs|sheets|slides>")
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
            files = client.drive.list_drive_files(max_results=50, query=query)
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
    else:
        print(f"[!] Unknown action: '{action}'. Use: list")
        sys.exit(1)
