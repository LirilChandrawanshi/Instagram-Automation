"""
Instagram automation actions: like, follow, comment, DM, upload.
Uses InstagramClient (Playwright), random delays, and scroll simulation.
"""
import re
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import get_settings, get_testing_mode
from app.models.instagram_account import InstagramAccount
from app.bot.instagram_client import InstagramClient, BASE_URL
from app.utils.random_delay import async_random_delay


class ActionBlockedError(RuntimeError):
    """Raised when Instagram shows action block / try again later."""

    pass


async def _action_delay() -> None:
    """Human-like delay between actions (config: 20-60s default). Short when testing mode."""
    if get_testing_mode():
        await async_random_delay(0, 2)
        return
    s = get_settings()
    min_s = getattr(s, "delay_between_actions_min_sec", 20)
    max_s = getattr(s, "delay_between_actions_max_sec", 60)
    await async_random_delay(min_s, max_s)


async def _check_action_block(page: Page) -> None:
    """Raise ActionBlockedError if page shows block message."""
    try:
        content = await page.content()
        if "Action blocked" in content or "Try again later" in content:
            raise ActionBlockedError("Action blocked by Instagram. Account paused for 24h.")
    except ActionBlockedError:
        raise
    except Exception:
        pass


async def _wait_optional(page: Page, selector: str, timeout: float = 5000) -> bool:
    """Wait for selector to appear; return True if found."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


async def like_post(account: InstagramAccount, post_url: str) -> None:
    """Open post URL and click like. Uses random delay and optional scroll."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(post_url, wait_until="domcontentloaded")
        await async_random_delay(1, 3)

        like_selectors = [
            'section span svg[aria-label="Like"]',
            'svg[aria-label="Like"]',
            'button span svg[aria-label="Like"]',
        ]
        clicked = False
        for sel in like_selectors:
            if await _wait_optional(client.page, sel, timeout=3000):
                el = await client.page.query_selector(sel)
                if el:
                    await el.click()
                    clicked = True
                    break
        if not clicked:
            raise RuntimeError("Like button not found; post may already be liked or selector changed")

        await _check_action_block(client.page)
        await _action_delay()


def _follow_button_variants(page: Page):
    """Yield (locator, is_follow_clickable) for Follow / Requested / Following."""
    # Exact role+name (primary)
    yield page.get_by_role("button", name="Follow"), True
    yield page.get_by_role("button", name="Requested"), False
    yield page.get_by_role("button", name="Following"), False
    # Regex for locale or extra text (e.g. "Seguir", "Follow back")
    yield page.get_by_role("button", name=re.compile(r"^Follow\b", re.I)), True
    yield page.get_by_role("button", name=re.compile(r"Requested", re.I)), False
    yield page.get_by_role("button", name=re.compile(r"Following", re.I)), False


async def follow_user(account: InstagramAccount, username: str) -> None:
    """Open profile and click Follow. Simulates scroll before action."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(f"{BASE_URL}/{username.strip()}/", wait_until="domcontentloaded")
        await async_random_delay(2, 4)

        # Wait for profile section (follow button or following state)
        for _ in range(8):
            follow_btn = client.page.get_by_role("button", name="Follow")
            following_btn = client.page.get_by_role("button", name="Following")
            if await follow_btn.count() > 0 or await following_btn.count() > 0:
                break
            await async_random_delay(0.8, 1.2)
        await client.scroll_down(150)
        await async_random_delay(0.5, 1)

        clicked = False
        for locator, should_click in _follow_button_variants(client.page):
            if await locator.count() > 0:
                if should_click:
                    await locator.first.click()
                    clicked = True
                break
        if not clicked and await client.page.get_by_role("button", name="Follow").count() == 0:
            following = client.page.get_by_role("button", name="Following")
            requested = client.page.get_by_role("button", name="Requested")
            if await following.count() == 0 and await requested.count() == 0:
                raise RuntimeError("Follow button not found; may already follow this user")

        await _check_action_block(client.page)
        await _action_delay()


async def comment_post(account: InstagramAccount, post_url: str, message: str) -> None:
    """Open post/reel and submit comment."""
    import logging
    log = logging.getLogger(__name__)

    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(post_url, wait_until="domcontentloaded")
        await async_random_delay(3, 5)

        # Wait for page to fully settle (Instagram loads dynamically)
        await client.page.wait_for_timeout(3000)

        # Step 1: Click the Comment icon to open / focus the comment area.
        # On reels this is essential — the input isn't visible until you click it.
        comment_icon_clicked = False
        comment_icon_selectors = [
            'svg[aria-label="Comment"]',
            '[aria-label="Comment"]',
            'svg[aria-label="Comment on this"]',
        ]
        for sel in comment_icon_selectors:
            try:
                el = await client.page.query_selector(sel)
                if el:
                    await el.click()
                    comment_icon_clicked = True
                    log.info("Clicked comment icon: %s", sel)
                    await async_random_delay(1, 2)
                    break
            except Exception:
                continue

        # Step 2: Also try clicking any "Add a comment…" placeholder text
        if not comment_icon_clicked:
            placeholder_locator = client.page.get_by_text(re.compile(r"Add a comment", re.I))
            if await placeholder_locator.count() > 0:
                await placeholder_locator.first.click()
                log.info("Clicked 'Add a comment' placeholder text")
                await async_random_delay(1, 2)

        # Step 3: Find the actual comment input element.
        # Instagram uses <input> for reels, <textarea> or contenteditable div for posts.
        comment_selectors = [
            'input[placeholder*="comment" i]',                       # reels use <input>
            'input[placeholder="Add a comment…"]',                   # reel exact match
            'input[placeholder="Add a comment..."]',
            'div[role="textbox"][contenteditable="true"]',           # modern contenteditable
            'div[aria-label="Add a comment…"][contenteditable]',     # aria-label variant
            'div[aria-label="Add a comment..."][contenteditable]',
            'form div[contenteditable="true"]',                      # inside form
            'textarea[placeholder="Add a comment…"]',                # legacy
            'textarea[placeholder="Add a comment..."]',
            'textarea[aria-label="Add a comment…"]',
            'textarea[aria-label="Add a comment..."]',
            "textarea[placeholder*='comment' i]",
            'div[contenteditable="true"]',                           # broadest fallback
        ]
        comment_el = None
        for sel in comment_selectors:
            if await _wait_optional(client.page, sel, timeout=2000):
                comment_el = await client.page.query_selector(sel)
                if comment_el:
                    log.info("Found comment input: %s", sel)
                    break

        # Last resort: use Playwright's get_by_placeholder
        if not comment_el:
            pl = client.page.get_by_placeholder(re.compile(r"comment", re.I))
            if await pl.count() > 0:
                comment_el = await pl.first.element_handle()
                log.info("Found comment input via get_by_placeholder")

        if not comment_el:
            # Debug: save screenshot and page info for troubleshooting
            debug_path = "/tmp/ig_comment_debug.png"
            html_path = "/tmp/ig_comment_debug.html"
            try:
                await client.page.screenshot(path=debug_path, full_page=False)
                html = await client.page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                log.error("Comment input not found. Screenshot: %s, HTML: %s, URL: %s",
                          debug_path, html_path, client.page.url)
            except Exception as e:
                log.error("Failed to save debug info: %s", e)
            raise RuntimeError(
                f"Comment input not found. Debug screenshot saved to {debug_path}"
            )

        # Step 4: Click to activate the input, then re-query.
        # Instagram's React swaps the placeholder <input> for a new active element
        # when clicked, so the original element handle becomes detached.
        try:
            await comment_el.click()
        except Exception:
            pass  # element may detach during click — that's expected
        await async_random_delay(0.5, 1)

        # Re-query for the now-active comment input (after React re-render)
        active_el = None
        active_selectors = [
            'input[placeholder*="comment" i]:focus',
            'input[placeholder*="comment" i]',
            'textarea:focus',
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="true"]:focus',
            'textarea[placeholder*="comment" i]',
        ]
        for sel in active_selectors:
            active_el = await client.page.query_selector(sel)
            if active_el:
                log.info("Re-queried active comment input: %s", sel)
                break

        # Fallback: try the Playwright locator (auto re-queries)
        if not active_el:
            pl = client.page.get_by_placeholder(re.compile(r"comment", re.I))
            if await pl.count() > 0:
                active_el = await pl.first.element_handle()
                log.info("Re-queried via get_by_placeholder")

        if not active_el:
            raise RuntimeError("Comment input lost after activation click")

        # Enter the text
        tag = await active_el.evaluate("el => el.tagName.toLowerCase()")
        if tag in ("input", "textarea"):
            await active_el.fill(message)
        else:
            await active_el.click()
            await client.page.keyboard.type(message, delay=50)
        await async_random_delay(0.5, 1)

        # Step 5: Submit — Click "Post" button (Enter doesn't submit on Instagram)
        post_btn = client.page.get_by_role("button", name=re.compile(r"^Post$", re.I))
        if await post_btn.count() > 0:
            await post_btn.first.click()
        else:
            # Fallback: try Enter key
            await client.page.keyboard.press("Enter")

        await async_random_delay(1, 2)
        await _check_action_block(client.page)
        await _action_delay()


async def view_story(account: InstagramAccount, username: str) -> None:
    """Open user profile and view their story (first available). Uses random delay."""
    import asyncio
    import random
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(f"{BASE_URL}/{username.strip()}/", wait_until="domcontentloaded")
        await async_random_delay(2, 4)

        # Story ring: clickable circle around profile pic (has gradient border when there's a story)
        story_ring_selectors = [
            'span[role="link"]',  # story link wrapper
            'a[href*="/stories/"]',
            'div[role="button"]',  # first might be story
        ]
        clicked = False
        for sel in story_ring_selectors:
            try:
                els = await client.page.query_selector_all(sel)
                for el in els[:3]:
                    box = await el.bounding_box()
                    if box and box.get("width", 0) > 40 and box.get("height", 0) > 40:
                        await el.click()
                        clicked = True
                        break
            except Exception:
                pass
            if clicked:
                break
        if not clicked:
            raise RuntimeError("Story not found; user may have no active story")

        await async_random_delay(1, 2)
        watch_sec = 3 if get_testing_mode() else random.randint(4, 8)
        await asyncio.sleep(watch_sec)

        # Close story (Escape or click outside)
        await client.page.keyboard.press("Escape")
        await async_random_delay(0.5, 1)
        await _check_action_block(client.page)
        await _action_delay()


async def view_reel(account: InstagramAccount, reel_url: str) -> None:
    """Open reel URL and let it play for several seconds to count as a view. Uses random delay."""
    import asyncio
    import random
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(reel_url, wait_until="domcontentloaded")
        await async_random_delay(2, 4)

        # Let the reel play long enough to count as a view (Instagram typically counts after ~3s)
        watch_sec = 5 if get_testing_mode() else random.randint(5, 9)
        await asyncio.sleep(watch_sec)

        await _check_action_block(client.page)
        await _action_delay()


async def send_dm(account: InstagramAccount, username: str, message: str) -> None:
    """Open Direct and send message to username."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(f"{BASE_URL}/direct/new/", wait_until="domcontentloaded")
        await async_random_delay(2, 4)

        search_selectors = [
            'input[placeholder="Search..."]',
            'input[aria-label="Search input"]',
        ]
        search_el = None
        for sel in search_selectors:
            if await _wait_optional(client.page, sel, timeout=5000):
                search_el = await client.page.query_selector(sel)
                if search_el:
                    break
        if not search_el:
            raise RuntimeError("DM search input not found")

        await search_el.fill(username.strip())
        await async_random_delay(1, 2)

        # First result row (user)
        user_row = client.page.locator('div[role="button"]').first
        if await user_row.count() == 0:
            raise RuntimeError("User not found in DM search")
        await user_row.click()
        await async_random_delay(0.5, 1)

        next_btn = client.page.get_by_role("button", name="Next")
        if await next_btn.count() > 0:
            await next_btn.first.click()
            await async_random_delay(0.5, 1)

        msg_selectors = [
            'textarea[placeholder="Message..."]',
            'textarea[aria-label="Message"]',
        ]
        msg_el = None
        for sel in msg_selectors:
            if await _wait_optional(client.page, sel, timeout=5000):
                msg_el = await client.page.query_selector(sel)
                if msg_el:
                    break
        if not msg_el:
            raise RuntimeError("Message input not found")
        await msg_el.fill(message)
        await client.page.keyboard.press("Enter")
        await _check_action_block(client.page)
        await _action_delay()


async def upload_post(account: InstagramAccount, image_path: str, caption: str) -> None:
    """Create new post: upload image and set caption."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        await async_random_delay(1, 2)

        # Create post: link to create or plus icon
        create_selectors = [
            'a[href="#"] span svg[aria-label="New post"]',
            'svg[aria-label="New post"]',
            'span[aria-label="New post"]',
        ]
        created = False
        for sel in create_selectors:
            if await _wait_optional(client.page, sel, timeout=3000):
                el = await client.page.query_selector(sel)
                if el:
                    await el.click()
                    created = True
                    break
        if not created:
            raise RuntimeError("New post button not found")

        await async_random_delay(1, 2)

        file_input = await client.page.query_selector('input[type="file"]')
        if not file_input:
            raise RuntimeError("File input not found")
        await file_input.set_input_files(image_path)
        await async_random_delay(1, 2)

        next_btn = client.page.get_by_role("button", name="Next")
        if await next_btn.count() > 0:
            await next_btn.first.click()
        await async_random_delay(0.5, 1)

        caption_selectors = [
            'textarea[placeholder="Write a caption..."]',
            'textarea[aria-label="Write a caption..."]',
        ]
        caption_el = None
        for sel in caption_selectors:
            if await _wait_optional(client.page, sel, timeout=5000):
                caption_el = await client.page.query_selector(sel)
                if caption_el:
                    break
        if caption_el:
            await caption_el.fill(caption)

        share_btn = client.page.get_by_role("button", name="Share")
        if await share_btn.count() > 0:
            await share_btn.first.click()
        await async_random_delay(2, 5)


async def upload_reel(account: InstagramAccount, video_path: str, caption: str) -> None:
    """Create new Reel: upload video and set caption."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await _action_delay()

        await client.page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        await async_random_delay(1, 2)

        create_selectors = [
            'svg[aria-label="New post"]',
            'span[aria-label="New post"]',
            'svg[aria-label="New reel"]',
        ]
        created = False
        for sel in create_selectors:
            if await _wait_optional(client.page, sel, timeout=3000):
                el = await client.page.query_selector(sel)
                if el:
                    await el.click()
                    created = True
                    break
        if not created:
            raise RuntimeError("New post/reel button not found")
        await async_random_delay(1, 2)

        reel_tab = client.page.get_by_text(re.compile(r"Reel", re.I))
        if await reel_tab.count() > 0:
            await reel_tab.first.click()
            await async_random_delay(0.5, 1)

        file_input = await client.page.query_selector('input[type="file"]')
        if not file_input:
            raise RuntimeError("File input not found")
        await file_input.set_input_files(video_path)
        await async_random_delay(2, 4)

        next_btn = client.page.get_by_role("button", name="Next")
        while await next_btn.count() > 0:
            await next_btn.first.click()
            await async_random_delay(0.5, 1)
            next_btn = client.page.get_by_role("button", name="Next")

        caption_el = None
        for sel in ['textarea[placeholder="Write a caption..."]', 'textarea[aria-label="Write a caption..."]']:
            if await _wait_optional(client.page, sel, timeout=5000):
                caption_el = await client.page.query_selector(sel)
                if caption_el:
                    break
        if caption_el:
            await caption_el.fill(caption or "")

        share_btn = client.page.get_by_role("button", name="Share")
        if await share_btn.count() > 0:
            await share_btn.first.click()
        await async_random_delay(3, 6)
        await _check_action_block(client.page)
        await _action_delay()
