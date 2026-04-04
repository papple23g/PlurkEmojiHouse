import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    target_url = f"{base_url.rstrip('/')}/PlurkEmojiHouse"

    with sync_playwright() as p:
        # Record a video so we can review real interactions.
        artifacts_dir = Path("artifacts/e2e")
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        browser = p.chromium.launch()
        context = browser.new_context(
            record_video_dir=str(artifacts_dir),
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        # Capture console + page errors to detect Brython/JS failures.
        console_lines: list[str] = []
        page_errors: list[str] = []

        def on_console(msg):
            try:
                console_lines.append(f"{msg.type}: {msg.text}")
            except Exception:
                console_lines.append("console: <unreadable>")

        def on_page_error(exc):
            page_errors.append(str(exc))

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        page.goto(target_url, wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        page.screenshot(path=str(artifacts_dir / "01_loaded.png"), full_page=True)

        # Wait for Brython app to remove loading message (done in PlurkEmojiPage.py).
        page.wait_for_timeout(500)
        try:
            page.wait_for_selector("#loading_webpage_msg", state="detached", timeout=20000)
        except Exception:
            # If still present, keep going but report in output.
            pass
        page.screenshot(path=str(artifacts_dir / "02_brython_ready.png"), full_page=True)

        # Ensure main UI elements exist.
        page.wait_for_selector("#button_bar_add_emoji", timeout=20000)
        page.wait_for_selector("#button_bar_search_emoji", timeout=20000)

        # ---- Browse flow: "show all" triggers initial results already, but click again.
        page.click("#show_all_emoji_btn")
        page.wait_for_timeout(800)
        browse_ok = False
        try:
            # Either table view, block view, or a "no results" message should appear.
            page.wait_for_selector(
                "#emoji_result_table table, #div_emojiReslutBlock, #emoji_result_table p",
                timeout=20000,
            )
            browse_ok = True
        except Exception:
            browse_ok = False
        page.screenshot(path=str(artifacts_dir / "03_browse.png"), full_page=True)

        # ---- Add flow: switch to add tab and submit a known emoji URL.
        page.click("#button_bar_add_emoji")
        page.wait_for_timeout(500)
        page.screenshot(path=str(artifacts_dir / "04_add_tab.png"), full_page=True)

        # The add page defaults to "公開噗文網址"; switch to "表符圖片網址" so the URL input is visible.
        page.select_option("#select_adding_emoji_method", label="表符圖片網址")
        page.wait_for_timeout(200)

        sample_url = (
            "https://emos.plurk.com/2658f2e2cffb4e9d6b72d4a6374597f9_w48_h48.jpeg"
        )
        page.fill("#input_input_emoji_url_to_add_emoji_elt", sample_url)
        page.screenshot(path=str(artifacts_dir / "05_add_filled.png"), full_page=True)
        page.click("#button_send_to_add_emoji")

        add_ok = False
        try:
            # New emoji result should render a table into the adding area.
            page.wait_for_selector("#div_show_adding_emoji_result_table_area table", timeout=30000)
            add_ok = True
        except Exception:
            add_ok = False
        page.wait_for_timeout(300)
        page.screenshot(path=str(artifacts_dir / "06_add_result.png"), full_page=True)

        context.close()
        browser.close()

    # Heuristics for errors: any pageerror is a failure; console "Error" also suspicious.
    # Filter out known-benign console noise (3rd-party integrations, browser policy warnings).
    ignore_console_patterns = [
        r"Permissions-Policy header",
        r"\[PostHog\.js\]",
        r"Failed to load resource: the server responded with a status of 403",
        r"\bstatus:\s*403\b",
        r"\bForbidden\b",
    ]
    ignore_re = re.compile("|".join(ignore_console_patterns), flags=re.I) if ignore_console_patterns else None
    errorish_console = []
    for line in console_lines:
        if ignore_re and ignore_re.search(line):
            continue
        if re.search(r"\b(error|exception|traceback)\b", line, flags=re.I):
            errorish_console.append(line)

    print("E2E Brython smoke")
    print(f"- url: {target_url}")
    print(f"- artifacts_dir: {artifacts_dir.resolve()}")
    print(f"- browse_ok: {browse_ok}")
    print(f"- add_ok: {add_ok}")
    print(f"- page_errors: {len(page_errors)}")
    print(f"- suspicious_console: {len(errorish_console)}")

    if page_errors:
        print("\nPage errors:")
        for e in page_errors[:20]:
            print(f"- {e}")

    if errorish_console:
        print("\nSuspicious console:")
        for l in errorish_console[:40]:
            print(f"- {l}")

    if not browse_ok or not add_ok or page_errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

