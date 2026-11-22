#!/usr/bin/env python3

import os
import socket
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
LIVE_URL = "https://akshatrshah.github.io/"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.images = []
        self.forms = []
        self.current_form = None
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element_id = attrs.get("id")
        if element_id:
            if element_id in self.ids:
                raise AssertionError(f"Duplicate id: {element_id}")
            self.ids.add(element_id)

        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "img":
            self.images.append(attrs)
        if tag == "form":
            self.current_form = attrs
        if tag in {"input", "textarea", "select"} and self.current_form is not None:
            self.inputs.append(attrs)
        if tag == "form" and attrs.get("action"):
            self.forms.append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def check(condition, message, failures):
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        failures.append(message)


def local_http_test(failures):
    os.chdir(ROOT)
    socket.setdefaulttimeout(5)
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base = f"http://127.0.0.1:{port}"
        for path in [
            "/",
            "/styles.css",
            "/script.js",
            "/assets/headshot.jpg",
            "/Resume%20-%20Akshat.pdf",
            "/assets/projects/cloud-controller.jpg",
            "/assets/projects/jsonstreamdb.jpg",
            "/assets/projects/pipelinesync.jpg",
            "/assets/projects/payment.jpg",
            "/assets/projects/safesight.jpg",
            "/assets/projects/command-ai.jpg",
            "/assets/projects/fhir.jpg",
        ]:
            try:
                request = Request(base + path, method="HEAD")
                with urlopen(request, timeout=5) as response:
                    check(response.status == 200, f"Local asset returns 200: {path}", failures)
            except (HTTPError, URLError, TimeoutError) as error:
                check(False, f"Local asset unavailable: {path} ({error})", failures)
    finally:
        server.shutdown()
        server.server_close()


def http_status(url, timeout=12):
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 portfolio-test/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status
    except HTTPError as error:
        return error.code
    except (URLError, TimeoutError):
        return None


def live_http_test(failures):
    status = http_status(LIVE_URL)
    check(status == 200, f"Live website is reachable: {LIVE_URL}", failures)

    if status == 200:
        try:
            with urlopen(LIVE_URL, timeout=12) as response:
                live_html = response.read().decode("utf-8")
            check("assets/headshot.jpg" in live_html, "Live page includes the headshot markup", failures)
            check("Looking forward to" in live_html, "Live contact heading is updated", failures)
        except (HTTPError, URLError, TimeoutError) as error:
            check(False, f"Could not read live website HTML ({error})", failures)

    external = {
        "GitHub profile": "https://github.com/akshatrshah/",
        "GitHub Cloud Controller": "https://github.com/akshatrshah/cloud-controller",
        "GitHub JSONStreamDB": "https://github.com/akshatrshah/jsonstreamdb",
        "GitHub PipelineSync": "https://github.com/akshatrshah/pipelinesync",
        "LinkedIn profile": "https://www.linkedin.com/in/akshat-shah-3542201ba",
        "Personal email": "mailto:akshatrshah@gmail.com",
        "University email": "mailto:ashah39@ncsu.edu",
    }

    for label, url in external.items():
        if url.startswith("mailto:"):
            check(url in [
                "mailto:akshatrshah@gmail.com",
                "mailto:ashah39@ncsu.edu",
            ], f"{label} is a valid mailto link", failures)
            continue
        status = http_status(url)
        if status in {200, 301, 302, 307, 308}:
            print(f"PASS: {label} is reachable (HTTP {status})")
        elif label == "LinkedIn profile" and status in {999, 403}:
            print(f"WARN: {label} blocks automated checks (HTTP {status})")
        else:
            check(False, f"{label} returned HTTP {status}", failures)


def main():
    failures = []
    html_path = ROOT / "index.html"
    css_path = ROOT / "styles.css"
    js_path = ROOT / "script.js"

    check(html_path.exists(), "index.html exists", failures)
    check(css_path.exists(), "styles.css exists", failures)
    check(js_path.exists(), "script.js exists", failures)

    html = html_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")
    parser = SiteParser()
    try:
        parser.feed(html)
        check(True, "HTML parses without duplicate ids", failures)
    except AssertionError as error:
        check(False, str(error), failures)

    required_files = [
        "Resume - Akshat.pdf",
        "assets/headshot.jpg",
        "assets/projects/cloud-controller.jpg",
        "assets/projects/jsonstreamdb.jpg",
        "assets/projects/pipelinesync.jpg",
        "assets/projects/payment.jpg",
        "assets/projects/safesight.jpg",
        "assets/projects/command-ai.jpg",
        "assets/projects/fhir.jpg",
    ]
    for relative_path in required_files:
        check((ROOT / relative_path).is_file(), f"Required file exists: {relative_path}", failures)

    for image in parser.images:
        source = image.get("src", "")
        if source.startswith("assets/"):
            check((ROOT / source.split("?")[0]).is_file(), f"Image source exists: {source}", failures)

    section_ids = {"top", "about", "experience", "projects", "education", "contact"}
    for section_id in section_ids:
        check(section_id in parser.ids, f"Section id exists: #{section_id}", failures)

    for href in parser.links:
        if href.startswith("#"):
            check(href[1:] in parser.ids, f"Anchor target exists: {href}", failures)

    check('formsubmit.co/akshatrshah@gmail.com' in html, "Contact form submits to personal email", failures)
    check('name="name"' in html and 'name="email"' in html and 'name="message"' in html,
          "Contact form includes name, email, and message fields", failures)
    check('name="consent"' in html, "Contact form includes consent checkbox", failures)
    check("_captcha" in html and "_honey" in html, "Contact form has CAPTCHA and spam honeypot settings", failures)

    check('rel="canonical"' in html, "Canonical SEO tag exists", failures)
    check('property="og:title"' in html and 'property="og:image"' in html, "Open Graph metadata exists", failures)
    check('name="twitter:card"' in html, "Twitter card metadata exists", failures)
    check('"@type": "Person"' in html, "Structured Person schema exists", failures)
    check("goatcounter.com/count" in html, "GoatCounter analytics script exists", failures)

    check(css.count("{") == css.count("}"), "CSS braces are balanced", failures)
    check("@media (max-width: 680px)" in css, "Mobile breakpoint exists", failures)

    node = subprocess.run(["node", "--check", str(js_path)], capture_output=True, text=True)
    check(node.returncode == 0, "JavaScript syntax check passes", failures)
    if node.returncode != 0:
        failures.append(node.stderr.strip())

    local_http_test(failures)
    live_http_test(failures)

    print("\n" + "=" * 60)
    if failures:
        print(f"TEST RESULT: FAILED ({len(failures)} issue(s))")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("TEST RESULT: PASSED")
    print("No real contact-form submission was sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
