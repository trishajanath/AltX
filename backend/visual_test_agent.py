"""
AI Visual Testing Agent - Autonomous Application Testing

Uses SYNC Playwright API in thread pool for Windows compatibility.
"""

import asyncio
import base64
import json
import os
import time
import re
import concurrent.futures
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

# Try to import Playwright SYNC API for Windows compatibility
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not installed. Run: pip install playwright && playwright install chromium")


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class TestStep:
    step_number: int
    action: str
    description: str
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    status: TestStatus = TestStatus.SKIPPED
    ai_observation: str = ""
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class TestCase:
    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)
    status: TestStatus = TestStatus.SKIPPED
    total_duration_ms: int = 0


@dataclass
class TestReport:
    app_name: str
    app_url: str
    test_started_at: str
    test_completed_at: str
    total_duration_seconds: float
    test_cases: List[TestCase] = field(default_factory=list)
    overall_status: TestStatus = TestStatus.SKIPPED
    ai_summary: str = ""
    issues_found: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    screenshots: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_name": self.app_name,
            "app_url": self.app_url,
            "test_started_at": self.test_started_at,
            "test_completed_at": self.test_completed_at,
            "total_duration_seconds": self.total_duration_seconds,
            "overall_status": self.overall_status.value,
            "ai_summary": self.ai_summary,
            "issues_found": self.issues_found,
            "suggestions": self.suggestions,
            "recommendations": self.suggestions,
            "ai_observations": self.ai_summary,
            "test_results": [
                {
                    "name": tc.name,
                    "description": tc.description,
                    "passed": tc.status == TestStatus.PASSED,
                    "status": tc.status.value,
                    "total_duration_ms": tc.total_duration_ms,
                    "error": next((s.error for s in tc.steps if s.error), None),
                    "steps": [
                        {
                            "step_number": s.step_number,
                            "action": s.action,
                            "description": s.description,
                            "success": s.status == TestStatus.PASSED,
                            "status": s.status.value,
                            "details": s.ai_observation,
                            "error": s.error,
                            "duration_ms": s.duration_ms
                        }
                        for s in tc.steps
                    ]
                }
                for tc in self.test_cases
            ],
            "total_test_cases": len(self.test_cases),
            "passed": sum(1 for tc in self.test_cases if tc.status == TestStatus.PASSED),
            "failed": sum(1 for tc in self.test_cases if tc.status == TestStatus.FAILED),
            "warnings": sum(1 for tc in self.test_cases if tc.status == TestStatus.WARNING),
            "total_duration": f"{self.total_duration_seconds:.1f}s"
        }


class SyncVisualTestAgent:
    """Synchronous visual testing agent using Playwright sync API."""
    
    def __init__(self, preview_url: str, app_name: str = "Generated App"):
        self.preview_url = preview_url
        self.app_name = app_name
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots: List[Dict[str, str]] = []
        self.console_logs: List[str] = []
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        self.vision_model = genai.GenerativeModel("gemini-2.0-flash")
        
        self.safety_settings = [
            {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
        ]
        
        print(f"🤖 Visual Test Agent initialized for: {preview_url}")
    
    def start_browser(self) -> None:
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=2
        )
        self.page = self.context.new_page()
        self.page.on("console", lambda msg: self.console_logs.append(f"[{msg.type}] {msg.text}"))
        self.page.on("pageerror", lambda err: self.console_logs.append(f"[ERROR] {err}"))
        print("🌐 Browser started")
    
    def close_browser(self) -> None:
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        print("🌐 Browser closed")
    
    def take_screenshot(self, name: str = "screenshot") -> str:
        if not self.page:
            raise RuntimeError("Browser not started")
        screenshot_bytes = self.page.screenshot(full_page=False)
        base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
        self.screenshots.append({"name": name, "timestamp": datetime.now().isoformat(), "base64": base64_image})
        return base64_image
    
    def analyze_screenshot(self, screenshot_base64: str, context: str = "") -> Dict[str, Any]:
        prompt = f"""Analyze this web app screenshot as a QA tester.
{f'Context: {context}' if context else ''}

Return JSON:
{{"page_type": "type", "visible_elements": [{{"type": "button/link/input", "text": "text", "clickable": true}}], "suggested_actions": [{{"action": "click/type/verify", "target": "element"}}], "observations": ["notes"], "potential_issues": ["issues"], "overall_quality": "good/acceptable/needs_work"}}"""

        try:
            response = self.vision_model.generate_content(
                contents=[{"mime_type": "image/png", "data": screenshot_base64}, prompt],
                generation_config={"temperature": 0.2, "max_output_tokens": 4096, "response_mime_type": "application/json"},
                safety_settings=self.safety_settings
            )
            if response.candidates and response.candidates[0].content.parts:
                result_text = response.candidates[0].content.parts[0].text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                return json.loads(result_text.strip())
            return {"error": "No response"}
        except Exception as e:
            return {"error": str(e), "visible_elements": [], "suggested_actions": []}
    
    def navigate_to(self, url: str, timeout: int = 30000) -> bool:
        if not self.page:
            return False
        try:
            self.page.goto(url, timeout=timeout, wait_until="networkidle")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"⚠️ Navigation failed: {e}")
            return False
    
    def click_element(self, selector: str, timeout: int = 5000) -> bool:
        if not self.page:
            return False
        try:
            self.page.click(selector, timeout=timeout)
            time.sleep(0.5)
            return True
        except:
            return False
    
    def type_text(self, selector: str, text: str) -> bool:
        if not self.page:
            return False
        try:
            self.page.fill(selector, text)
            return True
        except:
            return False
    
    def scroll_page(self, direction: str = "down", amount: int = 300) -> bool:
        if not self.page:
            return False
        try:
            self.page.evaluate(f"window.scrollBy(0, {amount if direction == 'down' else -amount})")
            time.sleep(0.3)
            return True
        except:
            return False
    
    def find_element_by_ai(self, description: str) -> Optional[str]:
        if not self.page:
            return None
        try:
            html = self.page.content()[:20000]
            prompt = f'Find CSS selector for: "{description}"\nHTML:\n{html[:10000]}\n\nReturn ONLY a CSS selector or "NOT_FOUND".'
            response = self.vision_model.generate_content(prompt, generation_config={"temperature": 0.1, "max_output_tokens": 100}, safety_settings=self.safety_settings)
            if response.candidates:
                selector = response.candidates[0].content.parts[0].text.strip().strip('"\'`')
                if selector and selector != "NOT_FOUND" and self.page.query_selector(selector):
                    return selector
        except:
            pass
        return None
    
    def generate_test_plan(self, screenshot: str) -> List[TestCase]:
        print("🤖 AI generating test plan...")
        prompt = """Analyze this screenshot and create test cases.

Return JSON array:
[{"name": "Test Name", "description": "What it tests", "steps": [{"action": "click|type|scroll|verify|wait", "description": "what to do"}]}]

Generate 3-4 practical test cases."""

        try:
            response = self.vision_model.generate_content(
                contents=[{"mime_type": "image/png", "data": screenshot}, prompt],
                generation_config={"temperature": 0.3, "max_output_tokens": 4096, "response_mime_type": "application/json"},
                safety_settings=self.safety_settings
            )
            if response.candidates:
                result = response.candidates[0].content.parts[0].text
                if "```" in result:
                    result = result.split("```")[1].split("```")[0]
                    if result.startswith("json"):
                        result = result[4:]
                test_data = json.loads(result.strip())
                test_cases = []
                for tc in test_data:
                    steps = [TestStep(i+1, s.get("action", "verify"), s.get("description", "")) for i, s in enumerate(tc.get("steps", []))]
                    test_cases.append(TestCase(tc.get("name", "Test"), tc.get("description", ""), steps))
                print(f"📋 Generated {len(test_cases)} test cases")
                return test_cases
        except Exception as e:
            print(f"⚠️ Test plan error: {e}")
        
        return [TestCase("Page Load", "Verify page loads", [TestStep(1, "verify", "Check page loads"), TestStep(2, "scroll", "scroll down")])]
    
    def run_test_case(self, test_case: TestCase) -> TestCase:
        print(f"\n🧪 Test: {test_case.name}")
        start = time.time()
        all_passed = True
        
        for step in test_case.steps:
            step_start = time.time()
            print(f"  Step {step.step_number}: {step.description}")
            
            try:
                step.screenshot_before = self.take_screenshot(f"{test_case.name}_s{step.step_number}_before")
                success = False
                
                if step.action == "click":
                    selector = self.find_element_by_ai(step.description)
                    if selector:
                        success = self.click_element(selector)
                    else:
                        for sel in [f"text={step.description}", f"button:has-text('{step.description}')", f"a:has-text('{step.description}')"]:
                            try:
                                if self.page.query_selector(sel):
                                    success = self.click_element(sel)
                                    if success:
                                        break
                            except:
                                continue
                
                elif step.action == "type":
                    match = re.match(r"type ['\"](.+?)['\"] into ['\"](.+?)['\"]", step.description, re.I)
                    if match:
                        text, field = match.groups()
                        selector = self.find_element_by_ai(field)
                        if selector:
                            success = self.type_text(selector, text)
                
                elif step.action == "scroll":
                    success = self.scroll_page("down" if "down" in step.description.lower() else "up")
                
                elif step.action == "verify":
                    screenshot = self.take_screenshot(f"{test_case.name}_s{step.step_number}_verify")
                    analysis = self.analyze_screenshot(screenshot, step.description)
                    step.ai_observation = str(analysis.get("observations", []))[:300]
                    success = "error" not in analysis
                
                elif step.action == "wait":
                    time.sleep(2)
                    success = True
                else:
                    step.error = f"Unknown action: {step.action}"
                
                step.screenshot_after = self.take_screenshot(f"{test_case.name}_s{step.step_number}_after")
                
                if success:
                    analysis = self.analyze_screenshot(step.screenshot_after)
                    step.ai_observation = str(analysis.get("observations", []))[:300]
                    step.status = TestStatus.WARNING if analysis.get("potential_issues") else TestStatus.PASSED
                else:
                    step.status = TestStatus.FAILED
                    all_passed = False
                    if not step.error:
                        step.error = "Action failed"
                        
            except Exception as e:
                step.status = TestStatus.FAILED
                step.error = str(e)
                all_passed = False
            
            step.duration_ms = int((time.time() - step_start) * 1000)
            icon = "✅" if step.status == TestStatus.PASSED else "⚠️" if step.status == TestStatus.WARNING else "❌"
            print(f"    {icon} {step.status.value}")
        
        test_case.total_duration_ms = int((time.time() - start) * 1000)
        test_case.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
        return test_case
    
    def generate_summary(self, test_cases: List[TestCase]) -> Tuple[str, List[str], List[str]]:
        results = [f"- {tc.name}: {tc.status.value}" for tc in test_cases]
        for tc in test_cases:
            for s in tc.steps:
                if s.status != TestStatus.PASSED:
                    results.append(f"  - Step {s.step_number}: {s.status.value} - {s.error or ''}")
        
        errors = [l for l in self.console_logs if "ERROR" in l.upper()]
        prompt = f"""Summarize test results:\n{chr(10).join(results)}\nErrors: {chr(10).join(errors[:5]) if errors else 'None'}\n\nReturn JSON: {{"summary": "summary", "issues_found": ["issues"], "suggestions": ["fixes"]}}"""

        try:
            response = self.vision_model.generate_content(prompt, generation_config={"temperature": 0.2, "max_output_tokens": 1024, "response_mime_type": "application/json"}, safety_settings=self.safety_settings)
            if response.candidates:
                data = json.loads(response.candidates[0].content.parts[0].text)
                return data.get("summary", ""), data.get("issues_found", []), data.get("suggestions", [])
        except:
            pass
        passed = sum(1 for tc in test_cases if tc.status == TestStatus.PASSED)
        return f"Completed {passed}/{len(test_cases)} tests.", [], []
    
    def run_full_test(self, custom_tests: List[TestCase] = None) -> TestReport:
        start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"🤖 AI VISUAL TEST AGENT")
        print(f"📱 App: {self.app_name}")
        print(f"🌐 URL: {self.preview_url}")
        print(f"{'='*60}\n")
        
        report = TestReport(app_name=self.app_name, app_url=self.preview_url, test_started_at=start_time.isoformat(), test_completed_at="", total_duration_seconds=0)
        
        try:
            self.start_browser()
            print(f"🌐 Loading: {self.preview_url}")
            if not self.navigate_to(self.preview_url):
                raise RuntimeError("Failed to load app")
            
            time.sleep(2)
            initial_ss = self.take_screenshot("initial")
            print("\n🔍 Analyzing page...")
            analysis = self.analyze_screenshot(initial_ss)
            print(f"   Type: {analysis.get('page_type', 'Unknown')}")
            print(f"   Quality: {analysis.get('overall_quality', 'Unknown')}")
            
            test_cases = custom_tests or self.generate_test_plan(initial_ss)
            print(f"\n🏃 Running {len(test_cases)} tests...\n")
            
            for tc in test_cases:
                report.test_cases.append(self.run_test_case(tc))
                self.navigate_to(self.preview_url)
                time.sleep(0.5)
            
            summary, issues, suggestions = self.generate_summary(report.test_cases)
            report.ai_summary = summary
            report.issues_found = issues
            report.suggestions = suggestions
            
            passed = sum(1 for tc in report.test_cases if tc.status == TestStatus.PASSED)
            failed = sum(1 for tc in report.test_cases if tc.status == TestStatus.FAILED)
            report.overall_status = TestStatus.PASSED if failed == 0 else TestStatus.WARNING if passed > failed else TestStatus.FAILED
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            report.issues_found.append(f"Error: {str(e)}")
            report.overall_status = TestStatus.FAILED
        finally:
            self.close_browser()
        
        end_time = datetime.now()
        report.test_completed_at = end_time.isoformat()
        report.total_duration_seconds = (end_time - start_time).total_seconds()
        report.screenshots = self.screenshots
        
        print(f"\n{'='*60}")
        print(f"📊 RESULTS: {report.overall_status.value.upper()}")
        passed = sum(1 for tc in report.test_cases if tc.status == TestStatus.PASSED)
        failed = sum(1 for tc in report.test_cases if tc.status == TestStatus.FAILED)
        print(f"Tests: {passed}✅ {failed}❌ | Duration: {report.total_duration_seconds:.1f}s")
        if report.ai_summary:
            print(f"Summary: {report.ai_summary}")
        print(f"{'='*60}\n")
        
        return report


# Thread pool for running sync Playwright on Windows
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _run_test_sync(preview_url: str, app_name: str, custom_tests: List[TestCase] = None) -> TestReport:
    agent = SyncVisualTestAgent(preview_url, app_name)
    return agent.run_full_test(custom_tests)


async def run_visual_test(preview_url: str, app_name: str = "Generated App", custom_tests: List[TestCase] = None) -> TestReport:
    """Run visual test asynchronously using thread pool - works on Windows."""
    loop = asyncio.get_event_loop()
    report = await loop.run_in_executor(_executor, _run_test_sync, preview_url, app_name, custom_tests)
    return report


# Backwards compatibility wrapper
class VisualTestAgent:
    def __init__(self, preview_url: str, app_name: str = "Generated App"):
        self.preview_url = preview_url
        self.app_name = app_name
    
    async def run_full_test(self, custom_test_cases: List[TestCase] = None) -> TestReport:
        return await run_visual_test(self.preview_url, self.app_name, custom_test_cases)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visual_test_agent.py <url> [app_name]")
        sys.exit(1)
    report = asyncio.run(run_visual_test(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "Test"))
    print(json.dumps(report.to_dict(), indent=2))
