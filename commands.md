# Predefined CLI Commands Reference

Use these commands directly in your terminal to sync, link, and manipulate workspace data. These commands run local operations or direct API calls, bypassing the LLM to save token costs.

---

## 1. Google Account Commands

### Account Management
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat link google <profile>` | Authenticate and link a new Google account profile. | `ragchat link google dev` |
| `ragchat rename-profile google <old_name> <new_name>` | Rename a Google account profile and migrate database records. | `ragchat rename-profile google dev work` |

### Gmail
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat -g <profile> <time>` | Sync and list Gmail messages within a specific time window. | `ragchat -g dev 10h` <br> `ragchat -g dev 1m` |

### Google Sheets
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat sheet <profile> list` | Lists all spreadsheet files and their IDs in your Google Drive. | `ragchat sheet dev list` |
| `ragchat sheet <profile> create <title>` | Creates a new Google Spreadsheet workbook. | `ragchat sheet dev create "My Budget"` |
| `ragchat sheet <profile> <spreadsheet_id> add-tab <tab_title>` | Creates a new tab (sheet) inside an existing spreadsheet. | `ragchat sheet dev <id> add-tab "Sheet2"` |
| `ragchat sheet <profile> <spreadsheet_id> delete-tab <tab_title>` | Deletes an existing tab (sheet) from a spreadsheet. | `ragchat sheet dev <id> delete-tab "Sheet2"` |
| `ragchat sheet <profile> <spreadsheet_id> get-tabs` | Lists all sheet tab names inside an existing spreadsheet. | `ragchat sheet dev <id> get-tabs` |
| `ragchat sheet <profile> <spreadsheet_id> append <range> <values>` | Appends a row of comma-separated values to a sheet range. | `ragchat sheet dev <id> append "Sheet1!A1" "Name,Email"` |

---

## 2. Microsoft Account Commands

### Account Management
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat link microsoft <profile>` | Authenticate and link a new Microsoft account profile. | `ragchat link microsoft work` |
| `ragchat rename-profile microsoft <old_name> <new_name>` | Rename a Microsoft account profile and migrate database records. | `ragchat rename-profile microsoft dev personal` |

### Outlook Mail
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat -m <profile> <time>` | Sync and list Outlook emails within a specific time window. | `ragchat -m work 2d` |

---

## 3. Social & Messaging Commands

### Telegram
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat link telegram <profile>` | Link a Telegram account profile. | `ragchat link telegram personal` |

### Discord
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat link discord <profile>` | Link a Discord account profile (Bot or User token). | `ragchat link discord work` |

---

## 4. General Commands

### Interactive Mode & Sync
| Command Template | Description | Example Usage |
| :--- | :--- | :--- |
| `ragchat` | Launches the interactive visual text menu. | `ragchat` |
| `ragchat chat <collection>` | Start interactive chat with an ingested collection. | `ragchat chat work_docs` |
| `ragchat sync` | Run full sync daemon on connected channels. | `ragchat sync` |
| `ragchat help` | Displays the terminal help guide. | `ragchat --help` |

---

## Time Window Parameter Reference

Append these suffix letters to numbers for time windows:

| Suffix | Meaning | Example |
| :---: | :--- | :--- |
| **h** | Hours | `10h` (last 10 hours) |
| **d** | Days | `3d` (last 3 days) |
| **w** | Weeks | `2w` (last 2 weeks) |
| **m** | Months | `1m` (last 30 days) |
| **y** | Years | `1y` (last 365 days) |
