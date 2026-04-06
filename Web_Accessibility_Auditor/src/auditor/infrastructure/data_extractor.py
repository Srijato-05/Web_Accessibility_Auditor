"""
DATA EXTRACTION LAYER
======================

Playwright-based extraction of structured DOM, CSS, and screenshot data
from a live browser page. This runs WHILE the page is still open, before
the browser closes.

Produces a PageData object consumed by all accessibility agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from auditor.shared.logging import auditor_logger

logger = auditor_logger.getChild("DataExtractor")


@dataclass
class ElementData:
    """Structured representation of a single DOM element with computed styles."""

    tag: str
    selector: str
    html: str
    text: str
    computed_styles: Dict[str, str]
    attributes: Dict[str, str]
    bounding_box: Dict[str, float]
    parent_styles: Dict[str, str]


@dataclass
class PageData:
    """All extracted data from a single page, ready for agent analysis."""

    url: str
    links: List[ElementData]
    text_elements: List[ElementData]
    form_elements: List[ElementData]
    images: List[ElementData]
    screenshot: Optional[bytes]
    session_id: UUID


# --------------------------------------------------------------------------
# EXTRACTION SCRIPTS (JavaScript executed in the browser context)
# --------------------------------------------------------------------------

EXTRACT_LINKS_JS = """() => {
    const links = Array.from(document.querySelectorAll('a'));
    return links.slice(0, 200).map(el => {
        const style = window.getComputedStyle(el);
        const parent = el.parentElement;
        const parentStyle = parent ? window.getComputedStyle(parent) : {};
        const rect = el.getBoundingClientRect();
        return {
            tag: el.tagName.toLowerCase(),
            html: el.outerHTML.slice(0, 300),
            text: (el.innerText || '').slice(0, 200),
            selector: el.tagName.toLowerCase()
                + (el.id ? '#' + el.id : '')
                + (el.className && typeof el.className === 'string'
                   ? '.' + el.className.trim().split(/\\s+/).join('.') : ''),
            computedStyles: {
                color: style.color,
                backgroundColor: style.backgroundColor,
                textDecoration: style.textDecoration,
                textDecorationLine: style.textDecorationLine || '',
                fontWeight: style.fontWeight,
                borderBottomWidth: style.borderBottomWidth,
                borderBottomStyle: style.borderBottomStyle,
                borderBottomColor: style.borderBottomColor,
                borderColor: style.borderColor,
                outlineWidth: style.outlineWidth,
                display: style.display
            },
            attributes: {
                href: el.getAttribute('href') || '',
                role: el.getAttribute('role') || '',
                ariaLabel: el.getAttribute('aria-label') || ''
            },
            boundingBox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
            parentStyles: {
                color: parentStyle.color || '',
                backgroundColor: parentStyle.backgroundColor || '',
                textDecoration: parentStyle.textDecoration || '',
                fontWeight: parentStyle.fontWeight || ''
            }
        };
    });
}"""

EXTRACT_TEXT_ELEMENTS_JS = """() => {
    const elements = Array.from(document.querySelectorAll(
        'p, span, li, td, th, label, strong, em, mark, ins, del, .text-danger, .text-success, .text-warning, .error, .success, .warning, [class*="status"], [class*="alert"]'
    ));
    return elements.slice(0, 300).map(el => {
        const style = window.getComputedStyle(el);
        const parent = el.parentElement;
        const parentStyle = parent ? window.getComputedStyle(parent) : {};
        const rect = el.getBoundingClientRect();
        return {
            tag: el.tagName.toLowerCase(),
            html: el.outerHTML.slice(0, 300),
            text: (el.innerText || '').slice(0, 200),
            selector: el.tagName.toLowerCase()
                + (el.id ? '#' + el.id : '')
                + (el.className && typeof el.className === 'string'
                   ? '.' + el.className.trim().split(/\\s+/).join('.') : ''),
            computedStyles: {
                color: style.color,
                backgroundColor: style.backgroundColor,
                textDecoration: style.textDecoration,
                fontWeight: style.fontWeight,
                borderColor: style.borderColor,
                borderBottomColor: style.borderBottomColor,
                borderBottomWidth: style.borderBottomWidth,
                outlineWidth: style.outlineWidth,
                display: style.display
            },
            attributes: {
                role: el.getAttribute('role') || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                className: el.className && typeof el.className === 'string' ? el.className : ''
            },
            boundingBox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
            parentStyles: {
                color: parentStyle.color || '',
                backgroundColor: parentStyle.backgroundColor || '',
                textDecoration: parentStyle.textDecoration || '',
                fontWeight: parentStyle.fontWeight || ''
            }
        };
    });
}"""

EXTRACT_FORM_ELEMENTS_JS = """() => {
    const elements = Array.from(document.querySelectorAll(
        'input, select, textarea, [role="textbox"], [role="combobox"], [role="listbox"]'
    ));
    return elements.slice(0, 150).map(el => {
        const style = window.getComputedStyle(el);
        const parent = el.parentElement;
        const parentStyle = parent ? window.getComputedStyle(parent) : {};
        const rect = el.getBoundingClientRect();

        // Check for nearby error/success text
        const siblingText = Array.from(parent ? parent.children : [])
            .filter(c => c !== el)
            .map(c => (c.innerText || '').trim().slice(0, 100))
            .join(' ');

        return {
            tag: el.tagName.toLowerCase(),
            html: el.outerHTML.slice(0, 300),
            text: siblingText,
            selector: el.tagName.toLowerCase()
                + (el.id ? '#' + el.id : '')
                + (el.name ? '[name="' + el.name + '"]' : ''),
            computedStyles: {
                color: style.color,
                backgroundColor: style.backgroundColor,
                borderColor: style.borderColor,
                borderBottomColor: style.borderBottomColor,
                borderWidth: style.borderWidth,
                outlineColor: style.outlineColor,
                outlineWidth: style.outlineWidth,
                boxShadow: style.boxShadow
            },
            attributes: {
                type: el.getAttribute('type') || '',
                name: el.getAttribute('name') || '',
                required: el.hasAttribute('required') ? 'true' : '',
                ariaInvalid: el.getAttribute('aria-invalid') || '',
                ariaRequired: el.getAttribute('aria-required') || '',
                ariaDescribedby: el.getAttribute('aria-describedby') || '',
                className: el.className && typeof el.className === 'string' ? el.className : ''
            },
            boundingBox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
            parentStyles: {
                color: parentStyle.color || '',
                backgroundColor: parentStyle.backgroundColor || ''
            }
        };
    });
}"""

EXTRACT_IMAGES_JS = """() => {
    const images = Array.from(document.querySelectorAll('img, svg, canvas, [role="img"]'));
    return images.slice(0, 100).map(el => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();

        // Check for figcaption
        const figure = el.closest('figure');
        const hasFigcaption = figure ? !!figure.querySelector('figcaption') : false;

        return {
            tag: el.tagName.toLowerCase(),
            html: el.outerHTML.slice(0, 300),
            text: '',
            selector: el.tagName.toLowerCase()
                + (el.id ? '#' + el.id : '')
                + (el.className && typeof el.className === 'string'
                   ? '.' + el.className.trim().split(/\\s+/).join('.') : ''),
            computedStyles: {
                display: style.display,
                width: style.width,
                height: style.height
            },
            attributes: {
                alt: el.getAttribute('alt') || '',
                src: el.getAttribute('src') || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                ariaHidden: el.getAttribute('aria-hidden') || '',
                role: el.getAttribute('role') || '',
                title: el.getAttribute('title') || '',
                hasFigcaption: hasFigcaption ? 'true' : ''
            },
            boundingBox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
            parentStyles: {}
        };
    });
}"""


def _parse_element(raw: Dict[str, Any]) -> ElementData:
    """Convert raw JS extraction output to an ElementData object."""
    return ElementData(
        tag=raw.get("tag", ""),
        selector=raw.get("selector", ""),
        html=raw.get("html", ""),
        text=raw.get("text", ""),
        computed_styles=raw.get("computedStyles", {}),
        attributes=raw.get("attributes", {}),
        bounding_box=raw.get("boundingBox", {}),
        parent_styles=raw.get("parentStyles", {}),
    )


async def extract_page_data(
    page: Any,
    session_id: UUID,
    capture_screenshot: bool = False,
) -> PageData:
    """
    Extract structured accessibility data from a live Playwright page.

    Args:
        page: A Playwright Page object (must still be open).
        session_id: The audit session UUID.
        capture_screenshot: If True, capture a full-page PNG screenshot.

    Returns:
        PageData with all extracted elements and optional screenshot.
    """
    url = page.url
    logger.info(f"Extracting page data from: {url}")

    links_raw = await page.evaluate(EXTRACT_LINKS_JS)
    links = [_parse_element(r) for r in (links_raw or [])]
    logger.debug(f"Extracted {len(links)} link elements")

    text_raw = await page.evaluate(EXTRACT_TEXT_ELEMENTS_JS)
    text_elements = [_parse_element(r) for r in (text_raw or [])]
    logger.debug(f"Extracted {len(text_elements)} text elements")

    form_raw = await page.evaluate(EXTRACT_FORM_ELEMENTS_JS)
    form_elements = [_parse_element(r) for r in (form_raw or [])]
    logger.debug(f"Extracted {len(form_elements)} form elements")

    images_raw = await page.evaluate(EXTRACT_IMAGES_JS)
    images = [_parse_element(r) for r in (images_raw or [])]
    logger.debug(f"Extracted {len(images)} image elements")

    screenshot = None
    if capture_screenshot:
        try:
            screenshot = await page.screenshot(full_page=True, type="png")
            logger.debug(f"Screenshot captured: {len(screenshot)} bytes")
        except Exception as e:
            logger.warning(f"Screenshot capture failed: {e}")

    logger.info(
        f"Data extraction complete: "
        f"{len(links)} links, {len(text_elements)} text, "
        f"{len(form_elements)} forms, {len(images)} images"
    )

    return PageData(
        url=url,
        links=links,
        text_elements=text_elements,
        form_elements=form_elements,
        images=images,
        screenshot=screenshot,
        session_id=session_id,
    )
