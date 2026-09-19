from logging import getLogger, StreamHandler, FileHandler, Formatter, INFO, DEBUG
logger1 = getLogger(__name__+".1")
logger1.setLevel(INFO)
formatter = Formatter(fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console = StreamHandler()
console.setFormatter(formatter)
console.setLevel(INFO)

file = FileHandler(filename='main.log', encoding='utf-8')
file.setFormatter(formatter)
file.setLevel(INFO)

logger1.addHandler(console)
logger1.addHandler(file)


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        # if msg.startswith('[debug] '): 
        #     pass
        # else:
        #     self.info(msg)
        logger1.debug(f"YOUTUBE-DLP: {msg}")

    def info(self, msg):
        logger1.info(f"YOUTUBE-DLP: {msg}")

    def warning(self, msg):
        #if not ('Some formats' or 'Falling back') in msg:
        logger1.warning(f"YOUTUBE-DLP: {msg}")

    def error(self, msg):
        # if 'is not a valid URL. Set --default-search "ytsearch"' and 'to search YouTube' in msg:
        #     pass
        # else:
        logger1.error(f"YOUTUBE-DLP: {msg}")
