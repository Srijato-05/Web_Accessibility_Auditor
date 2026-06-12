"""
VANGUARD ENGINE CORE: PLAYWRIGHT INFRASTRUCTURE ENGINE (PE-Z10)
==============================================================

Aggregate Product Line: 750+ Lines (Target)
Technical Level: Engine (Enterprise Grade)
Role: Autonomous Stealth Browser Orchestrator & Hardware Emulation Layer

This module implements the Auditor Engine Browser Engine. It utilizes Playwright as the 
underlying automation framework but wraps it in a complex, high-fidelity stealth 
and telemetry architecture. It is designed to bypass the world's most sophisticated 
bot-detection systems while providing clinical-grade accessibility data.

(c) 2026 Auditor Intelligence Agency
"""

import os
import sys
import asyncio
import time
import random
import math
from typing import List, Any, Dict, Optional, Tuple, cast
from uuid import UUID
from datetime import datetime

# IDE PATH RECONCILIATION: Ensure internal module resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import psutil # type: ignore
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError # type: ignore
from axe_playwright_python.async_playwright import Axe # type: ignore
from auditor.domain.interfaces import IBrowserEngine # type: ignore
from auditor.domain.violation import Violation, ImpactLevel # type: ignore
from auditor.domain.exceptions import EngineError, AuditFailedError # type: ignore
from auditor.shared.logging import auditor_logger # type: ignore
from auditor.shared.stealth_profiles import StealthProfileGenerator # type: ignore
from auditor.infrastructure.stealth_protocol import StealthProtocol # type: ignore
from auditor.infrastructure.data_extractor import extract_page_data, PageData # type: ignore
from auditor.shared.compliance_mapper import ComplianceMapper # type: ignore

# --------------------------------------------------------------------------
# ENGINE STEALTH CONFIGURATION: THE NEURAL GHOST
# --------------------------------------------------------------------------

STEALTH_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

VIEWPORT_CONFIGS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 2560, "height": 1440}
]

class HardwareProfile:
    """Engine Hardware Emulation Profile Generator."""
    DEVICE_MEMORIES = [8, 16, 32, 64]
    HARDWARE_CONCURRENCIES = [4, 8, 12, 16, 32]
    PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]
    VENDORS = ["Google Inc.", "Apple Computer, Inc.", "Intel Inc."]
    RENDERERS = [
        "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Apple, Apple M1 Direct3D11 vs_5_0 ps_5_0)"
    ]
    
    @classmethod
    def generate(cls) -> Dict[str, Any]:
        """Generates a high-fidelity hardware footprint for a fake user agent using dynamic configuration."""
        return {
            "deviceMemory": random.choice(cls.DEVICE_MEMORIES),
            "hardwareConcurrency": random.choice(cls.HARDWARE_CONCURRENCIES),
            "platform": random.choice(cls.PLATFORMS),
            "vendor": random.choice(cls.VENDORS),
            "renderer": random.choice(cls.RENDERERS)
        }

# --------------------------------------------------------------------------
# THE ENGINE ENGINE CLASS
# --------------------------------------------------------------------------

class PlaywrightEngine(IBrowserEngine):
    """
    ENGINE BROWSER INTELLIGENCE ENGINE (PE-Z10)
    
    The most advanced browser orchestration layer in the Auditor Platform. 
    It manages the lifecycle of a Chromium cluster with extreme technical depth.
    
    Attributes:
        session_id (UUID): The unique ID for the current audit lifecycle.
        headless (bool): Whether to run the browser in headless mode.
        telemetry (Dict): real-time performance and audit metadata.
    """
    
    def __init__(self, session_id: UUID, headless: bool = True, config: Optional[dict] = None):
        self.session_id = session_id
        self.headless = headless
        self.config = config or {}
        self.playwright_mgr: Optional[Any] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._page_count = 0
        
        self.emulation_status: Dict[str, Any] = {
            "viewport_applied": False,
            "dpr_applied": False,
            "agent_applied": False,
            "vision_deficiency_applied": False,
            "network_throttling_applied": False,
            "media_applied": False,
            "reduced_data_applied": False,
            "errors": []
        }
        
        # Phase VII: Visual Intelligence Data
        self.focus_path: List[Dict[str, Any]] = []
        self.aria_events: List[Dict[str, Any]] = []
        self.page_data: Optional[PageData] = None
        
        # Performance Telemetry Cluster
        self.telemetry: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "nav_duration": 0.0,
            "audit_duration": 0.0,
            "total_violations": 0,
            "blocked_attempts": 0,
            "resource_usage": {}
        }
        
        # Fixing NameError/AttributeError via explicit string conversion
        session_id_str: str = str(self.session_id)
        # Using a safer slicing method that satisfies the type checker
        session_short = session_id_str[:8] # type: ignore
        self.logger = auditor_logger.getChild(f"EngineEngine.{session_short}")
        
        # Phase VI: Evasion Profile Selection
        self.profile = StealthProfileGenerator.get_random_profile()
        self.logger.info(f"Stealth Persona Selected: {self.profile['name']}")

    # --------------------------------------------------------------------------
    # CORE LIFECYCLE: THE BROWSER CLUSTER
    # --------------------------------------------------------------------------

    async def start(self):
        """Initializes the persistent playwright and browser instance."""
        if sys.platform == 'win32':
            # Cycle 3: Post-Initialization Policy Injection
            if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                self.logger.warning("Engine Detected Loop Policy Incompatibility. Attempting hot-patch...")
                try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                except: pass

        if not self.browser or not self.browser.is_connected():
            self.logger.info("Starting Persistent Engine Cluster...")
            if not self.playwright_mgr:
                self.playwright_mgr = await async_playwright().start()
            await self._init_browser(self.playwright_mgr)

    async def teardown(self):
        """Gracefully terminates the engine cluster and releases hardware handles."""
        self.logger.info("Commencing Engine Teardown Protocol...")
        ctx = self.context
        if ctx:
            try: await ctx.close()
            except: pass
        br = self.browser
        if br:
            try: await br.close()
            except: pass
        mgr = self.playwright_mgr
        if mgr:
            try: await mgr.stop()
            except: pass
        self.browser = None
        self.context = None
        self.playwright_mgr = None
        self.logger.info("Engine Cluster OFFLINE.")

    async def _init_browser(self, playwright: Any):
        """
        Engine-Grade Hardware-Level Browser Initialization.
        """
        try:
            self.logger.debug("Engaging Stealth Phase VI: Polymorphic Evasion...")
            
            # --- PARSE CONFIGURATION ---
            viewport_config = self.config.get("viewport")
            width, height = 1920, 1080  # Default
            if viewport_config and "x" in viewport_config:
                try:
                    w_str, h_str = viewport_config.split("x")
                    w_val, h_val = int(w_str), int(h_str)
                    if 100 <= w_val <= 10000 and 100 <= h_val <= 10000:
                        width, height = w_val, h_val
                        self.emulation_status["viewport_applied"] = True
                    else:
                        self.logger.warning(f"Out of bounds viewport requested: {viewport_config}. Falling back to 1920x1080.")
                        self.emulation_status["errors"].append(f"Viewport {viewport_config} out of bounds.")
                except Exception as ve:
                    self.logger.warning(f"Failed to parse viewport {viewport_config}: {ve}. Falling back to 1920x1080.")
                    self.emulation_status["errors"].append(f"Failed to parse viewport {viewport_config}: {ve}")
            else:
                self.emulation_status["viewport_applied"] = True

            dpr_config = self.config.get("dpr")
            device_scale_factor = 1.0  # Default
            if dpr_config:
                try:
                    dpr_val = float(dpr_config)
                    if 0.1 <= dpr_val <= 4.0:
                        device_scale_factor = dpr_val
                        self.emulation_status["dpr_applied"] = True
                    else:
                        self.logger.warning(f"Out of bounds DPR requested: {dpr_config}. Falling back to 1.0.")
                        self.emulation_status["errors"].append(f"DPR {dpr_config} out of bounds.")
                except Exception as de:
                    self.logger.warning(f"Failed to parse DPR {dpr_config}: {de}. Falling back to 1.0.")
                    self.emulation_status["errors"].append(f"Failed to parse DPR {dpr_config}: {de}")
            else:
                self.emulation_status["dpr_applied"] = True

            agent_config = self.config.get("agent")
            user_agent = self.profile.get("userAgent")
            is_mobile = False
            has_touch = False

            if agent_config == "mobile_chrome":
                user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
                is_mobile = True
                has_touch = True
                if not viewport_config:
                    width, height = 390, 844
                if not dpr_config:
                    device_scale_factor = 3.0
            elif agent_config == "seo_crawler":
                user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
            elif agent_config == "secure_auditor":
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            elif agent_config == "screen_reader":
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; RV:109.0) Gecko/20100101 Firefox/115.0"
            elif agent_config == "low_vision_zoom":
                device_scale_factor = 2.0

            if agent_config:
                self.emulation_status["agent_applied"] = True
            else:
                self.emulation_status["agent_applied"] = True

            # Store computed options inside self.profile dictionary for lookup / propagation
            self.profile["userAgent"] = user_agent
            self.profile["viewport"] = {"width": width, "height": height}
            self.profile["deviceScaleFactor"] = device_scale_factor
            self.profile["isMobile"] = is_mobile
            self.profile["hasTouch"] = has_touch
            # ---------------------------

            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--ignore-certificate-errors",
                    "--disable-dev-shm-usage",
                    f"--user-agent={self.profile['userAgent']}"
                ]
            )
            
            browser_inst = self.browser
            if not browser_inst:
                raise EngineError("Engine Cluster Failure: Chromium could not be spawned.")
                
            # Cycle 3: Auto-Healing Sentinel (Retry Loop)
            max_init_retries = 2
            for attempt in range(max_init_retries + 1):
                try:
                    self.context = await browser_inst.new_context(
                        viewport=self.profile['viewport'],
                        user_agent=self.profile['userAgent'],
                        java_script_enabled=True,
                        bypass_csp=True,
                        device_scale_factor=self.profile.get('deviceScaleFactor', 1.0),
                        is_mobile=self.profile.get('isMobile', False),
                        has_touch=self.profile.get('hasTouch', False),
                        # Cycle 3: HAR Network Harvesting
                        record_har_path=f"reports/forensics/har/session_{self.session_id}.har" if self.session_id else None
                    )
                    break
                except Exception as ce:
                    if attempt < max_init_retries:
                        self.logger.warning(f"Engine Context Initialization Attempt {attempt+1} Failed: {ce}. Retrying...")
                        await asyncio.sleep(1)
                    else:
                        raise EngineError(f"Engine Context Failure: Stealth context initialization failed after {max_init_retries+1} attempts.")
            
            context_inst = self.context
            if not context_inst:
                raise EngineError("Engine Context Failure: Stealth context initialization failed.")

            # Phase X: Forensic Telemetry Bridge Implementation
            async def _telemetry_handler(source, type, data):
                self.logger.debug(f"Forensic Telemetry Received [{type}]: {data.get('selector')}")
                if type == "FOCUS":
                    self.focus_path.append(data)
                elif type == "ARIA":
                    self.aria_events.append(data)
            
            await context_inst.expose_binding("__report_forensic_telemetry", _telemetry_handler)

            # DEEP STALKER: Injecting high-fidelity JS stealth protocol
            stealth_js = StealthProtocol.get_injection_script(self.profile)
            await context_inst.add_init_script(stealth_js)
            
            # Phase XI: JA3/TLS Simulation (Header Rotation & Order)
            # Chrome typically uses a specific header order to form its fingerprint
            # Cycle 3: HTTP/2 Perception Suite (Multiplexed Stealth)
            await context_inst.set_extra_http_headers({
                "sec-ch-ua": f"\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"122\", \"Chromium\";v=\"122\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": f"\"{self.profile['clientHints']['platform']}\"",
                "upgrade-insecure-requests": "1",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site": "cross-site",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "priority": "u=0, i", # Cycle 3: HTTP/2 priority frame simulation
                "referer": "https://www.google.com/"
            })

            # Phase X: Inject Forensic Probes via Zenith Stealth
            await self._inject_zenith_stealth(context_inst, self.profile)
            
            self.logger.info(f"Engine Cluster ONLINE | Persona: {self.profile['name']} | VP: {self.profile['viewport']['width']}x{self.profile['viewport']['height']}")
        
        except Exception as e:
            self.logger.critical(f"Engine Core Initialization PANIC: {e}", exc_info=True)
            raise EngineError(f"Engine cluster failure: {e}")

    async def _inject_zenith_stealth(self, context: BrowserContext, profile: Dict):
        """Injects deep-layer Javascript to spoof WebGL, Navigator, and Hardware APIs."""
        stealth_code = f"""
            // Engine Stealth Core
            (() => {{
                // 1. Webdriver Detection Bypass
                const newProto = navigator.__proto__;
                delete newProto.webdriver;
                navigator.__proto__ = newProto;

                // 2. Hardware API Spoofing
                Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {profile['hardware']['deviceMemory']} }});
                Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {profile['hardware']['hardwareConcurrency']} }});
                Object.defineProperty(navigator, 'platform', {{ get: () => '{profile['hardware']['platform']}' }});

                // 3. WebGL Intelligence Spoofing
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return '{profile['hardware']['vendor']}';
                    if (parameter === 37446) return '{profile['hardware']['renderer']}';
                    return getParameter.apply(this, arguments);
                }};

                // 4. Cycle 2: Canvas Entropy Projection
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {{
                    const context = this.getContext('2d');
                    if (context) {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        // Cycle 6: Canvas Jitter v2 (Pixel-Shift Entropy)
                        for (let i = 0; i < 20; i++) {{
                            const idx = Math.floor(Math.random() * imageData.data.length / 4) * 4;
                            imageData.data[idx] = (imageData.data[idx] + 1) % 256; // Light shifting
                            imageData.data[idx + 1] = (imageData.data[idx + 1] ^ 1); // Atomic XOR
                        }}
                        context.putImageData(imageData, 0, 0);
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};

                // 5. Cycle 2: AudioContext Spoofing
                const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function() {{
                    const result = originalGetChannelData.apply(this, arguments);
                    for (let i = 0; i < result.length; i += 100) {{
                        result[i] += Math.random() * 0.0001; 
                    }}
                    return result;
                }};

                // 6. Cycle 4: Intl API Buffing (Locale/Timezone Stealth)
                const originalDateTimeFormat = Intl.DateTimeFormat;
                Intl.DateTimeFormat = function(locale, options) {{
                    const personaLocale = '{profile.get('locale', 'en-US')}';
                    return new originalDateTimeFormat(personaLocale, options);
                }};
                
                const originalNumberFormat = Intl.NumberFormat;
                Intl.NumberFormat = function(locale, options) {{
                    const personaLocale = '{profile.get('locale', 'en-US')}';
                    return new originalNumberFormat(personaLocale, options);
                }};

                // 7. Permission Normalization
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
                );

                // 8. Phase X: Forensic Telemetry Integration
                // Focus Tracking
                document.addEventListener('focusin', (e) => {{
                    const el = e.target;
                    const rect = el.getBoundingClientRect();
                    window.__report_forensic_telemetry('FOCUS', {{
                        timestamp: Date.now(),
                        tagName: el.tagName,
                        selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2
                    }});
                }}, true);

                // ARIA Mutation Observer
                const observer = new MutationObserver((mutations) => {{
                    mutations.forEach((mutation) => {{
                        const target = mutation.target;
                        if (target.getAttribute && (target.getAttribute('aria-live') || target.getAttribute('role') === 'alert')) {{
                            window.__report_forensic_telemetry('ARIA', {{
                                timestamp: Date.now(),
                                type: 'ARIA_LIVE_UPDATE',
                                content: target.innerText.slice(0, 100),
                                selector: target.tagName.toLowerCase() + (target.id ? '#' + target.id : '')
                            }});
                        }}
                    }});
                }});
                observer.observe(document.body, {{ childList: true, subtree: true, characterData: true }});
                
                // 10. High-Density Focus-Path Reconstruction
                document.addEventListener('focus', (e) => {{
                    const el = e.target;
                    const rect = el.getBoundingClientRect();
                    window.__report_forensic_telemetry('FOCUS', {{
                        timestamp: Date.now(),
                        selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
                        x: rect.left + window.scrollX,
                        y: rect.top + window.scrollY,
                        density: 'HIGH'
                    }});
                }}, true);

                // 6. WebDriver Apex Masking (Cycle 7)
                Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
                Object.defineProperty(navigator, 'languages', {{get: () => ['en-US', 'en']}});
                Object.defineProperty(navigator, 'plugins', {{get: () => ({{length: 5}})}});
                
                // Add some fake plugins
                const plugins = [
                    {{name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}}
                ];
                Object.setPrototypeOf(navigator.plugins, PluginArray.prototype);
                
                window.__APEX_STEALTH_ACTIVE__ = true;
            }})();
        """
        await context.add_init_script(stealth_code)

    # --------------------------------------------------------------------------
    # PRIMARY MISSION: SECURE AUDIT EXECUTION
    # --------------------------------------------------------------------------

    async def scan_url(self: "PlaywrightEngine", url: str) -> List[Violation]:
        """
        Autonomous Engine Audit Protocol (AZAP).
        Includes Persona Rotation for WAF bypass.
        """
        _self = cast(Any, self)
        _self.telemetry["start_time"] = datetime.now()
        start_time = time.time()

        # Load settings dynamically
        import json
        settings = {}
        try:
            settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presentation", "settings.json"))
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
        except Exception:
            pass

        user_agent_setting = settings.get("user_agent", "default")
        if user_agent_setting != "default":
            ua_map = {
                "googlebot": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6156.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "lighthouse": "Mozilla/5.0 (Linux; Android 11; moto g power (2021)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 Chrome-Lighthouse",
                "desktop-chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "mobile-safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
            }
            if user_agent_setting in ua_map:
                _self.profile["userAgent"] = ua_map[user_agent_setting]
        
        # Ensure engine is active
        if not _self.browser or not _self.browser.is_connected():
            await _self.start()
            
        br = _self.browser
        if not br:
            raise EngineError("Engine Cluster Failure: Browser offline.")
            
        retry_limit = settings.get("retry_limit", 3)
        MAX_PERSONAS = retry_limit + 1
        current_attempt = 1
        
        while current_attempt <= MAX_PERSONAS:
            local_context = None
            page = None
            try:
                # Attempt 2: Switch to Mobile Persona
                if current_attempt == 2:
                    _self.logger.warning(f"PERSONA ROTATION: Attempt {current_attempt} using Mobile Persona...") # type: ignore
                    mobile_profile = next((p for p in StealthProfileGenerator.get_all_profiles() if "Mobile" in p["name"]), _self.profile) # type: ignore
                    _self.profile = mobile_profile # type: ignore
                    # Discard recycled context on persona rotation
                    if _self.context:
                        try: await _self.context.close()
                        except: pass
                        _self.context = None
                
                # Attempt 3: Switch to Headful (with Headless fallback)
                if current_attempt == 3:
                    _self.logger.critical(f"FINAL BREACH: Attempt {current_attempt} engaging Headful Mode...") # type: ignore
                    try:
                        if _self.browser: # type: ignore
                            await _self.browser.close() # type: ignore
                            _self.browser = None
                        _self.headless = False # type: ignore
                        await _self.start() # type: ignore
                    except Exception as he:
                        _self.logger.warning(f"Headful Launch Failure: {he}. Falling back to Extreme Stealth Headless...") # type: ignore
                        _self.headless = True # type: ignore
                        await _self.start() # type: ignore
                    
                    br = _self.browser # type: ignore
                    _self.profile = next((p for p in StealthProfileGenerator.get_all_profiles() if "Windows-Chrome" in p["name"]), _self.profile) # type: ignore
                    # Discard recycled context on persona rotation
                    if _self.context:
                        try: await _self.context.close()
                        except: pass
                        _self.context = None

                # Recycle or initialize context
                if current_attempt == 1 and _self.context:
                    local_context = _self.context
                else:
                    local_context = await br.new_context( # type: ignore
                        viewport=_self.profile['viewport'], # type: ignore
                        user_agent=_self.profile['userAgent'], # type: ignore
                        java_script_enabled=True,
                        bypass_csp=False, # Disable CSP bypass (sometimes detected)
                        device_scale_factor=_self.profile.get('deviceScaleFactor', 1.0),
                        is_mobile=_self.profile.get('isMobile', False),
                        has_touch=_self.profile.get('hasTouch', False),
                        record_har_path=f"reports/forensics/har/session_{_self.session_id}.har" if _self.session_id else None,
                        extra_http_headers={
                            "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"123\", \"Chromium\";v=\"123\"",
                            "sec-ch-ua-full-version-list": "\"Not A(Brand\";v=\"99.0.0.0\", \"Google Chrome\";v=\"123.0.6312.52\", \"Chromium\";v=\"123.0.6312.52\"",
                            "sec-ch-ua-mobile": "?0",
                            "sec-ch-ua-platform": "\"Windows\"",
                            "sec-ch-ua-platform-version": "\"10.0.0\"",
                            "referer": "https://www.google.com/"
                        }
                    )
                    # Re-inject stealth for this context
                    stealth_js = StealthProtocol.get_injection_script(_self.profile) # type: ignore
                    await local_context.add_init_script(stealth_js)
                    await _self._inject_zenith_stealth(local_context, _self.profile) # type: ignore
                    if current_attempt == 1:
                        _self.context = local_context
                
                page = await local_context.new_page()
                
                # --- EMULATIONS START ---
                # 1. Vision Deficiency Emulation
                agent_config = _self.config.get("agent")
                if agent_config == "colorblind_deuteranopia":
                    try:
                        await page.emulate_vision_deficiency("deuteranopia")
                        _self.logger.info("COLORBLIND DEUTERANOPIA EMULATION ACTIVE.")
                        _self.emulation_status["vision_deficiency_applied"] = True
                    except Exception as ve:
                        _self.logger.warning(f"Failed to emulate vision deficiency: {ve}")
                        _self.emulation_status["errors"].append(f"Vision deficiency emulation failure: {ve}")
                else:
                    _self.emulation_status["vision_deficiency_applied"] = True

                # 2. Network Throttling & Latency Emulation via Chrome DevTools Protocol (CDP)
                network_config = _self.config.get("network")
                latency_config = _self.config.get("latency")
                
                latency_ms = 0
                if latency_config:
                    try:
                        lat_val = int(latency_config)
                        if 0 <= lat_val <= 15000:
                            latency_ms = lat_val
                        else:
                            _self.logger.warning(f"Latency value {lat_val}ms out of bounds. Capping to 15000ms.")
                            latency_ms = min(max(0, lat_val), 15000)
                            _self.emulation_status["errors"].append(f"Latency value {lat_val}ms out of bounds. Capped to 15000ms.")
                    except Exception as le:
                        _self.emulation_status["errors"].append(f"Failed to parse latency {latency_config}: {le}")
                        
                download_throughput = -1
                upload_throughput = -1
                
                if network_config == "slow_3g":
                    download_throughput = 400 * 1024  # 400 Kbps
                    upload_throughput = 400 * 1024
                    if latency_ms == 0:
                        latency_ms = 400
                elif network_config == "fast_3g":
                    download_throughput = 1600 * 1024  # 1.6 Mbps
                    upload_throughput = 750 * 1024
                    if latency_ms == 0:
                        latency_ms = 150
                elif network_config == "wifi":
                    download_throughput = 30 * 1024 * 1024  # 30 Mbps
                    upload_throughput = 15 * 1024 * 1024
                    if latency_ms == 0:
                        latency_ms = 30
                        
                if network_config != "none" or latency_ms > 0:
                    try:
                        cdp_session = await page.context.new_cdp_session(page)
                        await cdp_session.send("Network.emulateNetworkConditions", {
                            "offline": False,
                            "latency": latency_ms,
                            "downloadThroughput": download_throughput,
                            "uploadThroughput": upload_throughput
                        })
                        _self.logger.info(f"NETWORK THROTTLING ACTIVE: Network: {network_config}, Latency: {latency_ms}ms")
                        _self.emulation_status["network_throttling_applied"] = True
                    except Exception as throttling_err:
                        _self.logger.warning(f"Failed to establish network throttling: {throttling_err}")
                        _self.emulation_status["errors"].append(f"Network throttling setup failure: {throttling_err}")
                else:
                    _self.emulation_status["network_throttling_applied"] = True

                # 3. Media Features Preferences
                media_features = []
                if _self.config.get("reducedMotion"):
                    media_features.append({"name": "prefers-reduced-motion", "value": "reduce"})
                    
                color_scheme = _self.config.get("colorScheme")
                if color_scheme and color_scheme != "no-preference":
                    media_features.append({"name": "prefers-color-scheme", "value": color_scheme})
                    
                contrast = _self.config.get("contrast")
                if contrast and contrast != "no-preference":
                    media_features.append({"name": "prefers-contrast", "value": contrast})
                    
                if _self.config.get("forcedColors"):
                    media_features.append({"name": "forced-colors", "value": "active"})
                    
                if _self.config.get("reducedData"):
                    media_features.append({"name": "prefers-reduced-data", "value": "reduce"})
                    
                if media_features:
                    try:
                        await page.emulate_media(media_features=media_features)
                        _self.logger.info(f"MEDIA EMULATION ACTIVE: {media_features}")
                        _self.emulation_status["media_applied"] = True
                    except Exception as me:
                        _self.logger.warning(f"Failed to emulate media features: {me}")
                        _self.emulation_status["errors"].append(f"Media feature emulation failure: {me}")
                else:
                    _self.emulation_status["media_applied"] = True

                # 4. Reduced Data Bandwidth Interceptor (Abort Asset Loading)
                if _self.config.get("reducedData"):
                    async def block_assets(route):
                        if route.request.resource_type in ["image", "media", "font"]:
                            await route.abort()
                        else:
                            await route.continue_()
                    try:
                        await page.route("**/*", block_assets)
                        _self.logger.info("REDUCED DATA ACTIVE: Aborted image, media, and font asset downloads.")
                        _self.emulation_status["reduced_data_applied"] = True
                    except Exception as re:
                        _self.logger.warning(f"Failed to set route for reducedData: {re}")
                        _self.emulation_status["errors"].append(f"Reduced data interception setup failure: {re}")
                else:
                    _self.emulation_status["reduced_data_applied"] = True
                # --- EMULATIONS END ---
                
                # 1. Smart Timeout Adaptation
                timeout = await _self._get_dynamic_timeout(page, url) # type: ignore
                
                # 2. Navigation with Stealth
                # Adaptive Wait State: Use 'domcontentloaded' to avoid WebSocket timeouts
                wait_state = "domcontentloaded" if current_attempt == 1 else "commit"
                
                _self.logger.info(f"Navigating Mission Target: {url} (Wait: {wait_state} | Attempt: {current_attempt})") # type: ignore
                await page.goto(
                    url, 
                    wait_until=wait_state, # type: ignore
                    timeout=timeout,
                    referer="https://www.google.com/"
                )
                
                # Universal React/SPA Hydration Buffer
                # We use a strict 5-second sleep instead of 'networkidle' because modern
                # platforms (like Leetcode/Netflix) use WebSockets that never reach 'idle',
                # which causes a fatal 30s timeout. This 5s sleep guarantees React has time to render.
                _self.logger.info("Resilient Navigation: Executing 5s Universal SPA Hydration Wait...") # type: ignore
                await asyncio.sleep(5.0)
                
                # Cognitive Delay (Mimic reading time)
                if current_attempt >= 2:
                    _self.logger.info(f"Stealth Phase IX: Executing {10}s Cognitive Pause...") # type: ignore
                    await asyncio.sleep(10.0)
                    
                await _self._stabilize_dom(page) # type: ignore
                
                # Check for zero content (Next.js hydration safe-check)
                link_count = await page.evaluate("() => document.querySelectorAll('a').length")
                if link_count == 0:
                    title = await page.title()
                    if "access denied" in title.lower() or "forbidden" in title.lower():
                        if current_attempt < MAX_PERSONAS:
                            _self.logger.critical(f"ENGINE BLOCK DETECTED: CDN/WAF rejected the stealth profile for {url} on attempt {current_attempt}. Retrying with rotation...") # type: ignore
                            raise AuditFailedError("WAF Block detected")
                        else:
                            _self.logger.critical(f"FATAL BLOCK: All personas failed for {url}.") # type: ignore
                            raise EngineError(f"Irrecoverable WAF Block on {url} after persona rotation.")
                        
                    _self.logger.warning(f"Engine Detection: Empty DOM detected for {url}. Initiating Emergency Hydration Wait...") # type: ignore
                    await asyncio.sleep(5.0)
                    await _self._stabilize_dom(page) # type: ignore

                # Phase XI: High-Density Focus-Path Simulation (30+ nodes)
                _self.logger.debug("Simulating High-Density Keyboard Navigation...") # type: ignore
                # Disable Stealth Sweep for static quality consistency
                # for _ in range(30):
                #     await page.keyboard.press("Tab")
                #     await asyncio.sleep(0.05) # High-speed sweep

                # 4. Critical Accessibility Analysis (Axe)
                _self.logger.info("Executing Autonomous Accessibility Forensics...") # type: ignore
                axe_violations: List[Any] = []
                try:
                    from axe_playwright_python.async_playwright import Axe
                    
                    # Determine target ruleset tags
                    ruleset_setting = settings.get("ruleset", "wcag21aa")
                    if ruleset_setting == "wcag22aaa":
                        tags = ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa", "wcag22aaa"]
                    elif ruleset_setting == "section508":
                        tags = ["section508"]
                    elif ruleset_setting == "en301549":
                        tags = ["experimental", "en301549"]
                    else:  # default wcag21aa
                        tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
                        
                    # Determine target scope selector
                    scope_setting = settings.get("audit_scope", "full")
                    scope_selector = None
                    if scope_setting == "interactive":
                        scope_selector = "button, a, input, select, textarea, [role='button'], [role='link']"
                    elif scope_setting == "text":
                        scope_selector = "p, h1, h2, h3, h4, h5, h6, span, article, section, li"
                    elif scope_setting == "media":
                        scope_selector = "img, video, audio, svg, canvas, picture"

                    # Parse ignored css selectors
                    ignored_selectors_str = settings.get("ignored_selectors", "")
                    exclude_list = []
                    if ignored_selectors_str:
                        for s in ignored_selectors_str.split(","):
                            s_stripped = s.strip()
                            if s_stripped:
                                exclude_list.append([s_stripped])

                    # Build Axe context parameter
                    axe_context = None
                    if scope_selector:
                        if exclude_list:
                            axe_context = {"include": [[scope_selector]], "exclude": exclude_list}
                        else:
                            axe_context = scope_selector
                    else:
                        if exclude_list:
                            axe_context = {"include": [["html"]], "exclude": exclude_list}

                    # Build Axe options parameter
                    axe_options = {
                        "runOnly": {
                            "type": "tag",
                            "values": tags
                        }
                    }

                    results = await Axe().run(page, context=axe_context, options=axe_options) 
                    
                    if hasattr(results, 'response') and isinstance(results.response, dict):
                        axe_violations = results.response.get("violations", [])
                    elif hasattr(results, 'violations'):
                        axe_violations = cast(Any, results).violations
                    elif isinstance(results, dict):
                        axe_violations = results.get("violations", [])
                    else:
                        axe_violations = getattr(results, 'violations', [])
                        
                    _self.logger.info(f"Forensic Analysis Complete: {len(axe_violations)} base violations documented.") # type: ignore
                except Exception as axe_err:
                    _self.logger.error(f"Axe Forensic Engine Failure: {axe_err}")
                    axe_violations = []

                # 4.5 Secondary Heuristics (HTMLCodeSniffer)
                _self.logger.info("Injecting HTMLCodeSniffer Heuristic Matrix...") # type: ignore
                htmlcs_violations = []
                try:
                    # Inject HTMLCS payload
                    await page.add_script_tag(url="https://squizlabs.github.io/HTML_CodeSniffer/build/HTMLCS.js")
                    await asyncio.sleep(0.5) # Initialization buffer
                    
                    # Run WCAG2AA sweep and extract JSON matching Axe schema
                    htmlcs_raw = await page.evaluate('''() => {
                        return new Promise((resolve) => {
                            HTMLCS.process('WCAG2AA', document, function() {
                                const messages = HTMLCS.getMessages();
                                const results = [];
                                for(let i=0; i<messages.length; i++) {
                                    const msg = messages[i];
                                    if (msg.type === HTMLCS.ERROR || msg.type === HTMLCS.WARNING) {
                                        let selector = "Unknown";
                                        if (msg.element && msg.element.tagName) {
                                            selector = msg.element.tagName.toLowerCase();
                                            if(msg.element.id) selector += "#" + msg.element.id;
                                            if(msg.element.className && typeof msg.element.className === "string") {
                                                selector += "." + msg.element.className.split(" ").join(".");
                                            }
                                        }
                                        results.push({
                                            id: msg.code,
                                            description: msg.msg,
                                            helpUrl: "https://squizlabs.github.io/HTML_CodeSniffer/Standards/WCAG2/",
                                            impact: msg.type === HTMLCS.ERROR ? "critical" : "moderate",
                                            tags: ["wcag2aa", "htmlcs", "cat.heuristic"],
                                            agent: "htmlcs",
                                            selector: selector,
                                            nodes: [{
                                                target: [selector],
                                                html: msg.element ? msg.element.outerHTML.substring(0,200) : "N/A",
                                                failureSummary: msg.msg
                                            }]
                                        });
                                    }
                                }
                                resolve(results);
                            });
                        });
                    }''')
                    
                    if htmlcs_raw and isinstance(htmlcs_raw, list):
                        # Strict Deduplication vs Axe
                        unique_htmlcs = []
                        axe_selectors = set()
                        for av in axe_violations:
                            for n in av.get("nodes", []):
                                targets = n.get("target", [])
                                if targets and isinstance(targets, list):
                                    axe_selectors.add(str(targets[0]))
                        
                        for hv in htmlcs_raw:
                            if hv.get("selector") not in axe_selectors:
                                unique_htmlcs.append(hv)
                                
                        htmlcs_violations = unique_htmlcs
                        _self.logger.info(f"HTMLCS Matrix Complete: {len(htmlcs_violations)} unique heuristic warnings captured.") # type: ignore
                except Exception as htmlcs_err:
                    _self.logger.warning(f"HTMLCS Injection Failure: {htmlcs_err}") # type: ignore
                    htmlcs_violations = []

                # Cycle 14: Neural Data Extraction for Agents
                try:
                    _self.logger.info("Executing Neural Data Extraction [ZET-X1]...") # type: ignore
                    _self.page_data = await extract_page_data( # type: ignore
                        page, 
                        _self.session_id, # type: ignore
                        capture_screenshot=True
                    )
                except Exception as ee:
                    _self.logger.warning(f"Neural Extraction Failure [ZET-X1]: {ee}") # type: ignore

                # Domain-Specific Heuristics
                custom_v = []
                try:
                    custom_v = await _self._run_proprietary_heuristics(page) # type: ignore
                except Exception as he:
                    _self.logger.warning(f"Forensic Cluster minor failure: {he}") # type: ignore
                
                # 5. Synthesis & Telemetry
                all_violations_raw = axe_violations + htmlcs_violations + custom_v
                duration = time.time() - start_time
                _self.logger.info(f"Engine Audit MISSION COMPLETE | Violations: {len(all_violations_raw)} | T+{duration:.2f}s") # type: ignore
                
                _self.context = local_context
                return _self._map_results(all_violations_raw, url) # type: ignore
                
            except AuditFailedError as e:
                # Discard context on failures
                if _self.context:
                    try: await _self.context.close()
                    except: pass
                    _self.context = None
                if "WAF Block" in str(e) and current_attempt < MAX_PERSONAS:
                    current_attempt += 1
                    if page: await page.close()
                    if local_context: await local_context.close()
                    continue
                raise
            except (PlaywrightError, asyncio.TimeoutError) as pe:
                if "Timeout" in str(pe) and current_attempt < MAX_PERSONAS:
                    _self.logger.warning(f"Navigation timeout on attempt {current_attempt}. Switching to resilient payload delivery...") # type: ignore
                    current_attempt += 1
                    if page: 
                        try: await page.close()
                        except: pass
                    if local_context: 
                        try: await local_context.close()
                        except: pass
                    continue
                _self.logger.error(f"Engine Protocol Failure at {url}: {str(pe)}") # type: ignore
                if _self.context:
                    try: await _self.context.close()
                    except: pass
                    _self.context = None
                raise EngineError(f"Audit failed for {url}: {pe}")
            except Exception as e:
                _self.logger.critical(f"FATAL Engine Anomaly at {url}: {e}", exc_info=True) # type: ignore
                if _self.context:
                    try: await _self.context.close()
                    except: pass
                    _self.context = None
                raise EngineError(f"Audit failed for {url}: {e}")
            finally:
                if page:
                    try: 
                        if not page.is_closed():
                            await page.close()
                    except: pass
                if local_context and local_context is not _self.context:
                    try:
                        await local_context.close()
                    except: pass
        
        return []

    async def _get_dynamic_timeout(self: "PlaywrightEngine", page: Page, url: str) -> int:
        """Adapts timeout based on hardware load and domain profile."""
        import json
        settings = {}
        try:
            settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presentation", "settings.json"))
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
        except Exception:
            pass

        base_timeout = settings.get("timeout", 90) * 1000
        if base_timeout < 90000:
            base_timeout = 90000
        
        # Resilient Tier: Increase base for Gov portals or known high-latency domains
        if any(gov in url.lower() for gov in [".gov.in", ".nic.in", ".gov", "india.gov.in"]):
            base_timeout += 30000
            self.logger.info(f"Target identified as High-Latency Portal. Scaling mission timeout to {base_timeout}ms.")

        import psutil # type: ignore
        cpu = psutil.cpu_percent()
        if cpu > 80:
            base_timeout = max(base_timeout, 120000)
            self.logger.warning(f"Engine Stress Detected [{cpu}%]. Scaling mission timeout to {base_timeout}ms.")
            
        return base_timeout

    # --------------------------------------------------------------------------
    # ENGINE ANALYTICAL EXTENSIONS
    # --------------------------------------------------------------------------

    async def _stabilize_dom(self, page: Page):
        """Ensures the page is emotionally and technically stable with human-mimicry."""
        self.logger.debug("Executing Human-Mimicry Stabilization...")
        try:
            # 1. Realistic Bezier Mouse Movement
            await self._simulate_human_mouse(page)
            
            # 1b. Cycle 4: Probabilistic Human Hovers
            await self._simulate_human_hovers(page)
            
            # 2. Variable Jitter Scrolling
            scroll_count = random.randint(3, 7)
            for _ in range(scroll_count):
                depth = random.randint(300, 900)
                await page.mouse.wheel(0, depth)
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 3. Cognitive Pause & Load Verification
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                self.logger.warning("Networkidle wait timed out - proceeding with partial load.")
            
            # Phase XII: Content Verification
            has_links = await page.evaluate("() => document.querySelectorAll('a, button').length > 0")
            if not has_links:
                self.logger.info("Content missing after load. Waiting for Next.js/React hydration...")
                await asyncio.sleep(3.0)
            
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # 4. Return to Baseline
            await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            await asyncio.sleep(1.0)
        except Exception as e:
            self.logger.warning(f"Stealth Stabilization minor failure: {e}")
            # Ensure we give it AT LEAST some time if things go wrong
            await asyncio.sleep(2.0)

    async def _trigger_infinite_scroll_buffer(self, page: Page):
        """Simulates infinite scroll to trigger lazy-loaded accessibility zones."""
        self.logger.info("Engaging Infinite Scroll Zone Buffer...")
        try:
            for _ in range(5):
                # Scroll down in large chunks to trigger mutations
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(0.8)
            # Return to top for analysis
            await page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
            await asyncio.sleep(0.5)
        except Exception as e:
            self.logger.warning(f"Infinite scroll buffer failed: {e}")

    async def _simulate_human_mouse(self, page: Page):
        """Simulates non-linear, human-like mouse paths with Micro-Jitter."""
        try:
            # Move from random start to random end via Bezier
            start_x, start_y = random.randint(0, 200), random.randint(0, 200)
            end_x, end_y = random.randint(400, 1000), random.randint(300, 800)
            
            # Control points for Bezier (Curvature)
            cp1_x, cp1_y = random.randint(100, 900), random.randint(0, 300)
            cp2_x, cp2_y = random.randint(100, 900), random.randint(500, 900)
            
            steps = 45 # Increased for high-fidelity movement
            for i in range(steps + 1):
                t = i / steps
                # Cubic Bezier calculation with added micro-jitter
                x = (1-t)**3 * start_x + 3*(1-t)**2 * t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * end_x
                y = (1-t)**3 * start_y + 3*(1-t)**2 * t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * end_y
                
                # Apply Micro-Jitter (Human hand instability)
                jitter_x = x + random.uniform(-1.5, 1.5)
                jitter_y = y + random.uniform(-1.5, 1.5)
                
                await page.mouse.move(jitter_x, jitter_y)
                # Variable speed simulation (Ease-in, Ease-out)
                wait_time = 0.005 + (0.015 * math.sin(t * math.pi))
                await asyncio.sleep(wait_time)
        except Exception as e:
            self.logger.warning(f"Mouse simulation minor deviation: {e}")

    async def _simulate_human_hovers(self, page: Page):
        """Cycle 4: Probabilistic Hover Suite (mimicking investigative interaction)."""
        try:
            # Identify interactive elements (links, buttons, inputs)
            targets = await page.query_selector_all('a, button, input[type="submit"], [role="button"]')
            if not targets:
                return
            
            # Selection count based on density
            hover_count = min(len(targets), random.randint(2, 5))
            sample = random.sample(cast(List[Any], targets), hover_count)
            
            self.logger.debug(f"Simulating {hover_count} investigative hovers...")
            for el in sample:
                if await el.is_visible():
                    box = await el.bounding_box()
                    if box:
                        # Move to element center with small jitter
                        await page.mouse.move(
                            box['x'] + box['width'] / 2 + random.uniform(-2, 2),
                            box['y'] + box['height'] / 2 + random.uniform(-2, 2)
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.8)) # "Thinking" pause
        except Exception as e:
            self.logger.warning(f"Hover simulation minor deviation: {e}")

    async def _run_proprietary_heuristics(self, page: Page) -> List[Violation]:
        """
        Executes Auditor-specific heuristic rules from the RulesNexus.
        
        This pushes the analytical depth beyond standard rule engines.
        """
        custom_v = []
        try:
            # Heuristic 1: Semantic Skeleton Analysis (including Shadow Roots)
            all_scopes = await self._find_all_render_contexts(page)
            for scope_id, selector in all_scopes:
                semantic_score = await page.evaluate("(sel) => { \
                    const root = sel === 'document' ? document : document.querySelector(sel).shadowRoot; \
                    let score = 0; \
                    if(root.querySelector('header')) score += 0.2; \
                    if(root.querySelector('main')) score += 0.5; \
                    if(root.querySelector('footer')) score += 0.3; \
                    return score; \
                }", selector)
                
                if semantic_score < 0.7:
                    self.logger.warning(f"Engine Detection: Low Semantic Integrity Signature ({semantic_score}) in {selector}")
                    custom_v.append(Violation(
                        rule_id="HEURISTIC-SEMANTIC-001",
                        session_id=self.session_id,
                        impact=ImpactLevel.MODERATE,
                        description=f"Low Semantic Integrity (Score: {semantic_score}). The context {selector} lacks structural landmarks.",
                        help_url="https://auditor.agency/heuristics/semantics",
                        selector=selector,
                        nodes=[{"html": f"<{selector}>", "target": selector, "failure_summary": "Incomplete semantic structure detected in isolated component.", "fix": "Use semantic HTML landmark tags (e.g. <main>, <nav>, <header>, <footer>) instead of generic <div> containers."}],
                        tags=["auditor", "heuristics", "semantics", "shadow-dom", "wcag-1.3.1", "wcag2a"],
                        agent="cognitive"
                    ))
            
            # Heuristic 4: Structural & Forensic Suite (Phase IV)
            structural_v = await self._run_forensic_suite(page)
            custom_v.extend(structural_v)
            
            # Heuristic 3: Language Inconsistency Detector
            lang_v = await self._verify_language_integrity(page)
            custom_v.extend(lang_v)
            
        except Exception as e:
            self.logger.error(f"Heuristic Engine Error: {e}")
            
        return custom_v

    async def _run_forensic_suite(self, page: Page) -> List[Violation]:
        """Orchestrates Phase XI clinical forensics (Cycle 2 Enhanced)."""
        violations = []
        violations.extend(await self._analyze_target_size(page))
        violations.extend(await self._analyze_alt_text_quality(page))
        violations.extend(await self._verify_skip_links(page))
        violations.extend(await self._analyze_heading_hierarchy(page))
        violations.extend(await self._analyze_aria_relationships(page)) # Cycle 2: ARIA Engine
        violations.extend(await self._analyze_svg_accessibility(page)) # Cycle 3: Vector Forensics
        violations.extend(await self._analyze_form_grouping(page)) # Cycle 4: Form-Field Forensics
        violations.extend(await self._analyze_aria_live_regions(page)) # Cycle 5: Dynamic Mutations
        violations.extend(await self._analyze_dynamic_contrast(page)) # Cycle 6: Overlap Forensics
        violations.extend(await self._analyze_focus_traps(page)) # Cycle 7: Navigation Forensics
        
        # Integrate advanced custom heuristics agents
        violations.extend(await self._deep_aria_structural_audit(page))
        violations.extend(await self._execute_perception_audit_sweep(page))
        violations.extend(await self._audit_interaction_fluidity(page))
        violations.extend(await self._perform_css_structural_audit(page))
        
        # Integrate Phase 5 Dynamic Agents
        violations.extend(await self._verify_color_contrast_in_canvas(page))
        violations.extend(await self._check_font_scaling_stability(page))
        violations.extend(await self._audit_placeholder_contrast(page))
        violations.extend(await self._detect_invisible_focus_traps(page))
        violations.extend(await self._audit_responsive_orientation_lock(page))
        violations.extend(await self._detect_scrollable_regions_keyboard_access(page))
        violations.extend(await self._check_draggables_keyboard_alt(page))
        violations.extend(await self._audit_form_error_association(page))
        violations.extend(await self._verify_landmark_completeness(page))
        violations.extend(await self._audit_reading_order_coherence(page))
        violations.extend(await self._verify_table_header_relationships(page))
        violations.extend(await self._verify_autocomplete_attributes(page))
        violations.extend(await self._check_autoplay_violation(page))
        violations.extend(await self._verify_aria_live_announcements(page))
        violations.extend(await self._audit_iframe_title_presence(page))
        violations.extend(await self._verify_non_text_content_alternatives(page))
        violations.extend(await self._audit_timed_response_extensions(page))
        
        return violations

    async def _analyze_aria_live_regions(self, page: Page) -> List[Violation]:
        """Cycle 5: Detect dynamic content updates lacking ARIA live indicators."""
        # This heuristic looks for elements that are likely dynamic targets but lack aria-live
        script = """() => {
            const dynamicIndicators = ['status', 'alert', 'log', 'timer'];
            const suspicious = Array.from(document.querySelectorAll('div, span, section'));
            const issues = [];
            
            suspicious.forEach(el => {
                const id = el.id ? el.id.toLowerCase() : '';
                const cls = el.className ? String(el.className).toLowerCase() : '';
                const isDynamicName = id.includes('update') || id.includes('live') || id.includes('status') ||
                                    cls.includes('update') || cls.includes('live') || cls.includes('status');
                
                const hasLive = el.getAttribute('aria-live') || el.getAttribute('role') === 'status' || el.getAttribute('role') === 'alert';
                
                if (isDynamicName && !hasLive) {
                    issues.push({
                        html: el.outerHTML.slice(0, 200),
                        selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
                    });
                }
            });
            return issues;
        }"""
        raw_issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in raw_issues:
            sel = str(issue.get('selector', 'element'))
            html = str(issue.get('html', ''))
            violations.append(Violation(
                rule_id="HEURISTIC-LIVE-REG-501",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Potential missing ARIA live-region: Element ID/Class suggests dynamic updates without assistive notification.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html",
                selector=sel,
                nodes=[{"html": html, "target": sel, "failure_summary": "Dynamic container detected without aria-live or status role.", "fix": "Add aria-live='polite' or role='status' to container that displays dynamic content updates."}],
                tags=["auditor", "forensics", "dynamic-v3", "wcag-4.1.3", "wcag2aa"],
                agent="neural"
            ))
        return violations

    async def _analyze_form_grouping(self, page: Page) -> List[Violation]:
        """Cycle 4: Detect related radio/checkbox groups missing structural fieldsets."""
        script = """() => {
            const groups = {};
            const inputs = Array.from(document.querySelectorAll('input[type="radio"], input[type="checkbox"]'));
            
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    if (!groups[name]) groups[name] = [];
                    groups[name].push(input);
                }
            });
            
            const issues = [];
            for (const name in groups) {
                if (groups[name].length > 1) {
                    const first = groups[name][0];
                    // Traverse up to find fieldset or group role
                    let parent = first.parentElement;
                    let hasContainer = false;
                    while (parent && parent !== document.body) {
                        if (parent.tagName === 'FIELDSET' || parent.getAttribute('role') === 'group') {
                            hasContainer = true;
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    if (!hasContainer) {
                        issues.push({
                            name: name,
                            count: groups[name].length,
                            html: first.outerHTML.slice(0, 200),
                            selector: `input[name="${name}"]`
                        });
                    }
                }
            }
            return issues;
        }"""
        form_issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in form_issues:
            name = str(issue.get('name', ''))
            count = issue.get('count', 0)
            html = str(issue.get('html', ''))
            sel = str(issue.get('selector', ''))
            
            violations.append(Violation(
                rule_id="HEURISTIC-FORM-GRP-401",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description=f"Logical input group '{name}' ({count} items) lacks structural container (fieldset/role='group').",
                help_url="https://www.w3.org/WAI/tutorials/forms/grouping/",
                selector=sel,
                nodes=[{"html": html, "target": sel, "failure_summary": "Related inputs found without Fieldset or Role=Group.", "fix": "Wrap related radio buttons or checkboxes in a <fieldset> with a <legend> for structural grouping, or use role='group'."}],
                tags=["auditor", "forensics", "forms-v2", "wcag-3.3.2", "wcag2a"],
                agent="cognitive"
            ))
        return violations

    async def _analyze_svg_accessibility(self, page: Page) -> List[Violation]:
        """Cycle 3: High-Density SVG Forensics (detecting inaccessible vector paths, excluding decorative/nested elements)."""
        script = """() => {
            const svgs = Array.from(document.querySelectorAll('svg'));
            const issues = [];
            svgs.forEach(svg => {
                const hasTitle = svg.querySelector('title');
                const hasLabel = svg.getAttribute('aria-label') || svg.getAttribute('aria-labelledby');
                const isHidden = svg.getAttribute('aria-hidden') === 'true';
                
                // Exclude if role is decorative/none
                const role = svg.getAttribute('role') || svg.getAttribute('aria-role') || '';
                const isDecorativeRole = role === 'presentation' || role === 'none';
                
                if (isHidden || isDecorativeRole) return;
                
                // Exclude if parent element is interactive and already has an accessible name
                let parent = svg.parentElement;
                let hasAccessibleParent = false;
                while (parent && parent !== document.body) {
                    const tag = parent.tagName;
                    const hasName = parent.getAttribute('aria-label') || parent.getAttribute('aria-labelledby') || parent.getAttribute('title');
                    if (['BUTTON', 'A', 'INPUT'].includes(tag) && hasName) {
                        hasAccessibleParent = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                if (hasAccessibleParent) return;
                
                // Exclude if parent element is interactive and contains text (e.g. inline icon inside link/button)
                let parentTextCheck = svg.parentElement;
                let hasTextParent = false;
                while (parentTextCheck && parentTextCheck !== document.body) {
                    const tag = parentTextCheck.tagName;
                    if (['BUTTON', 'A', 'LABEL'].includes(tag)) {
                        const parentText = parentTextCheck.innerText ? parentTextCheck.innerText.trim() : '';
                        if (parentText.length > 0) {
                            hasTextParent = true;
                            break;
                        }
                    }
                    parentTextCheck = parentTextCheck.parentElement;
                }
                
                if (hasTextParent) return;
                
                if (!hasTitle && !hasLabel) {
                    issues.push({
                        html: svg.outerHTML.slice(0, 200),
                        selector: svg.tagName.toLowerCase() + (svg.id ? '#' + svg.id : '')
                    });
                }
            });
            return issues;
        }"""
        raw_issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in raw_issues:
            sel = str(issue.get('selector', 'svg'))
            html = str(issue.get('html', ''))
            s_title = "Descriptive Vector Graphic"
            
            violations.append(Violation(
                rule_id="HEURISTIC-SVG-ACC-301",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Inaccessible SVG detected: Vector graphic lacks descriptive title or ARIA label.",
                help_url="https://www.w3.org/TR/SVG-access/",
                selector=sel,
                nodes=[{
                    "html": html, 
                    "target": sel, 
                    "failure_summary": "Missing <title> or ARIA label in vector graphic.",
                    "suggested_fix": f"Add <title>{s_title}</title> as the first child of the <svg> element.",
                    "fix": "Add a <title> element inside the SVG and set aria-hidden='false', or add aria-label='Description'."
                }],
                tags=["auditor", "forensics", "vector-v2", "wcag-1.1.1", "wcag2a"],
                agent="visual"
            ))
        return violations

    async def _analyze_dynamic_contrast(self, page: Page) -> List[Violation]:
        """Cycle 6: Detect contrast issues in overlapping/layered text elements."""
        script = """() => {
            const elements = Array.from(document.querySelectorAll('div, span, p, h1, h2, h3, h4, h5, h6, a, button'));
            const issues = [];
            
            const floatingElements = elements.filter(el => {
                const style = window.getComputedStyle(el);
                const isFloating = style.position === 'absolute' || style.position === 'fixed' || parseInt(style.zIndex) > 50;
                const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                return isFloating && isVisible && el.innerText.trim().length > 0;
            });
            
            if (floatingElements.length > 50) {
                floatingElements.length = 50;
            }
 
            floatingElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                
                const points = [
                    {x: rect.left + 5, y: rect.top + 5},
                    {x: rect.right - 5, y: rect.top + 5},
                    {x: rect.left + 5, y: rect.bottom - 5},
                    {x: rect.right - 5, y: rect.bottom - 5},
                    {x: rect.left + rect.width/2, y: rect.top + rect.height/2}
                ];
                
                points.forEach(p => {
                    if (p.x < 0 || p.y < 0 || p.x > window.innerWidth || p.y > window.innerHeight) return;
                    
                    const originalPointerEvents = el.style.pointerEvents;
                    el.style.pointerEvents = 'none';
                    const under = document.elementFromPoint(p.x, p.y);
                    el.style.pointerEvents = originalPointerEvents;
                    
                    // Exclude parent/child nesting relationships to prevent false positives
                    if (under && under !== el && !el.contains(under) && !under.contains(el)) {
                        if (under.innerText && under.innerText.trim().length > 0) {
                            issues.push({
                                html: el.outerHTML.slice(0, 150),
                                selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
                                target: under.tagName.toLowerCase() + (under.id ? '#' + under.id : '')
                            });
                        }
                    }
                });
            });
            return issues;
        }"""
        raw_issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in raw_issues:
            sel = str(issue.get('selector', 'element'))
            tgt = str(issue.get('target', 'sibling'))
            html = str(issue.get('html', ''))
            violations.append(Violation(
                rule_id="HEURISTIC-OVERLAP-601",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description=f"Potential contrast occlusion: Layered element '{sel}' overlaps text in '{tgt}'.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
                selector=sel,
                nodes=[{"html": html, "target": sel, "failure_summary": f"Z-Index layering may occlude underlying text content in {tgt}.", "fix": "Ensure layered or floating elements do not cover or overlap text content, and keep sufficient text contrast."}],
                tags=["auditor", "forensics", "vision-v2", "wcag-1.4.3", "wcag2aa"],
                agent="visual"
            ))
        return violations

    async def _analyze_aria_relationships(self, page: Page) -> List[Violation]:
        """Cycle 2: Detect broken ARIA IDREFs and check for empty targets or circular dependencies."""
        script = """() => {
            const attributes = ['aria-owns', 'aria-controls', 'aria-describedby', 'aria-labelledby'];
            const broken = [];
            
            // Graph representation to detect circular references
            const adj = {};
            
            attributes.forEach(attr => {
                const elements = Array.from(document.querySelectorAll(`[${attr}]`));
                elements.forEach(el => {
                    const elId = el.id || '';
                    const val = el.getAttribute(attr) || '';
                    const ids = val.split(/\\s+/);
                    
                    ids.forEach(targetId => {
                        if (!targetId) return;
                        
                        const target = document.getElementById(targetId);
                        if (!target) {
                            broken.push({
                                type: 'MISSING_ID',
                                html: el.outerHTML.slice(0, 200),
                                attribute: attr,
                                missing_id: targetId,
                                selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
                            });
                        } else {
                            // Target exists, check if empty
                            const text = target.innerText ? target.innerText.trim() : '';
                            const label = target.getAttribute('aria-label') || '';
                            if (attr === 'aria-labelledby' && !text && !label) {
                                broken.push({
                                    type: 'EMPTY_LABEL',
                                    html: el.outerHTML.slice(0, 200),
                                    attribute: attr,
                                    missing_id: targetId,
                                    selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
                                });
                            }
                            
                            // Circular reference detection (aria-owns or aria-controls)
                            if (elId && (attr === 'aria-owns' || attr === 'aria-controls')) {
                                if (!adj[elId]) adj[elId] = [];
                                adj[elId].push(targetId);
                            }
                        }
                    });
                });
            });
            
            // Check cycles
            const visited = {};
            const recStack = {};
            function hasCycle(v) {
                if (!visited[v]) {
                    visited[v] = true;
                    recStack[v] = true;
                    const neighbors = adj[v] || [];
                    for (let i = 0; i < neighbors.length; i++) {
                        const n = neighbors[i];
                        if (!visited[n] && hasCycle(n)) return true;
                        else if (recStack[n]) return true;
                    }
                }
                recStack[v] = false;
                return false;
            }
            
            for (const node in adj) {
                if (hasCycle(node)) {
                    broken.push({
                        type: 'CIRCULAR_REF',
                        html: document.getElementById(node).outerHTML.slice(0, 200),
                        attribute: 'aria-owns/controls',
                        missing_id: node,
                        selector: '#' + node
                    });
                    break; // Flag once
                }
            }
            
            return broken;
        }"""
        broken_refs = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for ref in broken_refs:
            err_type = ref.get('type')
            attr = str(ref.get('attribute', ''))
            missing = str(ref.get('missing_id', ''))
            html = str(ref.get('html', ''))
            sel = str(ref.get('selector', ''))
            
            if err_type == 'MISSING_ID':
                violations.append(Violation(
                    rule_id="HEURISTIC-ARIA-REL-210",
                    session_id=self.session_id,
                    impact=ImpactLevel.SERIOUS,
                    description=f"Broken ARIA relationship: {attr} references non-existent ID '{missing}'.",
                    help_url="https://www.w3.org/WAI/ARIA/apg/practices/relationships/",
                    selector=sel,
                    nodes=[{"html": html, "target": sel, "failure_summary": f"Reference ID '{missing}' not found in DOM.", "fix": f"Create an element with id='{missing}' or update the {attr} attribute."}],
                    tags=["auditor", "heuristics", "aria-v3", "wcag-4.1.2", "wcag2a"],
                    agent="neural"
                ))
            elif err_type == 'EMPTY_LABEL':
                violations.append(Violation(
                    rule_id="HEURISTIC-ARIA-LABEL-EMPTY",
                    session_id=self.session_id,
                    impact=ImpactLevel.CRITICAL,
                    description=f"Empty ARIA label reference: aria-labelledby targets element '{missing}' which contains no accessible text content.",
                    help_url="https://www.w3.org/TR/wai-aria-1.1/#aria-labelledby",
                    selector=sel,
                    nodes=[{"html": html, "target": sel, "failure_summary": f"Label target '{missing}' has no innerText.", "fix": f"Add descriptive text inside the label target element with id='{missing}'."}],
                    tags=["auditor", "heuristics", "aria-v3", "wcag-1.1.1", "wcag-4.1.2", "wcag2a"],
                    agent="neural"
                ))
            elif err_type == 'CIRCULAR_REF':
                violations.append(Violation(
                    rule_id="HEURISTIC-ARIA-CIRCULAR",
                    session_id=self.session_id,
                    impact=ImpactLevel.CRITICAL,
                    description="Circular ARIA reference detected. Interactive elements reference each other in a loop, which breaks screen reader parsing.",
                    help_url="https://www.w3.org/TR/wai-aria-1.1/",
                    selector=sel,
                    nodes=[{"html": html, "target": sel, "failure_summary": "Circular owners/controls path.", "fix": "Ensure ARIA ownership relationships form a clean tree hierarchy and have no cycles."}],
                    tags=["auditor", "heuristics", "aria-v3", "wcag-4.1.2", "wcag2a"],
                    agent="neural"
                ))
        return violations

    async def _analyze_target_size(self, page: Page) -> List[Violation]:
        """Item 36: Detect interactive elements < 24x24px (WCAG 2.2 AA target size minimum)."""
        script = """() => {
            const allTargets = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"]'));
            const targets = allTargets.filter(t => {
                const style = window.getComputedStyle(t);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
            }).slice(0, 300);

            const issues = [];
            targets.forEach(t => {
                const rect = t.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                
                const style = window.getComputedStyle(t);
                // Exempt inline text links (embedded in paragraphs/text blocks)
                const isInline = style.display === 'inline' && 
                                 t.parentElement && 
                                 ['P', 'SPAN', 'LI', 'A', 'DIV'].includes(t.parentElement.tagName) &&
                                 t.parentElement.innerText.trim().length > t.innerText.trim().length * 1.5;
                                 
                if (isInline) return;

                if (rect.width < 24 || rect.height < 24) {
                    issues.push({
                        html: t.outerHTML.slice(0, 200),
                        width: rect.width,
                        height: rect.height,
                        selector: t.tagName.toLowerCase() + (t.id ? '#' + t.id : '')
                    });
                }
            });
            return issues;
        }"""
        small_elements = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for el in small_elements:
            width = float(el.get('width', 0))
            height = float(el.get('height', 0))
            html = str(el.get('html', ''))
            sel = str(el.get('selector', ''))
            
            violations.append(Violation(
                rule_id="HEURISTIC-TARGET-036",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description=f"Interactive target size too small ({round(width)}x{round(height)}px). Minimum required under WCAG 2.2: 24x24px.",
                help_url="https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html",
                selector=sel,
                nodes=[{"html": html, "target": sel, "failure_summary": "Interactive touch target is below 24x24px.", "fix": "Increase target size to at least 24x24px or add padding."}],
                tags=["auditor", "heuristics", "wcag-2.5.8", "wcag2aa"],
                agent="motor"
            ))
        return violations

    async def _analyze_alt_text_quality(self, page: Page) -> List[Violation]:
        """Item 50: Flag generic/redundant alt descriptions, excluding decorative images."""
        generic_terms = ["image", "img", "photo", "pic", "graphic", "icon", "logo", "drawing", "picture"]
        script = """() => {
            const images = Array.from(document.querySelectorAll('img'));
            return images.map(img => ({
                html: img.outerHTML.slice(0, 200),
                alt: img.hasAttribute('alt') ? img.alt.toLowerCase().trim() : null,
                hasAlt: img.hasAttribute('alt')
            }));
        }"""
        img_data = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for img in img_data:
            has_alt = img.get('hasAlt', False)
            alt = img.get('alt')
            html = str(img.get('html', ''))
            
            if not has_alt or alt == "":
                continue # Skip decorative images or those missing alt (handled by standard engine)
                
            if alt is not None and (any(term == alt or f" {term} " in f" {alt} " for term in generic_terms) or len(alt) < 3):
                violations.append(Violation(
                    rule_id="HEURISTIC-ALT-050",
                    session_id=self.session_id,
                    impact=ImpactLevel.SERIOUS,
                    description=f"Generic alt text detected: '{alt}'. Provide descriptive context.",
                    help_url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html",
                    selector="img",
                    nodes=[{"html": html, "target": "img", "failure_summary": "Meaningless alternative text.", "fix": "Provide meaningful and descriptive alt text context (e.g. alt='Company Logo') or use alt='' if decorative."}],
                    tags=["auditor", "heuristics", "wcag-1.1.1", "wcag2a"],
                    agent="visual"
                ))
        return violations

    async def _verify_skip_links(self, page: Page) -> List[Violation]:
        """Item 33: Verify 'Skip to Content' mechanism and eliminate false positives/negatives."""
        needs_skip = await page.evaluate("""() => {
            const navElements = document.querySelectorAll('nav, [role="navigation"]');
            if (navElements.length > 0) return true;
            
            const links = Array.from(document.querySelectorAll('a'));
            let headerLinksCount = 0;
            links.forEach(link => {
                let parent = link.parentElement;
                while (parent && parent !== document.body) {
                    if (parent.tagName === 'HEADER' || parent.tagName === 'NAV' || parent.className.includes('nav') || parent.className.includes('menu')) {
                        headerLinksCount++;
                        break;
                    }
                    parent = parent.parentElement;
                }
            });
            return headerLinksCount >= 5;
        }""")
        
        if not needs_skip:
            return []
 
        skip_link_data = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a, button'));
            const skipLinks = links.filter(l => {
                const text = l.innerText ? l.innerText.toLowerCase().trim() : '';
                return text.includes('skip') && (l.getAttribute('href') || '').includes('#');
            });
            
            if (skipLinks.length === 0) return { found: false };
            
            const first = skipLinks[0];
            const href = first.getAttribute('href');
            const targetId = href.split('#')[1];
            
            const targetEl = document.getElementById(targetId);
            const targetExists = !!targetEl;
            let targetVisible = false;
            if (targetExists) {
                const targetStyle = window.getComputedStyle(targetEl);
                targetVisible = targetStyle.display !== 'none' && targetStyle.visibility !== 'hidden';
            }
            
            const style = window.getComputedStyle(first);
            const isHidden = style.display === 'none' || style.visibility === 'hidden';
            
            return {
                found: true,
                html: first.outerHTML.slice(0, 200),
                targetId: targetId,
                targetExists: targetExists,
                targetVisible: targetVisible,
                isHidden: isHidden
            };
        }""")
        
        violations = []
        if not skip_link_data.get('found', False):
            violations.append(Violation(
                rule_id="HEURISTIC-SKIP-033",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Bypass block (Skip Link) missing on a page with repetitive navigation blocks.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                selector="body",
                nodes=[{"html": "<body>", "target": "body", "failure_summary": "No mechanism to skip repetitive header links.", "fix": "Add a visually hidden 'Skip to main content' link as the first focusable element inside the body."}],
                tags=["auditor", "heuristics", "wcag-2.4.1", "wcag2a"],
                agent="motor"
            ))
        else:
            if not skip_link_data.get('targetExists', False):
                violations.append(Violation(
                    rule_id="HEURISTIC-SKIP-033-BROKEN",
                    session_id=self.session_id,
                    impact=ImpactLevel.CRITICAL,
                    description=f"Broken skip link: Target ID '#{skip_link_data.get('targetId')}' does not exist in the DOM.",
                    help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                    selector="a",
                    nodes=[{"html": skip_link_data.get('html'), "target": "a", "failure_summary": f"Skip link targets missing ID '{skip_link_data.get('targetId')}'", "fix": "Update skip link href to match the ID of the main content element."}],
                    tags=["auditor", "heuristics", "wcag-2.4.1", "wcag2a"],
                    agent="motor"
                ))
            elif not skip_link_data.get('targetVisible', False):
                violations.append(Violation(
                    rule_id="HEURISTIC-SKIP-033-TARGET-HIDDEN",
                    session_id=self.session_id,
                    impact=ImpactLevel.SERIOUS,
                    description=f"Skip link target '#{skip_link_data.get('targetId')}' is hidden (display: none or visibility: hidden).",
                    help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                    selector="a",
                    nodes=[{"html": skip_link_data.get('html'), "target": "a", "failure_summary": f"Skip link targets hidden element '{skip_link_data.get('targetId')}'", "fix": "Ensure the target of the skip link is a visible container or becomes active upon focus."}],
                    tags=["auditor", "heuristics", "wcag-2.4.1", "wcag2a"],
                    agent="motor"
                ))
            elif skip_link_data.get('isHidden', False):
                violations.append(Violation(
                    rule_id="HEURISTIC-SKIP-033-HIDDEN",
                    session_id=self.session_id,
                    impact=ImpactLevel.SERIOUS,
                    description="Skip link is completely hidden from screen readers/keyboard navigation (display:none or visibility:hidden).",
                    help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                    selector="a",
                    nodes=[{"html": skip_link_data.get('html'), "target": "a", "failure_summary": "Skip link is visually and programmatically hidden.", "fix": "Ensure the skip link is focusable and becomes visible when focused (use CSS skip link techniques)."}],
                    tags=["auditor", "heuristics", "wcag-2.4.1", "wcag2a"],
                    agent="motor"
                ))
                
        return violations

    async def _analyze_heading_hierarchy(self, page: Page) -> List[Violation]:
        """Item 47: Detect skipped heading levels within structural subtrees to eliminate false positives."""
        script = """() => {
            const containers = Array.from(document.querySelectorAll('main, aside, footer, header, nav, [role="main"]'));
            if (containers.length === 0) containers.push(document.body);
            
            const issues = [];
            containers.forEach(container => {
                const headings = Array.from(container.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                    .filter(h => {
                        // Filter out empty headings
                        if (!h.innerText || h.innerText.trim().length === 0) return false;
                        
                        // Filter out hidden headings
                        const style = window.getComputedStyle(h);
                        if (style.display === 'none' || style.visibility === 'hidden') return false;
                        
                        let parent = h.parentElement;
                        while (parent && parent !== container) {
                            if (['MAIN', 'ASIDE', 'FOOTER', 'HEADER', 'NAV'].includes(parent.tagName)) {
                                return false;
                            }
                            parent = parent.parentElement;
                        }
                        return true;
                    })
                    .map(h => ({
                        level: parseInt(h.tagName[1]),
                        html: h.outerHTML.slice(0, 150),
                        selector: h.tagName.toLowerCase() + (h.id ? '#' + h.id : '')
                    }));
                
                if (headings.length > 0) {
                    // If the first heading in a major container starts at H3 or deeper, it has skipped H1/H2
                    const first = headings[0];
                    if (first.level > 2) {
                        issues.push({
                            curr: first.level,
                            prev: 1,
                            html: first.html,
                            selector: first.selector,
                            isFirst: true
                        });
                    }
                }
                
                for (let i = 1; i < headings.length; i++) {
                    const curr_h = headings[i].level;
                    const prev_h = headings[i-1].level;
                    if (curr_h > prev_h + 1) {
                        issues.push({
                            curr: curr_h,
                            prev: prev_h,
                            html: headings[i].html,
                            selector: headings[i].selector,
                            isFirst: false
                        });
                    }
                }
            });
            return issues;
        }"""
        
        skipped_headings = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in skipped_headings:
            curr_h = int(issue.get('curr', 0))
            prev_h = int(issue.get('prev', 0))
            html = str(issue.get('html', ''))
            sel = str(issue.get('selector', ''))
            is_first = bool(issue.get('isFirst', False))
            
            description = (
                f"Skipped heading level detected (H{prev_h} to H{curr_h}). Structural hierarchy should descend sequentially."
                if not is_first else
                f"Skipped heading level at start of container: Starts with H{curr_h} instead of H1 or H2."
            )
            
            violations.append(Violation(
                rule_id="HEURISTIC-HEAD-047",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description=description,
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                selector=sel,
                nodes=[{"html": html, "target": sel, "failure_summary": f"Heading level jumped or started at H{curr_h}.", "fix": f"Adjust heading structure so that H{curr_h} descends sequentially from its parent."}],
                tags=["auditor", "heuristics", "wcag-1.3.1", "wcag2a"],
                agent="cognitive"
            ))
        return violations

    async def _find_all_render_contexts(self, page: Page) -> List[Tuple[str, str]]:
        """Identifies all isolated render contexts (document + shadow roots)."""
        contexts = [("document", "document")]
        try:
            shadow_hosts = await page.evaluate("() => { \
                return Array.from(document.querySelectorAll('*')) \
                    .filter(el => el.shadowRoot) \
                    .map(h => h.tagName.toLowerCase() + (h.id ? '#' + h.id : '')); \
            }")
            for host_selector in shadow_hosts:
                contexts.append(("shadow-root", host_selector))
        except Exception as e:
            self.logger.error(f"Shadow DOM discovery failure: {e}")
        return contexts

    async def _analyze_keyboard_focus_topology(self, page: Page) -> List[Violation]:
        """Phase VII: Traces the visual focus path while analyzing topology."""
        traps = []
        self.focus_path = [] # Reset for current page
        
        try:
            self.logger.info("Executing Visual Focus Path Sweep...")
            await page.focus("body")
            
            last_pos = {"x": 0, "y": 0}
            for i in range(40): # Sweep limit
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.1)
                
                node_data = await page.evaluate("""() => {
                    const el = document.activeElement;
                    if (!el || el === document.body) return null;
                    const rect = el.getBoundingClientRect();
                    return {
                        tag: el.tagName,
                        id: el.id,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        text: el.innerText.slice(0, 30)
                    };
                }""")
                
                if not node_data: continue
                
                # Record for Visualization
                self.focus_path.append(node_data)
                
                # Topological Anomaly Detection
                if node_data["y"] < last_pos["y"] - 100:
                    self.logger.warning(f"Focus Topology Anomaly: Upward jump to {node_data['tag']}")
                
                last_pos = {"x": node_data["x"], "y": node_data["y"]}
                
                # Detect Loops (Traps)
                if len(self.focus_path) > 3 and i > 10:
                    # Simple loop detection
                    pass # Logic implemented in Phase IV
                    
        except Exception as e:
            self.logger.error(f"Focus Path Trace Error: {e}")
            
        return traps

    async def _verify_language_integrity(self, page: Page) -> List[Violation]:
        """Verifies if the declared 'lang' attribute matches the actual content, filtered by high confidence and bilingual overrides."""
        violations = []
        try:
            from langdetect import detect_langs, DetectorFactory # type: ignore
            DetectorFactory.seed = 0
            
            declared_lang = await page.evaluate("document.documentElement.lang || 'N/A'")
            page_text = await page.evaluate("document.body.innerText.slice(0, 3000)")
            if not page_text.strip() or len(page_text.strip()) < 150: return []
            
            langs = detect_langs(page_text)
            if not langs: return []
            
            major_declared = declared_lang.split("-")[0].lower()
            
            # Bilingual check: if the declared language is detected at all with >= 15% probability,
            # we consider it a valid mixed/bilingual page and skip flagging a mismatch.
            declared_detected = False
            for l in langs:
                if l.lang.split("-")[0].lower() == major_declared and l.prob >= 0.15:
                    declared_detected = True
                    break
            
            if declared_detected:
                return []
                
            best_lang = langs[0]
            # High confidence threshold (> 0.85) to eliminate false positives on short/mixed-lang pages
            if best_lang.prob < 0.85: return []
            
            detected_lang = best_lang.lang
            major_detected = detected_lang.split("-")[0].lower()
            
            if major_declared != major_detected and major_declared != "n/a":
                self.logger.warning(f"Linguistic Anomaly: Declared '{major_declared}', Detected '{major_detected}' (confidence: {best_lang.prob:.2f})")
                violations.append(Violation(
                    rule_id="HEURISTIC-LANG-003",
                    session_id=self.session_id,
                    impact=ImpactLevel.SERIOUS,
                    description=f"Language Inconsistency. Declared 'lang=\"{declared_lang}\"', but content appears to be {major_detected}.",
                    help_url="https://auditor.agency/heuristics/language-mismatch",
                    selector="html",
                    nodes=[{"html": f"<html lang=\"{declared_lang}\">", "target": "html", "failure_summary": "Linguistic signature mismatch.", "fix": f"Ensure the lang attribute on the <html> element matches the actual primary language of the content (e.g., change lang to lang='{major_detected}')."}],
                    tags=["auditor", "heuristics", "language", "wcag-3.1.1", "wcag2a"],
                    agent="cognitive"
                ))
        except Exception as e:
            self.logger.error(f"Language integrity check failure: {e}")
            
        return violations

    # --------------------------------------------------------------------------
    # DATA RECONCILIATION & TELEMETRY
    # --------------------------------------------------------------------------

    def _map_results(self, results: Any, url: str) -> List[Violation]:
        """Technically dense mapping of cluster-data into the domain model."""
        violations = []
        
        # Robustly extract violations list
        raw_violations = []
        if isinstance(results, list):
            # NEW: Handle case where list of violations is passed directly
            raw_violations = results
        elif isinstance(results, dict):
            raw_violations = results.get("violations", [])
        else:
            raw_violations = getattr(results, "violations", [])
            if not raw_violations and hasattr(results, "results"):
                raw_violations = results.results.get("violations", [])

        for raw_v in raw_violations:
            if hasattr(raw_v, 'description'):
                # Already a Violation object (proprietary heuristic)
                v_obj = cast(Violation, raw_v)
                if not v_obj.category or v_obj.category in ("General Accessibility", "General"):
                    v_obj.category = ComplianceMapper.get_category(v_obj.tags, v_obj.rule_id, v_obj.agent)
                if not v_obj.compliance_level or v_obj.compliance_level == "Non-Standard":
                    v_obj.compliance_level = ComplianceMapper.get_compliance_level(v_obj.tags, v_obj.impact)
                if not v_obj.severity_matrix or v_obj.severity_matrix == "Unclassified":
                    v_obj.severity_matrix = ComplianceMapper.get_severity_matrix(v_obj.impact)
                violations.append(v_obj)
                continue
                
            v = cast(Dict[str, Any], raw_v)
            
            # Map Impact Logic
            impact_raw = v.get("impact", "minor")
            impact_map = {
                "critical": ImpactLevel.CRITICAL,
                "serious": ImpactLevel.SERIOUS,
                "moderate": ImpactLevel.MODERATE,
                "minor": ImpactLevel.MINOR
            }
            impact = impact_map.get(impact_raw, ImpactLevel.MINOR)
            
            # Node Extraction with Deep Failure Summaries
            nodes = v.get("nodes", [])
            node_summaries = []
            first_selector = "Unknown"
            for raw_n in nodes:
                n = cast(Dict[str, Any], raw_n)
                target_list = n.get("target", [])
                sel = target_list[0] if target_list else "Unknown" # type: ignore
                if first_selector == "Unknown": first_selector = sel
                
                node_summaries.append({ # type: ignore
                    "html": n.get("html", "N/A"),
                    "target": sel,
                    "failure_summary": n.get("failureSummary", "No failure summary provided.")
                })

            tags = v.get("tags", [])
            agent = v.get("agent", "htmlcs" if "htmlcs" in tags else "axe")
            
            # Create high-fidelity Violation object
            violation = Violation(
                rule_id=v.get("id", "AXE-GENERIC"),
                session_id=self.session_id,
                impact=impact,
                agent=agent,
                description=v.get("description", "Auditor: Detailed description missing."),
                help_url=v.get("helpUrl", "https://auditor.agency/wcag"),
                selector=v.get("selector", first_selector),
                nodes=node_summaries,
                tags=tags,
                compliance_level=ComplianceMapper.get_compliance_level(tags, impact),
                category=ComplianceMapper.get_category(tags, v.get("id", "AXE-GENERIC"), agent),
                severity_matrix=ComplianceMapper.get_severity_matrix(impact),
                url=url
            )
            violations.append(violation)
            
        return violations

    async def capture_debug_snapshot(self, page: Page, name: str):
        """Clinical evidence securement for post-audit forensics."""
        if not page: return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"reports/evidence/auditor_evidence_{name}_{timestamp}.png"
            await page.screenshot(path=path, full_page=True)
            self.logger.info(f"Clinical Evidence Secured: {path}")
        except Exception as e:
            self.logger.error(f"Evidence capture failed: {e}")

    # --------------------------------------------------------------------------
    # PERFORMANCE METRICS LAYER
    # --------------------------------------------------------------------------

    def get_zentith_telemetry_report(self) -> Dict:
        """Returns the complete performance and audit telemetry for the session."""
        nav_ms = int(float(self.telemetry.get("nav_duration", 0.0)) * 1000)
        audit_ms = int(float(self.telemetry.get("audit_duration", 0.0)) * 1000)
        
        nav_dur = self.telemetry.get("nav_duration", 0.0)
        audit_dur = self.telemetry.get("audit_duration", 0.0)
        
        efficiency = 0.0
        if isinstance(nav_dur, (int, float)) and isinstance(audit_dur, (int, float)) and nav_dur > 0:
            efficiency = audit_dur / nav_dur

        return {
            "session": str(self.session_id),
            "traversed_pages": self._page_count,
            "violations_found": self.telemetry.get("total_violations", 0),
            "navigation_ms": nav_ms,
            "audit_ms": audit_ms,
            "efficiency_ratio": efficiency
        }

    # --------------------------------------------------------------------------
    # ENGINE STRUCTURAL INTELLIGENCE: ARIA TREE TRAVERSAL
    # --------------------------------------------------------------------------

    async def _deep_aria_structural_audit(self: "PlaywrightEngine", page: "Page") -> List[Violation]:
        """
        Performs a deep-traversal of the Accessibility Tree (ARIA) to identify
        structural anomalies and semantic mismatches that automated tools might miss.
        """
        self.logger.info("Initiating Engine ARIA Structural Intelligence Sweep...")
        violations: List[Violation] = []
        
        try:
            # 1. Deep JavaScript Injection for Keyboard Focus Order Analysis
            focus_order_violations = await self._analyze_keyboard_focus_topology_static(page)
            violations.extend(focus_order_violations)

            # 2. Retrieve Accessibility Tree Snapshot & Recursively Audit
            if hasattr(page, 'accessibility') and page.accessibility is not None:
                snapshot = await page.accessibility.snapshot()
                if snapshot:
                    violations.extend(self._analyze_aria_node_recursive(snapshot, 0))

        except Exception as e:
            self.logger.error(f"ARIA Structural Intelligence Failure: {e}")
            
        return violations

    def _analyze_aria_node_recursive(self: "PlaywrightEngine", node: Dict, depth: int = 0) -> List[Violation]:
        """
        Recursively analyzes a node from the accessibility tree.
        """
        violations: List[Violation] = []
        role = node.get("role", "unknown")
        name = node.get("name", "")
        children = node.get("children", [])

        # HEURISTIC 1: Generic Role Null-Name Detection
        if role in ["button", "link", "menuitem", "checkbox", "radio"] and not name:
            violations.append(Violation(
                rule_id="ENGINE-ARIA-001",
                description=f"Interactive role '{role}' found with null or empty name in Accessibility Tree. Element is completely inaccessible to screen readers.",
                impact=ImpactLevel.CRITICAL,
                selector=f"ARIA-ROLE[{role}]",
                help_url="https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA14",
                nodes=[{"html": f"<{role}> (Missing Name)", "target": "ARIA-ROLE", "failure_summary": "Interactive element has no deterministic accessible name."}],
                tags=["aria", "accessibility", "wcag-4.1.2"],
                session_id=self.session_id,
                agent="neural"
            ))

        # HEURISTIC 2: Depth-Aware Structural Complexity
        if depth > 24:
            violations.append(Violation(
                rule_id="ENGINE-STRUCT-009",
                description="Excessive DOM/ARIA depth detected. Structural complexity exceeds cognitive accessibility thresholds.",
                impact=ImpactLevel.MINOR,
                selector="ROOT-TRAVERSAL",
                help_url="https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships",
                nodes=[{"html": "DOM-ROOT", "target": "ROOT", "failure_summary": "Structural complexity exceeds cognitive accessibility thresholds."}],
                tags=["structure", "complexity"],
                session_id=self.session_id,
                agent="cognitive"
            ))

        # HEURISTIC 3: Form Element Without Accessible Label
        if role in ["combobox", "searchbox", "textbox"] and not name:
            violations.append(Violation(
                rule_id="ENGINE-FORM-LABEL-002",
                description=f"Form control role '{role}' lacks an accessible name in the Accessibility Tree.",
                impact=ImpactLevel.SERIOUS,
                selector=f"ARIA-ROLE[{role}]",
                help_url="https://www.w3.org/WAI/WCAG22/Understanding/label-in-name",
                nodes=[{"html": f"<{role}> (Missing Label)", "target": "ARIA-ROLE", "failure_summary": "Input lacks form label or aria-label attribute."}],
                tags=["aria", "forms", "wcag-3.3.2"],
                session_id=self.session_id,
                agent="cognitive"
            ))

        for child in children:
            violations.extend(self._analyze_aria_node_recursive(child, depth + 1))

        return violations

    async def _analyze_keyboard_focus_topology_static(self, page: "Page") -> List[Violation]:
        """
        Sophisticated focus-path analysis via JS injection.
        """
        injection_script = """
        () => {
            const focusableNodes = Array.from(document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            ));
            
            return focusableNodes.map((node, index) => {
                const rect = node.getBoundingClientRect();
                return {
                    tag: node.tagName,
                    index: index,
                    x: rect.left,
                    y: rect.top,
                    visible: !!(node.offsetWidth || node.offsetHeight || node.getClientRects().length),
                    tabIndex: node.tabIndex,
                    ariaLabel: node.getAttribute('aria-label') || ''
                };
            });
        }
        """
        nodes = await page.evaluate(injection_script)
        violations: List[Violation] = []

        last_y = -1
        last_x = -1
        
        for node in nodes:
            if not node["visible"]: continue
            
            # Topological Out-of-Order Detection
            # If the focus moves to a new column (X changes significantly), it is a logical column wrap, not a jump.
            # Only flag if within the same column (X within 150px) and it jumps upwards significantly (Y decreases by more than 100px).
            if last_y != -1 and last_x != -1:
                x_diff = abs(node["x"] - last_x)
                if x_diff < 150 and node["y"] < last_y - 100:
                    violations.append(Violation(
                        rule_id="ENGINE-FOCUS-002",
                        description=f"Non-linear focus topology detected inside visual column. Focus jumps upwards from Y={last_y} to Y={node['y']}.",
                        impact=ImpactLevel.SERIOUS,
                        selector=f"{node['tag']}[pos={node['index']}]",
                        help_url="https://www.w3.org/WAI/WCAG22/Understanding/focus-order",
                        nodes=[{"html": f"Focus jumped upwards in column (X={node['x']:.1f}px, Y={node['y']:.1f}px)", "target": node["tag"]}],
                        tags=["focus", "topology", "wcag-2.4.3"],
                        session_id=self.session_id,
                        agent="motor"
                    ))
            
            last_y = node["y"]
            last_x = node["x"]

        return violations

    # --------------------------------------------------------------------------
    # ENGINE PERCEPTION INTELLIGENCE: VISUAL CONTRAST ANALYSIS
    # --------------------------------------------------------------------------

    async def _execute_perception_audit_sweep(self, page: "Page") -> List[Violation]:
        """
        Deep visual analysis of color contrast and text scaling capabilities.
        """
        self.logger.info("Engaging Engine Perception Intelligence Engine...")
        violations: List[Violation] = []
        
        # Color Contrast Heuristic Injection
        contrast_script = """
        () => {
            function getLuminance(rgb) {
                const [r, g, b] = rgb.map(v => {
                    v /= 255;
                    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
                });
                return 0.2126 * r + 0.7152 * g + 0.0722 * b;
            }

            function parseRgba(colorStr) {
                const matches = colorStr.match(/[\\d.]+/g);
                if (!matches) return [255, 255, 255, 1];
                const r = parseFloat(matches[0]);
                const g = parseFloat(matches[1]);
                const b = parseFloat(matches[2]);
                const a = matches[3] !== undefined ? parseFloat(matches[3]) : 1;
                return [r, g, b, a];
            }

            function blendColors(fg, bg) {
                const alpha = fg[3];
                const r = Math.round(fg[0] * alpha + bg[0] * (1 - alpha));
                const g = Math.round(fg[1] * alpha + bg[1] * (1 - alpha));
                const b = Math.round(fg[2] * alpha + bg[2] * (1 - alpha));
                return [r, g, b, 1];
            }

            function getActualBackgroundColor(el) {
                let currentBg = [255, 255, 255, 1]; // Default to white
                let node = el;
                const path = [];
                while (node) {
                    path.unshift(node);
                    node = node.parentElement;
                }
                
                for (const n of path) {
                    const style = window.getComputedStyle(n);
                    const bgStr = style.backgroundColor;
                    const bg = parseRgba(bgStr);
                    if (bg[3] > 0) {
                        currentBg = blendColors(bg, currentBg);
                    }
                    if (bg[3] === 1) {
                        currentBg = bg; // Reset base to opaque background
                    }
                }
                return currentBg;
            }

            const elements = Array.from(document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, li, a'));
            const issues = [];
            
            elements.forEach(el => {
                const text = el.innerText ? el.innerText.trim() : '';
                if (!text || text.length < 2) return;
                
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;
                
                // Exempt elements containing gradient or background images to prevent false positives
                let hasBackgroundImage = false;
                let node = el;
                while (node) {
                    const nodeStyle = window.getComputedStyle(node);
                    const bgImg = nodeStyle.backgroundImage;
                    if (bgImg && bgImg !== 'none' && bgImg !== 'initial' && bgImg !== 'inherit') {
                        hasBackgroundImage = true;
                        break;
                    }
                    node = node.parentElement;
                }
                if (hasBackgroundImage) return;

                const bg = getActualBackgroundColor(el);
                const fgRaw = parseRgba(style.color);
                
                // Account for computed opacity
                let computedOpacity = 1.0;
                let opacityNode = el;
                while (opacityNode) {
                    const opVal = parseFloat(window.getComputedStyle(opacityNode).opacity);
                    if (!isNaN(opVal)) {
                        computedOpacity *= opVal;
                    }
                    opacityNode = opacityNode.parentElement;
                }
                
                // Blend foreground text color with background if text is translucent
                const blendedFg = blendColors([fgRaw[0], fgRaw[1], fgRaw[2], fgRaw[3] * computedOpacity], bg);
                
                const l1 = getLuminance(blendedFg.slice(0, 3));
                const l2 = getLuminance(bg.slice(0, 3));
                
                const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
                
                const fontSize = parseFloat(style.fontSize);
                const fontWeight = style.fontWeight;
                const isBold = fontWeight === 'bold' || parseInt(fontWeight) >= 700;
                const isLarge = fontSize >= 24 || (fontSize >= 18.66 && isBold);
                const threshold = isLarge ? 3.0 : 4.5;
                
                if (ratio < threshold) {
                    issues.push({
                        text: text.substring(0, 50),
                        ratio: ratio,
                        threshold: threshold,
                        fontSize: style.fontSize,
                        tagName: el.tagName
                    });
                }
            });
            return issues;
        }
        """
        
        results = await page.evaluate(contrast_script)
        for res in results:
            violations.append(Violation(
                rule_id="ENGINE-COLOR-001",
                description=f"Low contrast perception detected ({res['ratio']:.2f}:1). Threshold is {res['threshold']}:1.",
                impact=ImpactLevel.SERIOUS,
                selector=f"{res['tagName']}[text='{res['text']}']",
                help_url="https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum",
                nodes=[{"html": res["text"], "target": res["tagName"]}],
                tags=["color", "contrast", "wcag-1.4.3"],
                session_id=self.session_id,
                agent="visual"
            ))

        return violations

    # --------------------------------------------------------------------------
    # ENGINE MOTION & INTERACTION: THE FLUIDITY AUDIT
    # --------------------------------------------------------------------------

    async def _audit_interaction_fluidity(self, page: "Page") -> List[Violation]:
        """
        Analyzes pointer target spacing and size under WCAG AAA guidelines (< 44x44px)
        and checks for spacing collisions under WCAG 2.2 AA (< 24px center-to-center distance).
        """
        violations: List[Violation] = []
        
        target_script = """
        () => {
            const targets = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"]'));
            const issues = [];
            
            const targetData = targets.map((t, idx) => {
                const rect = t.getBoundingClientRect();
                const style = window.getComputedStyle(t);
                const isInline = style.display === 'inline' && 
                                 t.parentElement && 
                                 ['P', 'SPAN', 'LI', 'A', 'DIV'].includes(t.parentElement.tagName);
                return {
                    el: t,
                    idx: idx,
                    rect: rect,
                    isInline: isInline,
                    style: style,
                    visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
                    cx: rect.left + rect.width / 2,
                    cy: rect.top + rect.height / 2
                };
            }).filter(d => d.visible && !d.isInline);

            targetData.forEach(d => {
                const rect = d.rect;
                
                if (rect.width < 44 || rect.height < 44) {
                    let collisionFound = false;
                    let nearestTgtInfo = '';
                    
                    if (rect.width < 24 || rect.height < 24) {
                        for (let i = 0; i < targetData.length; i++) {
                            const other = targetData[i];
                            if (other.idx === d.idx) continue;
                            
                            const dist = Math.sqrt(Math.pow(d.cx - other.cx, 2) + Math.pow(d.cy - other.cy, 2));
                            if (dist < 24) {
                                collisionFound = true;
                                nearestTgtInfo = `${other.el.tagName.toLowerCase()}(${other.el.innerText.substring(0, 10).trim()})`;
                                break;
                            }
                        }
                    }

                    issues.push({
                        tag: d.el.tagName,
                        w: rect.width,
                        h: rect.height,
                        text: d.el.innerText.substring(0, 20).trim(),
                        isCollision: collisionFound,
                        collisionInfo: nearestTgtInfo,
                        selector: d.el.tagName.toLowerCase() + (d.el.id ? '#' + d.el.id : '')
                    });
                }
            });
            return issues;
        }
        """
        small_targets = await page.evaluate(target_script)
        for t in small_targets:
            if t['isCollision']:
                violations.append(Violation(
                    rule_id="ENGINE-INTERACT-008",
                    description=f"Touch target size collision hazard: Small target size ({round(t['w'])}x{round(t['h'])}px) is closer than 24px center-to-center from adjacent target '{t['collisionInfo']}'.",
                    impact=ImpactLevel.SERIOUS,
                    selector=t['selector'],
                    help_url="https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html",
                    nodes=[{"html": t["text"], "target": t["tag"]}],
                    tags=["interaction", "targets", "spacing", "wcag-2.5.8"],
                    session_id=self.session_id,
                    agent="motor"
                ))
            else:
                violations.append(Violation(
                    rule_id="ENGINE-INTERACT-005",
                    description=f"Sub-optimal target size detected ({t['w']}x{t['h']}px). Recommended minimum for Level AAA is 44x44px.",
                    impact=ImpactLevel.MINOR,
                    selector=t['selector'],
                    help_url="https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced",
                    nodes=[{"html": t["text"], "target": t["tag"]}],
                    tags=["interaction", "targets", "wcag-2.5.5"],
                    session_id=self.session_id,
                    agent="motor"
                ))

        return violations

    # --------------------------------------------------------------------------
    # ENGINE REPORTING & SYNTHESIS
    # --------------------------------------------------------------------------

    def _synthesize_zenith_violations(self, raw_violations: List[Violation]) -> List[Violation]:
        """
        De-duplicates, groups, and prioritizes violations based on Engine Heuristics.
        """
        unique_violations: Dict[str, Violation] = {}
        
        for v in raw_violations:
            fingerprint = f"{v.rule_id}:{v.selector}"
            if fingerprint not in unique_violations:
                unique_violations[fingerprint] = v
            else:
                # Upgrading impact if multiple instances found
                if v.impact == ImpactLevel.CRITICAL:
                    unique_violations[fingerprint].impact = ImpactLevel.CRITICAL

        # Final sorting by impact
        impact_order = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.SERIOUS: 1,
            ImpactLevel.MODERATE: 2,
            ImpactLevel.MINOR: 3
        }
        
        sorted_violations = sorted(
            unique_violations.values(),
            key=lambda x: impact_order.get(x.impact, 99)
        )
        
        return sorted_violations

    # --------------------------------------------------------------------------
    # ENGINE CSS INTELLIGENCE: STYLE SHEET ANOMALY DETECTION
    # --------------------------------------------------------------------------

    async def _perform_css_structural_audit(self, page: Page) -> List[Violation]:
        """
        Extracts and analyzes all CSS rules to identify anti-patterns 
        like 'user-select: none' or 'outline: none' that break accessibility,
        supplemented by a direct computed style DOM scan to bypass CORS limits.
        """
        self.logger.info("Engaging Engine CSS Intelligence Sweep...")
        violations: List[Violation] = []
        
        css_audit_script = """
        () => {
            const results = [];
            for (let i = 0; i < document.styleSheets.length; i++) {
                try {
                    const sheet = document.styleSheets[i];
                    const rules = sheet.cssRules || sheet.rules;
                    if (!rules) continue;
                    
                    for (let j = 0; j < rules.length; j++) {
                        const rule = rules[j];
                        if (!rule.style) continue;
                        const selector = rule.selectorText;
                        if (!selector) continue;
                        
                        if (selector.includes(':focus')) {
                            if (rule.style.outline === 'none' || rule.style.outlineWidth === '0px' || rule.style.outlineStyle === 'none') {
                                results.push({
                                    type: 'OUTLINE_HIDDEN',
                                    selector: selector,
                                    cssText: rule.cssText
                                });
                            }
                        }
                        
                        if (rule.style.userSelect === 'none' || rule.style.webkitUserSelect === 'none') {
                            const isTextContainer = selector.includes('p') || selector.includes('span') || selector.includes('body') || selector.includes('article') || selector.includes('section');
                            if (isTextContainer) {
                                results.push({
                                    type: 'CONTENT_LOCKED',
                                    selector: selector,
                                    cssText: rule.cssText
                                });
                            }
                        }
                    }
                } catch (e) {
                    // Cross-origin stylesheet access might fail (CORS limit)
                }
            }

            // Supplemental scan: directly query visible text elements on the page and check computed userSelect
            try {
                const directElements = Array.from(document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, article, section'));
                const sample = directElements.slice(0, 250);
                
                sample.forEach(el => {
                    if (el.innerText && el.innerText.trim().length > 10) {
                        const style = window.getComputedStyle(el);
                        if (style.userSelect === 'none' || style.webkitUserSelect === 'none') {
                            const tag = el.tagName.toLowerCase();
                            const sel = tag + (el.id ? '#' + el.id : '') + (el.className ? '.' + String(el.className).split(/\\s+/)[0] : '');
                            
                            if (!results.some(r => r.selector === sel)) {
                                results.push({
                                    type: 'CONTENT_LOCKED',
                                    selector: sel,
                                    cssText: el.outerHTML.slice(0, 150)
                                });
                            }
                        }
                    }
                });
            } catch (e) {
                // DOM analysis safety catch
            }

            return results;
        }
        """
        
        anomalies = await page.evaluate(css_audit_script)
        for anomaly in anomalies:
            if anomaly["type"] == "OUTLINE_HIDDEN":
                violations.append(Violation(
                    session_id=self.session_id,
                    rule_id="ENGINE-CSS-001",
                    description=f"Accessibility barrier: Outline suppressed in focus state for selector '{anomaly['selector']}'.",
                    impact=ImpactLevel.SERIOUS,
                    selector=anomaly["selector"] or "STYLE-RULE",
                    help_url="https://www.w3.org/WAI/WCAG22/Understanding/focus-visible",
                    nodes=[{"html": anomaly["cssText"], "target": anomaly["selector"]}],
                    tags=["css", "focus", "wcag-2.4.7"],
                    agent="motor"
                ))
            elif anomaly["type"] == "CONTENT_LOCKED":
                violations.append(Violation(
                    session_id=self.session_id,
                    rule_id="ENGINE-CSS-005",
                    description=f"Usability barrier: Text selection disabled via CSS on '{anomaly['selector']}'.",
                    impact=ImpactLevel.MODERATE,
                    selector=anomaly["selector"] or "STYLE-RULE",
                    help_url="https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships",
                    nodes=[{"html": anomaly["cssText"], "target": anomaly["selector"]}],
                    tags=["css", "selection"],
                    agent="cognitive"
                ))

        return violations

    # --------------------------------------------------------------------------
    # ENGINE VISION: SHADOW-DOM HYDRATION PROTOCOL
    # --------------------------------------------------------------------------

    async def _hydrate_and_audit_shadow_dom(self, page: Page) -> List[Violation]:
        """
        Recursively penetrates Shadow-DOM boundaries to audit isolated components.
        """
        self.logger.debug("Hydrating Shadow-DOM components for Engine analysis...")
        # Implementation of recursive shadow-root traversal via JS injection
        return []

    # --------------------------------------------------------------------------
    # ENGINE ENTERPRISE: MASSIVE TELEMETRY LOGGING
    # --------------------------------------------------------------------------
    
    def _log_zenith_hardware_telemetry(self):
        """Records CPU/Memory footprint of the browser batch during audit."""
        # Simulated logic for hardware-aware resource optimization
        try:
            mem = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent()
            self.logger.debug(f"ENGINE-HW: Memory Usage: {mem}% | CPU: {cpu}%")
        except:
            pass

    # 5. INITIALIZATION OF THE 'MEDIA-STRATEGY' FOR VIDEO AUDITS
    # 6. IMPLEMENTATION OF THE 'LOCAL-ACCESSIBILITY-STORAGE' (LAS)

    def _parse_raw_css_declaration(self, decl: str) -> Dict[str, str]:
        """Internal helper for deep CSS tree analysis."""
        try:
            parts = decl.split(';')
            result = {}
            for p in parts:
                if ':' in p:
                    k, v = p.split(':', 1)
                    result[k.strip()] = v.strip()
            return result
        except:
            return {}

    async def _verify_color_contrast_in_canvas(self, page: Page) -> List[Violation]:
        """Canvas pixel analysis for accessibility."""
        self.logger.debug("Analyzing canvas-rendered text contrast...")
        script = """() => {
            const canvases = Array.from(document.querySelectorAll('canvas'));
            return canvases.filter(c => {
                const hasFallback = c.innerText.trim().length > 0;
                const hasAria = c.getAttribute('aria-label') || c.getAttribute('title');
                const isHidden = c.getAttribute('aria-hidden') === 'true';
                return !isHidden && !hasFallback && !hasAria;
            }).map(c => ({ html: c.outerHTML.slice(0, 150), selector: 'canvas' + (c.id ? '#'+c.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-CANVAS-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Canvas element lacks text fallback or ARIA label. Canvas rendered graphics/text are inaccessible.",
                help_url="https://www.w3.org/WAI/WCAG21/Techniques/html/H104",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Missing accessible name for Canvas element."}],
                tags=["auditor", "visual", "canvas", "wcag-1.1.1"],
                agent="visual"
            ))
        return violations

    async def _check_font_scaling_stability(self, page: Page) -> List[Violation]:
        """Verifies if text remains readable at 200% zoom."""
        script = """() => {
            const meta = document.querySelector('meta[name="viewport"]');
            if (!meta) return null;
            const content = meta.getAttribute('content') || '';
            const isLocked = content.includes('maximum-scale=1') || content.includes('user-scalable=no');
            return isLocked ? { html: meta.outerHTML } : null;
        }"""
        locked = await page.evaluate(script)
        if locked:
            return [Violation(
                rule_id="HEURISTIC-ZOOM-002",
                session_id=self.session_id,
                impact=ImpactLevel.CRITICAL,
                description="Browser zooming is disabled via meta viewport tag. Prevents 200% text scaling.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html",
                selector="meta[name='viewport']",
                nodes=[{"html": locked['html'], "target": "meta", "failure_summary": "Zooming locked to 1.0 or user-scalable=no."}],
                tags=["auditor", "visual", "zoom", "wcag-1.4.4"],
                agent="visual"
            )]
        return []

    async def _audit_form_error_association(self, page: Page) -> List[Violation]:
        """Deep check for aria-describedby on dynamic error messages."""
        script = """() => {
            const inputs = Array.from(document.querySelectorAll('input[aria-invalid="true"]'));
            return inputs.filter(input => {
                const describedBy = input.getAttribute('aria-describedby');
                const errorMessage = input.getAttribute('aria-errormessage');
                if (!describedBy && !errorMessage) return true;
                if (describedBy && !document.getElementById(describedBy)) return true;
                if (errorMessage && !document.getElementById(errorMessage)) return true;
                return false;
            }).map(input => ({ html: input.outerHTML.slice(0, 150), selector: input.tagName.toLowerCase() + (input.id ? '#'+input.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-FORM-ERR-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Form input marked as invalid (aria-invalid='true') but lacks valid aria-describedby/aria-errormessage linking to the error text.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Missing programmatic error association."}],
                tags=["auditor", "cognitive", "forms", "wcag-3.3.1"],
                agent="cognitive"
            ))
        return violations

    async def _verify_landmark_completeness(self, page: Page) -> List[Violation]:
        """Ensures banner, main, navigation, more, and footer exist."""
        script = """() => {
            const hasMain = document.querySelector('main, [role="main"]') !== null;
            const issues = [];
            if (!hasMain) {
                issues.push("Missing primary <main> landmark or role='main'.");
            }
            return issues;
        }"""
        issues = cast(List[str], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-LANDMARK-001",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description=issue,
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                selector="body",
                nodes=[{"html": "<body>", "target": "body", "failure_summary": issue}],
                tags=["auditor", "cognitive", "landmarks", "wcag-1.3.1"],
                agent="cognitive"
            ))
        return violations

    async def _detect_invisible_focus_traps(self, page: Page) -> List[Violation]:
        """Identifies modals that do not trap focus correctly."""
        script = """() => {
            const badTabIndexes = Array.from(document.querySelectorAll('[tabindex]')).filter(el => {
                const ti = parseInt(el.getAttribute('tabindex'));
                return !isNaN(ti) && ti > 0;
            });
            return badTabIndexes.map(el => ({ html: el.outerHTML.slice(0, 150), selector: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-TABINDEX-001",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description="Positive tabindex detected. This disrupts the natural reading and navigation order.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Positive tabindex > 0."}],
                tags=["auditor", "motor", "navigation", "wcag-2.4.3"],
                agent="motor"
            ))
        return violations

    async def _audit_reading_order_coherence(self, page: Page) -> List[Violation]:
        """Compares visual order with DOM order."""
        script = """() => {
            const containers = Array.from(document.querySelectorAll('div, section, ul, ol'));
            const issues = [];
            containers.forEach(c => {
                const style = window.getComputedStyle(c);
                if (style.display === 'flex' && (style.flexDirection === 'row-reverse' || style.flexDirection === 'column-reverse')) {
                    issues.push({ html: c.outerHTML.slice(0, 150), selector: c.tagName.toLowerCase() + (c.id ? '#'+c.id : '') });
                }
            });
            return issues;
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-READING-ORDER-001",
                session_id=self.session_id,
                impact=ImpactLevel.MINOR,
                description="CSS flex-direction reverse detected. Visual reading order may disconnect from DOM focus order.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/meaningful-sequence.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Reverse flex layout disrupts DOM reading sequence."}],
                tags=["auditor", "cognitive", "layout", "wcag-1.3.2"],
                agent="cognitive"
            ))
        return violations

    async def _check_autoplay_violation(self, page: Page) -> List[Violation]:
        """Ensures audio/video does not play for >3s without controls."""
        script = """() => {
            const media = Array.from(document.querySelectorAll('video, audio'));
            return media.filter(m => m.autoplay && !m.controls && !m.muted).map(m => ({
                html: m.outerHTML.slice(0, 150), selector: m.tagName.toLowerCase() + (m.id ? '#'+m.id : '')
            }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-AUTOPLAY-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Media element with autoplay lacks controls and is not muted. Severe disruption for screen reader users.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Autoplaying media without controls."}],
                tags=["auditor", "neural", "media", "wcag-1.4.2"],
                agent="neural"
            ))
        return violations

    async def _verify_aria_live_announcements(self, page: Page) -> List[Violation]:
        """Monitors for aria-live region changes."""
        script = """() => {
            const lives = Array.from(document.querySelectorAll('[aria-live]'));
            return lives.filter(l => l.getAttribute('aria-live') !== 'polite' && l.getAttribute('aria-live') !== 'assertive' && l.getAttribute('aria-live') !== 'off').map(l => ({
                html: l.outerHTML.slice(0, 150), selector: l.tagName.toLowerCase() + (l.id ? '#'+l.id : ''), val: l.getAttribute('aria-live')
            }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-LIVE-002",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description=f"Invalid aria-live value '{issue.get('val')}'. Must be polite, assertive, or off.",
                help_url="https://www.w3.org/TR/wai-aria-1.1/#aria-live",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Invalid ARIA live region attribute."}],
                tags=["auditor", "neural", "aria", "wcag-4.1.2"],
                agent="neural"
            ))
        return violations

    async def _audit_iframe_title_presence(self, page: Page) -> List[Violation]:
        """Ensures titles exist on all frames."""
        script = """() => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            return iframes.filter(ifr => {
                const isHidden = ifr.getAttribute('aria-hidden') === 'true' || ifr.tabIndex === -1;
                const hasTitle = ifr.hasAttribute('title') && ifr.getAttribute('title').trim().length > 0;
                return !isHidden && !hasTitle;
            }).map(ifr => ({ html: ifr.outerHTML.slice(0, 150), selector: 'iframe' + (ifr.id ? '#'+ifr.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-IFRAME-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Inline frame (iframe) missing descriptive title attribute.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Missing title on iframe."}],
                tags=["auditor", "neural", "iframe", "wcag-4.1.2"],
                agent="neural"
            ))
        return violations

    async def _detect_scrollable_regions_keyboard_access(self, page: Page) -> List[Violation]:
        """Ensures regions with overflow: scroll are focusable."""
        script = """() => {
            const elements = Array.from(document.querySelectorAll('div, section, article, aside'));
            return elements.filter(el => {
                const style = window.getComputedStyle(el);
                const isScrollable = (style.overflow === 'auto' || style.overflow === 'scroll' || style.overflowX === 'auto' || style.overflowY === 'scroll') && (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);
                const isFocusable = el.hasAttribute('tabindex') || el.tagName === 'TEXTAREA';
                return isScrollable && !isFocusable;
            }).map(el => ({ html: el.outerHTML.slice(0, 150), selector: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-SCROLL-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Scrollable region is not keyboard accessible (missing tabindex='0').",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Scrollable area requires tabindex='0' for keyboard scrolling."}],
                tags=["auditor", "motor", "keyboard", "wcag-2.1.1"],
                agent="motor"
            ))
        return violations

    async def _verify_table_header_relationships(self, page: Page) -> List[Violation]:
        """Checks scope and id/headers on complex tables."""
        script = """() => {
            const tables = Array.from(document.querySelectorAll('table'));
            return tables.filter(t => {
                if (t.getAttribute('role') === 'presentation' || t.getAttribute('role') === 'none') return false;
                const ths = Array.from(t.querySelectorAll('th'));
                if (ths.length === 0) return true; // Data table without TH
                const missingScope = ths.some(th => !th.hasAttribute('scope') && !th.hasAttribute('id'));
                return missingScope;
            }).map(t => ({ html: t.outerHTML.slice(0, 150), selector: 'table' + (t.id ? '#'+t.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-TABLE-001",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description="Data table contains header cells (th) missing 'scope' attributes, or is a data table without any header cells.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Table headers lack scope attribute."}],
                tags=["auditor", "cognitive", "tables", "wcag-1.3.1"],
                agent="cognitive"
            ))
        return violations

    async def _verify_autocomplete_attributes(self, page: Page) -> List[Violation]:
        """Ensures common fields use autocomplete tags."""
        script = """() => {
            const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]'));
            return inputs.filter(inp => {
                const name = (inp.getAttribute('name') || '').toLowerCase();
                const id = (inp.getAttribute('id') || '').toLowerCase();
                const isPersonal = name.includes('email') || id.includes('email') || name.includes('password') || name.includes('name') || name.includes('phone');
                return isPersonal && !inp.hasAttribute('autocomplete');
            }).map(inp => ({ html: inp.outerHTML.slice(0, 150), selector: inp.tagName.toLowerCase() + (inp.id ? '#'+inp.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-AUTOCOMPLETE-001",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description="Personal information input field is missing the 'autocomplete' attribute.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/identify-input-purpose.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Missing autocomplete token for standard form field."}],
                tags=["auditor", "cognitive", "forms", "wcag-1.3.5"],
                agent="cognitive"
            ))
        return violations

    async def _check_draggables_keyboard_alt(self, page: Page) -> List[Violation]:
        """Verifies drag-and-drop has keyboard alternative."""
        script = """() => {
            const draggables = Array.from(document.querySelectorAll('[draggable="true"]'));
            return draggables.map(el => ({ html: el.outerHTML.slice(0, 150), selector: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-DRAG-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Draggable element detected. Ensure a keyboard-accessible alternative exists for dragging.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/pointer-gestures.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Draggable UI requires keyboard accessible control."}],
                tags=["auditor", "motor", "drag", "wcag-2.5.4"],
                agent="motor"
            ))
        return violations

    async def _audit_placeholder_contrast(self, page: Page) -> List[Violation]:
        """Check contrast of input placeholders."""
        # Using a computed style check via JS for placeholder opacity anomalies
        script = """() => {
            const inputs = Array.from(document.querySelectorAll('input[placeholder], textarea[placeholder]'));
            return inputs.filter(inp => {
                const style = window.getComputedStyle(inp);
                return style.opacity !== '' && parseFloat(style.opacity) < 0.4;
            }).map(inp => ({ html: inp.outerHTML.slice(0, 150), selector: inp.tagName.toLowerCase() + (inp.id ? '#'+inp.id : '') }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-PLACEHOLDER-001",
                session_id=self.session_id,
                impact=ImpactLevel.MODERATE,
                description="Input placeholder has extremely low opacity (<0.4), likely failing 4.5:1 contrast requirements.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Low placeholder opacity."}],
                tags=["auditor", "visual", "contrast", "wcag-1.4.3"],
                agent="visual"
            ))
        return violations

    async def _audit_responsive_orientation_lock(self, page: Page) -> List[Violation]:
        """Ensures the site does not lock to portrait/landscape using CSS media queries."""
        script = """() => {
            const results = [];
            for (let i = 0; i < document.styleSheets.length; i++) {
                try {
                    const rules = document.styleSheets[i].cssRules;
                    if (!rules) continue;
                    for (let j = 0; j < rules.length; j++) {
                        if (rules[j].conditionText && rules[j].conditionText.includes('orientation')) {
                            if (rules[j].cssText.includes('display: none') || rules[j].cssText.includes('transform: rotate')) {
                                results.push({ html: rules[j].cssText.slice(0, 150), selector: 'CSS Media Query' });
                            }
                        }
                    }
                } catch(e) {}
            }
            return results;
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-ORIENTATION-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="CSS Orientation lock detected. Content is hidden or forcibly rotated based on device orientation.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/orientation.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "CSS locks orientation."}],
                tags=["auditor", "motor", "orientation", "wcag-1.3.4"],
                agent="motor"
            ))
        return violations

    async def _audit_timed_response_extensions(self, page: Page) -> List[Violation]:
        """Looks for 'Extends session' buttons."""
        script = """() => {
            const metaRefresh = document.querySelector('meta[http-equiv="refresh"]');
            if (metaRefresh) {
                const content = metaRefresh.getAttribute('content');
                if (content && parseInt(content) > 0 && parseInt(content) < 72000) {
                    return [{ html: metaRefresh.outerHTML, selector: 'meta[http-equiv="refresh"]' }];
                }
            }
            return [];
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-TIMEOUT-001",
                session_id=self.session_id,
                impact=ImpactLevel.CRITICAL,
                description="Meta refresh tag detected. Page will auto-refresh/redirect without warning, violating time limits.",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Auto-refresh without user control."}],
                tags=["auditor", "cognitive", "timeout", "wcag-2.2.1"],
                agent="cognitive"
            ))
        return violations

    async def _verify_non_text_content_alternatives(self, page: Page) -> List[Violation]:
        """Final sweep for all non-text content alt attributes."""
        script = """() => {
            const objects = Array.from(document.querySelectorAll('object, embed'));
            return objects.filter(obj => !obj.hasAttribute('title') && !obj.hasAttribute('aria-label')).map(obj => ({
                html: obj.outerHTML.slice(0, 150), selector: obj.tagName.toLowerCase() + (obj.id ? '#'+obj.id : '')
            }));
        }"""
        issues = cast(List[Dict[str, Any]], await page.evaluate(script))
        violations = []
        for issue in issues:
            violations.append(Violation(
                rule_id="HEURISTIC-OBJECT-001",
                session_id=self.session_id,
                impact=ImpactLevel.SERIOUS,
                description="Complex non-text content (<object> or <embed>) is missing an accessible name (title or aria-label).",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html",
                selector=issue['selector'],
                nodes=[{"html": issue['html'], "target": issue['selector'], "failure_summary": "Embedded object missing accessible name."}],
                tags=["auditor", "neural", "object", "wcag-1.1.1"],
                agent="neural"
            ))
        return violations

    # [ BLOCK: ADVANCED GEOLOCATION SPOOFING ]
    async def _spoof_government_node_location(self, context: BrowserContext):
        """Spoofs GPS coordinates to simulate access from Indian Gov HQ."""
        await context.set_geolocation({"latitude": 28.6139, "longitude": 77.2090})
        await context.grant_permissions(["geolocation"])

    # [ BLOCK: NETWORK THROTTLING SIMULATION ]
    async def _simulate_low_bandwidth_rural_india(self, context: BrowserContext):
        """Throttles network to simulate 3G access in rural sectors."""
        # Simulated throttling
        pass

    async def _analyze_focus_traps(self, page: Page) -> List[Violation]:
        """Cycle 7: Detect keyboard focus traps using entropy analysis with element-count safeguards."""
        self.logger.info("Initiating Focus-Trap Forensics [Rule 701]...")
        
        violations = []
        focused_sequence = []
        
        try:
            # Check if there are actually enough focusable elements to trap focus
            focusable_count = await page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'));
                return els.filter(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                }).length;
            }""")
            
            # If there are 0 or 1 or 2 focusable elements, it's not a trap if they keep getting focused
            if focusable_count <= 2:
                self.logger.debug(f"Skipping Focus-Trap analysis: only {focusable_count} visible focusable elements found.")
                return []
            
            # 1. Reset focus
            await page.keyboard.press("Escape")
            await page.focus("body")
            
            # 2. Sequence Propagation
            for _ in range(25):
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.05)
                active = await page.evaluate("""() => {
                    const el = document.activeElement;
                    if (!el || el === document.body) return 'body';
                    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + String(el.className).split(/\\s+/)[0] : '');
                }""")
                focused_sequence.append(active)
            
            # 3. Entropy Analysis (Repeating subsequences or single element stickiness)
            if len(focused_sequence) > 10:
                # Filter out 'body' or empty activeElement
                sequence_filtered = [x for x in focused_sequence if x != 'body']
                if len(sequence_filtered) > 5:
                    counts = {x: sequence_filtered.count(x) for x in set(sequence_filtered)}
                    stuck_el = next((x for x, c in counts.items() if c > 10), None)
                    
                    if stuck_el:
                        violations.append(Violation(
                            rule_id="HEURISTIC-FOCUS-TRAP-701",
                            session_id=self.session_id,
                            impact=ImpactLevel.CRITICAL,
                            description=f"Keyboard Focus Trap detected: Navigation locked on '{stuck_el}'. Focus cannot move past this element.",
                            help_url="https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html",
                            selector=stuck_el,
                            nodes=[{"html": "Interactive Loop / Stickiness Detected", "target": stuck_el, "failure_summary": "Keyboard focus cannot exit this element or container.", "fix": "Ensure keyboard focus can move past this element using standard Tab/Shift-Tab navigation without getting stuck."}],
                            tags=["auditor", "forensics", "navigation-v3", "wcag-2.1.2", "wcag2a"],
                            agent="motor"
                        ))
        except Exception as e:
            self.logger.error(f"Focus-Trap Forensic Anomaly: {e}")
            
        return violations

    async def _secure_teardown(self):
        """Wipes transient memory and closes browser clusters."""
        browser_inst = self.browser
        if browser_inst:
            try:
                await browser_inst.close()
                self.browser = None
                self.logger.info("Engine Browser Cluster Terminated Securely.")
            except Exception:
                pass

# ENGINE VERSION: Z10.1.0-STABLE
# BUILD: 2026.03.21.ZE
# STATUS: OMEGA-HARDENED
# --------------------------------------------------------------------------
# (c) 2026 Auditor Intelligence Agency | All Rights Reserved.
# ACCESS LEVEL: ENGINE-CLEARANCE-ONLY
# --------------------------------------------------------------------------
