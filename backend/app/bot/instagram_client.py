"""
Playwright-based Instagram web client.
Provides InstagramClient context manager, browser/context lifecycle, and session restore.
"""
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from app.bot.device_fingerprint import get_device_profile
from app.config import get_settings
from app.models.instagram_account import InstagramAccount

settings = get_settings()
BASE_URL = "https://www.instagram.com"
DEFAULT_TIMEOUT_MS = 90_000  # 1 min 30 sec


_SAME_SITE_MAP = {
    "no_restriction": "None",
    "none": "None",
    "lax": "Lax",
    "strict": "Strict",
}


def _normalize_cookie(c: Dict[str, Any]) -> Dict[str, Any]:
    """Convert browser-extension cookie to Playwright-compatible format.

    Handles field renames (expirationDate → expires), sameSite value mapping
    (no_restriction → None), and strips unknown fields that Playwright rejects.
    """
    out: Dict[str, Any] = {"name": c.get("name"), "value": str(c.get("value", ""))}

    if c.get("domain"):
        out["domain"] = c["domain"]
    if c.get("path"):
        out["path"] = c["path"]

    # expires / expirationDate
    exp = c.get("expirationDate") or c.get("expires")
    if exp is not None:
        out["expires"] = int(float(exp))

    # httpOnly & secure
    if "httpOnly" in c:
        out["httpOnly"] = bool(c["httpOnly"])
    if "secure" in c:
        out["secure"] = bool(c["secure"])

    # sameSite: Cookie-Editor uses "no_restriction", Playwright needs "None"
    raw_ss = c.get("sameSite")
    if raw_ss and isinstance(raw_ss, str):
        out["sameSite"] = _SAME_SITE_MAP.get(raw_ss.lower(), "Lax")
    # If sameSite is None/null, omit it — Playwright will use default

    return out


def _parse_cookies(session_cookie: Optional[str]) -> List[Dict[str, Any]]:
    """Parse session_cookie (JSON array of cookie dicts) for add_cookies."""
    if not session_cookie or not session_cookie.strip():
        return []
    try:
        data = json.loads(session_cookie)
        if isinstance(data, list):
            return [_normalize_cookie(c) for c in data if c.get("name") and c.get("value") is not None]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


async def _restore_session(context: BrowserContext, account: InstagramAccount) -> None:
    """Restore session from account.session_cookie (JSON cookies or storage state JSON)."""
    raw = account.session_cookie
    if not raw or not raw.strip():
        return
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return

    # Storage state: { "cookies": [...], "origins": [...] } from context.storage_state()
    if isinstance(data, dict) and "cookies" in data:
        raw_cookies = data.get("cookies", [])
        normalized = [_normalize_cookie(c) for c in raw_cookies if isinstance(c, dict) and c.get("name") and c.get("value") is not None]
        if normalized:
            await context.add_cookies(normalized)
        return

    if isinstance(data, list):
        normalized = [_normalize_cookie(c) for c in data if isinstance(c, dict) and c.get("name") and c.get("value") is not None]
        if normalized:
            await context.add_cookies(normalized)
        return


async def get_context(
    account: InstagramAccount,
    browser: Browser,
) -> BrowserContext:
    """Create a browser context with device profile, optional proxy, and session restore."""
    profile = account.device_profile or get_device_profile()
    viewport = profile.get("viewport", {"width": 1920, "height": 1080})
    user_agent = profile.get("user_agent") or get_device_profile()["user_agent"]
    locale = profile.get("locale", "en-US")

    opts: dict[str, Any] = {
        "viewport": viewport,
        "user_agent": user_agent,
        "locale": locale,
        "ignore_https_errors": True,
    }

    proxy = getattr(account, "proxy", None)
    if account.proxy_id and proxy:
        opts["proxy"] = {
            "server": f"http://{proxy.ip}:{proxy.port}",
            "username": proxy.username or None,
            "password": proxy.password or None,
        }

    context = await browser.new_context(**opts)
    context.set_default_timeout(DEFAULT_TIMEOUT_MS)
    await _restore_session(context, account)
    return context


async def ensure_logged_in(page: Page, account: InstagramAccount) -> bool:
    """Navigate to Instagram and return True if logged in. Waits for redirect/cookies then checks."""
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    # Instagram often shows login first then redirects after cookies; wait longer for that
    await page.wait_for_timeout(7000)
    url = page.url or ""
    # Clear sign: still on login page = not logged in
    if "accounts/login" in url or "accounts/login/" in url:
        return False
    # Positive checks for logged-in (any one is enough)
    if await page.locator('nav a[href="/"]').count() > 0:
        return True
    if await page.locator('a[href="/"]').count() > 0:
        return True
    if await page.get_by_role("link", name="Home").count() > 0:
        return True
    # Home icon (aria-label)
    if await page.locator('a[aria-label="Home"], a[aria-label="Home (current tab)"]').count() > 0:
        return True
    # Login form present = not logged in
    login_input = await page.query_selector('input[name="username"]')
    if login_input:
        return False
    # Not on login URL and no login form = treat as logged in (feed/challenge/different UI)
    return True


async def scroll_page(page: Page, direction: str = "down", amount: Optional[int] = None) -> None:
    """Simulate human scroll. direction: 'down' or 'up'. amount: pixels or random if None."""
    import random
    if amount is None:
        amount = random.randint(200, 600)
    if direction == "up":
        amount = -amount
    await page.mouse.wheel(0, amount)
    await page.wait_for_timeout(random.randint(300, 800))


class InstagramClient:
    """
    Playwright Instagram automation client. Use as async context manager.
    Handles browser launch, context (device + proxy + session), and optional scroll simulation.
    """

    def __init__(self, account: InstagramAccount, headless: Optional[bool] = None):
        self.account = account
        self._headless = headless if headless is not None else settings.playwright_headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self) -> "InstagramClient":
        self._playwright = await async_playwright().start()
        browser_type = getattr(self._playwright, settings.playwright_browser, self._playwright.chromium)
        launch_opts = {"headless": self._headless}
        if settings.playwright_browser == "chromium":
            launch_opts["args"] = ["--disable-blink-features=AutomationControlled"]
        self._browser = await browser_type.launch(**launch_opts)
        self._context = await get_context(self.account, self._browser)
        self._page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("InstagramClient not started; use async with InstagramClient(...)")
        return self._page

    async def ensure_logged_in(self) -> bool:
        """Return True if session is logged in."""
        return await ensure_logged_in(self.page, self.account)

    async def scroll_down(self, amount: Optional[int] = None) -> None:
        """Human-like scroll down."""
        await scroll_page(self.page, "down", amount)

    async def scroll_up(self, amount: Optional[int] = None) -> None:
        """Human-like scroll up."""
        await scroll_page(self.page, "up", amount)

    async def save_storage_state(self) -> Dict[str, Any]:
        """Capture current context storage state (cookies + localStorage) for session persistence."""
        if not self._context:
            raise RuntimeError("InstagramClient not started")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            await self._context.storage_state(path=path)
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
