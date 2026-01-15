# -*- coding: utf-8 -*-
import logging
import os
import asyncio
import time
import re
import shutil
import subprocess
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import pytz
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
# For transcription
import speech_recognition as sr

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('logs.txt', mode='a')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Config from env
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.critical('BOT_TOKEN environment variable not set')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
LOGIN_URL = 'https://www.orangecarrier.com/login'
LIVE_CALLS_URL = 'https://www.orangecarrier.com/live/calls'
ORANGE_EMAIL = os.getenv('ORANGE_EMAIL', '')
ORANGE_PASSWORD = os.getenv('ORANGE_PASSWORD', '')
ORANGE_COOKIE = os.getenv('ORANGE_COOKIE', '')
ORANGE_USER_AGENT = os.getenv('ORANGE_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
DEVELOPER_NAME = os.getenv('DEVELOPER_NAME', 'Bot Developer')
DEVELOPER_URL = os.getenv('DEVELOPER_URL', 'https://t.me/nyla_r2')

# Settings
SETTINGS_FILE = 'settings.json'
ADMIN_IDS_FILE = 'admin_ids.json'
APPROVED_CHATS_FILE = 'approved_chats.json'
processed_calls = set()
approved_chat_ids = set()
admin_ids = set()

bot_settings = {
    'scraping_mode': 'playButton',
    'enable_voice_transcription': False,
    'use_cli_as_otp': False,
    'enable_translation': False,
    'refresh_interval_minutes': 20,
    'audio_transcription_retries': 3,
    'audio_download_delay_seconds': 14,
    'headless': True,
    'cookie_refresh_interval_minutes': 10
}

COUNTRY_NAME_TO_CODE = {
    'INDONESIA': 'ID', 'UNITED STATES': 'US', 'UNITED KINGDOM': 'GB', 'RUSSIA': 'RU', 'CHINA': 'CN'
}

# Global authenticated session (requests.Session)
session = None
session_lock = asyncio.Lock()

# Helpers

def load_settings():
    global bot_settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                bot_settings.update(saved)
                logger.info('Loaded settings.json')
        except Exception as e:
            logger.error(f'Error loading settings: {e}')
    else:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(bot_settings, f, indent=2)


def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(bot_settings, f, indent=2)


def load_admin_ids():
    global admin_ids
    admin_ids = set()
    try:
        if os.path.exists(ADMIN_IDS_FILE):
            with open(ADMIN_IDS_FILE, 'r') as f:
                admin_ids.update(json.load(f))
        if ADMIN_ID:
            admin_ids.add(ADMIN_ID)
    except Exception as e:
        logger.error(f'Failed to load admin ids: {e}')


def save_admin_ids():
    try:
        with open(ADMIN_IDS_FILE, 'w') as f:
            json.dump(list(admin_ids), f)
    except Exception as e:
        logger.error(f'Failed to save admin ids: {e}')


def load_approved_chats():
    global approved_chat_ids
    approved_chat_ids = set()
    try:
        if os.path.exists(APPROVED_CHATS_FILE):
            with open(APPROVED_CHATS_FILE, 'r') as f:
                approved_chat_ids.update(json.load(f))
    except Exception as e:
        logger.error(f'Failed to load approved chats: {e}')


def save_approved_chats():
    try:
        with open(APPROVED_CHATS_FILE, 'w') as f:
            json.dump(list(approved_chat_ids), f)
    except Exception as e:
        logger.error(f'Failed to save approved chats: {e}')


def escape_md_v2(text):
    return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))


def get_country_flag(country_name):
    code = COUNTRY_NAME_TO_CODE.get(country_name.strip().upper(), 'UN')
    try:
        if code == 'UN':
            return '🌍'
        return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code.upper())
    except Exception:
        return '🌍'


# Networking helpers (direct requests using requests.Session)

def get_auth_headers():
    headers = {
        'User-Agent': ORANGE_USER_AGENT,
        'Accept': '*/*',
        'Referer': LIVE_CALLS_URL,
        'Origin': 'https://www.orangecarrier.com',
    }
    if ORANGE_COOKIE:
        headers['Cookie'] = ORANGE_COOKIE
    return headers


def create_session_via_login(max_attempts=2):
    """Attempt to log in using ORANGE_EMAIL / ORANGE_PASSWORD and return an authenticated requests.Session or None."""
    if not ORANGE_EMAIL or not ORANGE_PASSWORD:
        logger.info('ORANGE_EMAIL/ORANGE_PASSWORD not set; skipping automatic login')
        return None
    for attempt in range(1, max_attempts + 1):
        try:
            s = requests.Session()
            s.headers.update(get_auth_headers())
            # GET login page to collect possible hidden fields
            r = s.get(LOGIN_URL, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            payload = {}
            form = soup.find('form')
            if form:
                # collect hidden inputs
                for inp in form.find_all('input'):
                    name = inp.get('name')
                    if not name:
                        continue
                    val = inp.get('value', '')
                    payload[name] = val
                action = form.get('action') or LOGIN_URL
            else:
                action = LOGIN_URL
            # set credentials (common field names)
            # try common names: email / username, password
            # Overwrite or set these keys
            # If form uses different names, this might fail (fallback to cookie env)
            payload.update({'email': ORANGE_EMAIL, 'username': ORANGE_EMAIL, 'password': ORANGE_PASSWORD})
            login_url = requests.compat.urljoin(LOGIN_URL, action)
            post = s.post(login_url, data=payload, timeout=20, allow_redirects=True)
            # verify by fetching live calls page
            test = s.get(LIVE_CALLS_URL, timeout=20)
            if test.status_code == 200 and 'LiveCalls' in test.text:
                logger.info('Login via requests succeeded')
                return s
            else:
                logger.warning(f'Login attempt {attempt} may have failed (status {test.status_code})')
        except Exception as e:
            logger.warning(f'Login attempt {attempt} error: {e}')
        time.sleep(2 * attempt)
    logger.error('Automatic login via requests failed')
    return None


def ensure_session():
    """Ensure global session is available by trying automatic login; fallback to headers with ORANGE_COOKIE."""
    global session
    # Double-checked locking style
    if session is not None:
        return session
    # create session in background thread (blocking) to avoid event loop issues
    s = create_session_via_login()
    if s:
        session = s
        return session
    # fallback: create session with only headers (cookie) if ORANGE_COOKIE provided
    if ORANGE_COOKIE:
        sess = requests.Session()
        sess.headers.update(get_auth_headers())
        session = sess
        logger.info('Using ORANGE_COOKIE fallback for session')
        return session
    logger.error('No authenticated session available (set ORANGE_EMAIL/PASSWORD or ORANGE_COOKIE)')
    return None


def fetch_calls_direct(use_session=True):
    """Fetch live calls table via requests and parse audio URLs. Returns list of call dicts."""
    try:
        s = None
        if use_session:
            s = ensure_session()
        if s:
            r = s.get(LIVE_CALLS_URL, timeout=30)
        else:
            r = requests.get(LIVE_CALLS_URL, headers=get_auth_headers(), timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        tbody = soup.find('tbody', id='LiveCalls')
        if not tbody:
            logger.warning('LiveCalls tbody not found in page')
            return []
        calls = []
        rows = tbody.find_all('tr')
        for row in rows:
            try:
                if not row.get_text(strip=True):
                    continue
                play_button = row.find('button', attrs={'onclick': re.compile(r'Play', re.I)})
                if not play_button:
                    continue
                onclick = play_button.get('onclick', '')
                match = re.search(r"Play\['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]", onclick)
                if not match:
                    continue
                did, uuid = match.groups()
                if uuid in processed_calls:
                    continue
                processed_calls.add(uuid)
                tds = row.find_all('td')
                country = tds[0].get_text(strip=True) if len(tds) > 0 else 'Unknown'
                number = tds[1].get_text(strip=True) if len(tds) > 1 else ''
                cli = tds[2].get_text(strip=True) if len(tds) > 2 else ''
                audio_url = f'https://www.orangecarrier.com/live/calls/sound?did={did}&uuid={uuid}'
                calls.append({'country': country, 'number': number, 'cli_number': cli, 'audio_url': audio_url})
            except Exception as e:
                logger.debug(f'row parse error: {e}')
        return calls
    except Exception as e:
        logger.error(f'fetch_calls_direct failed: {e}')
        return []


def download_audio_direct(url, filename_base, retries=5, delay=5):
    """Download file (mp4/mp3) via requests using authenticated session if available."""
    s = session or None
    headers = get_auth_headers()
    for attempt in range(1, retries + 1):
        try:
            if s:
                r = s.get(url, timeout=60, stream=True)
            else:
                r = requests.get(url, headers=headers, timeout=60, stream=True)
            r.raise_for_status()
            tmp_path = filename_base + '.download'
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=32 * 1024):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(tmp_path) <= 1024:
                os.remove(tmp_path)
                raise Exception('Downloaded file too small')
            with open(tmp_path, 'rb') as fh:
                head = fh.read(64)
            if b'ftyp' in head or b'moov' in head or b'MP4' in head:
                saved = os.path.splitext(filename_base)[0] + '.mp4'
            else:
                saved = os.path.splitext(filename_base)[0] + '.mp3'
            os.replace(tmp_path, saved)
            logger.info(f'Downloaded {saved}')
            return saved
        except Exception as e:
            logger.warning(f'download attempt {attempt} failed: {e}')
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.error('All download attempts failed')
                return None


async def process_call_worker(call_data, context: ContextTypes.DEFAULT_TYPE):
    country = call_data.get('country')
    number = call_data.get('number')
    cli_number = call_data.get('cli_number')
    audio_url = call_data.get('audio_url')
    detection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    processed_country = country.split(' ')[0] if country else 'Unknown'
    country_flag = get_country_flag(processed_country)
    masked_num = number if not number else (number[:4] + '*' * max(0, len(number) - 8) + number[-4:])
    otp = ''
    if bot_settings.get('use_cli_as_otp'):
        otp = cli_number

    pre_message_ids = {}
    if audio_url:
        pre_text = f"{country_flag} {processed_country} {masked_num} OTP is coming soon 🎉✨"
        for chat_id in approved_chat_ids:
            try:
                sent = await context.bot.send_message(chat_id=chat_id, text=pre_text)
                pre_message_ids[chat_id] = sent.message_id
            except Exception as e:
                logger.error(f'Failed to send pre-message to {chat_id}: {e}')

        temp_base = f'temp_audio_{int(time.time())}'
        await asyncio.sleep(bot_settings.get('audio_download_delay_seconds', 5))
        # ensure session (may perform login); run in thread
        await asyncio.to_thread(ensure_session)
        downloaded_path = await asyncio.to_thread(download_audio_direct, audio_url, temp_base, 5, 5)

        if downloaded_path:
            extracted_audio = None
            try:
                if downloaded_path.lower().endswith('.mp4'):
                    ffmpeg_path = shutil.which('ffmpeg')
                    if ffmpeg_path:
                        mp3_out = os.path.splitext(downloaded_path)[0] + '_extracted.mp3'
                        cmd = [ffmpeg_path, '-y', '-i', downloaded_path, '-vn', '-acodec', 'libmp3lame', '-ar', '44100', '-ac', '2', mp3_out]
                        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
                        if proc.returncode == 0 and os.path.exists(mp3_out):
                            extracted_audio = mp3_out
                    # send video first (whole mp4)
                    for chat_id in approved_chat_ids:
                        for attempt in range(3):
                            try:
                                with open(downloaded_path, 'rb') as vf:
                                    input_video = InputFile(vf, filename=os.path.basename(downloaded_path))
                                    await context.bot.send_video(chat_id=chat_id, video=input_video, caption=f"✨ New Call » {processed_country} » {masked_num}", parse_mode='MarkdownV2', supports_streaming=True)
                                break
                            except Exception as e:
                                logger.error(f'Failed to send video to {chat_id} (attempt {attempt+1}): {e}')
                                if attempt < 2:
                                    await asyncio.sleep(2)
                    # if extracted audio exists send as audio
                    if extracted_audio:
                        for chat_id in approved_chat_ids:
                            for attempt in range(3):
                                try:
                                    with open(extracted_audio, 'rb') as af:
                                        input_audio = InputFile(af, filename=os.path.basename(extracted_audio))
                                        await context.bot.send_audio(chat_id=chat_id, audio=input_audio, caption=f"🔊 Audio extracted for {masked_num}", parse_mode='MarkdownV2')
                                    break
                                except Exception as e:
                                    logger.error(f'Failed to send extracted audio to {chat_id} (attempt {attempt+1}): {e}')
                                    if attempt < 2:
                                        await asyncio.sleep(2)
                else:
                    # audio-only file
                    for chat_id in approved_chat_ids:
                        for attempt in range(3):
                            try:
                                with open(downloaded_path, 'rb') as af:
                                    input_audio = InputFile(af, filename=os.path.basename(downloaded_path))
                                    await context.bot.send_audio(chat_id=chat_id, audio=input_audio, caption=f"✨ New Call » {processed_country} » {masked_num}", parse_mode='MarkdownV2')
                                break
                            except Exception as e:
                                logger.error(f'Failed to send audio to {chat_id} (attempt {attempt+1}): {e}')
                                if attempt < 2:
                                    await asyncio.sleep(2)

                # transcription if requested and audio available
                audio_for_transcription = extracted_audio if extracted_audio else (downloaded_path if downloaded_path.lower().endswith('.mp3') else None)
                if bot_settings.get('enable_voice_transcription') and audio_for_transcription:
                    try:
                        r = sr.Recognizer()
                        with sr.AudioFile(audio_for_transcription) as source:
                            audio_data = r.record(source)
                        text = r.recognize_google(audio_data)
                        otp = ''.join(re.findall(r'\d', text))
                    except Exception as e:
                        logger.error(f'Transcription failed: {e}')

                # send OTP text message if found
                if otp:
                    msg = f"🔑 OTP detected: {escape_md_v2(otp)}\nCountry: {escape_md_v2(processed_country)}\nNumber: {escape_md_v2(masked_num)}\nTime: {escape_md_v2(detection_time)}"
                    for chat_id in approved_chat_ids:
                        try:
                            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='MarkdownV2')
                        except Exception as e:
                            logger.error(f'Failed to send OTP message to {chat_id}: {e}')

            except Exception as e:
                logger.error(f'Error preparing/sending media: {e}')
            finally:
                # cleanup
                try:
                    if downloaded_path and os.path.exists(downloaded_path) and not downloaded_path.lower().endswith('.mp4'):
                        os.remove(downloaded_path)
                except Exception:
                    pass
                try:
                    if extracted_audio and os.path.exists(extracted_audio):
                        os.remove(extracted_audio)
                except Exception:
                    pass
        else:
            logger.error('Downloaded path is None')
    else:
        logger.debug('No audio_url in call_data')


async def monitor_calls(context: ContextTypes.DEFAULT_TYPE):
    if bot_settings['scraping_mode'] != 'playButton':
        return
    # Ensure we have session available (login if needed)
    await asyncio.to_thread(ensure_session)
    calls = await asyncio.to_thread(fetch_calls_direct)
    if calls:
        for call_data in calls:
            asyncio.create_task(process_call_worker(call_data, context))


async def cmd_start(update, context):
    chat = update.effective_chat
    if chat.type in ['group', 'supergroup']:
        gid = chat.id
        if gid not in approved_chat_ids:
            approved_chat_ids.add(gid)
            save_approved_chats()
            await update.message.reply_text('Group added to approved chats')
    await update.message.reply_text('Monitoring started...')
    context.job_queue.run_repeating(monitor_calls, interval=5, first=1)


async def cmd_status(update, context):
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text('❌ You do not have permission')
        return
    status_msg = f"Calls processed: {len(processed_calls)}\nApproved groups: {len(approved_chat_ids)}\nTranscription: {'ON' if bot_settings.get('enable_voice_transcription') else 'OFF'}"
    await update.message.reply_text(status_msg)


async def cmd_add_admin(update, context):
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text('❌ You do not have permission')
        return
    if not context.args:
        await update.message.reply_text('Usage: /add_admin <user_id>')
        return
    try:
        new_id = int(context.args[0])
        admin_ids.add(new_id)
        save_admin_ids()
        await update.message.reply_text(f'Added admin {new_id}')
    except Exception as e:
        await update.message.reply_text('Invalid id')


async def cmd_add_group(update, context):
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text('❌ You do not have permission')
        return
    if not context.args:
        await update.message.reply_text('Usage: /add_group <chat_id>')
        return
    try:
        gid = int(context.args[0])
        approved_chat_ids.add(gid)
        save_approved_chats()
        await update.message.reply_text(f'Added group {gid}')
    except Exception:
        await update.message.reply_text('Invalid id')


async def post_init(app):
    # send startup message to admins
    for aid in list(admin_ids):
        try:
            await app.bot.send_message(chat_id=aid, text='Bot started (auto-login enabled)')
        except Exception as e:
            logger.error(f'Failed to send startup to {aid}: {e}')


def main():
    load_settings()
    load_approved_chats()
    load_admin_ids()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(CommandHandler('add_admin', cmd_add_admin))
    app.add_handler(CommandHandler('add_group', cmd_add_group))

    print('Bot is ready. Use /start in group to enable monitoring.')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()