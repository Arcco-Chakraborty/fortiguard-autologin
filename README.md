# FortiGuard Auto-Login

Tired of logging into the BITS WiFi every time? Same.

This tool sits in your system tray and automatically re-logs you in whenever FortiGuard kicks you out. No browser, no typing passwords, no pain. Just WiFi that works.

Built for BITS Pilani. Works on Windows and macOS.

## Setup (takes 30 seconds)

1. Grab the latest build from [Releases](../../releases/latest)
   - **Windows**: `FortiGuardAutoLogin.exe`
   - **Mac**: `FortiGuardAutoLogin-mac`
2. Run it
   - **Windows**: You'll see a "Windows protected your PC" popup. Click **More info** then **Run anyway**. This is normal for unsigned apps. It only happens the first time.
   - **Mac**: If blocked, go to System Settings > Privacy & Security and click **Open Anyway**.
3. Enter your BITS WiFi credentials (the ones you use on the FortiGuard login page) and hit **Save & Start**

Done. It runs in the background now. It also auto-starts when you boot your laptop so you never have to think about it again.

## How it works

- Checks your connection every 10 seconds
- If FortiGuard has logged you out, it grabs the login page, extracts the magic token, and posts your credentials automatically
- Sends keepalive pings so you stay connected longer
- If something goes wrong, it retries with backoff

## System tray

Look for the colored dot in your system tray (bottom right, you might need to click the ^ arrow).

- **Green dot** - you're connected
- **Yellow dot** - reconnecting, give it a sec

Right-click for options:
- Check status
- Update your credentials
- Turn auto-start on/off
- Quit

## Your credentials are safe

Passwords are stored in your OS credential manager (Windows Credential Manager / macOS Keychain). Nothing is saved in plain text, nothing leaves your machine.

## Building from source

If you want to build it yourself instead of using the release:

```
pip install -r requirements.txt
python main.py
```

Or build the exe:

```
pip install pyinstaller
pyinstaller --onefile --windowed --name FortiGuardAutoLogin main.py
```

