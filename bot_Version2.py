# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import logging
import os
import asyncio
import time
import re
import shutil
import winreg
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, InputFile
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import pytz
from telegram.ext import JobQueue
import subprocess
from telegram.ext import ConversationHandler, MessageHandler, filters
# For transcription
import speech_recognition as sr
# Configure logging - both file and console
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler('logs.txt', mode='a')
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# Telegram bot configuration
BOT_TOKEN = "8550068285:AAHepdxHY5Gz31CBMWkaXWFVEjg0PZ2mzuM"
ADMIN_ID = 7799092693 # IMPORTANT: set this to YOUR Telegram user id
# Website configuration
LOGIN_URL = "https://www.orangecarrier.com/login"
LIVE_CALLS_URL = "https://www.orangecarrier.com/live/calls"
# Credentials (use environment variables in production)
USERNAME = os.getenv("ORANGE_EMAIL", "nusacorp31@gmail.com")
PASSWORD = os.getenv("ORANGE_PASSWORD", "Ramuri310505@")
# Developer Info
DEVELOPER_NAME = "Bot Developer"
DEVELOPER_URL = "https://t.me/nyla_r2"
# Proxy (if needed)
PROXY_URL = 'YOUR_PROXY_URL_HERE'
# Set to store processed calls
processed_calls = set()
# Country name to code mappings
COUNTRY_NAME_TO_CODE = {
    'AFGHANISTAN': 'AF', 'ALBANIA': 'AL', 'ALGERIA': 'DZ', 'AMERICAN SAMOA': 'AS', 'ANDORRA': 'AD', 'ANGOLA': 'AO', 'ANGUILLA': 'AI', 'ANTARCTICA': 'AQ', 'ANTIGUA AND BARBUDA': 'AG',
    'ARGENTINA': 'AR', 'ARMENIA': 'AM', 'ARUBA': 'AW', 'AUSTRALIA': 'AU', 'AUSTRIA': 'AT', 'AZERBAIJAN': 'AZ', 'BAHAMAS': 'BS', 'BAHRAIN': 'BH', 'BANGLADESH': 'BD', 'BARBADOS': 'BB',
    'BELARUS': 'BY', 'BELGIUM': 'BE', 'BELIZE': 'BZ', 'BENIN': 'BJ', 'BERMUDA': 'BM', 'BHUTAN': 'BT', 'BOLIVIA': 'BO', 'BOSNIA AND HERZEGOVINA': 'BA', 'BOTSWANA': 'BW', 'BRAZIL': 'BR',
    'BRITISH INDIAN OCEAN TERRITORY': 'IO', 'BRUNEI DARUSSALAM': 'BN', 'BULGARIA': 'BG', 'BURKINA FASO': 'BF', 'BURUNDI': 'BI', 'CAMBODIA': 'KH', 'CAMEROON': 'CM', 'CANADA': 'CA',
    'CAPE VERDE': 'CV', 'CAYMAN ISLANDS': 'KY', 'CENTRAL AFRICAN REPUBLIC': 'CF', 'CHAD': 'TD', 'CHILE': 'CL', 'CHINA': 'CN', 'CHRISTMAS ISLAND': 'CX', 'COCOS (KEELING) ISLANDS': 'CC',
    'COLOMBIA': 'CO', 'COMOROS': 'KM', 'CONGO': 'CG', 'CONGO, THE DEMOCRATIC REPUBLIC OF THE': 'CD', 'COOK ISLANDS': 'CK', 'COSTA RICA': 'CR', "CÔTE D'IVOIRE": 'CI',
    'CROATIA': 'HR', 'CUBA': 'CU', 'CYPRUS': 'CY', 'CZECH REPUBLIC': 'CZ', 'DENMARK': 'DK', 'DJIBOUTI': 'DJ', 'DOMINICA': 'DM', 'DOMINICAN REPUBLIC': 'DO', 'ECUADOR': 'EC', 'EGYPT': 'EG',
    'EL SALVADOR': 'SV', 'EQUATORIAL GUINEA': 'GQ', 'ERITREA': 'ER', 'ESTONIA': 'EE', 'ETHIOPIA': 'ET', 'FALKLAND ISLANDS (MALVINAS)': 'FK', 'FAROE ISLANDS': 'FO', 'FIJI': 'FJ',
    'FINLAND': 'FI', 'FRANCE': 'FR', 'FRENCH GUIANA': 'GF', 'FRENCH POLYNESIA': 'PF', 'GABON': 'GA', 'GAMBIA': 'GM', 'GEORGIA': 'GE', 'GERMANY': 'DE', 'GHANA': 'GH', 'GIBRALTAR': 'GI',
    'GREECE': 'GR', 'GREENLAND': 'GL', 'GRENADA': 'GD', 'GUADELOUPE': 'GP', 'GUAM': 'GU', 'GUATEMALA': 'GT', 'GUINEA': 'GN', 'GUINEA-BISSAU': 'GW', 'GUYANA': 'GY', 'HAITI': 'HT',
    'HONDURAS': 'HN', 'HONG KONG': 'HK', 'HUNGARY': 'HU', 'ICELAND': 'IS', 'INDIA': 'IN', 'INDONESIA': 'ID', 'IRAN, ISLAMIC REPUBLIC OF': 'IR', 'IRAQ': 'IQ', 'IRELAND': 'IE',
    'ISRAEL': 'IL', 'ITALY': 'IT', 'JAMAICA': 'JM', 'JAPAN': 'JP', 'JORDAN': 'JO', 'KAZAKHSTAN': 'KZ', 'KENYA': 'KE', 'KIRIBATI': 'KI', 'KOREA, DEMOCRATIC PEOPLE\'S REPUBLIC OF': 'KP',
    'KOREA, REPUBLIC OF': 'KR', 'KUWAIT': 'KW', 'KYRGYZSTAN': 'KG', 'LAO PEOPLE\'S DEMOCRATIC REPUBLIC': 'LA', 'LATVIA': 'LV', 'LEBANON': 'LB', 'LESOTHO': 'LS', 'LIBERIA': 'LR',
    'LIBYAN ARAB JAMAHIRIYA': 'LY', 'LIBYA': 'LY', 'LIECHTENSTEIN': 'LI', 'LITHUANIA': 'LT', 'LUXEMBOURG': 'LU', 'MACAO': 'MO', 'MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF': 'MK',
    'MADAGASCAR': 'MG', 'MALAWI': 'MW', 'MALAYSIA': 'MY', 'MALDIVES': 'MV', 'MALI': 'ML', 'MALTA': 'MT', 'MARSHALL ISLANDS': 'MH', 'MARTINIQUE': 'MQ', 'MAURITANIA': 'MR', 'MAURITIUS': 'MU',
    'MAYOTTE': 'YT', 'MEXICO': 'MX', 'MICRONESIA, FEDERATED STATES OF': 'FM', 'MOLDOVA, REPUBLIC OF': 'MD', 'MONACO': 'MC', 'MONGOLIA': 'MN', 'MONTSERRAT': 'MS', 'MOROCCO': 'MA',
    'MOZAMBIQUE': 'MZ', 'MYANMAR': 'MM', 'NAMIBIA': 'NA', 'NAURU': 'NR', 'NEPAL': 'NP', 'NETHERLANDS': 'NL', 'NETHERLANDS ANTILLES': 'AN', 'NEW CALEDONIA': 'NC', 'NEW ZEALAND': 'NZ',
    'NICARAGUA': 'NI', 'NIGER': 'NE', 'NIGERIA': 'NG', 'NIUE': 'NU', 'NORFOLK ISLAND': 'NF', 'NORTHERN MARIANA ISLANDS': 'MP', 'NORWAY': 'NO', 'OMAN': 'OM', 'PAKISTAN': 'PK',
    'PALAU': 'PW', 'PALESTINIAN TERRITORY, OCCUPIED': 'PS', 'PANAMA': 'PA', 'PAPUA NEW GUINEA': 'PG', 'PARAGUAY': 'PY', 'PERU': 'PE', 'PHILIPPINES': 'PH', 'PITCAIRN': 'PN',
    'POLAND': 'PL', 'PORTUGAL': 'PT', 'PUERTO RICO': 'PR', 'QATAR': 'QA', 'RÉUNION': 'RE', 'ROMANIA': 'RO', 'RUSSIAN FEDERATION': 'RU', 'RUSSIA': 'RU', 'RWANDA': 'RW', 'SAINT HELENA': 'SH',
    'SAINT KITTS AND NEVIS': 'KN', 'SAINT LUCIA': 'LC', 'SAINT PIERRE AND MIQUELON': 'PM', 'SAINT VINCENT AND THE GRENADINES': 'VC', 'SAMOA': 'WS', 'SAN MARINO': 'SM',
    'SAO TOME AND PRINCIPE': 'ST', 'SAUDI ARABIA': 'SA', 'SENEGAL': 'SN', 'SERBIA': 'RS', 'SEYCHELLES': 'SC', 'SIERRA LEONE': 'SL', 'SINGAPORE': 'SG', 'SLOVAKIA': 'SK',
    'SLOVENIA': 'SI', 'SOLOMON ISLANDS': 'SB', 'SOMALIA': 'SO', 'SOUTH AFRICA': 'ZA', 'SPAIN': 'ES', 'SRI LANKA': 'LK', 'SUDAN': 'SD', 'SURINAME': 'SR', 'SWAZILAND': 'SZ',
    'SWEDEN': 'SE', 'SWITZERLAND': 'CH', 'SYRIAN ARAB REPUBLIC': 'SY', 'TAIWAN, PROVINCE OF CHINA': 'TW', 'TAJIKSTAN': 'TJ', 'TANZANIA, UNITED REPUBLIC OF': 'TZ',
    'THAILAND': 'TH', 'TIMOR-LESTE': 'TL', 'TOGO': 'TG', 'TOKELAU': 'TK', 'TONGA': 'TO', 'TRINIDAD AND TOBAGO': 'TT', 'TUNISIA': 'TN', 'TURKEY': 'TR', 'TURKMENISTAN': 'TM',
    'TURKS AND CAICOS ISLANDS': 'TC', 'TUVALU': 'TV', 'VANUATU': 'VU', 'VENEZUELA': 'VE', 'VIETNAM': 'VN', 'VIRGIN ISLANDS, BRITISH': 'VG', 'VIRGIN ISLANDS, U.S.': 'VI',
    'WALLIS AND FUTUNA': 'WF', 'WESTERN SAHARA': 'EH', 'YEMEN': 'YE', 'ZAMBIA': 'ZM', 'ZIMBABWE': 'ZW', 'ÅLAND ISLANDS': 'AX', 'BONAIRE, SINT EUSTATIUS AND SABA': 'BQ',
    'CURAÇAO': 'CW', 'GUERNSEY': 'GG', 'ISLE OF MAN': 'IM', 'JERSEY': 'JE', 'MONTENEGRO': 'ME', 'SAINT BARTHÉLEMY': 'BL', 'SAINT MARTIN (FRENCH PART)': 'MF',
    'SINT MAARTEN (DUTCH PART)': 'SX', 'SOUTH SUDAN': 'SS'
}
}
# Settings Management
SETTINGS_FILE = 'settings.json'
bot_settings = {
    "scraping_mode": "playButton",
    "enable_voice_transcription": False,
    "use_cli_as_otp": False,
    "enable_translation": False,
    "refresh_interval_minutes": 20,
    "audio_transcription_retries": 3,
    "audio_download_delay_seconds": 14,
    "headless": True,
    "cookie_refresh_interval_minutes": 10
}
def load_settings():
    global bot_settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            saved_settings = json.load(f)
            bot_settings.update(saved_settings)
            logger.info("Loaded settings from settings.json.")
    else:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(bot_settings, f, indent=2)
        logger.info("Created default settings.json file.")
def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(bot_settings, f, indent=2)
    logger.info("Settings saved to settings.json.")
# Approved Chats
APPROVED_CHATS_FILE = 'approved_chats.json'
approved_chat_ids = set()

# Admin IDs
ADMIN_IDS_FILE = 'admin_ids.json'
admin_ids = {ADMIN_ID}

def load_admin_ids():
    global admin_ids
    admin_ids = {ADMIN_ID}  # Always include main admin
    if os.path.exists(ADMIN_IDS_FILE):
        try:
            with open(ADMIN_IDS_FILE, 'r') as f:
                loaded_ids = set(json.load(f))
                admin_ids.update(loaded_ids)
                logger.info(f"Loaded {len(admin_ids)} admin ID(s).")
        except Exception as e:
            logger.error(f"Error loading admin_ids.json: {e}")
    else:
        save_admin_ids()

def save_admin_ids():
    try:
        with open(ADMIN_IDS_FILE, 'w') as f:
            json.dump(list(admin_ids), f)
        logger.info("Admin IDs saved to admin_ids.json.")
    except Exception as e:
        logger.error(f"Error saving admin_ids.json: {e}")

def load_approved_chats():
    global approved_chat_ids
    if os.path.exists(APPROVED_CHATS_FILE):
        with open(APPROVED_CHATS_FILE, 'r') as f:
            approved_chat_ids = set(json.load(f))
            logger.info(f"Loaded {len(approved_chat_ids)} approved chat(s).")
    else:
        with open(APPROVED_CHATS_FILE, 'w') as f:
            json.dump(list(approved_chat_ids), f)
        logger.info("Created approved_chats.json file.")
def save_approved_chats():
    with open(APPROVED_CHATS_FILE, 'w') as f:
        json.dump(list(approved_chat_ids), f)
# Helper Functions
def get_country_flag(country_name):
    country_name_upper = country_name.strip().upper()
    country_code = COUNTRY_NAME_TO_CODE.get(country_name_upper, 'UNKNOWN')
    if country_code == 'UNKNOWN':
        return '🌍'
    try:
        flag = ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper())
        return flag
    except:
        return '🌍'
def extract_country_from_termination(text):
    if not text or text == 'Unknown':
        return 'Unknown'
    return text.split(' ')[0]
def mask_number(number):
    if len(number) < 8:
        return number
    return number[:4] + '*' * (len(number) - 8) + number[-4:]
def escape_md_v2(text):
    return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))
def get_chrome_major_version():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        major = int(version.split('.')[0])
        logger.info(f"Detected Chrome v{major}")
        return major
    except Exception as e:
        logger.warning(f"Chrome version detection failed: {e}. Using fallback version 141.")
        return 141
def clear_uc_cache():
    cache_path = os.path.expanduser(r"~\AppData\Roaming\undetected_chromedriver")
    if os.path.exists(cache_path):
        try:
            # Attempt to remove cache directory but tolerate permission errors
            shutil.rmtree(cache_path)
            logger.info("Undetected ChromeDriver cache cleared.")
        except Exception as e:
            # If permission denied, log guidance but continue
            logger.warning(f"Failed to clear cache: {e}. You can delete {cache_path} manually or run the script as Administrator to remove it.")
def is_network_available():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except:
        return False
async def wait_for_network(max_attempts=60, delay=10):
    for attempt in range(max_attempts):
        if is_network_available():
            logger.info("Network connection restored.")
            return True
        logger.warning(f"Network unavailable. Waiting {delay} seconds... (Attempt {attempt+1}/{max_attempts})")
        await asyncio.sleep(delay)
    logger.critical("Network connection not restored after max attempts.")
    return False
def selenium_prepare_login(max_login_attempts=5):
    clear_uc_cache()
    chrome_version = get_chrome_major_version()
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options, version_main=chrome_version, use_subprocess=True, headless=bot_settings['headless'])
    except Exception as e:
        logger.critical(f"Failed to create Chrome driver: {e}")
        return None
    for login_attempt in range(max_login_attempts):
        try:
            logger.info(f"Opening login page (Attempt {login_attempt+1})...")
            driver.get(LOGIN_URL)
            # Wait for login page to load properly
            email_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            time.sleep(0.5)
            email_input.clear()
            email_input.send_keys(USERNAME)
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(PASSWORD)
            time.sleep(0.5)
            # Find and click login button
            logger.info("Attempting to find and click login button...")
            selectors = [
                "//button[@id='loginSubmit']",
                "//button[@type='submit']",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'loading please wait')]",
                "//input[@type='submit' and contains(@value, 'Sign')]",
                "//input[@type='submit' and contains(@value, 'Login')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in') and contains(@href, '#')]",
                "//div[@role='button' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//button[contains(@class, 'btn') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]",
            ]
            signin_btn = None
            for sel in selectors:
                try:
                    signin_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, sel)))
                    logger.info(f"Found login button using: {sel}")
                    break
                except:
                    continue
            if not signin_btn:
                raise Exception("No login button found")
            
            # Click button with robust error handling (try normal click, then JS click)
            click_ok = False
            for click_retry in range(3):
                try:
                    try:
                        signin_btn.click()
                    except Exception as click_err_inner:
                        # Fallback to JS click if regular click fails
                        try:
                            driver.execute_script("arguments[0].click();", signin_btn)
                        except Exception:
                            # re-raise original click exception to be handled by outer except
                            raise click_err_inner

                    logger.info(f"Clicked Sign In button (attempt {click_retry+1})")
                    click_ok = True
                    break
                except Exception as click_err:
                    logger.warning(f"Click attempt {click_retry+1} failed: {click_err}")
                    # If the exception indicates a broken connection, quit driver to force a recreate on next login attempt
                    if isinstance(click_err, (ConnectionResetError, OSError)):
                        logger.error(f"Connection-level error during click: {click_err}. Quitting driver to recreate.")
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                        break
                    if click_retry < 2:
                        time.sleep(2)
                    else:
                        raise Exception(f"Click failed after 3 attempts: {click_err}")

            if not click_ok:
                raise Exception("Click button failed")
            
            logger.info("Sign In button clicked. Waiting for redirect (may take a while)...")
            # Wait for successful login redirect with very long timeout to handle network delays
            try:
                WebDriverWait(driver, 60).until(EC.url_contains("https://www.orangecarrier.com/"))
                logger.info("Redirect successful")
            except Exception as wait_err:
                logger.warning(f"URL redirect timeout/check failed ({wait_err}), continuing anyway...")
                time.sleep(3)
            
            logger.info("Login completed, preparing live calls page...")
            time.sleep(3)
            # Robustly load Live Calls with retries to handle transient network resets
            live_loaded = False
            for live_attempt in range(1, 5):
                try:
                    logger.info(f"Navigating to Live Calls (attempt {live_attempt})...")
                    driver.get(LIVE_CALLS_URL)
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
                    logger.info("Live Calls page loaded.")
                    live_loaded = True
                    break
                except Exception as live_err:
                    logger.warning(f"Live Calls load attempt {live_attempt} failed: {live_err}")
                    # Backoff a bit before retrying
                    time.sleep(2 * live_attempt)
                    # If the driver appears unhealthy, quit and let outer login retry recreate it
                    try:
                        _ = driver.current_url
                    except Exception as drv_err:
                        logger.error(f"WebDriver is unhealthy after live load failure: {drv_err}. Quitting driver to recreate.")
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                        break

            if live_loaded:
                return driver

            # If we couldn't load Live Calls, clean up this driver and allow an outer login retry
            logger.warning("Could not load Live Calls after retries; will retry full login if attempts remain.")
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Login attempt {login_attempt+1} failed: {e}")
            if login_attempt < max_login_attempts - 1:
                time.sleep(2)  # Wait before retrying in same browser
            else:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                logger.critical("All login attempts failed.")
                return None
def check_session(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        return driver
    except Exception as e:
        logger.warning(f"Session expired: {e}. Checking network and re-logging in...")
        if not is_network_available():
            loop = asyncio.get_event_loop()
            network_restored = loop.run_until_complete(wait_for_network())
            if not network_restored:
                return None
        if driver:
            try:
                print('Closing Chrome driver...')
                try:
                    driver.quit()
                    print('Chrome driver closed successfully!')
                except OSError as e:
                    print(f"Error while closing driver: {e}")
                except Exception:
                    pass
            except Exception:
                pass
        return selenium_prepare_login()
# FIXED: Audio download using real browser session with retry + page reload on failure
def download_audio(url, headers, filename_base, driver, retries=5, delay=5):
    """Download an audio resource using headers/cookies from the webdriver session.
    Returns the saved filename (with extension) on success, or None on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            # Refresh cookies and user agent from current driver session
            user_agent = driver.execute_script("return navigator.userAgent;")
            cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in driver.get_cookies()])
            full_headers = {
                'User-Agent': user_agent,
                'Referer': 'https://www.orangecarrier.com/live/calls',
                'Origin': 'https://www.orangecarrier.com',
                'Accept': 'audio/mpeg,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'audio',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cookie': cookie_string
            }

            r = requests.get(url, headers=full_headers, timeout=30, stream=True)
            r.raise_for_status()

            tmp_path = filename_base + ".download"
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Basic size check
            if os.path.getsize(tmp_path) <= 1024:
                logger.warning(f"Downloaded file too small (attempt {attempt})")
                try:
                    os.remove(tmp_path)
                except:
                    pass
            else:
                # Detect container heuristically
                with open(tmp_path, 'rb') as fh:
                    head = fh.read(32)
                if b'ftyp' in head or b'MP4' in head or b'moov' in head:
                    saved_path = os.path.splitext(filename_base)[0] + '.mp4'
                else:
                    saved_path = os.path.splitext(filename_base)[0] + '.mp3'

                os.replace(tmp_path, saved_path)
                logger.info(f"Audio downloaded successfully: {saved_path}")
                return saved_path

        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt < retries:
                logger.info("Reloading Live Calls page and retrying download...")
                try:
                    driver.get(LIVE_CALLS_URL)
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
                    time.sleep(3)
                except Exception as reload_err:
                    logger.error(f"Failed to reload page during retry: {reload_err}")
                time.sleep(delay)

    logger.error("All download attempts failed after retries and reloads.")
    return None
# FIXED: process_call_worker now takes driver
async def process_call_worker(call_data, cookies, context: ContextTypes.DEFAULT_TYPE, driver):
    country = call_data.get('country')
    number = call_data.get('number')
    cli_number = call_data.get('cli_number')
    audio_url = call_data.get('audio_url')

    detection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    processed_country = extract_country_from_termination(country)
    country_flag = get_country_flag(processed_country)
    masked_num = mask_number(number)
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
                logger.error(f"Failed to send pre-message to chat {chat_id}: {e}")

        temp_file_base = f"temp_audio_{int(time.time())}"
        logger.info(f"Downloading audio for {cli_number}...")
        await asyncio.sleep(bot_settings.get('audio_download_delay_seconds', 5))
        downloaded_path = download_audio(audio_url, {}, temp_file_base, driver)

        if downloaded_path:
            # We'll try to produce an MP4 for delivery (preferred). Steps:
            # - If we received MP4 container from site, send it as video (send_video).
            # - Also attempt to extract audio (mp3) with ffmpeg (if available) and send as send_audio alongside video.
            # - If we received MP3 (audio-only), send as audio (send_audio).
            final_mp3 = os.path.splitext(downloaded_path)[0] + '.mp3'
            extracted_audio = None
            try:
                # If the download was an MP4 container, prefer sending it directly as VIDEO
                if downloaded_path.lower().endswith('.mp4'):
                    ffmpeg_path = shutil.which('ffmpeg')
                    if ffmpeg_path:
                        # Extract audio (re-encode to mp3) but keep original MP4 untouched
                        mp3_from_mp4 = os.path.splitext(downloaded_path)[0] + '_extracted.mp3'
                        cmd = [ffmpeg_path, '-y', '-i', downloaded_path, '-vn', '-acodec', 'libmp3lame', '-ar', '44100', '-ac', '2', mp3_from_mp4]
                        logger.info(f"Extracting audio {downloaded_path} -> {mp3_from_mp4} using ffmpeg (mp4->mp3)")
                        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
                        if proc.returncode == 0 and os.path.exists(mp3_from_mp4):
                            extracted_audio = mp3_from_mp4
                            logger.info(f"Successfully extracted audio: {mp3_from_mp4}")
                        else:
                            logger.error(f"ffmpeg mp4->mp3 extraction failed: {proc.stderr.decode(errors='ignore') if proc else 'no proc'}")
                            extracted_audio = None
                    else:
                        # No ffmpeg: we still will send the MP4 as video (no separate audio/transcription)
                        extracted_audio = None

                else:
                    # Not an MP4 container. Ensure we have an MP3 file available for transcription if needed.
                    if not downloaded_path.lower().endswith('.mp3'):
                        # rename unknown audio to .mp3 so libraries like speech_recognition can open it
                        try:
                            os.replace(downloaded_path, final_mp3)
                            downloaded_path = final_mp3
                            extracted_audio = final_mp3
                        except Exception:
                            # If rename fails, keep original path
                            extracted_audio = downloaded_path
                    else:
                        extracted_audio = downloaded_path

                # Optional transcription (use extracted_audio if available)
                if bot_settings.get('enable_voice_transcription') and extracted_audio:
                    for retry in range(bot_settings.get('audio_transcription_retries', 1)):
                        try:
                            r = sr.Recognizer()
                            with sr.AudioFile(extracted_audio) as source:
                                audio_data = r.record(source)
                            text = r.recognize_google(audio_data)
                            otp = ' '.join(re.findall(r'\d', text))
                            break
                        except Exception as e:
                            logger.error(f"Transcription attempt {retry+1} failed: {e}")
                            if retry == bot_settings.get('audio_transcription_retries', 1) - 1:
                                otp = ''

                # Prepare the caption/message (include OTP if found)
                processed_country_esc = escape_md_v2(processed_country)
                masked_num_esc = escape_md_v2(masked_num)
                detection_time_esc = escape_md_v2(detection_time)
                message = f"✨ *New Call Activity Detected* ✨\n\n{country_flag} *Country:* {processed_country_esc}\n☎️ *Number:* {masked_num_esc}\n⌛ *Time:* {detection_time_esc}"
                if otp:
                    otp_esc = escape_md_v2(otp)
                    message += f"\n🔑 *OTP:* {otp_esc}"

                # Send to groups:
                # - If we have MP4: send_video (always). If extracted_audio available, send_audio right after.
                # - If we only have mp3/audio: send_audio.
                if downloaded_path.lower().endswith('.mp4'):
                    # Send video + optional audio
                    for chat_id in approved_chat_ids:
                        for attempt in range(3):
                            try:
                                # Send video as video (so Telegram treats as video, not photo/doc)
                                with open(downloaded_path, 'rb') as vf:
                                    input_video = InputFile(vf, filename=os.path.basename(downloaded_path))
                                    await context.bot.send_video(
                                        chat_id=chat_id,
                                        video=input_video,
                                        caption=message,
                                        parse_mode='MarkdownV2',
                                        supports_streaming=True,
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{DEVELOPER_NAME}", url=DEVELOPER_URL)]])
                                    )
                                logger.info(f"Sent mp4 video to chat {chat_id} successfully")
                                break
                            except Exception as e:
                                logger.error(f"Failed to send mp4 video to chat {chat_id} (attempt {attempt+1}): {e}")
                                if attempt < 2:
                                    await asyncio.sleep(3)

                    # If we extracted audio, also send it as audio (so users can play audio directly)
                    if extracted_audio:
                        for chat_id in approved_chat_ids:
                            for attempt in range(3):
                                try:
                                    with open(extracted_audio, 'rb') as af:
                                        input_audio = InputFile(af, filename=os.path.basename(extracted_audio))
                                        await context.bot.send_audio(
                                            chat_id=chat_id,
                                            audio=input_audio,
                                            caption=f"🔊 Audio (extracted) — {masked_num_esc}",
                                            parse_mode='MarkdownV2',
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{DEVELOPER_NAME}", url=DEVELOPER_URL)]])
                                        )
                                    logger.info(f"Sent extracted audio to chat {chat_id} successfully")
                                    break
                                except Exception as e:
                                    logger.error(f"Failed to send extracted audio to chat {chat_id} (attempt {attempt+1}): {e}")
                                    if attempt < 2:
                                        await asyncio.sleep(3)

                else:
                    # audio-only (mp3): send as audio
                    for chat_id in approved_chat_ids:
                        for attempt in range(3):
                            try:
                                with open(downloaded_path, 'rb') as af:
                                    input_audio = InputFile(af, filename=os.path.basename(downloaded_path))
                                    await context.bot.send_audio(
                                        chat_id=chat_id,
                                        audio=input_audio,
                                        caption=message,
                                        parse_mode='MarkdownV2',
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{DEVELOPER_NAME}", url=DEVELOPER_URL)]])
                                    )
                                logger.info(f"Sent audio to chat {chat_id} successfully")
                                break
                            except Exception as e:
                                logger.error(f"Failed to send audio to chat {chat_id} (attempt {attempt+1}): {e}")
                                if attempt < 2:
                                    await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Failed preparing/sending media: {e}")
                # Delete pre-messages
                for chat_id, msg_id in pre_message_ids.items():
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    except:
                        pass
                processed_country_esc = escape_md_v2(processed_country)
                masked_num_esc = escape_md_v2(masked_num)
                detection_time_esc = escape_md_v2(detection_time)
                message = f"✨ *New Call Activity Detected* ✨\n\n{country_flag} *Country:* {processed_country_esc}\n☎️ *Number:* {masked_num_esc}\n⌛ *Time:* {detection_time_esc}\n\nFile [...]"
                if otp:
                    otp_esc = escape_md_v2(otp)
                    message += f"\n🔑 *OTP:* {otp_esc}"
                await send_to_all_approved_groups(message, context)

            finally:
                # Cleanup downloaded and converted files (keep mp4 until sent; extracted audio may be removed)
                try:
                    if downloaded_path and os.path.exists(downloaded_path):
                        # keep mp4 for now; but if it's audio-only file (mp3) we can remove
                        if not downloaded_path.lower().endswith('.mp4'):
                            os.remove(downloaded_path)
                except Exception:
                    pass
                try:
                    # Clean up extracted audio if created
                    if extracted_audio and os.path.exists(extracted_audio):
                        os.remove(extracted_audio)
                except Exception:
                    pass

        else:
            # Download failed: remove pre-messages and notify
            for chat_id, msg_id in pre_message_ids.items():
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except:
                    pass
            processed_country_esc = escape_md_v2(processed_country)
            masked_num_esc = escape_md_v2(masked_num)
            detection_time_esc = escape_md_v2(detection_time)
            message = f"✨ *New Call Activity Detected* ✨\n\n{country_flag} *Country:* {processed_country_esc}\n☎️ *Number:* {masked_num_esc}\n⌛ *Time:* {detection_time_esc}\n\nAudio dow[...]"
            if otp:
                otp_esc = escape_md_v2(otp)
                message += f"\n🔑 *OTP:* {otp_esc}"
            await send_to_all_approved_groups(message, context)
    else:
        processed_country_esc = escape_md_v2(processed_country)
        masked_num_esc = escape_md_v2(masked_num)
        detection_time_esc = escape_md_v2(detection_time)
        message = f"✨ *New Call Activity Detected* ✨\n\n{country_flag} *Country:* {processed_country_esc}\n☎️ *Number:* {masked_num_esc}\n⌛ *Time:* {detection_time_esc}"
        if otp:
            otp_esc = escape_md_v2(otp)
            message += f"\n🔑 *OTP:* {otp_esc}"
        await send_to_all_approved_groups(message, context)
async def send_to_all_approved_groups(message, context: ContextTypes.DEFAULT_TYPE, retries=3):
    for chat_id in approved_chat_ids:
        for attempt in range(retries):
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{DEVELOPER_NAME}", url=DEVELOPER_URL)]])
                )
                break
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id} (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
async def send_audio_to_all_approved_groups(caption, file_path, context: ContextTypes.DEFAULT_TYPE, retries=3):
    for chat_id in approved_chat_ids:
        for attempt in range(retries):
            try:
                with open(file_path, 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio_file,
                        caption=caption,
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{DEVELOPER_NAME}", url=DEVELOPER_URL)]])
                    )
                break
            except Exception as e:
                logger.error(f"Failed to send audio to chat {chat_id} (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
async def monitor_calls(context: ContextTypes.DEFAULT_TYPE):
    driver = context.bot_data.get("driver")
    if not driver:
        await context.bot.send_message(chat_id=list(approved_chat_ids)[0] if approved_chat_ids else ADMIN_ID, text="WebDriver not initialized.")
        return
    if not await wait_for_network(1, 1):  # Quick check
        return
    driver = check_session(driver)
    if not driver:
        await context.bot.send_message(chat_id=list(approved_chat_ids)[0] if approved_chat_ids else ADMIN_ID, text="Session expired and re-login failed.")
        return
    context.bot_data["driver"] = driver
    now = time.time()
    last_refresh = context.bot_data.get("last_refresh_time", now)
    last_cookie_refresh = context.bot_data.get("last_cookie_refresh_time", now)
    if now - last_refresh >= bot_settings['refresh_interval_minutes'] * 60:
        logger.info("Refreshing page per interval...")
        driver.refresh()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        context.bot_data["last_refresh_time"] = now
    if now - last_cookie_refresh >= bot_settings['cookie_refresh_interval_minutes'] * 60:
        logger.info("Refreshing cookies...")
        driver.refresh()  # Refresh to update cookies
        context.bot_data["last_cookie_refresh_time"] = now
    if bot_settings['scraping_mode'] == 'playButton':
        calls = scrape_play_button(driver)
    else:
        calls = []
    if calls:
        for call_data in calls:
            asyncio.create_task(process_call_worker(call_data, driver.get_cookies(), context, driver))
def scrape_play_button(driver):
    calls = []
    try:
        logger.info("Scraping for new calls...")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        time.sleep(1)  # Reduced from 3s
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        tbody = soup.find('tbody', id='LiveCalls')
        if not tbody:
            logger.warning("tbody#LiveCalls not found.")
            return []
        rows = tbody.find_all('tr')
        logger.info(f"Found {len(rows)} row(s) in #LiveCalls tbody.")
        for row in rows:
            try:
                if not row.get_text(strip=True):
                    continue
                play_button = row.find('button', attrs={'onclick': re.compile(r'Play', re.I)})
                if not play_button:
                    continue
                onclick = play_button.get('onclick', '')
                match = re.search(r"Play\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)", onclick)
                if not match:
                    continue
                did, uuid = match.groups()
                if uuid in processed_calls:
                    continue
                processed_calls.add(uuid)
                tds = row.find_all('td')
                if len(tds) < 5:
                    continue
                country = tds[0].get_text(strip=True)
                number = tds[1].get_text(strip=True)
                cli_number = tds[2].get_text(strip=True)
                audio_url = f"https://www.orangecarrier.com/live/calls/sound?did={did}&uuid={uuid}"
                calls.append({
                    'country': country,
                    'number': number,
                    'cli_number': cli_number,
                    'audio_url': audio_url
                })
                logger.info(f"NEW CALL → {country} | {number} | CLI: {cli_number} | UUID: {uuid}")
            except Exception as e:
                logger.error(f"Row parse error: {e}")
        return calls
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return []
async def start(update, context):
    chat = update.message.chat
    if chat.type in ['group', 'supergroup']:
        chat_id = chat.id
        if chat_id not in approved_chat_ids:
            approved_chat_ids.add(chat_id)
            save_approved_chats()
            logger.info(f"Added chat {chat_id} to approved chats.")
    driver = context.bot_data.get("driver")
    if not driver:
        await update.message.reply_text("Bot not initialized. Restart the script.")
        return
    await update.message.reply_text("Monitoring started...")
    context.job_queue.run_repeating(monitor_calls, interval=5, first=1)


async def startt(update, context):
    """Admin-only start command. Starts monitor job if not already running."""
    # Only admin allowed
    try:
        user_id = update.message.chat.id
    except Exception:
        await update.message.reply_text("Unable to determine chat id.")
        return
    if user_id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return

    # Ensure driver is available
    driver = context.bot_data.get("driver")
    if not driver:
        await update.message.reply_text("WebDriver not initialized. Attempting to initialize...")
        new_driver = selenium_prepare_login()
        if not new_driver:
            await update.message.reply_text("Failed to initialize WebDriver. See logs for details.")
            return
        context.bot_data["driver"] = new_driver

    # Prevent duplicate scheduling using a flag in bot_data
    if context.bot_data.get("monitoring_started"):
        await update.message.reply_text("Monitoring is already running.")
        return

    context.job_queue.run_repeating(monitor_calls, interval=5, first=1)
    context.bot_data["monitoring_started"] = True
    await update.message.reply_text("✅ Monitoring started by admin.")
async def stop(update, context):
    if context.job_queue:
        context.job_queue.stop()
        await update.message.reply_text("Monitoring stopped.")
    try:
        context.bot_data["driver"].quit()
        logger.info("Browser closed.")
    except:
        pass

async def status(update, context):
    """Send bot status to admin"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    driver = context.bot_data.get("driver")
    driver_status = "✅ Active" if driver else "❌ Inactive"
    
    try:
        # Check if session is alive
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        session_status = "✅ Valid"
    except:
        session_status = "⚠️ Expired/Invalid"
    
    calls_monitored = len(processed_calls)
    approved_groups = len(approved_chat_ids)
    
    status_msg = (
        f"🤖 **BOT STATUS REPORT**\n\n"
        f"🔧 Driver: {driver_status}\n"
        f"🔐 Session: {session_status}\n"
        f"📞 Calls Processed: {calls_monitored}\n"
        f"👥 Approved Groups: {approved_groups}\n"
        f"⚙️ Mode: {bot_settings.get('scraping_mode', 'N/A')}\n"
        f"🎤 Voice Transcription: {'🔊 ON' if bot_settings.get('enable_voice_transcription') else '🔇 OFF'}\n"
        f"🌐 Network: {'✅ Online' if is_network_available() else '❌ Offline'}"
    )
    
    await update.message.reply_text(status_msg, parse_mode="Markdown")
    logger.info(f"Status report sent to admin {update.message.chat.id}")

async def clear_cache(update, context):
    """Clear processed calls cache"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    global processed_calls
    cleared_count = len(processed_calls)
    processed_calls.clear()
    
    await update.message.reply_text(f"✅ Cache cleared! Removed {cleared_count} processed calls.")
    logger.info(f"Cache cleared by admin. Removed {cleared_count} calls.")

async def settings_cmd(update, context):
    """View or change bot settings"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    if not context.args:
        # Show current settings
        settings_str = "⚙️ **Current Bot Settings:**\n\n"
        for key, value in bot_settings.items():
            settings_str += f"• `{key}`: {value}\n"
        await update.message.reply_text(settings_str, parse_mode="Markdown")
        logger.info("Settings displayed to admin")
    else:
        # Parse: /settings key value
        if len(context.args) >= 2:
            key = context.args[0]
            value = ' '.join(context.args[1:])
            
            # Try to convert to appropriate type
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            
            if key in bot_settings:
                bot_settings[key] = value
                save_settings()
                await update.message.reply_text(f"✅ Setting updated: `{key}` = `{value}`", parse_mode="Markdown")
                logger.info(f"Admin changed setting: {key} = {value}")
            else:
                await update.message.reply_text(f"❌ Unknown setting: `{key}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Usage: `/settings key value`", parse_mode="Markdown")

async def logs(update, context):
    """Send logs.txt file to admin as document"""
    # Check if user is admin
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access logs.")
        return
    
    try:
        if os.path.exists("logs.txt"):
            with open("logs.txt", "rb") as log_file:
                await context.bot.send_document(
                    chat_id=update.message.chat.id,
                    document=log_file,
                    caption="📋 Bot Logs (logs.txt)"
                )
            logger.info(f"Logs sent to admin {update.message.chat.id}")
        else:
            await update.message.reply_text("❌ logs.txt file not found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending logs: {e}")
        logger.error(f"Failed to send logs file: {e}")

async def refresh_web(update, context):
    """Admin-only: Refresh website page only (not login)"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    try:
        # Get driver from bot_data
        driver = context.bot_data.get("driver") if context.bot_data else None
        
        if not driver:
            await update.message.reply_text("❌ WebDriver not available. Cannot refresh page.")
            return
        
        # Just refresh the current page
        driver.refresh()
        time.sleep(1)
        
        await update.message.reply_text(
            "✅ Website page refreshed successfully!"
        )
        logger.info(f"Website page refreshed by admin {update.message.chat.id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error refreshing session: {str(e)}")
        logger.error(f"Failed to refresh web session: {e}")


async def add_premium(update, context):
    # Simulate adding premium
    premium_chat = update.message.chat.id
    if premium_chat not in approved_chat_ids:
        approved_chat_ids.add(premium_chat)
        save_approved_chats()
        await update.message.reply_text(f"Chat {premium_chat} added to premium list.")
    else:
        await update.message.reply_text(f"Chat {premium_chat} is already in the premium list.")


async def translate_mp3(update, context):
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("You do not have permission to access this command.")
        return
    # Add the translation logic here (e.g., Google Translate API)
    await update.message.reply_text("Translation feature is under development.")


async def add_admin(update, context):
    """Admin-only: Add new admin ID to whitelist"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("❌ Usage: `/add_admin <user_id>`\nExample: `/add_admin 123456789`", parse_mode="Markdown")
        return
    
    try:
        new_admin_id = int(context.args[0])
        
        if new_admin_id in admin_ids:
            await update.message.reply_text(f"⚠️ User ID {new_admin_id} is already an admin.")
            return
        
        admin_ids.add(new_admin_id)
        save_admin_ids()
        
        await update.message.reply_text(
            f"✅ User ID {new_admin_id} has been added as admin.\n"
            f"Total admins: {len(admin_ids)}",
            parse_mode="Markdown"
        )
        logger.info(f"Admin added by {ADMIN_ID}: {new_admin_id}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")

async def add_group(update, context):
    """Admin-only: Add new group/chat ID to approved_chat_ids"""
    if update.message.chat.id not in admin_ids:
        await update.message.reply_text("❌ You do not have permission to access this command.")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Usage: `/add_group <chat_id>`\n"
            "Example: `/add_group -1001234567890` (use negative ID for groups)\n"
            "Or: In a group, use `/add_group` without arguments to add current group.",
            parse_mode="Markdown"
        )
        return
    
    try:
        # If called in a group without args, add current group
        if len(context.args) == 0 and update.message.chat.type in ['group', 'supergroup']:
            new_group_id = update.message.chat.id
        else:
            new_group_id = int(context.args[0])
        
        if new_group_id in approved_chat_ids:
            await update.message.reply_text(f"⚠️ Chat/Group {new_group_id} is already in the approved list.")
            return
        
        approved_chat_ids.add(new_group_id)
        save_approved_chats()
        
        await update.message.reply_text(
            f"✅ Chat/Group ID {new_group_id} has been added to approved list.\n"
            f"Total approved groups: {len(approved_chat_ids)}",
            parse_mode="Markdown"
        )
        logger.info(f"Group added by admin {ADMIN_ID}: {new_group_id}")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Must be a number.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error adding group: {e}")
        logger.error(f"Error in add_group: {e}")


async def admin_start(update, context):
    """Admin /start: show full features and action buttons"""
    user_id = None
    try:
        # For messages
        user_id = update.message.chat.id
    except Exception:
        try:
            # For callback queries
            user_id = update.effective_user.id
        except Exception:
            pass

    # Check if user is admin (in private chat or in admin_ids list)
    is_admin = (user_id in admin_ids)
    
    if not is_admin:
        await update.message.reply_text("Hello! This bot monitors OrangeCarrier live calls. Contact the admin for access.")
        return

    features = (
        "🤖 *Orange Carrier Bot*\n\n"
        "I monitor https://www.orangecarrier.com live calls, download MP3 audio, optionally transcribe voice to OTP, and post to approved Telegram groups.\n\n"
        "*Key Features:*\n"
        "• MP3 audio delivery to approved groups\n"
        "• Optional voice transcription (OTP extraction)\n"
        "• Admin controls: start/stop/status/logs/settings\n"
        "• Auto re-login and cookie refresh\n"
        "• Configurable polling and timeouts via /settings\n"
    )

    keyboard = [
        [InlineKeyboardButton("Start Monitoring", callback_data="admin:start_monitor"), InlineKeyboardButton("Stop Monitoring", callback_data="admin:stop_monitor")],
        [InlineKeyboardButton("Status", callback_data="admin:status"), InlineKeyboardButton("Logs", callback_data="admin:logs")],
        [InlineKeyboardButton("Settings", callback_data="admin:settings")],
        [InlineKeyboardButton("Add Me as Admin", callback_data="admin:add_me"), InlineKeyboardButton("Add This Group", callback_data="admin:add_group_here")],
        [InlineKeyboardButton("Refresh Web", callback_data="admin:refresh_web"), InlineKeyboardButton("Clear Cache", callback_data="admin:clear_cache")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    # Use message reply if available, else send to admin
    try:
        if update.message:
            await update.message.reply_text(features, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=user_id, text=features, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Failed to send admin start message: {e}")

    # Include a short hint about /add_admin_id for interactive admin addition
    try:
        hint_text = "Tip: Untuk menambahkan admin dengan ID secara manual, jalankan perintah /add_admin_id di chat ini."
        if update.message:
            await update.message.reply_text(hint_text)
        else:
            await context.bot.send_message(chat_id=user_id, text=hint_text)
    except Exception:
        pass


async def admin_button_callback(update, context):
    query = update.callback_query
    data = query.data if query else None
    await query.answer()

    # Ensure only admins can use admin buttons
    user = update.effective_user
    if not user or user.id not in admin_ids:
        try:
            await query.message.reply_text("❌ You do not have permission to perform this action.")
        except:
            pass
        return

    if not data:
        return

    # Reply target
    reply_target = query.message

    if data == 'admin:start_monitor':
        # Start monitoring (admin)
        driver = context.bot_data.get("driver")
        if not driver:
            try:
                await reply_target.reply_text("Initializing WebDriver and logging in...")
            except:
                pass
            new_driver = selenium_prepare_login()
            if not new_driver:
                await reply_target.reply_text("❌ Failed to initialize WebDriver. Check logs.")
                return
            context.bot_data["driver"] = new_driver

        if context.bot_data.get("monitoring_started"):
            await reply_target.reply_text("Monitoring is already running.")
            return

        job = context.job_queue.run_repeating(monitor_calls, interval=5, first=1)
        context.bot_data["monitor_job"] = job
        context.bot_data["monitoring_started"] = True
        await reply_target.reply_text("✅ Monitoring started by admin.")

    elif data == 'admin:stop_monitor':
        # Stop monitoring
        try:
            context.job_queue.stop()
        except Exception:
            pass
        try:
            drv = context.bot_data.get("driver")
            if drv:
                drv.quit()
        except Exception:
            pass
        context.bot_data["monitoring_started"] = False
        await reply_target.reply_text("🛑 Monitoring stopped by admin.")

    elif data == 'admin:status':
        driver = context.bot_data.get("driver")
        driver_status = "✅ Active" if driver else "❌ Inactive"
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
            session_status = "✅ Valid"
        except Exception:
            session_status = "⚠️ Expired/Invalid"
        calls_monitored = len(processed_calls)
        approved_groups = len(approved_chat_ids)
        status_msg = (
            f"🤖 **BOT STATUS REPORT**\n\n"
            f"🔧 Driver: {driver_status}\n"
            f"🔐 Session: {session_status}\n"
            f"📞 Calls Processed: {calls_monitored}\n"
            f"👥 Approved Groups: {approved_groups}\n"
            f"⚙️ Mode: {bot_settings.get('scraping_mode', 'N/A')}\n"
            f"🎤 Voice Transcription: {'🔊 ON' if bot_settings.get('enable_voice_transcription') else '🔇 OFF'}\n"
            f"🌐 Network: {'✅ Online' if is_network_available() else '❌ Offline'}"
        )
        await reply_target.reply_text(status_msg, parse_mode="Markdown")

    elif data == 'admin:logs':
        # Send logs as file document instead of text
        try:
            if os.path.exists("logs.txt"):
                with open("logs.txt", "rb") as log_file:
                    await context.bot.send_document(
                        chat_id=user.id,
                        document=log_file,
                        caption="📋 Bot Logs (logs.txt)"
                    )
                logger.info(f"Logs sent to admin {user.id}")
            else:
                await reply_target.reply_text("❌ logs.txt file not found.")
        except Exception as e:
            await reply_target.reply_text(f"❌ Error sending logs: {e}")
            logger.error(f"Failed to send logs file: {e}")

    elif data == 'admin:settings':
        settings_str = "⚙️ **Current Bot Settings:**\n\n"
        for key, value in bot_settings.items():
            settings_str += f"• `{key}`: {value}\n"
        await reply_target.reply_text(settings_str, parse_mode="Markdown")

    elif data == 'admin:add_me':
        user = update.effective_user
        if not user:
            await reply_target.reply_text("Unable to determine user.")
            return
        uid = user.id
        if uid in admin_ids:
            await reply_target.reply_text(f"⚠️ You (ID: {uid}) are already an admin.")
            return
        admin_ids.add(uid)
        save_admin_ids()
        await reply_target.reply_text(f"✅ Your user ID ({uid}) has been added as an admin.")
        logger.info(f"Admin added via button by {uid}")

    elif data == 'admin:add_group_here':
        # If invoked in a group message, add the group. Otherwise inform admin to run in group.
        chat = query.message.chat if query and query.message else None
        if not chat:
            await reply_target.reply_text("Unable to determine chat. Please use this button from the target group message.")
            return
        if chat.type not in ['group', 'supergroup']:
            await reply_target.reply_text("This action must be performed from within the target group chat.")
            return
        gid = chat.id
        if gid in approved_chat_ids:
            await reply_target.reply_text(f"⚠️ This group (ID: {gid}) is already approved.")
            return
        approved_chat_ids.add(gid)
        save_approved_chats()
        await reply_target.reply_text(f"✅ This group (ID: {gid}) has been added to approved groups.")
        logger.info(f"Group {gid} added via button by admin {update.effective_user.id}")

    elif data == 'admin:refresh_web':
        # Refresh website page only (tidak login ulang)
        try:
            driver = context.bot_data.get("driver") if context.bot_data else None
            if not driver:
                await reply_target.reply_text("❌ WebDriver not available. Cannot refresh page.")
                return
            # Just refresh the current page
            driver.refresh()
            time.sleep(1)
            await reply_target.reply_text("✅ Website page refreshed successfully!")
            logger.info(f"Website page refreshed by admin (button) {update.effective_user.id}")
        except Exception as e:
            await reply_target.reply_text(f"❌ Error refreshing page: {e}")
            logger.error(f"Failed to refresh web page via button: {e}")

    elif data == 'admin:clear_cache':
        processed_cleared = len(processed_calls)
        processed_calls.clear()
        await reply_target.reply_text(f"✅ Cache cleared! Removed {processed_cleared} processed calls.")
        logger.info(f"Cache cleared by admin via button {update.effective_user.id}")

async def post_init(app: Application) -> None:
    """Async callback run when the Application starts."""
    try:
        driver_present = True if app.bot_data.get("driver") else False
        login_status_emoji = "✅" if driver_present else "❌"
        login_status = f"{login_status_emoji} Login: {'Successful' if driver_present else 'Failed'}"
        startup_msg = (
            "🤖 <b>BOT STARTED</b>\n\n"
            f"{login_status}\n"
            f"👤 Admin ID: {ADMIN_ID}\n"
            f"👥 Approved Groups: {len(approved_chat_ids)}\n"
            "📊 Monitoring: Ready\n"
            "🎤 Audio Format: MP3\n\n"
            "<b>Available Commands:</b>\n"
            "/startcall - Start monitoring\n"
            "/stopcall - Stop monitoring\n"
            "/status - Check bot status\n"
            "/logs - View system logs\n"
            "/settings - View/edit settings\n"
            "/clear_cache - Clear processed calls\n"
            "/refresh_web - Re-login to website\n"
            "/add_premium - Add this group\n"
            "/add_admin - Add new admin ID\n"
            "/add_group - Add new group ID\n"
        )
        # Add ffmpeg status and brief install hint
        ffmpeg_path = shutil.which('ffmpeg')
        ffmpeg_status = "✅ Installed" if ffmpeg_path else "❌ Not found"
        startup_msg = startup_msg + f"\nFFmpeg: {ffmpeg_status}\n\n" + (
            "Jika FFmpeg tidak terpasang, instalasi diperlukan untuk ekstraksi audio.\n"
            "Windows (Chocolatey): `choco install ffmpeg`\n"
            "Atau download: https://www.gyan.dev/ffmpeg/builds/ (tambahkan ke PATH)\n"
        )

        # Send startup message to every configured admin id
        for aid in list(admin_ids):
            try:
                await app.bot.send_message(chat_id=aid, text=startup_msg, parse_mode="HTML")
                logger.info(f"Startup message sent to admin {aid}. Login status: {login_status}; ffmpeg: {ffmpeg_status}")
            except Exception as e:
                logger.error(f"Failed to send startup message to admin {aid}: {e}")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")


def main():
    load_settings()
    load_approved_chats()
    load_admin_ids()  # Load admin IDs from file
    driver = selenium_prepare_login()
    # Store login status in a global for post_init to use
    global login_successful
    login_successful = driver is not None
    if not driver:
        print("Login failed. Exiting.")
        return
    job_queue = JobQueue()
    job_queue.scheduler.configure(timezone=pytz.timezone('Asia/Dhaka'))
    app = Application.builder().token(BOT_TOKEN).job_queue(job_queue).post_init(post_init).build()
    app.bot_data["driver"] = driver
    app.bot_data["last_refresh_time"] = time.time()
    app.bot_data["last_cookie_refresh_time"] = time.time()
    app.add_handler(CommandHandler("startcall", start))
    app.add_handler(CommandHandler("stopcall", stop))
    app.add_handler(CommandHandler("startt", startt))
    # Admin interactive start
    app.add_handler(CommandHandler("start", admin_start))
    app.add_handler(CallbackQueryHandler(admin_button_callback))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("refresh_web", refresh_web))
    app.add_handler(CommandHandler("add_premium", add_premium))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("clear_cache", clear_cache))
    app.add_handler(CommandHandler("translate_mp3", translate_mp3))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("add_group", add_group))
    # Conversation handler for interactive add admin by ID
    ADD_ADMIN_WAIT = 1

    async def add_admin_id_start(update, context):
        if update.message.chat.id not in admin_ids:
            await update.message.reply_text("❌ Anda tidak punya izin untuk menambahkan admin.")
            return ConversationHandler.END
        await update.message.reply_text("Silakan kirimkan User ID (angka) yang ingin ditambahkan sebagai admin:")
        return ADD_ADMIN_WAIT

    async def add_admin_id_receive(update, context):
        text = (update.message.text or '').strip()
        try:
            new_id = int(text)
        except Exception:
            await update.message.reply_text("ID tidak valid. Pastikan hanya angka. Batalkan dengan /cancel")
            return ADD_ADMIN_WAIT
        if new_id in admin_ids:
            await update.message.reply_text(f"⚠️ User ID {new_id} sudah menjadi admin.")
        else:
            admin_ids.add(new_id)
            save_admin_ids()
            await update.message.reply_text(f"✅ User ID {new_id} telah ditambahkan sebagai admin.")
            logger.info(f"Admin {new_id} added via interactive flow by {update.message.chat.id}")
        return ConversationHandler.END

    async def add_admin_cancel(update, context):
        await update.message.reply_text("Operasi dibatalkan.")
        return ConversationHandler.END

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_admin_id', add_admin_id_start)],
        states={
            ADD_ADMIN_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_id_receive)],
        },
        fallbacks=[CommandHandler('cancel', add_admin_cancel)],
        block=False,
    )
    app.add_handler(conv_handler)
    
    print("Bot is ready. Send /start in your group.")
    print("Monitoring will begin after /start command.")
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        try:
            print('Closing Chrome driver...')
            try:
                # Try to get driver from app if available
                drv = app.bot_data.get("driver") if app and app.bot_data else None
                if drv:
                    drv.quit()
                    print('Chrome driver closed successfully!')
            except OSError as e:
                print(f"Error while closing driver: {e}")
            except Exception:
                pass
            print('Chrome driver closed successfully!')
        except Exception:
            pass


if __name__ == "__main__":
    main()