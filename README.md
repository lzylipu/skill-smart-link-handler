# Smart Link Handler

Auto-detect Quark/YouTube/Bilibili links and trigger downloads.

## Features

- Quark share link auto-save via QAS
- YouTube/Bilibili video download via MeTube
- Episode matching (E01, E02...)
- aria2 integration for batch downloads

## Prerequisites

| Variable | Description |
|----------|-------------|
| QAS_ENDPOINT | QAS service URL |
| QAS_TOKEN | QAS API token |
| ALIST_ENDPOINT | Alist service URL |
| ALIST_TOKEN | Alist auth token |
| ARIA2_ENDPOINT | aria2 RPC URL |
| ARIA2_TOKEN | aria2 RPC token |

## Usage

```bash
# Download specific episodes
python3 scripts/quark-download.py "share_link" E01 E05 E10

# Download all
python3 scripts/quark-download.py "share_link"

# Task management
python3 scripts/quark-download.py --list
python3 scripts/quark-download.py --clear
```

## License

MIT
