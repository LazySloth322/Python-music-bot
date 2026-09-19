# __WORK IN PROGRESS__

# About
Multiserver python-based discord bot for listening SoundCloud tracks. This bot have dynamic music queue and support playlists up to 250 tracks.  

Interface: RU  
Logging: ENG

## Requirements
- [ffmpeg](https://www.ffmpeg.org/) binary to be in the same folder.
- `pip install -r requirements.txt`
- All Privileged Gateway Intents must be turned __ON__

## Commands
- **`-ping`** – current bot ping
- **`-hello`** – test command
- **`-play [link or title]`** – play single track
- **`-search [title]`** – precise search by name
- **`-loop`** – loop current track
- **`-unloop`** – unloop current track
- **`-np`** – show current playing track
- **`-pause`** – pause current track
- **`-resume`** – resume current paused track
- **`-skip`** – skip current track
- **`-queue`** – show tracks queue
- **`-clear`** – clear queue
  - _If bot exits the voice channel correctly, the queue is cleared automatically_
- **`-jump [№ in queue]`** – play track by its № in queue
- **`-leave`** – kick bot out of current voice channel (unprotected)
  - _If bot exits the voice channel correctly, the queue is cleared automatically_
## Known issues
- If you have any trouble with yt-dlp, try update it to `nightly` version.
