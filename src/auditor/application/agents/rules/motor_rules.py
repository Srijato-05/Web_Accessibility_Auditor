def is_keyboard_trap_candidate(attrs: dict) -> bool:
    tabindex = attrs.get('tabindex', '')
    if not tabindex:
        return False
    try:
        val = int(tabindex)
        return val < 0
    except ValueError:
        return False
