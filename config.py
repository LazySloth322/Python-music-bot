import yt_logger

MAX_PLAYLIST_LENGTH = 250

COMMAND_PREFIX="!"

BOT_TOKEN='YOUR TOKEN'

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'simulate': True,
    #'preferredquality': 0,
    'audioformat':'opus',
    'key': 'FFmpegExtractAudio',
    'quiet': True,
    'logger': yt_logger.MyLogger(),
    'player_client': 'web',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False
    #'ignoreerrors': True,
}

FFMPEG_PATH = "ffmpeg.exe"
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5' , 
    'options': '-vn'

}
