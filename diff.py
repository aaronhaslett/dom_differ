import os
import json
import sys
from functools import partial
import time
import yaml
from datetime import datetime

from playwright._impl._api_types import Error as PlaywrightError
from playwright.sync_api import sync_playwright


if not len(sys.argv) == 2:
    print("Usage: {} HAR_CAPTURE_FILE".format(os.path.basename(__file__)))
    exit(1)

cap_fn = sys.argv[1]

url = ""
with open(cap_fn, "r") as f:
    cap = json.load(f)
    url = cap["log"]["entries"][0]["request"]["url"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    old_page = browser.new_page()
    old_page.route_from_har(cap_fn)
    old_page.goto(url)
    new_page = browser.new_page()
    new_page.goto(url)
    time.sleep(5)

    print(old_page.locator("body").evaluate("e => e.className"))
    print(new_page.locator("body").evaluate("e => e.className"))

    browser.close()
