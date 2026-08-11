import sys
from services.google.auth import GoogleAuthManager
from services.google.client import GoogleClient

def handle_sheet_cli(args):
    """Handles Google Sheets management commands."""
    if len(args) < 3:
        print("[!] Usage:")
        print("  ragchat sheet <profile> list")
        print("  ragchat sheet <profile> create <title>")
        print("  ragchat sheet <profile> <spreadsheet_id> add-tab <tab_title>")
        print("  ragchat sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
        sys.exit(1)
        
    profile_name = args[1]
    action_or_id = args[2]
    
    if action_or_id.lower() not in ['list'] and len(args) < 4:
        print("[!] Usage:")
        print("  ragchat sheet <profile> create <title>")
        print("  ragchat sheet <profile> <spreadsheet_id> add-tab <tab_title>")
        print("  ragchat sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
        sys.exit(1)
    
    try:
        creds = GoogleAuthManager().get_credentials(profile_name)
        client = GoogleClient(creds)
    except Exception as e:
        print(f"[!] Authentication failed for Google profile '{profile_name}': {e}")
        sys.exit(1)
        
    if action_or_id.lower() == 'list':
        try:
            query = "mimeType = 'application/vnd.google-apps.spreadsheet'"
            files = client.drive.list_drive_files(max_results=50, query=query)
            if not files:
                print("[-] No spreadsheets found in your Drive.")
            else:
                print("[+] Spreadsheets in Google Drive:")
                for f in files:
                    print(f"  - {f['name']} (ID: {f['id']})")
        except Exception as e:
            print(f"[!] Failed to list spreadsheets: {e}")
        sys.exit(0)

    elif action_or_id.lower() == 'create':
        title = args[3]
        try:
            result = client.sheets.create_spreadsheet(title)
            print(f"[+] Spreadsheet created successfully!")
            print(f"    ID: {result.get('spreadsheetId')}")
            print(f"    URL: https://docs.google.com/spreadsheets/d/{result.get('spreadsheetId')}/edit")
        except Exception as e:
            print(f"[!] Failed to create spreadsheet: {e}")
        sys.exit(0)
        
    else:
        spreadsheet_id = action_or_id
        sub_action = args[3].lower()
        
        if sub_action == 'add-tab':
            if len(args) < 5:
                print("[!] Missing tab title. Usage: sheet <profile> <spreadsheet_id> add-tab <tab_title>")
                sys.exit(1)
            tab_title = args[4]
            try:
                client.sheets.add_sheet(spreadsheet_id, tab_title)
                print(f"[+] Added tab '{tab_title}' to spreadsheet '{spreadsheet_id}'.")
            except Exception as e:
                print(f"[!] Failed to add sheet tab: {e}")
            sys.exit(0)
            
        elif sub_action == 'append':
            if len(args) < 6:
                print("[!] Missing parameters. Usage: sheet <profile> <spreadsheet_id> append <range> <comma_separated_values>")
                sys.exit(1)
            range_name = args[4]
            raw_values = args[5]
            row_data = [val.strip() for val in raw_values.split(',')]
            try:
                client.sheets.append_spreadsheet_values(spreadsheet_id, range_name, [row_data])
                print(f"[+] Appended row {row_data} to range '{range_name}'.")
            except Exception as e:
                print(f"[!] Failed to append values: {e}")
            sys.exit(0)
            
        elif sub_action == 'delete-tab':
            if len(args) < 5:
                print("[!] Missing tab title. Usage: sheet <profile> <spreadsheet_id> delete-tab <tab_title>")
                sys.exit(1)
            tab_title = args[4]
            try:
                client.sheets.delete_sheet(spreadsheet_id, tab_title)
                print(f"[+] Deleted tab '{tab_title}' from spreadsheet '{spreadsheet_id}'.")
            except Exception as e:
                print(f"[!] Failed to delete sheet tab: {e}")
            sys.exit(0)
            
        elif sub_action == 'get-tabs':
            try:
                tabs = client.sheets.get_sheet_names(spreadsheet_id)
                print(f"[+] Tabs in spreadsheet '{spreadsheet_id}':")
                for tab in tabs:
                    print(f"  - {tab}")
            except Exception as e:
                print(f"[!] Failed to fetch tab names: {e}")
            sys.exit(0)
            
        else:
            print(f"[!] Unknown sheet action: '{sub_action}'. Use: add-tab, append, get-tabs")
            sys.exit(1)
