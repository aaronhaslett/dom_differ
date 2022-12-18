import os
import sys
import time
from datetime import datetime

from playwright._impl._api_types import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from constants import TIMESTAMP_FORMAT
from validate_url import string_is_url

if not len(sys.argv) in [2, 3]:
    print("Usage: {} URL [OUTPUT_PATH]".format(os.path.basename(__file__)))
    exit(1)

url = sys.argv[1]
if not string_is_url(url):
    print("ERROR: {} is not a url".format(url))
    exit(1)

output_filename = ""
if len(sys.argv) == 3:
    output_path = sys.argv[3]
else:
    output_path = "./{}.har".format(datetime.now().strftime(TIMESTAMP_FORMAT))

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(record_har_path=output_path)
    page = context.new_page()
    print("Capturing {}".format(url))
    page.goto(url)
    time.sleep(5)
    context.close()
    browser.close()
