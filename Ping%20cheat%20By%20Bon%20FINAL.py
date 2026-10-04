# ba_meta require api 9

"""Ping cheat By Bon - BombSquad 1.7.62 / API 9.

Adds a live green ping value next to each player name in the native Party/Chat
window. Uses the game's native get_client_ping() RTT value.
"""

from __future__ import annotations

import weakref

import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib import party


_PING_COLOR = (0.20, 1.0, 0.30)
_PING_SHADOW = 0.25
_UPDATE_SECONDS = 0.25

# Keep one global reference per currently-open PartyWindow.
_window_refs: list[weakref.ReferenceType] = []
_patched = False


def _exists(widget: object) -> bool:
    if widget is None:
        return False
    try:
        return bui.exists(widget)  # type: ignore[arg-type]
    except Exception:
        return False


def _safe_ping(client_id: object) -> int | None:
    """Return current client RTT in milliseconds, or None if unavailable."""
    if client_id is None or client_id == -1:
        # The host entry has no remote client RTT from our side.
        return None
    try:
        ping = int(round(float(bs.get_client_ping(int(client_id)))))
        return ping if ping >= 0 else None
    except Exception:
        return None


def _delete_labels(window: object) -> None:
    labels = getattr(window, '_bon_ping_labels', None)
    if not labels:
        return
    for label in list(labels):
        try:
            label.delete()
        except Exception:
            pass
    labels.clear()


def _add_ping_labels(window: object) -> None:
    """Draw labels using the exact same grid geometry as PartyWindow."""
    try:
        root = window._root_widget
        if not _exists(root):
            return

        roster = bs.get_game_roster()
        if not roster:
            _delete_labels(window)
            return

        # PartyWindow itself uses these values in its _update() method.
        width = float(window._width)
        height = float(window._height)
        columns = 1 if len(roster) == 1 else 2 if len(roster) == 2 else 3
        rows = (len(roster) + columns - 1) // columns
        c_width = (width * 0.9) / max(3, columns)
        c_width_total = c_width * columns
        c_height = 24

        # Recreate only our tiny overlay labels. The native PartyWindow owns
        # all player names and chat widgets.
        _delete_labels(window)
        labels = []

        for index, entry in enumerate(roster):
            try:
                x = index % columns
                y = index // columns

                # This is the native PartyWindow name position.
                pos_x = width * 0.53 - c_width_total * 0.5 + c_width * x - 23
                pos_y = height - 65 - c_height * y - 15

                ping = _safe_ping(entry.get('client_id'))
                if ping is None:
                    # Do not clutter the host entry with a fake number.
                    continue

                # Name width in the native UI is c_width * 0.85. Put the
                # ping at the right side of that same name area so it stays
                # visually attached to the corresponding player.
                label = bui.textwidget(
                    parent=root,
                    position=(pos_x + c_width * 0.60, pos_y - 1),
                    size=(c_width * 0.25, 28),
                    maxwidth=c_width * 0.25,
                    scale=0.42,
                    text=f'{ping}ms',
                    color=_PING_COLOR,
                    shadow=_PING_SHADOW,
                    flatness=1.0,
                    h_align='right',
                    v_align='center',
                )
                labels.append(label)
            except Exception:
                continue

        window._bon_ping_labels = labels
    except Exception:
        # Never break the game's PartyWindow if a UI detail differs.
        try:
            _delete_labels(window)
        except Exception:
            pass


def _refresh_all() -> None:
    alive: list[weakref.ReferenceType] = []
    for ref in list(_window_refs):
        try:
            window = ref()
        except Exception:
            window = None
        if window is None:
            continue
        alive.append(ref)
        try:
            _add_ping_labels(window)
        except Exception:
            pass
    _window_refs[:] = alive


def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    try:
        _window_refs.append(weakref.ref(self))
        # Wait until the native roster widgets have been created.
        babase.apptimer(0.05, lambda: _add_ping_labels(self))
    except Exception:
        pass


def _patched_update(self, *args, **kwargs):
    # Let the native PartyWindow update its roster/chat first.
    _original_update(self, *args, **kwargs)
    try:
        _add_ping_labels(self)
    except Exception:
        pass


_original_init = party.PartyWindow.__init__
_original_update = party.PartyWindow._update


# ba_meta export babase.Plugin
class PingCheatByBon(babase.Plugin):
    """Live player ping overlay for the native Party/Chat window."""

    def on_app_running(self) -> None:
        global _patched
        if _patched:
            return
        _patched = True

        # Patch the native PartyWindow only once. This is deliberately done
        # while the app is running, matching the structure of working API-9
        # plugins without replacing the entire PartyWindow implementation.
        party.PartyWindow.__init__ = _patched_init
        party.PartyWindow._update = _patched_update

        # Frequent refresh gives the requested near-live ping display.
        bui.AppTimer(
            _UPDATE_SECONDS,
            _refresh_all,
            repeat=True,
        )

