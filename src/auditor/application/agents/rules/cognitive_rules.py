import re

pii_pattern = re.compile(r'\b(email|password|username|login|phone|tel|address|street|zip|postal|country|card|cc\-|fname|lname|first\-name|last\-name|birth|dob)\b', re.IGNORECASE)

def is_missing_label_logic(attrs: dict, sibling_text: str) -> bool:
    has_aria_label = bool(attrs.get("ariaLabel", "").strip())
    has_aria_labelledby = bool(attrs.get("ariaLabelledby", "").strip())
    has_title = bool(attrs.get("title", "").strip())
    has_placeholder = bool(attrs.get("placeholder", "").strip())
    has_visible_text = bool(sibling_text.strip())
    return not (has_aria_label or has_aria_labelledby or has_title or has_placeholder or has_visible_text)

def is_missing_autocomplete(attrs: dict) -> bool:
    combined_sig = f"{attrs.get('id', '')} {attrs.get('name', '')} {attrs.get('type', '')}"
    is_personal = bool(pii_pattern.search(combined_sig))
    has_autocomplete = bool(attrs.get('autocomplete', '').strip())
    return is_personal and not has_autocomplete

def is_justified_text(styles: dict) -> bool:
    return styles.get('textAlign', '').lower() == 'justify'
