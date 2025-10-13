import asyncio
from discord import ClientException
from tolya_string import *
from config import *
from math import *
import nest_asyncio
import discord
from discord.ext import commands
import datetime
from datetime import timezone
import yt_dlp
from youtube_search import YoutubeSearch
import tolya_queue
from logging import getLogger, StreamHandler, FileHandler, Formatter, INFO, DEBUG

nest_asyncio.apply()
songs_queue=tolya_queue.Queue()


### LOGGING SECTION ###
logger = getLogger('__name__')
logger.setLevel(DEBUG)

formatter = Formatter(fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console = StreamHandler()
console.setFormatter(formatter)
console.setLevel(DEBUG)

file = FileHandler(filename='main.log', encoding='utf-8')
file.setFormatter(formatter)
file.setLevel(DEBUG)

logger.addHandler(console)
logger.addHandler(file)

######

intents = discord.Intents.all()
intents.message_content= True
intents.voice_states = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX,intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    logger.info(f'logged as {bot.user} successfully')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='mc hovanskiy'))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.message.reply(COMMAND_ERROR)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member,before,after):
    #print(type(str(member)),str(member.name))
    if str(member.name)==str(bot.user.name):
        pass
        #print(f"member: {member}; before: {before}; after: {after}")
    return


### SOME DEFAULT COMMANDS BLOCK ###
@bot.command(aliases=['HELP','Help','рудз','РУДЗ','Рудз'])
async def help(ctx,page=1):
    # cac=current available commands
    cac = [[HELP_PING, HELP_HELLO, HELP_PLAY, HELP_SEARCH, HELP_LOOP, HELP_UNLOOP, HELP_NOWPLAYING,
            HELP_PAUSE, HELP_RESUME, HELP_SKIP, HELP_JUMP, HELP_LEAVE, HELP_QUEUE, HELP_CLEAR],
           [HELP_PLAY_SHORTCUT, HELP_SEARCH_SHORTCUT, HELP_QUEUE_SHORTCUT, HELP_LEAVE_SHORTCUT]]
    maxpage = len(cac)
    if (page<1 or page>maxpage):
        await ctx.message.reply(HELP_NO_PAGE + f' ({page})')
        return
    else:
        await ctx.message.reply(f'{"".join(cac[page-1])}\n'
                f'{HELP_CURRENT_PAGE[0]} `{page} {HELP_CURRENT_PAGE[1]} {maxpage}` ({HELP_CURRENT_PAGE[2]} `-help 2`)')


@bot.command(aliases=['PING','Ping','зштп','ЗШТП','Зштп'])
async def ping(ctx):
    await ctx.message.reply(f'{round(bot.latency * 1000)}ms')


@bot.command(aliases=['HELLO','Hello','руддщ','РУДДЩ','Руддщ'])
async def hello(ctx):
    await ctx.send(f'{ctx.message.author.mention} :wave:')


async def msg_delete(msg):
    try:
        await msg.delete()
        return
    except Exception as e:
        logger.error(f'Message delete {e}')
        return


### MAIN BLOCK ###

@bot.command(aliases=['j', 'J', 'Join', 'JOIN', 'о', 'О','ощфшт','Ощшт','ОЩШТ'])
async def join(ctx):
    try:
        if ctx.message.author.voice:
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect(timeout=3,reconnect=False,self_deaf=True)
            else:
                if ctx.message.author.voice.channel.id != ctx.voice_client.channel.id:
                    if ctx.voice_client.is_playing():
                        await ctx.message.reply(JOIN_IS_IN_OTHER_CHANNEL)
                        return 1
                    else:
                        await ctx.voice_client.disconnect()
                        await ctx.author.voice.channel.connect(timeout=3,reconnect=False,self_deaf=True)
        else:
            await ctx.message.reply(JOIN_AUTHOR_NOT_IN_VOICE)
            return 1
    except asyncio.TimeoutError as e:
        await ctx.channel.send(JOIN_ERROR)
        logger.error(f'Bot cannot connect: {e}')
        return 1


async def add(ctx, url):
    if ((" -" in url) or ("-З" in url) or ("-з" in url) or ("-p" in url) or ("-P" in url)):
        #anti "-play -play -play ... " part
        url=url.split(" ")[len(url.split(" "))-1]

    author=ctx.message.author.name
    serverid=ctx.guild.id

    if ("&start_radio" in url) or ("=RDMM" in url) or ("=LL" in url) or ("=LM" in url) or ("&list=RD" in url):
        # проверка на "Мой джем" и на "Понравившиеся"
        await ctx.channel.send(ADD_MYMIX_WARNING)
        url = url.split("&list=")[0]

    url = url.split("?si=")[0]

    # Плейлисты
    if 'list' in url:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                msg = await ctx.channel.send(ADD_ON_PL_ADDING)
                playlist_info = ydl.extract_info(url,download=False,process=False)
                #process=False to get ONLY playlist info (length)
                if 'entries' in playlist_info:
                    entries=list(playlist_info['entries'])
                elif 'ie_key' in playlist_info:
                    url = playlist_info['url']
                    playlist_info = ydl.extract_info(url,download=False,process=False)
                    # process=False to get ONLY playlist info (length)
                    entries = list(playlist_info['entries'])
                else:
                    logger.debug(f'Incorrect playlist given by {author} in \"{ctx.guild.name}\"')
                    await msg_delete(msg)
                    raise Exception("Incorrect playlist given")

                playlist_len = len(entries)
                if playlist_len > MAX_PLAYLIST_LENGTH:
                    await ctx.message.reply(f'{ADD_PL_LEN_WARNING[0]} ({playlist_len}) '
                                            f'{ADD_PL_LEN_WARNING[1]} - {MAX_PLAYLIST_LENGTH} !\n'
                                            f'{ADD_PL_LEN_WARNING[2]} {MAX_PLAYLIST_LENGTH} {ADD_PL_LEN_WARNING[3]}.')
                    playlist_len=MAX_PLAYLIST_LENGTH

                start_time = datetime.datetime.now().timestamp()
                playtime = datetime.timedelta(seconds=0)
                playlist_name = playlist_info['title']
                try:
                    main_thumb = playlist_info['thumbnails'][0]['url']
                except:
                    main_thumb = "https://imgur.com/qSUM27B.png"
                skipped = ""

                for i in range(playlist_len):
                    try:
                        name = entries[i]['title']
                        #print(f"playlist: {i} {entries[i]}")
                        src_url=""
                        vid_url=entries[i]['url']
                        pause_time=0
                        no_play_time=0
                        try:
                            thumbnail_url = entries[i]['thumbnails'][0]['url']
                        except:
                            thumbnail_url = "https://imgur.com/qSUM27B.png"

                        length = datetime.timedelta(seconds=entries[i]['duration'])

                        if length > datetime.timedelta(seconds=60*60*24-1):  # more than 24h check
                             logger.error(f"Longer than 24h by {author} in \"{ctx.guild.name}\"")
                             raise Exception
                        else:
                            playtime += length
                            songs_queue.queue_add([name, length, start_time, src_url, vid_url, thumbnail_url, author,
                                                   pause_time,no_play_time],ctx.guild.id)
                    except:
                        #print(i)
                        skipped += f"{name}\n"
                        logger.debug(f'Track skipped – {name}.')

                if not skipped == "":
                    embed = discord.Embed(
                        description=f'**{ADD_PL_FINAL_INFO[0]}**\n[{playlist_name}]({url}) '
                                    f'({playtime})\n{ADD_PL_FINAL_INFO[1]}\n\n'
                                    f'_{ADD_PL_FINAL_INFO[2]}:\n\n{skipped} _', colour=discord.Colour.green())
                else:
                    embed = discord.Embed(
                        description=f'**{ADD_PL_FINAL_INFO[0]}**\n[{playlist_name}]({url}) '
                                    f'({playtime})\n{ADD_PL_FINAL_INFO[1]}\n\n',
                        colour=discord.Colour.green())
                embed.set_thumbnail(url=main_thumb)
                    
                await msg_delete(msg)
                await ctx.message.reply(embed=embed)
                logger.info(f"Playlist \"{playlist_name}\" ({url}) requested by {author} in \"{ctx.guild.name}\"")
                return
            except Exception as e:
                logger.error(f'Playlist error: {e}')
                #logger.exception(e)
                await ctx.message.reply(ADD_PL_PARSE_ERROR)
                return 1

    else:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            haveURL=False
            if ("youtube.com" or "youtu.be") in url:
                haveURL=True
                try:
                    info = ydl.extract_info(url.split(" ")[0], download=False, process=False)
                except Exception as e:
                    await ctx.message.reply(ADD_UNAVAILABLE_OR_AGE_RESTRICTION)
                    logger.error(f"Cannot extract info: {e} (Probably unavailable or age restricted)")
                    return 1
            else:
                msg = await ctx.channel.send(ADD_SEARCH_HINT)
                try:
                    info = (list(ydl.extract_info(f"ytsearch1:{url}", download=False,process=False)
                                            ['entries'])[0])
                    ydl.extract_info(info['url'], download=False, process=False)
                    #print(info)
                except Exception as e:
                    await msg_delete(msg)
                    await ctx.message.reply(ADD_UNAVAILABLE_OR_AGE_RESTRICTION)
                    logger.error(f"Cannot extract info: {e} (Probably unavailable or age restricted)")
                    return 1
            #print(info)
            ###checks
            if info['live_status']=='is_live':
                await ctx.message.reply(ADD_LIVE_STREAM_ERROR)
                logger.error("Live stream called")
                if not haveURL:
                    await msg_delete(msg)
                #raise Exception("Live stream called")
                return 1
            ###

            if not haveURL:
                #info = list(info['entries'])[0]
                url = info['url']
            else:
                url = info['original_url']
            start_time = datetime.datetime.now().timestamp()
            src_url = ""
            name = info['title']
            pause_time=0
            no_play_time=0
            try:
                thumbnail_url = info['thumbnails'][0]['url']
            except:
                thumbnail_url = "https://imgur.com/qSUM27B.png"
            length = datetime.timedelta(seconds=info['duration'])

            if length>datetime.timedelta(seconds=60*60*24-1): #more than 24h check
                embed = discord.Embed(description=f"{ADD_TRACK_LEN_ERROR[0]} - "
                                                  f"[{name}]({url}) {ADD_TRACK_LEN_ERROR[1]}!",
                                      colour=discord.Colour.red())
                logger.debug(f"Longer than 24h by {author} in \"{ctx.guild.name}\"")
            else:
                songs_queue.queue_add([name, length, start_time, src_url, url, thumbnail_url, author, pause_time,
                                       no_play_time], ctx.guild.id)
                embed = discord.Embed(description=f'**{ADD_TRACK_FINAL_INFO[0]}**\n'
                                                  f'[{name}]({url}) ({length})\n{ADD_TRACK_FINAL_INFO[1]}',
                                      colour=discord.Colour.green())
                embed.set_thumbnail(url=thumbnail_url)
                logger.info(f"{name} ({url}) requested by {author} in \"{ctx.guild.name}\"")
            if not haveURL:
                await msg_delete(msg)

            await ctx.message.reply(embed=embed)
            return

async def auto_skip(ctx,voice_client,avaliable=True):
    # next track after current ended if any left in queue
    serverid=ctx.guild.id
    if songs_queue.if_queue_exist(serverid):
        songs_queue.queue_next(serverid)
        songs_queue.set_start_time(serverid,datetime.datetime.now().timestamp())
        songs_queue.set_no_play_time(serverid,0)
        try:
            await audio_player(ctx,voice_client)
        except Exception as e:
            logger.error(f"audio_player: {e}")

async def audio_player(ctx,voice_client): #track player
    serverid=ctx.guild.id
    #channelid=ctx.channel.id
    try:
        if not voice_client.is_playing():
            if songs_queue.get_stream_link(serverid) == "":
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    try:
                        info = ydl.extract_info(songs_queue.get_yt_link(serverid), download=False)
                        songs_queue.set_stream_link(serverid, info['url'])
                    except:
                        logger.info(f"Skipping unavaliable video in \"{ctx.guild.name}\".")
                        # try:
                        #     asyncio.create_task(ctx.channel.send(f"Пропущено недоступное видео - "
                        #                            f"{songs_queue.get_track_name(serverid)}"))
                        # except Exception as e:
                        #     print(e)
                        songs_queue.tracks[serverid][1][songs_queue.get_index(serverid)][0]="(UNAVAILABLE) "+\
                                                    songs_queue.tracks[serverid][1][songs_queue.get_index(serverid)][0]
            if songs_queue.get_stream_link(serverid):
                voice_client.play(discord.FFmpegOpusAudio(source=songs_queue.get_stream_link(serverid),
                                            **FFMPEG_OPTIONS), after=lambda e: asyncio.run(auto_skip(ctx,voice_client)))
                #disconnect after time module
                try:
                    songs_queue.tracks[serverid][3] = 0
                    if (songs_queue.tracks[serverid][0]==0 and songs_queue.tracks[serverid][2]==False and
                            songs_queue.tracks[serverid][4]==False):
                        while True:
                            if ctx.voice_client.is_playing():
                                songs_queue.tracks[serverid][3] = 0
                            else:
                                songs_queue.tracks[serverid][3] += 1
                                #print("time", songs_queue.tracks[serverid][3])
                            if songs_queue.tracks[serverid][3] >= 300: #5 min
                                try:
                                    await disconnect(ctx, True)
                                    break
                                except Exception as e:
                                    logger.error(f'Disconnect error in timer module: {e}')
                                    logger.exception(e)
                                    break
                            await asyncio.sleep(1)
                except:
                    logger.debug(f'Exception raised (timer stopped) in \"{ctx.guild.name}\"')
            else:
                if (songs_queue.tracks[serverid][0]<songs_queue.queue_len(serverid)):
                    asyncio.run(auto_skip(ctx,voice_client, False))
                else:
                    logger.info(f"Queue ended in \"{ctx.guild.name}\"")
                    return
    except (ClientException, Exception) as e:
        logger.error(f"client {e}")
        logger.exception(e)
        return 1


@bot.command(description="plays music by url or keyword search",
             aliases=['p','PLAY','P','здфн','з','ЗДФН','З','Play','Здфн'])
async def play(ctx, *url):
    try:
        if not url:
            await ctx.message.reply(PLAY_NO_URL)
            return
        if await join(ctx)==1:
            return

        await asyncio.sleep(3.1) #waiting for join func

        if (await add(ctx, ' '.join(url))==1):
            raise Exception("Cannot extract info")        

        if (await audio_player(ctx,ctx.voice_client)==1):
            raise Exception
    except Exception as e:
        ctx.channel.send(f"{PLAY_ERROR} {e}")
        logger.error(f'Play error: {e}')
        return


@bot.command(description="search menu for tracks",
             aliases=['s','S','SEARCH','Ы','ы','ыуфкср','ЫУФКСР','Search','Ыуфкср'])
async def search(ctx, *user_request):
    if not user_request:
        await ctx.message.reply(SEARCH_NO_REQUEST)
        return
    if await join(ctx) == 1:
        return
    backslash_n = '\n'

    searchResult = YoutubeSearch(f"{user_request}", max_results=5).to_dict()

    await ctx.message.reply(f"```"
    f"{backslash_n.join(str(i) +') ' + searchResult[j]['title'] for i, j in enumerate(range(len(searchResult)), 1))}\n"
    f"\n{SEARCH_MENU_HINT}```")
    try:
        msg = await bot.wait_for("message",timeout=30, check=lambda m: m.author.id == ctx.author.id)

    except:
        logger.debug('[search module] given time ended')
        await ctx.message.reply(SEARCH_OUT_OF_TIME)
        return

    #print(f"content {msg.content}")
    # try:
    #     embed = discord.Embed(description=f'{msg.content}',
    #                           colour=discord.Colour.green())
    #     await ctx.channel.send(embed=embed)
    # except Exception as e:
    #     print(e)

    if msg.content:
        msg=msg.content

    if msg=='cancel':
        await ctx.message.reply(SEARCH_CANCELED)
        return
    else:
        try:
            int(msg)
            if 1<=int(msg)<=5:
                url='https://www.youtube.com/watch?v=' + searchResult[int(msg) - 1]['id']
            else:
                raise Exception
        except:
            await ctx.message.reply(SEARCH_INVALID_ARG)
            return

    if (await add(ctx, url) == 1):
        return

    await audio_player(ctx,ctx.voice_client)


@bot.command(description="loops current playing track",aliases=['LOOP','Loop','дщщз','ДЩЩЗ','Дщщз'])
async def loop(ctx):
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            songs_queue.loop(ctx.guild.id)
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
        else:
            await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description="unloops current playing looped track",aliases=['UNLOOP','Unloop','гтдщщз','ГТДЩЩЗ','Гтдщщз'])
async def unloop(ctx):
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            songs_queue.unloop(ctx.guild.id)
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
        else:
            await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description="pauses current track",
             aliases=['PAUSE','Pause','stop','STOP','Stop','зфгыу','ЗФГЫУ','Зфгыу','ыещз','ЫЕЩЗ','Ыещз'])
async def pause(ctx):
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice:
                voice.pause()
                songs_queue.set_pause_time(ctx.guild.id,datetime.datetime.now().timestamp())
                await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
                logger.info(f"Paused by {ctx.message.author} in \"{ctx.guild.name}\"")
        else:
            await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description="resumes paused track",
    aliases=['RESUME','Resume','unpause','Unpause','UNPAUSE','куыгьу','КУЫГЬУ','Куыгьу','гтзфгыу','ГТЗФЫУ','Гтзфгыу'])
async def resume(ctx):
    if ctx.voice_client:
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice:
            if voice.is_paused():
                serverid=ctx.guild.id
                now=datetime.datetime.now().timestamp()
                pause=songs_queue.get_pause_time(serverid)
                no_play=songs_queue.get_no_play_time(serverid)
                voice.resume()
                songs_queue.set_no_play_time(serverid,no_play+(now-pause))
                await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
                logger.info(f"Resumed by {ctx.message.author} in \"{ctx.guild.name}\"")
        else:
            await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description="skips current track",aliases=["ылшз","ЫЛШЗ","SKIP",'Skip','Ылшз'])
async def skip(ctx,fromjump=False):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            if voice:
                voice.stop()
                if not fromjump:
                    logger.info(f'Skipped in server \"{ctx.guild.name}\" by {ctx.message.author}')
                await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
        else:
            await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description="disconnets bot from voice channel",
    aliases=['DISCONNECT', 'DC', 'dc','Dc', 'leave', 'LEAVE','Leave','l','L', 'вс','ВС','Вс','дуфму','ДУФМУ','Дуфму'])
async def disconnect(ctx,fromTimeout=False):
    if ctx.voice_client:
        songs_queue.clear(ctx.guild.id, False)
        await ctx.voice_client.disconnect()
        if not fromTimeout:
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
            logger.info(f'Disconnected in server \"{ctx.guild.name}\" by {ctx.message.author}')
        else:
            await ctx.send(DISCONNECT_DISCONNECTED_BY_AFK)
            logger.info(f'Disconnected due to timeout of 5 minutes in \"{ctx.guild.name}\"')
    else:
        if not fromTimeout:
            await ctx.message.reply(BOT_DISCONNECTED)


### QUEUE BLOCK ###
@bot.command(description="shows current queue",aliases=['QUEUE','q','Q','йгугу','ЙГУГУ','й','Й','Queue','Йгугу'])
async def queue(ctx,page=0):
    serverid=ctx.guild.id
    k=0
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            tempvar = songs_queue.queue(serverid)
        else:
            tempvar = songs_queue.queue(serverid, False)
        if tempvar == -1:
            await ctx.message.reply(QUEUE_EMPTY)
        else:
            fq_pages=len(songs_queue.get_qfp(serverid))
            if page==0:
                for i in range(fq_pages):
                    if f"\t\t — {QUEUE_CURRENT}" in songs_queue.get_qfp(serverid)[i]:
                        await ctx.message.reply(f"{songs_queue.get_qfp(serverid)[i]}\n\n{QUEUE_CURRENT_PAGE[0]} {i+1} "
                                                f"{QUEUE_CURRENT_PAGE[1]} {fq_pages}. ({QUEUE_CURRENT_PAGE[2]} `-queue 2`)")
                        break
                    else:
                        k+=1
                if k==fq_pages:
                    await ctx.message.reply(f"{songs_queue.get_qfp(serverid)[page-1]}\n{QUEUE_CURRENT_PAGE[0]} {k} "
                                            f"{QUEUE_CURRENT_PAGE[1]} {fq_pages}. ({QUEUE_CURRENT_PAGE[2]} `-queue 2`)")
            else:
                if page>fq_pages or page<1:
                    await ctx.message.reply(QUEUE_NO_PAGE + f' ({page})')
                    return
                else:
                    await ctx.message.reply(f"{songs_queue.get_qfp(serverid)[page-1]}\n{QUEUE_CURRENT_PAGE[0]} {page} "
                                            f"{QUEUE_CURRENT_PAGE[1]} {fq_pages}. ({QUEUE_CURRENT_PAGE[2]} `-queue 2`)")
            songs_queue.set_qfp(serverid,[])
    else:
        await ctx.message.reply(QUEUE_EMPTY)


@bot.command(description="clears queue",aliases=['CLEAR','сдуфк','СДУФК','Clear','Сдуфк'])
async def clear(ctx):
    serverid=ctx.guild.id
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            songs_queue.clear(serverid,True)
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
        else:
            songs_queue.clear(serverid, False)
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
    else:
        await ctx.message.reply(BOT_DISCONNECTED)


@bot.command(description='Playing selected track from queue by its number',aliases=['JUMP','огьз','ОГЬЗ','Jump','Огьз'])
async def jump(ctx, value=-1):
    serverid=ctx.guild.id
    try:
        queue_check=songs_queue.queue(serverid)
    except:
        logger.debug('[queue_check module in jump function] Queue is not empty!')
        queue_check=0

    if queue_check==-1:
        await ctx.message.reply(QUEUE_EMPTY)
        return

    if value<1 :
        await ctx.message.reply(f"{JUMP_INVALID_ARG} **`-jump 1`**")
        return

    #value=-1
    #or type(value)!=int

    if value<=songs_queue.queue_len(serverid):
        current_time=datetime.datetime.now().timestamp()
        if ctx.voice_client.is_playing():
            songs_queue.jump(value - 2, serverid)
            songs_queue.set_start_time(serverid,current_time)
            songs_queue.tracks[serverid][4]=True
            await skip(ctx)
        else:
            songs_queue.jump(value - 1, serverid)
            songs_queue.set_start_time(serverid, current_time)
            songs_queue.tracks[serverid][4]=True
            await audio_player(ctx,ctx.guild.voice_client)
            await ctx.message.reply(BOT_DEFAULT_REPLY_ON_SUCCESS)
        logger.info(f'Jumped to track №{value} in server \"{ctx.guild.name}\" by {ctx.message.author}')
    else:
        await ctx.message.reply()


@bot.command(description='Current playing track', aliases=['np', 'тз','NP','ТЗ','Np','Тз'])
async def now_playing(ctx):
    try:
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                serverid=ctx.guild.id
                track_len=str(songs_queue.get_track_length(serverid))
                author=songs_queue.get_author(serverid)
                now=datetime.datetime.now().timestamp()
                start=songs_queue.get_start_time(serverid)
                no_play=songs_queue.get_no_play_time(serverid)
                current_time=datetime.datetime.fromtimestamp(now-(start+no_play),tz=timezone.utc).strftime("%H:%M:%S")
                splitted=current_time.split(":")

                time = track_len.split(":")
                seconds=(int(time[0])*60*60)+(int(time[1])*60)+(int(time[2]))

                track_len_part=ceil(seconds/12)
                dot_place=(int(splitted[0])*60*60+int(splitted[1])*60+int(splitted[2]))//track_len_part

                #print(f"now: {now}\nstart: {start}\ndiff={now-start}\n"
                # f"er={datetime.datetime.utcfromtimestamp(now-(start+no_play)).strftime('%H:%M:%S')}")
                embed = discord.Embed(description=f'**{NOWPLAYING_FINAL_INFO[0]}:**\n[{songs_queue.get_track_name(serverid)}]'
                                        f'({songs_queue.get_yt_link(serverid)})\n\n'
                                        f'{current_time} {"—" * (dot_place) + "⬤" + (11 - dot_place) * "—"} '
                                        f'{songs_queue.get_track_length(serverid)}\n\n'
                                        f'**{NOWPLAYING_FINAL_INFO[1]}**:\n{author}',
                                        colour=discord.Colour.green())
                embed.set_thumbnail(url=songs_queue.get_thumbnail_url(serverid))
                await ctx.message.reply(embed=embed)
            else:
                await ctx.message.reply(BOT_NOTHING_IS_PLAYING)
        else:
            await ctx.message.reply(BOT_DISCONNECTED)
    except Exception as e:
        logger.error(f"NOW_PLAYING function: {e}")
        logger.exception(e)



### BOT RUN ###
bot.run(BOT_TOKEN,log_formatter=formatter,log_handler=None)
