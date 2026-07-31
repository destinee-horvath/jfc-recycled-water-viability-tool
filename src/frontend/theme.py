"""frontend/theme.py — colour constants (mirrors config.py, which is the
single source) and the badge() renderer shared by every page."""

import config as C

COLOUR_PRIMARY = C.COLOUR_PRIMARY      # dark navy — headers, primary actions
COLOUR_SECONDARY = C.COLOUR_SECONDARY  # mid blue — secondary elements
COLOUR_SUCCESS = C.COLOUR_SUCCESS      # green — PROCEED / Compliant
COLOUR_WARNING = C.COLOUR_WARNING      # amber — CONDITIONAL / Pending
COLOUR_DANGER = C.COLOUR_DANGER        # red — REJECT / Not met
COLOUR_NEUTRAL = C.COLOUR_NEUTRAL      # gray — neutral / N/A states
COLOUR_BG = C.COLOUR_BG                # background


def badge(state: str, text: str = None) -> str:
    colour = C.STATE_COLOURS.get(state, COLOUR_NEUTRAL)
    return f'<span class="badge" style="background:{colour}">{text or state}</span>'


def accounting_amount(value: float, favourable: bool) -> str:
    """Accounting-style formatting: unfavourable renders red with
    parentheses (e.g. ($1,234)) instead of a minus sign. ``favourable``
    must be passed explicitly, not inferred from ``value``'s sign — what
    counts as favourable depends on what the figure represents (e.g. a
    positive water-cost saving is favourable, a positive transport-cost
    difference is not)."""
    magnitude = f"${abs(value):,.0f}"
    if favourable:
        return f'<span style="color:{COLOUR_SUCCESS};font-weight:700">{magnitude}</span>'
    return f'<span style="color:{COLOUR_DANGER};font-weight:700">({magnitude})</span>'
