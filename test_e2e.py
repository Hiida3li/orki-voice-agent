"""
End-to-end tests for Voice Agent using Playwright headless browser.
Tests all main pages and API endpoints.
"""

import asyncio
import sys
from playwright.async_api import async_playwright


BASE_URL = "https://localhost:8006"


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n=== Testing Health Endpoint ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        response = await page.goto(f"{BASE_URL}/health")
        assert response.status == 200, f"Health check failed with status {response.status}"

        content = await page.content()
        assert "healthy" in content, "Health check should return healthy status"
        print("  Health endpoint: OK")

        await browser.close()

    return True


async def test_business_context_page():
    """Test the business context page loads correctly."""
    print("\n=== Testing Business Context Page ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Test redirect from root to /business
        response = await page.goto(BASE_URL)
        await page.wait_for_load_state("networking")
        assert "/business" in page.url, f"Expected redirect to /business, got {page.url}"
        print("  Root redirect to /business: OK")

        # Check page elements
        title = await page.title()
        print(f"  Page title: {title}")

        # Check for key UI elements
        url_input = await page.query_selector('input[type="url"], input[placeholder*="website"], input[placeholder*="URL"]')
        assert url_input is not None, "URL input field not found"
        print("  URL input field: Found")

        # Check for submit button
        submit_btn = await page.query_selector('button')
        assert submit_btn is not None, "Submit button not found"
        print("  Submit button: Found")

        await browser.close()

    return True


async def test_enhanced_ui_page():
    """Test the enhanced UI page loads correctly."""
    print("\n=== Testing Enhanced UI Page ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        response = await page.goto(f"{BASE_URL}/enhanced")
        assert response.status == 200, f"Enhanced UI page failed with status {response.status}"
        print("  Enhanced UI page loads: OK")

        # Check for key UI elements
        title = await page.title()
        assert "AI Agent" in title, f"Expected 'AI Agent' in title, got {title}"
        print(f"  Page title: {title}")

        # Check for agent name input
        agent_name_input = await page.query_selector('#agentName')
        assert agent_name_input is not None, "Agent name input not found"
        print("  Agent name input: Found")

        # Check for personality chips
        personality_chips = await page.query_selector_all('#personalityChips .chip')
        assert len(personality_chips) >= 3, "Personality chips not found"
        print(f"  Personality chips: {len(personality_chips)} found")

        # Check for language chips
        language_chips = await page.query_selector_all('#languageChips .chip')
        assert len(language_chips) >= 2, "Language chips not found"
        print(f"  Language chips: {len(language_chips)} found")

        # Check for start session button
        start_btn = await page.query_selector('#startBtn')
        assert start_btn is not None, "Start session button not found"
        print("  Start session button: Found")

        # Check for create agent button
        create_btn = await page.query_selector('#createAgentBtn')
        assert create_btn is not None, "Create agent button not found"
        print("  Create agent button: Found")

        await browser.close()

    return True


async def test_enhanced_ui_interactions():
    """Test interactions on the enhanced UI page."""
    print("\n=== Testing Enhanced UI Interactions ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        await page.goto(f"{BASE_URL}/enhanced")
        await page.wait_for_load_state("networkidle")

        # Fill agent name
        await page.fill('#agentName', 'TestBot')
        print("  Filled agent name: TestBot")

        # Select gender
        gender_checkbox = await page.query_selector('#genderMale')
        if gender_checkbox:
            await gender_checkbox.click()
            print("  Selected gender: Male")

        # Click a personality chip
        personality_chip = await page.query_selector('#personalityChips .chip')
        if personality_chip:
            await personality_chip.click()
            print("  Selected first personality chip")

        # Click language chips
        english_chip = await page.query_selector('#languageChips .chip[data-value="English"]')
        if english_chip:
            await english_chip.click()
            print("  Selected English language")

        arabic_chip = await page.query_selector('#languageChips .chip[data-value="Arabic"]')
        if arabic_chip:
            await arabic_chip.click()
            print("  Selected Arabic language")

            # Check if dialect field appears
            await page.wait_for_timeout(500)
            dialect_field = await page.query_selector('#dialectField')
            if dialect_field:
                is_visible = await dialect_field.is_visible()
                assert is_visible, "Dialect field should be visible when Arabic is selected"
                print("  Arabic dialect field: Visible")

        # Add interaction steps
        add_step_btn = await page.query_selector('button.add-step-btn')
        if add_step_btn:
            await add_step_btn.click()
            await add_step_btn.click()
            steps = await page.query_selector_all('#stepsContainer .step-item')
            print(f"  Added {len(steps)} interaction steps")

        # Check JSON display updates
        json_display = await page.query_selector('#jsonDisplay')
        if json_display:
            json_content = await json_display.inner_text()
            assert 'TestBot' in json_content, "JSON should contain agent name"
            print("  JSON display updates correctly: OK")

        await browser.close()

    return True


async def test_api_endpoints():
    """Test API endpoints via the browser."""
    print("\n=== Testing API Endpoints ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Test health endpoint returns JSON
        response = await page.goto(f"{BASE_URL}/health")
        content = await page.content()
        assert "healthy" in content, "Health should be healthy"
        assert "active_sessions" in content, "Should include active_sessions"
        assert "tools_enabled" in content, "Should include tools_enabled"
        print("  Health API response: Valid JSON with expected fields")

        await browser.close()

    return True


async def run_all_tests():
    """Run all e2e tests."""
    print("=" * 60)
    print("  Voice Agent E2E Test Suite (Headless Browser)")
    print("=" * 60)

    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Business Context Page", test_business_context_page),
        ("Enhanced UI Page", test_enhanced_ui_page),
        ("Enhanced UI Interactions", test_enhanced_ui_interactions),
        ("API Endpoints", test_api_endpoints),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"  PASSED: {test_name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAILED: {test_name} - {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR: {test_name} - {e}")

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
