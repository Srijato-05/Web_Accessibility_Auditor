"""
STEALTH PROTOCOL: THE ZENITH PHANTOM
====================================

This module provides the low-level Javascript injection layer for the 
Accessibility Auditor. It is designed to neutralize advanced bot-detection 
signals by injecting entropy and normalizing browser API fingerprints.
"""

from typing import Dict, Any

class StealthProtocol:
    """Core Evasion Logic for the Auditor Engine."""
    
    @staticmethod
    def get_injection_script(profile: Dict[str, Any]) -> str:
        """Generates the high-fidelity JS payload for browser injection."""
        hardware = profile.get("hardware", {})
        hints = profile.get("clientHints", {})
        
        return f"""
        (() => {{
            // 1. Webdriver Detection Neutralization
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;

            // 2. Hardware API Spoofing
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {hardware.get('deviceMemory', 8)} }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hardware.get('hardwareConcurrency', 4)} }});
            Object.defineProperty(navigator, 'platform', {{ get: () => '{hardware.get('platform', 'Win32')}' }});

            // 3. WebGL Spoofing (Deep Layer)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) return '{hardware.get('vendor', 'Google Inc.')}';
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) return '{hardware.get('renderer', 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)')}';
                return getParameter.apply(this, arguments);
            }};

            // 4. Canvas Entropy Injection (The Ghost Pixel)
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {{
                const imageData = originalGetImageData.apply(this, arguments);
                // Inject 1-bit noise into the first pixel to break cryptographic hash consistency
                imageData.data[0] = (imageData.data[0] + (Math.random() > 0.5 ? 1 : -1)) % 256;
                return imageData;
            }};

            // 5. Client Hints Normalization (UserAgentData)
            if (navigator.userAgentData) {{
                const originalGetHighEntropyValues = navigator.userAgentData.getHighEntropyValues;
                navigator.userAgentData.getHighEntropyValues = function(hints) {{
                    return Promise.resolve({{
                        platform: '{hints.get('platform', 'Windows')}',
                        platformVersion: '{hints.get('platformVersion', '10.0.0')}',
                        architecture: '{hints.get('architecture', 'x86')}',
                        model: '{hints.get('model', '')}',
                        uaFullVersion: '{hints.get('uaFullVersion', '')}'
                    }});
                }};
            }}

            // 6. Chrome Runtime Simulation
            if (!window.chrome) {{
                window.chrome = {{
                    runtime: {{
                        id: 'nkbihfbeogaeaoehlefnkodbefgpgknn', // Metamask ID simulation
                        getURL: (s) => 'chrome-extension://' + s
                    }},
                    loadTimes: () => ({{}})
                }};
            }}

            // 7. Permission Normalization
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
            );

            // 8. WebRTC Sanitization (Anti-Leak)
            if (window.RTCPeerConnection) {{
                const originalCreateOffer = RTCPeerConnection.prototype.createOffer;
                RTCPeerConnection.prototype.createOffer = function() {{
                    return Promise.resolve({{ sdp: 'v=0\\r\\no=- 12345 67890 IN IP4 127.0.0.1\\r\\ns=-\\r\\nt=0 0\\r\\n' }});
                }};
            }}

            // 9. Timezone & Locale Normalization
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
                return {{
                    locale: 'en-US',
                    calendar: 'gregory',
                    numberingSystem: 'latn',
                    timeZone: 'UTC',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                }};
            }};
        }})();
        """
