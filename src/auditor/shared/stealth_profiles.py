"""
STEALTH PROFILE REPOSITORY: THE POLYMORPHIC LEDGER
================================================

This module provides high-fidelity hardware and browser profiles to ensure
that the Accessibility Auditor remains invisible to enterprise bot-detection.
Each profile is a coherent set of User-Agent, Viewport, and Hardware attributes.
"""

import random
from typing import Dict, Any, List

# High-Entropy User Agents (Updated for 2024/2026 realistic patterns)
DEVICE_PROFILES: List[Dict[str, Any]] = [
    {
        "name": "Desktop-Windows-Chrome",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "hardware": {
            "deviceMemory": 16,
            "hardwareConcurrency": 8,
            "platform": "Win32",
            "vendor": "Google Inc.",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        },
        "clientHints": {
            "platform": "Windows",
            "platformVersion": "10.0.0",
            "architecture": "x86",
            "model": "",
            "uaFullVersion": "121.0.6167.85"
        }
    },
    {
        "name": "Desktop-Mac-Safari",
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "viewport": {"width": 1440, "height": 900},
        "hardware": {
            "deviceMemory": 8,
            "hardwareConcurrency": 4,
            "platform": "MacIntel",
            "vendor": "Apple Inc.",
            "renderer": "Apple GPU",
        },
        "clientHints": {
            "platform": "macOS",
            "platformVersion": "14.2.1",
            "architecture": "arm",
            "model": "",
            "uaFullVersion": "17.2"
        }
    },
    {
        "name": "Desktop-Linux-Firefox",
        "userAgent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "viewport": {"width": 1366, "height": 768},
        "hardware": {
            "deviceMemory": 32,
            "hardwareConcurrency": 12,
            "platform": "Linux x86_64",
            "vendor": "Intel Open Source Technology Center",
            "renderer": "Mesa Intel(R) UHD Graphics 620 (KBL GT2)",
        },
        "clientHints": {
            "platform": "Linux",
            "platformVersion": "",
            "architecture": "x86",
            "model": "",
            "uaFullVersion": "122.0"
        }
    },
    {
        "name": "Mobile-iPhone-Chrome",
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/123.0.6312.52 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 393, "height": 852}, # iPhone 15 Pro
        "hardware": {
            "deviceMemory": 8,
            "hardwareConcurrency": 6,
            "platform": "iPhone",
            "vendor": "Apple Inc.",
            "renderer": "Apple GPU",
        },
        "clientHints": {
            "platform": "iOS",
            "platformVersion": "17.4.1",
            "architecture": "arm",
            "model": "iPhone15,2",
            "uaFullVersion": "123.0.6312.52"
        }
    }
]

class StealthProfileGenerator:
    """Generates polymorphic browser footprints."""
    
    @staticmethod
    def get_all_profiles() -> List[Dict[str, Any]]:
        """Returns the full list of available device profiles."""
        return DEVICE_PROFILES

    @staticmethod
    def get_random_profile() -> Dict[str, Any]:
        """Returns a randomized but coherent device profile."""
        profile = random.choice(DEVICE_PROFILES)
        # Add slight jitter to viewport for organic variance
        profile = profile.copy()
        profile["viewport"] = {
            "width": profile["viewport"]["width"] + random.randint(-20, 20),
            "height": profile["viewport"]["height"] + random.randint(-20, 20)
        }
        return profile
