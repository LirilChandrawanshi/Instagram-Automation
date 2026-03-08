"""
Instagram automation actions: like, follow, comment, DM, upload.
Uses InstagramClient (Playwright), random delays, and scroll simulation.
"""
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.models.instagram_account import InstagramAccount
from app.bot.instagram_client import InstagramClient, BASE_URL
from app.utils.random_delay import async_random_delay


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
        await async_random_delay(2, 5)

        await client.page.goto(post_url, wait_until="domcontentloaded")
        await async_random_delay(1, 3)

        # Like: aria-label "Like" on SVG, or button containing it
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

        await async_random_delay(2, 5)


async def follow_user(account: InstagramAccount, username: str) -> None:
    """Open profile and click Follow. Simulates scroll before action."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await async_random_delay(2, 5)

        await client.page.goto(f"{BASE_URL}/{username.strip()}/", wait_until="domcontentloaded")
        await async_random_delay(1, 3)

        # Optional scroll to load profile
        await client.scroll_down(150)
        await async_random_delay(0.5, 1)

        follow_btn = client.page.get_by_role("button", name="Follow")
        if await follow_btn.count() > 0:
            await follow_btn.first.click()
        else:
            # "Requested" or "Following" = no-op, not an error
            requested = client.page.get_by_role("button", name="Requested")
            following = client.page.get_by_role("button", name="Following")
            if await requested.count() == 0 and await following.count() == 0:
                raise RuntimeError("Follow button not found; may already follow this user")

        await async_random_delay(2, 5)


async def comment_post(account: InstagramAccount, post_url: str, message: str) -> None:
    """Open post and submit comment."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await async_random_delay(2, 5)

        await client.page.goto(post_url, wait_until="domcontentloaded")
        await async_random_delay(1, 3)

        comment_selectors = [
            'textarea[placeholder="Add a comment..."]',
            'textarea[aria-label="Add a comment..."]',
            "textarea[placeholder*='comment']",
        ]
        comment_el = None
        for sel in comment_selectors:
            if await _wait_optional(client.page, sel, timeout=3000):
                comment_el = await client.page.query_selector(sel)
                if comment_el:
                    break
        if not comment_el:
            raise RuntimeError("Comment input not found")

        await comment_el.fill(message)
        await async_random_delay(0.5, 1)
        await client.page.keyboard.press("Enter")
        await async_random_delay(2, 5)


async def send_dm(account: InstagramAccount, username: str, message: str) -> None:
    """Open Direct and send message to username."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await async_random_delay(2, 5)

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
        await async_random_delay(2, 5)


async def upload_post(account: InstagramAccount, image_path: str, caption: str) -> None:
    """Create new post: upload image and set caption."""
    async with InstagramClient(account) as client:
        if not await client.ensure_logged_in():
            raise RuntimeError("Not logged in to Instagram")
        await async_random_delay(2, 5)

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
