"""
Instagram Scraper с Selenium - Байпасва Rate Limit
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import time
import random
import os
import sys
import requests
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import re
import json
import traceback
from selenium.webdriver.common.keys import Keys


class InstagramSeleniumScraper:
    def __init__(self, download_folder="downloads", progress_callback=None, headless=False):
        """
        Инициализира Selenium scraper

        Args:
            download_folder: Папка където да се запазват снимките
            progress_callback: Функция за обновяване на прогреса
            headless: Дали да работи без визуален браузър
        """
        self.download_folder = download_folder
        self.progress_callback = progress_callback
        self.headless = headless
        self.driver = None

        # Създаване на папка за сваляне
        Path(self.download_folder).mkdir(parents=True, exist_ok=True)

    def _log(self, message):
        """Изпраща съобщение към callback функцията"""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)

    def _init_driver(self):
        """Инициализира Edge driver"""
        edge_options = Options()

        if self.headless:
            edge_options.add_argument("--headless")

        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0")

        # Скриване на грешки и логове
        edge_options.add_argument("--log-level=3")  # Само фатални грешки
        edge_options.add_argument("--silent")
        edge_options.add_argument("--disable-logging")

        # Изключване на Edge password manager и други pop-up-ове
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
            "autofill.profile_enabled": False,
        }
        edge_options.add_experimental_option("prefs", prefs)

        # Премахване на automation флагове
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        edge_options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Edge(options=edge_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self._log("✓ Edge browser started")
        except Exception as e:
            self._log(f"✗ Error starting Edge: {e}")
            self._log("💡 Make sure you have Microsoft Edge installed")
            raise

    def login(self, username, password):
        """Login to Instagram"""
        try:
            self._log("🔐 Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(random.uniform(3, 5))

            # Accept cookies (if present)
            try:
                self._log("⏳ Checking for cookie banner...")
                # Различни възможни селектори за cookie бутона
                cookie_selectors = [
                    "//button[contains(text(), 'Allow all cookies')]",
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Allow essential and optional cookies')]",
                    "//button[contains(text(), 'Приемам')]",
                    "//button[contains(., 'Allow')]",
                    "//button[@class and contains(@class, 'aOOlW') and contains(@class, 'bIiDR')]",  # Instagram cookie button class
                ]

                cookie_accepted = False
                for selector in cookie_selectors:
                    try:
                        cookie_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        cookie_button.click()
                        self._log("✓ Cookies accepted")
                        cookie_accepted = True
                        time.sleep(1)
                        break
                    except (Exception,):
                        continue

                if not cookie_accepted:
                    self._log("ℹ️ No cookie banner or already accepted")

            except Exception as e:
                self._log(f"ℹ️ No cookie banner: {e}")

            time.sleep(random.uniform(2, 3))

            # Find active field (already focused after cookie banner)
            self._log("⏳ Clicking on first field...")

            # Find input fields
            try:
                # Find all input fields
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                self._log(f"ℹ️ Found {len(inputs)} input fields")

                # Find username field (usually first visible)
                username_input = None
                for inp in inputs:
                    if inp.is_displayed() and inp.get_attribute("name") == "username":
                        username_input = inp
                        break

                if not username_input:
                    # Try first visible field
                    for inp in inputs:
                        if inp.is_displayed():
                            username_input = inp
                            self._log("ℹ️ Using first visible field")
                            break

                if not username_input:
                    self._log("✗ Cannot find input field!")
                    return False

                # Click on field
                username_input.click()
                time.sleep(0.5)

                # Enter username
                # 🔒 Security: Don't log username to prevent credential exposure
                self._log(f"⏳ Entering username: {'*' * len(username)}")
                username_input.send_keys(username)
                time.sleep(random.uniform(0.5, 1))

                self._log("✓ Username entered")

                # Press Tab to move to password
                self._log("⏳ Pressing Tab for password...")
                username_input.send_keys(Keys.TAB)
                time.sleep(0.5)

                # Enter password (active field is now password)
                self._log(f"⏳ Entering password...")
                password_element = self.driver.switch_to.active_element
                password_element.send_keys(password)
                time.sleep(random.uniform(0.8, 1.5))

                self._log("✓ Password entered")

                # Press Enter directly from password field (most natural)
                self._log("⏳ Pressing Enter to login...")
                password_element.send_keys(Keys.ENTER)
                time.sleep(0.5)

            except Exception as e:
                self._log(f"✗ Error during input: {e}")
                # Try to press Enter from wherever we are
                try:
                    self._log("⏳ Trying Enter from active field...")
                    active = self.driver.switch_to.active_element
                    active.send_keys(Keys.ENTER)
                except (Exception,):
                    pass
                return False

            self._log("⏳ Waiting for login...")
            time.sleep(random.uniform(6, 9))

            # Check for login error
            try:
                error_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Sorry') or contains(text(), 'incorrect')]")
                self._log("✗ Error: Invalid username or password!")
                return False
            except (Exception,):
                pass  # No error - good

            # Check for "Save Your Login Info" and skip
            try:
                self._log("⏳ Checking for 'Save Login Info'...")
                save_login_selectors = [
                    "//button[contains(text(), 'Not now')]",
                    "//button[contains(text(), 'Not Now')]",
                    "//button[text()='Not Now']",
                    "//div[contains(text(), 'Not now')]",
                    "//div[contains(text(), 'Not Now')]",
                    "//button[contains(@class, '_acan') and contains(text(), 'Not')]",
                    "//*[text()='Not Now']",
                    "//*[text()='Not now']",
                ]
                clicked = False
                for selector in save_login_selectors:
                    try:
                        btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        btn.click()
                        clicked = True
                        self._log("✓ Skipped 'Save Login Info'")
                        time.sleep(2)
                        break
                    except (Exception,):
                        continue
                if not clicked:
                    self._log("ℹ️ No 'Save Login Info' prompt")
            except (Exception,):
                self._log("ℹ️ No 'Save Login Info' prompt")

            # Check for "Turn on Notifications" and skip
            try:
                self._log("⏳ Checking for 'Notifications'...")
                notification_selectors = [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[text()='Not Now']",
                    "//div[@role='dialog']//button[contains(text(), 'Not Now')]",
                    "//*[@role='dialog']//*[text()='Not Now']",
                ]
                clicked = False
                for selector in notification_selectors:
                    try:
                        btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        btn.click()
                        clicked = True
                        self._log("✓ Skipped 'Notifications'")
                        time.sleep(2)
                        break
                    except (Exception,):
                        continue
                if not clicked:
                    self._log("ℹ️ No 'Notifications' prompt")
            except (Exception,):
                self._log("ℹ️ No 'Notifications' prompt")

            self._log("✓ Login successful!")
            return True

        except Exception as e:
            self._log(f"✗ Login error: {e}")
            self._log(f"Details: {traceback.format_exc()}")
            return False

    def _extract_reel_from_page_source(self, debug=False):
        """Извлича видео URL от page source за Reels"""
        try:
            page_source = self.driver.page_source

            # Търсене на video_url или playable_url в JSON данните
            patterns = [
                r'"video_url"\s*:\s*"([^"]+)"',
                r'"playable_url"\s*:\s*"([^"]+)"',
                r'"playable_url_quality_hd"\s*:\s*"([^"]+)"',
                r'"video_versions"\s*:\s*\[\s*\{\s*"[^"]*"\s*:\s*\d+\s*,\s*"[^"]*"\s*:\s*\d+\s*,\s*"url"\s*:\s*"([^"]+)"',
                r'video_url["\s:]+([^"]*cdninstagram[^"]*)',
                r'playable_url["\s:]+([^"]*cdninstagram[^"]*)',
            ]

            video_urls = []
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    # Декодиране на escaped символи
                    url = match.replace('\\u0026', '&').replace('\\/', '/')
                    if ('cdninstagram' in url or 'fbcdn' in url) and '.mp4' in url:
                        video_urls.append(url)
                        if debug:
                            self._log(f"  [DEBUG] Page source видео: {url[:70]}...")

            if video_urls:
                # Връщаме най-дългия URL (обикновено най-високо качество)
                best_url = max(video_urls, key=len)
                if debug:
                    self._log(f"  [DEBUG] Video URL: {best_url[:70]}...")
                return best_url

        except Exception as e:
            if debug:
                self._log(f"  [DEBUG] Page source грешка: {e}")

        return None

    def _find_post_media(self, debug=False, is_reel=False):
        """Намира URL на снимката или видеото в текущия пост"""

        # За Reels първо пробваме page source метода (най-надежден)
        if is_reel:
            if debug:
                self._log("  [DEBUG] Reel detected - searching in page source...")
            time.sleep(2)  # Изчакване за зареждане

            video_url = self._extract_reel_from_page_source(debug=debug)
            if video_url:
                return video_url, 'video'

            if debug:
                self._log("  [DEBUG] Page source does not contain video, trying DOM...")

        # Проверяваме за видео в DOM
        try:
            video_elements = self.driver.find_elements(By.TAG_NAME, "video")
            if debug and video_elements:
                self._log(f"  [DEBUG] Found  {len(video_elements)} video element")

            for video in video_elements:
                # Пробваме различни атрибути за видео URL
                src = video.get_attribute('src')

                # Ако няма src, пробваме currentSrc
                if not src:
                    src = video.get_attribute('currentSrc')

                # Пробваме да вземем от source елемент вътре във video
                if not src:
                    try:
                        source = video.find_element(By.TAG_NAME, "source")
                        src = source.get_attribute('src')
                    except (Exception,):
                        pass

                if debug and src:
                    self._log(f"  [DEBUG] Video src: {src[:50]}...")

                if src and ('cdninstagram' in src or 'fbcdn' in src) and not src.startswith('blob:'):
                    if debug:
                        self._log(f"  [DEBUG] Видео от DOM: {src[:70]}...")
                    return src, 'video'

                # За Reels с blob URL - кликваме и пробваме page source пак
                if is_reel and (not src or src.startswith('blob:')):
                    try:
                        if debug:
                            self._log("  [DEBUG] Blob URL - кликам на видеото...")
                        video.click()
                        time.sleep(1.5)
                        # Пробваме page source пак след клик
                        video_url = self._extract_reel_from_page_source(debug=debug)
                        if video_url:
                            return video_url, 'video'
                    except (Exception,):
                        pass
        except (Exception,):
            pass

        # Търсим всички img елементи на страницата
        try:
            all_images = self.driver.find_elements(By.TAG_NAME, "img")

            if debug:
                self._log(f"  [DEBUG] Total {len(all_images)} img elements")

            # Филтриране - търсим голяма снимка от CDN
            for img in all_images:
                try:
                    src = img.get_attribute('src') or ''
                    alt = img.get_attribute('alt') or ''

                    # Пропускаме ако няма src
                    if not src:
                        continue

                    # Пропускаме профилни снимки по alt текст
                    if 'profile picture' in alt.lower():
                        if debug:
                            self._log(f"  [DEBUG] Skipping profile picture: {alt[:40]}")
                        continue

                    # Пропускаме малки иконки (по размер в URL)
                    skip_patterns = [
                        's150x150', 's320x320', 's64x64', 's44x44', 's56x56', 's88x88', 's128x128',
                        '/44x44/', '/56x56/', '/64x64/', '/88x88/', '/150x150/', '/320x320/',
                        '/s32x32/', '/s40x40/', '/s77x77/', '/s100x100/', '/s240x240/',
                        'profile_pic', '_a.jpg'
                    ]

                    should_skip = any(p in src for p in skip_patterns)
                    if should_skip:
                        continue

                    # Проверка дали е от Instagram CDN и е достатъчно дълъг URL
                    if ('cdninstagram' in src or 'fbcdn' in src) and len(src) > 150:
                        if debug:
                            self._log(f"  [DEBUG] Selected: {src[:80]}...")
                            self._log(f"           alt='{alt[:50]}'")
                        return src, 'image'

                except Exception as e:
                    if debug:
                        self._log(f"  [DEBUG] Error img: {e}")
                    continue

        except Exception as e:
            if debug:
                self._log(f"  [DEBUG] Generic error: {e}")

        # Ако нищо не намерихме, пробваме srcset
        try:
            all_images = self.driver.find_elements(By.XPATH, "//img[@srcset]")
            for img in all_images:
                srcset = img.get_attribute('srcset') or ''
                if 'cdninstagram' in srcset or 'fbcdn' in srcset:
                    # Взимаме най-голямата снимка от srcset
                    parts = srcset.split(',')
                    if parts:
                        # Последната обикновено е най-голямата
                        last_src = parts[-1].strip().split(' ')[0]
                        if len(last_src) > 100:
                            if debug:
                                self._log(f"  [DEBUG] От srcset: {last_src[:70]}...")
                            return last_src, 'image'
        except (Exception,):
            pass

        if debug:
            self._log("  [DEBUG] Нищо не е намерено!")

        return None, None

    def _extract_post_description(self, debug=False):
        """Извлича описанието (caption) от текущо отворен пост"""
        try:
            # Метод 1: Директно от DOM - h1 елемент в div._a9zr
            # Структурата на поста е:
            #   ul._a9z6 > div > li._a9zj > div._a9zm > div._a9zo > div._a9zr
            #     ├── h2 (съдържа username линк)
            #     ├── div > h1._ap3a._aaco._aacu._aacx._aad7._aade (CAPTION)
            #     └── div > span > time (дата)
            # ВАЖНО: Коментарите също имат div._a9zr но с h3 и span._ap3a
            # Затова таргетираме САМО h1 (не span) за caption на поста

            # Първо опитваме най-точния селектор: h1 в първия _a9zr (поста)
            # ul._a9z6 е контейнерът на поста (не _a9ym който е за коментари)
            caption_selectors = [
                # Точен: h1 в поста (ul._a9z6), не в коментарите (ul._a9ym)
                "//ul[contains(@class, '_a9z6')]//div[contains(@class, '_a9zr')]//h1[contains(@class, '_ap3a') and contains(@class, '_aade')]",
                # Fallback: първият h1 с тези класове на страницата
                "//h1[contains(@class, '_ap3a') and contains(@class, '_aaco') and contains(@class, '_aacu') and contains(@class, '_aacx') and contains(@class, '_aad7') and contains(@class, '_aade')]",
                # По-общ: h1 в div._a9zr (постът винаги е първият)
                "//div[contains(@class, '_a9zr')]//h1[contains(@class, '_ap3a')]",
                # Най-общ h1 fallback
                "//h1[contains(@class, '_ap3a')]",
            ]

            for selector in caption_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 5:
                            if debug:
                                self._log(f"  [DEBUG] Description от DOM (h1): {text[:60]}...")
                            return text
                except (Exception,):
                    continue

            # Метод 2: Търсене в meta tag (og:description) като fallback
            try:
                meta = self.driver.find_element(By.XPATH, "//meta[@property='og:description']")
                content = meta.get_attribute('content') or ''
                if content:
                    # og:description обикновено е във формат: "X Likes, Y Comments - USERNAME on Instagram: "CAPTION""
                    match = re.search(r':\s*["\u201c](.+)["\u201d]\s*$', content, re.DOTALL)
                    if match:
                        description = match.group(1).strip()
                        if debug:
                            self._log(f"  [DEBUG] Description от meta tag: {description[:60]}...")
                        return description
                    if debug:
                        self._log(f"  [DEBUG] Description от meta (raw): {content[:60]}...")
                    return content
            except (Exception,):
                pass

            # Метод 3: Търсене в page source чрез JSON
            try:
                page_source = self.driver.page_source
                caption_patterns = [
                    r'"caption"\s*:\s*\{[^}]*"text"\s*:\s*"([^"]{5,})"',
                    r'"edge_media_to_caption"\s*:\s*\{"edges"\s*:\s*\[\s*\{\s*"node"\s*:\s*\{\s*"text"\s*:\s*"([^"]+)"',
                ]
                for pattern in caption_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        description = match.group(1)
                        # Decode JSON escape sequences properly (handles \uXXXX, \n, \t, etc.)
                        try:
                            description = json.loads(f'"{description}"')
                        except (json.JSONDecodeError, ValueError):
                            pass  # Keep original string if JSON decode fails
                        if debug:
                            self._log(f"  [DEBUG] Description от JSON: {description[:60]}...")
                        return description
            except (Exception,):
                pass

            if debug:
                self._log("  [DEBUG] Не е намерено описание за поста")
            return None

        except Exception as e:
            if debug:
                self._log(f"  [DEBUG] Грешка при извличане на описание: {e}")
            return None

    @staticmethod
    def extract_username_from_url(url_or_username):
        """Извлича потребителското име от URL"""
        pattern = r'(?:https?://)?(?:www\.)?instagram\.com/([^/?]+)'
        match = re.match(pattern, url_or_username.strip())

        if match:
            username = match.group(1)
        else:
            username = url_or_username.strip().lstrip('@')

        # 🔒 Security: Validate username to prevent path traversal and injection
        # Instagram usernames can only contain letters, numbers, periods, and underscores
        # and must be between 1-30 characters
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            raise ValueError(f"Invalid username: '{username}'. Only alphanumeric characters and '_' are allowed.")

        # 🔒 Security: Prevent path traversal attacks
        if '..' in username or '/' in username or '\\' in username:
            raise ValueError(f"Invalid username: '{username}'. Dangerous symbols.")

        return username

    def download_profile_posts(self, url_or_username, max_posts=None, delay_range=(3, 6)):
        """Download images from profile"""
        try:
            profile_username = self.extract_username_from_url(url_or_username)

            # 🔒 Security: Mask username in logs (show only first 3 chars)
            masked_username = profile_username[:3] + '*' * (len(profile_username) - 3) if len(profile_username) > 3 else '***'
            self._log(f"\n📥 Starting download from @{masked_username}...")

            # Open profile
            profile_url = f"https://www.instagram.com/{profile_username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))

            # Scroll down to load images
            self._log("📜 Loading images...")

            # Find all images
            image_links = []
            scroll_pause = 2
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while True:
                # Find all posts - /p/ (images) and /reel/ (videos)
                posts = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")

                for post in posts:
                    href = post.get_attribute('href')
                    if href and href not in image_links:
                        image_links.append(href)

                self._log(f"📊 Found {len(image_links)} posts...")

                # Check if we reached the limit
                if max_posts and len(image_links) >= max_posts:
                    image_links = image_links[:max_posts]
                    break

                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)

                # Check if there's more content
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            self._log(f"✓ Found total {len(image_links)} posts")

            # 🔒 Security: Sanitize profile_username to prevent directory traversal
            # Use os.path.basename to ensure we only get the filename part
            safe_username = os.path.basename(profile_username)

            # Create profile folder with subfolders for images and videos
            profile_folder = os.path.join(self.download_folder, safe_username)

            # 🔒 Security: Verify the path is within download_folder
            profile_folder = os.path.abspath(profile_folder)
            download_folder_abs = os.path.abspath(self.download_folder)
            if not profile_folder.startswith(download_folder_abs + os.sep):
                raise ValueError(f"Security error: Attempted path traversal detected!")

            images_folder = os.path.join(profile_folder, "images")
            videos_folder = os.path.join(profile_folder, "videos")
            Path(images_folder).mkdir(parents=True, exist_ok=True)
            Path(videos_folder).mkdir(parents=True, exist_ok=True)
            self._log(f"📁 Created folders: {profile_folder}/images and /videos")

            # Download media
            total_images = 0
            total_videos = 0
            total_descriptions = 0

            for idx, post_url in enumerate(image_links, 1):
                try:
                    # Delay between posts
                    delay = random.uniform(*delay_range)
                    self._log(f"⏳ Waiting {delay:.1f}s before post {idx}/{len(image_links)}...")
                    time.sleep(delay)

                    # Open post
                    self.driver.get(post_url)
                    time.sleep(random.uniform(2, 4))

                    # Fix #12: Detect rate limiting / challenge pages
                    page_source_check = self.driver.page_source.lower()
                    if 'challenge' in page_source_check or 'suspicious' in page_source_check:
                        self._log("⚠ Instagram challenge/captcha detected! Waiting 60s before retry...")
                        time.sleep(60)
                        self.driver.get(post_url)
                        time.sleep(random.uniform(3, 5))
                    elif 'login' in self.driver.current_url and '/p/' not in self.driver.current_url and '/reel/' not in self.driver.current_url:
                        self._log("⚠ Redirected to login — possible rate limit. Waiting 120s...")
                        time.sleep(120)
                        self.driver.get(post_url)
                        time.sleep(random.uniform(3, 5))

                    # Extract description from post
                    description = self._extract_post_description(debug=True)

                    # Find media - including carousel (slideshow)
                    try:
                        # Wait for media to load
                        time.sleep(1.5)

                        # Collect all media from post (including carousel)
                        post_media = []  # list of (url, type)
                        seen_urls = set()
                        slide_num = 0

                        while True:
                            slide_num += 1

                            # Find current media (image or video)
                            is_reel = '/reel/' in post_url
                            media_url, media_type = self._find_post_media(debug=True, is_reel=is_reel)

                            if media_url and media_url not in seen_urls:
                                seen_urls.add(media_url)
                                post_media.append((media_url, media_type))

                            # Check for carousel - look for "Next" button
                            try:
                                next_button = self.driver.find_element(
                                    By.XPATH,
                                    "//button[@aria-label='Next' or @aria-label='Напред' or contains(@class, 'coreSpriteRight')]"
                                )
                                if next_button.is_displayed():
                                    next_button.click()
                                    time.sleep(1.5)  # Wait for animation

                                    # Fix #5: Retry if same URL found (animation not finished)
                                    retry_url, retry_type = self._find_post_media(debug=False, is_reel=is_reel)
                                    if retry_url and retry_url in seen_urls:
                                        # Same media — wait more and retry once
                                        time.sleep(1.5)
                                else:
                                    break
                            except (Exception,):
                                # No Next button - this is the last/only media
                                break

                            # Protection from infinite loop
                            if slide_num > 20:
                                break

                        # Download all found media
                        if post_media:
                            # Determine target parent folder based on media type
                            # If any video is present (reel/video post) -> videos/, otherwise -> images/
                            has_video = any(mt == 'video' for _, mt in post_media)
                            parent_folder = videos_folder if has_video else images_folder

                            # Create post subfolder inside images/ or videos/
                            post_folder_name = f"post_{idx}"
                            post_folder = os.path.join(parent_folder, post_folder_name)

                            # 🔒 Security: Verify the path is within profile_folder
                            post_folder_abs = os.path.abspath(post_folder)
                            profile_folder_abs = os.path.abspath(profile_folder)
                            if not post_folder_abs.startswith(profile_folder_abs + os.sep):
                                self._log(f"⚠ Security: Skipping post with invalid path")
                                continue

                            # Fix #15: Overwrite protection — skip if folder already exists with content
                            if os.path.exists(post_folder) and os.listdir(post_folder):
                                self._log(f"⏭ Skipping post {idx} — already downloaded in {post_folder_name}/")
                                continue

                            Path(post_folder).mkdir(parents=True, exist_ok=True)

                            # Save description.txt in the post subfolder
                            if description:
                                desc_filepath = os.path.join(post_folder, "description.txt")
                                with open(desc_filepath, 'w', encoding='utf-8') as f:
                                    f.write(description)
                                total_descriptions += 1
                                self._log(f"📝 Saved description ({len(description)} chars)")

                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Referer': 'https://www.instagram.com/'
                            }

                            images_count = 0
                            videos_count = 0

                            for media_idx, (media_url, media_type) in enumerate(post_media, 1):
                                try:
                                    # Determine extension
                                    if media_type == 'video':
                                        ext = '.mp4'
                                    else:
                                        ext = '.jpg'

                                    # Fix #6: Filename - use zero-padded numbers for carousel (safe for any count)
                                    # 🔒 Security: Use safe_username for filename
                                    if len(post_media) > 1:
                                        filename = f"{safe_username}_{idx}_{media_idx:02d}{ext}"
                                    else:
                                        filename = f"{safe_username}_{idx}{ext}"

                                    filepath = os.path.join(post_folder, filename)

                                    # 🔒 Security: Verify filepath is within post folder
                                    filepath_abs = os.path.abspath(filepath)
                                    if not filepath_abs.startswith(post_folder_abs + os.sep):
                                        self._log(f"⚠ Security: Skipping file with invalid path: {filepath}")
                                        continue

                                    # Fix #7 & #8: Stream download to avoid loading entire file in RAM
                                    # timeout=(connect_timeout, read_timeout)
                                    with requests.get(
                                        media_url,
                                        headers=headers,
                                        verify=True,
                                        timeout=(10, 120),
                                        stream=True
                                    ) as response:
                                        response.raise_for_status()
                                        with open(filepath, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                f.write(chunk)

                                    # Актуализиране на броячите
                                    if media_type == 'video':
                                        videos_count += 1
                                        total_videos += 1
                                    else:
                                        images_count += 1
                                        total_images += 1
                                except requests.exceptions.SSLError as e:
                                    self._log(f"⚠ SSL error: Invalid certificate")
                                except requests.exceptions.Timeout as e:
                                    self._log(f"⚠ Timeout error: The request took too long")
                                except requests.exceptions.RequestException as e:
                                    self._log(f"⚠ Network error: {type(e).__name__}")
                                except Exception as e:
                                    self._log(f"⚠ Download error: {e}")

                            # Лог съобщение
                            category = "videos" if has_video else "images"
                            if len(post_media) > 1:
                                parts = []
                                if images_count > 0:
                                    parts.append(f"{images_count} images")
                                if videos_count > 0:
                                    parts.append(f"{videos_count} videos")
                                self._log(f"✓ Downloaded {' and '.join(parts)} from carousel → {category}/{post_folder_name}/ (post {idx}/{len(image_links)}) | Total: {total_images} img, {total_videos} vid")
                            else:
                                media_type_bg = "видео" if post_media[0][1] == 'video' else "снимка"
                                self._log(f"✓ Downloaded {media_type_bg} → {category}/{post_folder_name}/ (post {idx}/{len(image_links)}) | Total: {total_images} img, {total_videos} vid")
                        else:
                            self._log(f"⚠ Couldn't find media in post {idx}")

                    except Exception as e:
                        self._log(f"⚠ Couldn't find image in post {idx}: {e}")
                        continue

                except Exception as e:
                    self._log(f"✗ Post error {idx}: {e}")
                    continue

                # Прогрес съобщение на всеки 10 поста
                if idx % 10 == 0:
                    self._log(f"\n📊 Progress: {idx}/{len(image_links)} posts | {total_images} images, {total_videos} videos, {total_descriptions} descriptions\n")

            # Финално съобщение
            parts = []
            if total_images > 0:
                parts.append(f"{total_images} images")
            if total_videos > 0:
                parts.append(f"{total_videos} videos")
            if total_descriptions > 0:
                parts.append(f"{total_descriptions} descriptions")

            if parts:
                self._log(f"\n✅ Success! Downloaded {' and '.join(parts)} in '{profile_folder}'")
                self._log(f"📂 Each post is saved in its own subfolder (post_1/, post_2/, ...)")
            else:
                self._log(f"\n⚠ No posts found")

            return total_images, total_videos

        except Exception as e:
            self._log(f"✗ Error: {e}")
            return 0, 0

    def close(self):
        """Затваря браузъра"""
        if self.driver:
            self.driver.quit()
            self._log("✓ Browser  closed")



class SeleniumScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Scraper - Selenium (Anti-Ban)")
        self.root.geometry("900x850")
        self.root.resizable(True, True)
        self.root.minsize(750, 700)

        self.download_folder = "downloads"
        self.scraper = None
        self.is_downloading = False

        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Modern.TEntry",
            font=("Segoe UI", 11),
            padding=(10, 8),
        )

        style.configure(
            "Modern.TLabel",
            font=("Segoe UI", 10),
        )

        style.configure(
            "Modern.TCheckbutton",
            font=("Segoe UI", 10),
        )

        style.configure(
            "Modern.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )

        self.setup_ui()

    def setup_ui(self):
        header_h = 90
        title_canvas = tk.Canvas(self.root, height=header_h, highlightthickness=0)
        title_canvas.pack(fill=tk.X)

        def _hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(rgb):
            return "#%02x%02x%02x" % rgb

        def _lerp(a, b, t):
            return int(a + (b - a) * t)

        def _draw_horizontal_gradient(canvas, width, height, colors):
            stops = [_hex_to_rgb(c) for c in colors]
            n = len(stops) - 1
            for x in range(width):
                p = x / max(width - 1, 1)
                seg = min(int(p * n), n - 1)
                local_t = (p - seg / n) * n
                c1, c2 = stops[seg], stops[seg + 1]
                rgb = (
                    _lerp(c1[0], c2[0], local_t),
                    _lerp(c1[1], c2[1], local_t),
                    _lerp(c1[2], c2[2], local_t),
                )
                canvas.create_line(x, 0, x, height, fill=_rgb_to_hex(rgb))

        def redraw_header(event=None):
            title_canvas.delete("all")
            w = title_canvas.winfo_width()
            _draw_horizontal_gradient(
                title_canvas, w, header_h,
                ["#F58529", "#DD2A7B", "#8134AF", "#515BD4"]  # IG-like gradient
            )
            title_canvas.create_text(
                w // 2, 34,
                text="Instagram Scraper - Edge",
                font=("Segoe UI", 22, "bold"),
                fill="white"
            )
            title_canvas.create_text(
                w // 2, 65,
                text="Bypasses Rate Limit with Microsoft Edge",
                font=("Segoe UI", 10),
                fill="#F2F2F2"
            )

        title_canvas.bind("<Configure>", redraw_header)

        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Login (REQUIRED)
        login_frame = tk.LabelFrame(
            main_frame,
            text=" Login (required) ",
            font=("Segoe UI", 10, "bold"),
            padx=12, pady=10
        )
        login_frame.pack(fill=tk.X, pady=(10, 10))

        login_user_frame = tk.Frame(login_frame)
        login_user_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(login_user_frame, text="Username:", font=("Arial", 10), width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.login_username_var = tk.StringVar()
        tk.Entry(login_user_frame, textvariable=self.login_username_var, font=("Arial", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        login_pass_frame = tk.Frame(login_frame)
        login_pass_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(login_pass_frame, text="Password:", font=("Arial", 10), width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.login_password_var = tk.StringVar()
        tk.Entry(login_pass_frame, textvariable=self.login_password_var, font=("Arial", 10), show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        tk.Label(login_frame, text="⚠ Instagram requires login to access profiles", font=("Arial", 9), fg="red").pack(anchor=tk.W)

        # Instagram profile
        url_label = tk.Label(main_frame, text="Instagram profile (URL or username):", font=("Arial", 11))
        url_label.pack(anchor=tk.W, pady=(0, 5))

        self.url_entry = ttk.Entry(main_frame, style="Modern.TEntry")
        self.url_entry.pack(fill=tk.X, pady=(0, 15))
        self.url_entry.insert(0, "https://www.instagram.com/")

        # Max posts
        max_frame = tk.Frame(main_frame)
        max_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(max_frame, text="Maximum posts:", font=("Arial", 11)).pack(side=tk.LEFT)
        self.max_posts_var = tk.StringVar(value="")
        tk.Entry(max_frame, textvariable=self.max_posts_var, font=("Arial", 12), width=15).pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(max_frame, text="(empty = all)", font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=(5, 0))

        # Delay
        delay_frame = tk.LabelFrame(main_frame, text="⏱ Delay between posts", font=("Arial", 10, "bold"), padx=10, pady=10)
        delay_frame.pack(fill=tk.X, pady=(0, 15))

        delay_controls = tk.Frame(delay_frame)
        delay_controls.pack(fill=tk.X)

        tk.Label(delay_controls, text="From:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.delay_min_var = tk.StringVar(value="3")
        tk.Entry(delay_controls, textvariable=self.delay_min_var, font=("Arial", 10), width=5).pack(side=tk.LEFT, padx=(5, 10))

        tk.Label(delay_controls, text="To:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.delay_max_var = tk.StringVar(value="6")
        tk.Entry(delay_controls, textvariable=self.delay_max_var, font=("Arial", 10), width=5).pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(delay_controls, text="seconds", font=("Arial", 10)).pack(side=tk.LEFT, padx=(5, 0))

        # Headless mode
        self.headless_var = tk.BooleanVar(value=False)
        headless_check = ttk.Checkbutton(
            main_frame,
            text="Headless mode (no visible browser)",
            variable=self.headless_var,
            style="Modern.TCheckbutton"
        )
        headless_check.pack(anchor=tk.W, pady=(0, 15))

        # Folder
        folder_frame = tk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(folder_frame, text="Folder:", font=("Arial", 11)).pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=self.download_folder)
        tk.Entry(folder_frame, textvariable=self.folder_var, font=("Arial", 10), width=30).pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(
            folder_frame,
            text="Browse",
            command=self.choose_folder,
            style="Modern.TButton"
        ).pack(side=tk.LEFT)

        # Download button
        self.download_btn = tk.Button(
            main_frame,
            text="🚀 Download Media",
            command=self.start_download,
            font=("Arial", 14, "bold"),
            bg="#405DE6",
            fg="white",
            activebackground="#5B51D8",
            activeforeground="white",
            cursor="hand2",
            height=2
        )
        self.download_btn.pack(fill=tk.X, pady=(0, 15))

        # Progress
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # Log
        log_label = tk.Label(main_frame, text="Log:", font=("Arial", 11))
        log_label.pack(anchor=tk.W, pady=(0, 5))

        log_frame = tk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame, font=("Consolas", 9), bg="#f5f5f5", fg="#333", yscrollcommand=scrollbar.set, height=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        self.log("✨ Edge Scraper ready! This method bypasses Instagram API rate limits.")
        self.log("💡 Uses Microsoft Edge - no ChromeDriver needed!")
        self.log("⚠ IMPORTANT: You must login to Instagram for this to work!")

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.folder_var.set(folder)
            self.download_folder = folder

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_download(self):
        """Starts download"""
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress!")
            return

        # Check login (REQUIRED)
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter Instagram username and password!\n\nInstagram requires login to access profiles.")
            return

        # Check profile
        url_or_username = self.url_entry.get().strip()
        if not url_or_username or url_or_username == "https://www.instagram.com/":
            messagebox.showerror("Error", "Please enter an Instagram profile!")
            return

        # Check max posts
        max_posts_str = self.max_posts_var.get().strip()
        max_posts = None
        if max_posts_str:
            try:
                max_posts = int(max_posts_str)
                if max_posts <= 0:
                    messagebox.showerror("Error", "Number must be positive!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid number!")
                return

        # Check delay
        try:
            delay_min = float(self.delay_min_var.get())
            delay_max = float(self.delay_max_var.get())

            if delay_min < 0 or delay_max < 0:
                messagebox.showerror("Error", "Delay must be positive!")
                return

            if delay_min > delay_max:
                messagebox.showerror("Error", "Minimum cannot be greater than maximum!")
                return

            delay_range = (delay_min, delay_max)
        except ValueError:
            messagebox.showerror("Error", "Invalid delay values!")
            return

        # 🔒 Fix #3: Sync folder_var with download_folder (manual edits in the text field)
        self.download_folder = self.folder_var.get().strip() or "downloads"

        # Start
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED, text="⏳ Downloading...")
        self.progress_bar.start(10)
        self.log_text.delete(1.0, tk.END)

        thread = threading.Thread(
            target=self.download_thread,
            args=(username, password, url_or_username, max_posts, delay_range),
            daemon=True
        )
        thread.start()

    def download_thread(self, username, password, url_or_username, max_posts, delay_range):
        """Download thread"""
        try:
            # Create scraper
            self.scraper = InstagramSeleniumScraper(
                download_folder=self.download_folder,
                progress_callback=self.log,
                headless=self.headless_var.get()
            )

            # Initialize browser
            self.scraper._init_driver()

            # Login (REQUIRED)
            login_success = False
            try:
                login_success = self.scraper.login(username, password)
            finally:
                # Fix #1-2: Clear credentials from memory immediately after login
                password = None  # noqa: F841
                username = None  # noqa: F841
                # Clear GUI password field after login attempt
                self.root.after(0, lambda: self.login_password_var.set(""))

            if not login_success:
                self.root.after(0, lambda: messagebox.showerror("Error", "Login failed!"))
                return

            # Download
            total_images, total_videos = self.scraper.download_profile_posts(url_or_username, max_posts, delay_range)
            total_count = total_images + total_videos

            if total_count > 0:
                parts = []
                if total_images > 0:
                    parts.append(f"{total_images} images")
                if total_videos > 0:
                    parts.append(f"{total_videos} videos")
                message = f"Downloaded {' и '.join(parts)}!"
                self.root.after(0, lambda: messagebox.showinfo("Success", message))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Info", "No media found."))

        except Exception as e:
            self.log(f"✗ Error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        finally:
            # Fix #9: Always close browser (even on login failure)
            if self.scraper:
                self.scraper.close()

            # Reset UI
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        """Resets UI"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL, text="🚀 Download Media")
        self.progress_bar.stop()


def resource_path(relative_path: str) -> str:
    # Работи и в dev, и в PyInstaller bundle
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def main():
    """Главна функция"""
    root = tk.Tk()

    try:
        root.iconbitmap(resource_path("icon.ico"))
    except Exception as e:
        print("Icon load failed:", e)

    app = SeleniumScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()



