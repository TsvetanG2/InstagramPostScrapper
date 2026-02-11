# Instagram Scraper

A simple tool for downloading photos from Instagram profiles using Selenium with Microsoft Edge.

## Method: Selenium + Edge (recommended)

**File:** `scraper_selenium.py`

### Prerequisites
- Python 3.10+
- Microsoft Edge installed
- On Linux, you may need the `python3-tk` package for the GUI (tkinter is not always included by default).

### Advantages
- Bypasses common Instagram rate limits more reliably than API-based approaches
- Harder to detect than simple HTTP scraping (uses a real browser)
- Can keep working even after temporary 429/rate-limit blocks
- You can see what the browser is doing (or run headless)
- Uses Microsoft Edge (no ChromeDriver required if Edge WebDriver is available on your system)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run:

```bash
python scraper_selenium.py
```

## Usage notes
- Instagram changes often. If something breaks, update Selenium/Edge and retry.
- If you want headless mode, enable it in the script (search for `headless` options).

## Disclaimer
Use responsibly and comply with Instagram's Terms of Service and applicable laws.

## Pyinstaller installation for .exe file
```bash
python -m PyInstaller --onedir --windowed --name "InstagramScrapper" --icon "icon.ico" --version-file "version_info.txt" --add-data "icon.ico;." --collect-all selenium --hidden-import selenium.webdriver --hidden-import selenium.webdriver.common --hidden-import selenium.webdriver.support scraper_selenium.py
```
