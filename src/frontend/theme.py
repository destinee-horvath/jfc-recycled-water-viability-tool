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
