"""
frontend/theme.py
==================
Colour constants (mirrors config.py — single source is config) and the
badge() renderer shared by every page.
"""

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
    """Accounting-style money formatting for a signed comparison figure:
    an unfavourable amount renders in red with parentheses (e.g. ($1,234)),
    matching the convention finance teams use so the reader never has to
    parse a leading minus sign or mentally re-sign the number themselves.
    ``favourable`` must be passed explicitly by the caller rather than
    inferred from ``value``'s own sign — which direction counts as
    "favourable" depends on what the figure represents (e.g. a positive
    water-cost saving is favourable, but a positive transport-cost
    *difference* is not)."""
    magnitude = f"${abs(value):,.0f}"
    if favourable:
        return f'<span style="color:{COLOUR_SUCCESS};font-weight:700">{magnitude}</span>'
    return f'<span style="color:{COLOUR_DANGER};font-weight:700">({magnitude})</span>'
