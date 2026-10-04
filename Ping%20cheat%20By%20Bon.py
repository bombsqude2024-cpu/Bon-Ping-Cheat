# Ping cheat By Bon.py
# BombSquad 1.7.62 / API 9
# Shows live ping for every connected client in the Party/Chat window.

from __future__ import annotations

import weakref

import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib import party


_PLUGIN_NAME = 'Ping cheat By Bon'
_PING_COLOR = (0.25, 1.0, 0.35)
_PING_SHADOW = 0.25
_UPDATE_SECONDS = 0.25

_live_party_window_ref: weakref.ReferenceType | None = None
_ping_widgets: list[bui.Widget] = []
_ping_timer: bui.AppTimer | None = None
_orig_party_init = party.PartyWindow.__init__


def _widget_exists(widget) -> bool:
    if widget is None:
        return False
    try:
        return bui.exists(widget)
    except AttributeError:
        pass
    except Exception:
        return False
    try:
        return babase.exists(widget)
    except AttributeError:
        pass
    except Exception:
        return False
    return True


def _clear_ping_widgets() -> None:
    global _ping_widgets
    old = _ping_widgets
    _ping_widgets = []
    for widget in old:
        try:
            widget.delete()
        except Exception:
            pass


def _get_live_party_window():
    global _live_party_window_ref
    if _live_party_window_ref is None:
        return None
    try:
        return _live_party_window_ref()
    except Exception:
        return None


def _safe_ping(client_id) -> float:
    # The host is represented by client_id -1 in the normal Party roster.
    # There is no remote RTT to measure for the local host entry.
    if client_id is None or client_id == -1:
        return 0.0
    try:
        value = float(bs.get_client_ping(int(client_id)))
        if value < 0:
            return -1.0
        return value
    except Exception:
        return -1.0


def _player_label(entry: dict) -> str:
    try:
        players = entry.get('players') or []
        if len(players) == 1:
            return str(players[0].get('name_full') or players[0].get('name') or entry.get('display_string', '???'))
        if len(players) > 1:
            return '/'.join(str(p.get('name') or p.get('name_full') or '?') for p in players)
        return str(entry.get('display_string') or '???')
    except Exception:
        return '???'


def _update_ping_display() -> None:
    window = _get_live_party_window()
    if window is None:
        _clear_ping_widgets()
        return

    try:
        root = window._root_widget
        if not _widget_exists(root):
            _clear_ping_widgets()
            return

        roster = bs.get_game_roster()
        if not roster:
            _clear_ping_widgets()
            return

        # Rebuild only the small ping labels. The native PartyWindow continues
        # to own and update the player-name widgets and chat messages.
        _clear_ping_widgets()

        width = float(window._width)
        height = float(window._height)
        columns = 1 if len(roster) == 1 else 2 if len(roster) == 2 else 3
        rows = (len(roster) + columns - 1) // columns
        c_width = (width * 0.9) / max(3, columns)
        c_width_total = c_width * columns
        c_height = 24

        for index, entry in enumerate(roster):
            try:
                x = index % columns
                y = index // columns
                base_x = width * 0.53 - c_width_total * 0.5 + c_width * x - 23
                base_y = height - 65 - c_height * y - 15

                ping = _safe_ping(entry.get('client_id'))
                if ping < 0:
                    ping_text = '--ms'
                else:
                    ping_text = f'{int(round(ping))}ms'

                # Put the ping at the upper-right corner of the same roster
                # cell as the native player name. It stays visually attached
                # to that player's name while the chat window remains unchanged.
                ping_widget = bui.textwidget(
                    parent=root,
                    position=(base_x + c_width * 0.55, base_y + 10),
                    size=(c_width * 0.38, 18),
                    maxwidth=c_width * 0.38,
                    scale=0.48,
                    text=ping_text,
                    color=_PING_COLOR,
                    shadow=_PING_SHADOW,
                    flatness=1.0,
                    h_align='right',
                    v_align='center',
                )
                _ping_widgets.append(ping_widget)
            except Exception:
                continue
    except Exception:
        _clear_ping_widgets()


def _patched_party_init(self, *args, **kwargs):
    global _live_party_window_ref
    _orig_party_init(self, *args, **kwargs)
    try:
        _live_party_window_ref = weakref.ref(self)
        # Let the native PartyWindow finish its first roster update before we
        # place our labels on top of it.
        babase.apptimer(0.08, _update_ping_display)
    except Exception:
        pass


party.PartyWindow.__init__ = _patched_party_init


class PingCheatByBon(babase.Plugin):
    """Live per-player ping display for the BombSquad Party/Chat window."""

    def on_app_running(self) -> None:
        global _ping_timer
        try:
            _ping_timer = bui.AppTimer(
                _UPDATE_SECONDS,
                _update_ping_display,
                repeat=True,
            )
        except Exception:
            _ping_timer = None


# API 9 plugin metadata.
# ba_meta require api 9
# ba_meta export babase.Plugin
