# browser-file-server — Quick Start

A single one-liner downloads, installs, and runs the server in the background.
Open it in any browser at the URL it prints.

## The one-liner

```bash
curl -sL https://raw.githubusercontent.com/YuGiMob/browser-file-server/main/fileserver.py -o fileserver.py && nohup python3 fileserver.py ~ 8080 > fileserver.log 2>&1 & disown
```

Then open: **http://localhost:8080**

## What it does

1. `curl -sL … -o fileserver.py` — downloads the latest `fileserver.py` to the current directory
2. `nohup … &` — runs the server detached so it survives closing the terminal
3. `disown` — detaches the job from the shell's job table
4. `> fileserver.log 2>&1` — captures output to a log file

The default path it serves is `~` (your home directory). The default port is `8080`. Both can be changed by editing the last two arguments of the command.

## Useful follow-ups

```bash
# View the log
tail -f fileserver.log

# Stop the server
pkill -f fileserver.py

# Serve a different directory on a different port
nohup python3 fileserver.py /path/to/serve 9000 > fileserver.log 2>&1 & disown

# Open the file in your editor (or just edit through the browser at /?p=fileserver.py&edit=1)
```

## Requirements

- Python 3 (no extra packages — uses only the standard library)
- `curl` (for the download; alternatively you can `git clone` the repo and run the script directly)
