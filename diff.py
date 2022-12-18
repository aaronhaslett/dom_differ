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

script = """e => {
  const styles = {...window.getComputedStyle(e)};
  const parentStyles = {...window.getComputedStyle(e.parentElement)};
  Object.keys(parentStyles).forEach(k => {
    if (styles[k] == parentStyles[k]) delete styles[k];
  });
  return styles;
} """

def iterate_locator(locator):
    for i in range(locator.count()):
        el = locator.nth(i)
        tagname = el.evaluate("e => e.tagName") 
        if tagname.lower() not in ["style", "script", "meta"]:
            yield el

def details(path, old_element, new_element):
    old_styles = old_element.evaluate(script)
    new_styles = new_element.evaluate(script)
    diff = {k:(v,new_styles[k]) for (k,v) in old_styles.items() if v!=new_styles[k]}
    out = []
    old_tag = old_element.evaluate("e => `<${e.tagName.toLowerCase()} class='${e.className}'>`")
    new_tag = new_element.evaluate("e => `<${e.tagName.toLowerCase()} class='${e.className}'>`")
    new_path = path + " => " + new_tag
    if diff:
        out.append({
            "path": new_path,
            "old_tag": old_tag,
            "new_tag": new_tag,
            "diff": diff,
        })

    old_children = list(iterate_locator(old_element.locator("xpath=*")))
    new_children = list(iterate_locator(new_element.locator("xpath=*")))
    print("path:{}  children:{}".format(new_path, [e.evaluate("e=>e.tagName") for e in old_children]))
    if len(old_children) != len(new_children):
        print("DOM structure changes don't work yet, path=" + new_path)
        exit(1)

    for old_sub_element, new_sub_element in zip(old_children, new_children):
        out += details(new_path, old_sub_element, new_sub_element)

    return out

with sync_playwright() as p:
    browser = p.chromium.launch()
    old_page = browser.new_page()
    old_page.route_from_har(cap_fn)
    old_page.goto(url)
    new_page = browser.new_page()
    new_page.goto(url)
    time.sleep(5)

    results = {
        "head": details("head", old_page.locator("head"), new_page.locator("head")),
        "body": details("body", old_page.locator("body"), new_page.locator("body"))
    }

    with open("results.json", "w") as f:
        f.write(json.dumps(results))

    browser.close()
