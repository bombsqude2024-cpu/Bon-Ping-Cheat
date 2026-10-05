# Ping cheat By Bon - API 9
# BombSquad 1.7.62 / build 22837

from __future__ import annotations

import weakref

import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib import party


# ba_meta require api 9
# ba_meta export babase.Plugin


_POLL_SECONDS = 0.35
_LABEL_COLOR = (0.35, 1.0, 0.45)
_LABEL_SCALE = 0.62


class _PingOverlay:
    def __init__(self, window):
        self.window_ref = weakref.ref(window)
        self.labels = []
        self._timer = None
        self._make_labels()
        self._update()

    def _window(self):
        try:
            return self.window_ref()
        except Exception:
            return None

    def _root(self):
        window = self._window()
        if window is None:
            return None
        try:
            root = window._root_widget
            try:
                alive = bui.exists(root)
            except AttributeError:
                alive = True
            if not alive:
                return None
            return root
        except Exception:
            return None

    def _make_labels(self):
        root = self._root()
        if root is None:
            return

        # PartyWindow's roster occupies the upper part of the window.
        # We put one small green ping label above each roster entry.
        try:
            width = float(self._window()._width)
            height = float(self._window()._height)
        except Exception:
            width, height = 900.0, 600.0

        # Keep a generous maximum; labels are removed/reused as roster changes.
        for i in range(16):
            try:
                label = bui.textwidget(
                    parent=root,
                    position=(0, height - 73 - i * 31),
                    size=(width, 25),
                    text="",
                    scale=_LABEL_SCALE,
                    color=_LABEL_COLOR,
                    h_align="center",
                    v_align="center",
                    flatness=1.0,
                    shadow=0.0,
                )
                self.labels.append(label)
            except Exception:
                break

    @staticmethod
    def _roster():
        try:
            roster = bs.get_game_roster()
            if isinstance(roster, list):
                return roster
        except Exception:
            pass
        return []

    @staticmethod
    def _name(entry):
        try:
            value = entry.get("display_string")
            if value:
                return str(value)
        except Exception:
            pass
        try:
            players = entry.get("players", [])
            if players and isinstance(players, list):
                name = players[0].get("name", "")
                if name:
                    return str(name)
        except Exception:
            pass
        return "Player"

    @staticmethod
    def _client_id(entry):
        try:
            cid = entry.get("client_id")
            if cid is not None:
                return int(cid)
        except Exception:
            pass
        return None

    @staticmethod
    def _ping(client_id):
        if client_id is None:
            return None
        try:
            value = bs.get_client_ping(client_id)
            if value is None:
                return None
            value = int(round(float(value)))
            if value < 0:
                return None
            return value
        except Exception:
            return None

    def _update(self):
        root = self._root()
        if root is None:
            self.stop()
            return

        roster = self._roster()

        # Only show actual players; spectator/empty roster entries are skipped.
        rows = []
        for entry in roster:
            cid = self._client_id(entry)
            if cid is None:
                continue
            ping = self._ping(cid)
            if ping is None:
                continue
            rows.append((self._name(entry), ping))

        for index, label in enumerate(self.labels):
            try:
                if index < len(rows):
                    name, ping = rows[index]
                    # Name is included only as an anchor; the visible ping is
                    # green and placed at the roster-name line.
                    bui.textwidget(
                        edit=label,
                        text=f"{ping}ms",
                        color=_LABEL_COLOR,
                    )
                else:
                    bui.textwidget(edit=label, text="")
            except Exception:
                pass

        try:
            self._timer = babase.apptimer(_POLL_SECONDS, self._update)
        except Exception:
            self._timer = None

    def stop(self):
        try:
            for label in self.labels:
                if bui.exists(label):
                    bui.textwidget(edit=label, text="")
        except Exception:
            pass
        self.labels.clear()
        self._timer = None


class PingCheatByBon(babase.Plugin):
    """Shows live ping values for other players in the Party/chat window."""

    def __init__(self):
        self._installed = False
        self._original_init = None
        self._original_update = None
        self._overlays = []

    def on_app_running(self) -> None:
        # Install the UI hook only after the application is running.  This is
        # important on API 9 and avoids touching PartyWindow during startup.
        try:
            bui.screenmessage("Bon Ping Cheat: ON", color=(0.35, 1.0, 0.45))
        except Exception:
            pass
        babase.apptimer(0.5, self._install)

    def _install(self):
        if self._installed:
            return

        try:
            cls = party.PartyWindow
            if getattr(cls, "_bon_ping_hook", False):
                self._installed = True
                return

            self._original_init = cls.__init__
            self._original_update = getattr(cls, "_update", None)
            plugin_ref = weakref.ref(self)
            original_init = self._original_init
            original_update = self._original_update

            def patched_init(window, *args, **kwargs):
                original_init(window, *args, **kwargs)
                try:
                    plugin = plugin_ref()
                    if plugin is not None:
                        babase.apptimer(
                            0.12,
                            lambda: plugin._attach(window),
                        )
                except Exception:
                    pass

            cls.__init__ = patched_init

            # Do not require PartyWindow._update; some builds expose different
            # internals.  The overlay has its own safe timer instead.
            cls._bon_ping_hook = True
            self._installed = True
        except Exception as exc:
            # Never allow this plugin to break the rest of the user's mods.
            print("Ping cheat By Bon install error:", exc)

    def _attach(self, window):
        try:
            if window is None:
                return
            old = getattr(window, "_bon_ping_overlay", None)
            if old is not None:
                try:
                    old.stop()
                except Exception:
                    pass
            overlay = _PingOverlay(window)
            window._bon_ping_overlay = overlay
            self._overlays.append(weakref.ref(overlay))
        except Exception as exc:
            print("Ping cheat By Bon window error:", exc)

    def __del__(self):
        for ref in self._overlays:
            try:
                overlay = ref()
                if overlay is not None:
                    overlay.stop()
            except Exception:
                pass
