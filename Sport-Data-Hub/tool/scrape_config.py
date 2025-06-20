import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.7 Mobile/15E148 Safari/537.36"
    "Mozilla/5.0 (Android 13; Mobile; rv:119.0) Gecko/119.0 Firefox/119.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
]

DELAY_RANGE = (2, 20)  # Randomized delay range in seconds

# Mimic common headers seen in real browser requests
HEADERS = {
    "Host": "www.sofascore.com",
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "*/*",
    "Accept-Language": random.choice(["en-US,en;q=0.5", "en-GB,en;q=0.9", "fr-FR,fr;q=0.9"]),
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": random.choice(["https://www.sofascore.com/football", "https://www.sofascore.com/"]),
    "X-Requested-With": "12456b",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "TE": "trailers"
}

QUEUE_SLOTS = 3

NUMOFPASTMATCHES = 10