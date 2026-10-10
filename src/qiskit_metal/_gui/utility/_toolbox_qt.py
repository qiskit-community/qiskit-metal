# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""This is a utility module used for qt."""

from types import MethodType

# from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QDockWidget

__all__ = ["blend_colors", "qt_alive", "single_shot"]


def qt_alive(obj) -> bool:
    """Whether ``obj``'s C++ object still exists (``None`` counts as dead).

    For model poll timers: the model and its view are destroyed
    independently, so a tick can land after the view's C++ side is gone. A
    bare ``obj.show()`` then raises ``RuntimeError: ... already deleted``,
    which is the Python-visible face of a native use-after-free (see
    ``docs/architecture/gui_crash_defenses.md``). Fails closed: if
    ``shiboken6.isValid`` itself raises, the object is treated as dead.
    """
    if obj is None:
        return False
    try:
        import shiboken6

        return bool(shiboken6.isValid(obj))
    except Exception:  # pylint: disable=broad-except
        return False


def single_shot(parent: QObject, ms: int, callback) -> QTimer:
    """A ``QTimer.singleShot`` replacement whose timer dies with ``parent``.

    ``QTimer.singleShot(ms, bound_method)`` creates an internal timer with
    no reachable parent. If the object owning ``bound_method`` is destroyed
    before the timer fires, the callback lands on a dead C++ object — a
    ``RuntimeError`` when Python catches it, a native use-after-free when
    it doesn't. Issue #1048's nondeterministic teardown segfaults ("failure
    mode 4" in ``docs/architecture/gui_crash_defenses.md``) are this class
    of bug: deferred callbacks outliving the widgets they reference.

    Parenting the timer to the object the callback touches makes Qt stop
    and destroy the timer during that object's own destruction — the
    callback can then never fire on a dead target, by construction. Use
    this for every delayed call in ``_gui/``; never a naked
    ``QTimer.singleShot`` with a bound method.

    Args:
        parent (QObject): Owner whose destruction must cancel the callback
            — almost always the object whose method ``callback`` is.
        ms (int): Delay in milliseconds.
        callback: Zero-argument callable.

    Returns:
        QTimer: The started timer (rarely needed; kept for tests).
    """
    timer = QTimer(parent)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    # Once fired the timer has no further use. Left alive it is a child of
    # ``parent`` that ``findChildren(QTimer)`` still finds, and the main
    # window's ``showEvent`` restarts every inactive timer it finds -- which
    # replayed every past one-shot (focus-stealing ``_raise`` included) on
    # each show/un-minimize.
    timer.timeout.connect(timer.deleteLater)
    timer.start(ms)
    return timer


def blend_colors(color1: QColor, color2: QColor, r: float = 0.2, alpha=255) -> QColor:
    """Blend two qt colors together.

    Args:
        color1 (QColor): first color
        color2 (QColor): second color
        r (float): ratio
        alpha (int): alpha

    Returns:
        QColor: new color
    """
    color3 = QColor(
        color1.red() * (1 - r) + color2.red() * r,
        color1.green() * (1 - r) + color2.green() * r,
        color1.blue() * (1 - r) + color2.blue() * r,
        alpha,
    )
    return color3


# ------------------------------------------------------------------------------------------

# Qt stylesheets cascade: a rule set on a widget also matches every
# descendant that satisfies the selector. A bare ``QWidget { border: ... }``
# therefore outlined the widget *and* every child -- clicking Refresh
# red-boxed all the toolbars and icons inside the main view, not just the
# view. Scope by object name so only the target widget matches.
STYLE_HIGHLIGHT_TEMPLATE_ = "QWidget#{name} {{ border: 3px solid red; }}"

# Fallback object name for a target that has none, so the scoped selector
# above still has something to bind to.
_HIGHLIGHT_FALLBACK_NAME = "metalHighlightTarget"


def doShowHighlighWidget(self: QDockWidget, timeout=1500, style_highlight=None):
    """Highlight temporarily, raise, show the widget.
    Force resets the style at the component to None after a period.

    The highlight is scoped to this widget by object name; it does not
    outline child widgets.
    """
    if style_highlight is None:
        if not self.objectName():
            self.setObjectName(_HIGHLIGHT_FALLBACK_NAME)
        style_highlight = STYLE_HIGHLIGHT_TEMPLATE_.format(name=self.objectName())
    self.setStyleSheet(style_highlight)
    self.show()
    self.raise_()

    def doResetStyle(self: "QDockWidget"):
        """Reset the style of the widget."""
        self.setStyleSheet("")

    # Bind the method dynamically to the instance using MethodType
    self.doResetStyle = MethodType(doResetStyle, self)

    # self.doResetStyle = doResetStyle.__get__(self, type(self))
    # monkey patch class instance:
    # https://stackoverflow.com/questions/28127874/monkey-patching-python-an-instance-method

    # Parented to the dock: if it's destroyed before the timeout, the
    # reset silently never fires instead of calling into a dead widget.
    single_shot(self, timeout, self.doResetStyle)


def doToggleDockWidget(self: QDockWidget, timeout=1500, style_highlight=None):
    """Toggle-aware dock-raise: hide the dock if its icon is clicked while
    it is the one actually on screen, otherwise show/raise/highlight it
    like ``doShowHighlighWidget``.

    Works for tabified docks too, unlike a plain ``isVisible()`` check:
    every dock in a tabified group reports ``isVisible() == True`` once the
    group itself is shown, regardless of which tab is on top, because
    ``isVisible()`` doesn't know about the obscuring siblings. A dock that
    is tabified-but-not-the-active-tab has an *empty* ``visibleRegion()``
    (fully covered by whichever sibling is showing) even though
    ``isVisible()`` is True -- that combination is what distinguishes
    "raise/switch to this tab" from "this tab is already the one showing,
    so hide it."
    """
    currently_on_top = self.isVisible() and not self.visibleRegion().isEmpty()
    if currently_on_top:
        self.hide()
        return
    doShowHighlighWidget(self, timeout=timeout, style_highlight=style_highlight)


#: Red used for every "you have an unread error" cue -- icon fill, status
#: bar text. One constant so they read as the same signal.
ERROR_ALERT_COLOR = "#E53935"

#: Blink period, in ms, for the badged Log icon. Fast enough to actually
#: catch the eye (a first attempt used a small static corner dot -- too
#: subtle to notice without already looking for it), slow enough not to
#: be annoying while it's up.
_ERROR_BLINK_MS = 600


def badge_icon_alert(icon: QIcon, size: int = 20, color=None) -> QIcon:
    """Return a copy of ``icon`` on a filled, rounded red background.

    A full-background fill, not a small corner dot (tried first and found
    too subtle to notice without already looking for it) -- used with
    :func:`mark_dock_has_error`'s blink so the flagged icon alternates with
    the plain one rather than sitting there as a permanent, easy-to-tune-out
    fixture.

    Args:
        icon (QIcon): Base icon to badge.
        size (int): Icon edge length to render at, in pixels. Should match
            the toolbar's actual icon size or the fill will be mis-scaled.
        color (QColor): Fill color. Defaults to :data:`ERROR_ALERT_COLOR`.

    Returns:
        QIcon: A new icon composited onto the fill; the original ``icon``
        is left untouched.
    """
    if color is None:
        color = QColor(ERROR_ALERT_COLOR)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, size, size, 4, 4)
        painter.drawPixmap(0, 0, icon.pixmap(size, size))
    finally:
        painter.end()
    return QIcon(pixmap)


def make_help_icon(size: int = 20, color=None) -> QIcon:
    """Draw a red circle with a bold white "?" -- a Help icon that reads
    as Help at a glance, rather than the generic ``:/help`` resource icon
    it replaced (a user found it too unclear to register as "click here
    for shortcuts").

    Drawn programmatically rather than shipping a new icon asset, for the
    same reason :func:`badge_icon_alert` is: one function, easy to retint
    or resize later without touching a binary resource file.

    Args:
        size (int): Icon edge length to render at, in pixels.
        color (QColor): Circle fill color. Defaults to
            :data:`ERROR_ALERT_COLOR` -- red reads as "important/click
            me," which is exactly the point for a help button that was
            previously going unnoticed.

    Returns:
        QIcon: The composited icon.
    """
    if color is None:
        color = QColor(ERROR_ALERT_COLOR)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)

        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(int(size * 0.68))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "?")
    finally:
        painter.end()
    return QIcon(pixmap)


def mark_dock_has_error(dock: QDockWidget) -> None:
    """Flag a dock's toolbar icon (blinking) and status bar to signal an
    unread error.

    Operates purely on the dock -- no reference to the GUI or logger
    needed -- so it can be called from anywhere holding just a dock
    reference (the log widget already keeps one as ``self.dock_window``,
    the same reference it already uses for ``setWindowTitle``; this adds
    no new cross-widget reference, unlike a full popup mechanism would).
    The status bar is reached the same way, via ``dock._status_bar`` set
    alongside ``_icon_normal`` -- optional, so this degrades gracefully on
    a dock that was never wired up with one. A no-op if the dock was never
    set up with ``_add_dock_toolbar_action`` (no ``actionShow``/
    ``_icon_normal`` to badge) -- calling it repeatedly for further errors
    while already flagged is intentionally cheap (idempotent restart of
    the same blink), not additive.

    Args:
        dock (QDockWidget): The dock whose toolbar icon (and status bar,
            if wired) to flag.
    """
    action = getattr(dock, "actionShow", None)
    normal_icon = getattr(dock, "_icon_normal", None)
    if action is None or normal_icon is None:
        return

    alert_icon = badge_icon_alert(normal_icon)
    state = {"on": True}
    action.setIcon(alert_icon)

    timer = getattr(dock, "_error_blink_timer", None)
    if timer is None:
        timer = QTimer(dock)
        dock._error_blink_timer = timer

        def _toggle():
            state["on"] = not state["on"]
            action.setIcon(alert_icon if state["on"] else normal_icon)

        timer.timeout.connect(_toggle)
    timer.start(_ERROR_BLINK_MS)

    status_bar = getattr(dock, "_status_bar", None)
    if status_bar is not None:
        status_bar.setStyleSheet(f"QStatusBar{{color: {ERROR_ALERT_COLOR};}}")
        status_bar.showMessage(
            "⚠ Error logged — open the Log panel (left toolbar) to see it", 0
        )


def clear_dock_error_badge(dock: QDockWidget) -> None:
    """Undo :func:`mark_dock_has_error` -- stop the blink, restore the
    plain icon, and clear the status bar alert.

    Args:
        dock (QDockWidget): The dock whose toolbar icon/status bar to
            restore.
    """
    timer = getattr(dock, "_error_blink_timer", None)
    if timer is not None:
        timer.stop()

    action = getattr(dock, "actionShow", None)
    normal_icon = getattr(dock, "_icon_normal", None)
    if action is not None and normal_icon is not None:
        action.setIcon(normal_icon)

    status_bar = getattr(dock, "_status_bar", None)
    if status_bar is not None:
        status_bar.clearMessage()
        status_bar.setStyleSheet("")


### Alternative to doShowHighlighWidget:

# from PySide6.QtWidgets import QFrame, QWidget
# from PySide6 import QtCore
# obj = gui.canvas
# frame = QFrame(obj.parent())
# frame.setGeometry(obj.frameGeometry())
# frame.setFrameShape(QFrame.Box)
# frame.setLineWidth(3)
# frame.show()

# frame.setStyleSheet(r"""
#   border-radius: 10px;
#   outline: 3px solid red;
#   border: 3px solid red;
#   background-color: transparent;
#   border-image:none;
# """)
# ## the folloing make it dissapear altoheger
# # frame.setWindowFlags(QtCore.Qt.FramelessWindowHint)
# # frame.setAttribute(QtCore.Qt.WA_TranslucentBackground)

# # Alternative see:
# https://stackoverflow.com/questions/58458323/how-to-use-qt-stylesheet-to-customize-only-partial-qwidget-border

# ------------------------------------------------------------------------------------------
