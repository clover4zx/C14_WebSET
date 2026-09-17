"""
sidebar.py

This file defines the sidebar (the left-hand navigation menu). It is
"modular" because instead of hardcoding buttons, we describe each
button as a small NavItem object. Later, you can add things like a
badge (a small number, e.g. "3 findings") to any button just by
setting one extra field on NavItem — you won't need to change the
Sidebar class itself.

Two things live in this file:
    1. NavItem       - describes ONE button (its key, label, icon, etc.)
    2. Sidebar       - the actual widget that draws all the buttons

How another file uses this (you'll do this yourself soon):

    from app.sidebar import Sidebar, NavItem

    items = [
        NavItem("dashboard", "Dashboard", "🏠"),
        NavItem("static_scan", "Static Scan", "🔎"),
    ]

    sidebar = Sidebar(items)
    sidebar.navigation_requested.connect(some_function)

`some_function` will be called with the key ("dashboard", "static_scan",
etc.) whenever the user clicks a button.
"""

from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.widgets import make_nav_button


# ---------------------------------------------------------------------------
# NavItem: describes ONE sidebar button.
#
# A "dataclass" is just a normal Python class that auto-generates the
# boring __init__ code for you, based on the fields listed below.
# ---------------------------------------------------------------------------
@dataclass
class NavItem:
    key: str                       # internal id, e.g. "dashboard" — used in code, never shown to the user
    label: str                     # text shown to the user, e.g. "Dashboard"
    icon: str = ""                 # an emoji shown next to the label, e.g. "🏠"
    badge: Optional[str] = None    # OPTIONAL: small number/text shown on the button, e.g. "3"
    enabled: bool = True           # OPTIONAL: set False to grey the button out and disable clicking


# ---------------------------------------------------------------------------
# Sidebar: the actual widget
# ---------------------------------------------------------------------------
class Sidebar(QWidget):
    # This line declares a "signal" — a way for this widget to announce
    # "something happened" to whoever is listening, without needing to
    # know who that is. Here, it announces "a button with this key was
    # clicked".
    navigation_requested = pyqtSignal(str)

    def __init__(self, nav_items, title="WebSET", subtitle="Website Security Evaluation Tool", parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(230)

        self.nav_items = nav_items
        self.buttons = {}   # will map key -> the actual button widget, e.g. {"dashboard": <button>}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(2)

        # --- header text at the top of the sidebar ---
        title_label = QLabel(title)
        title_label.setObjectName("SidebarTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("SidebarSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        # --- one button per NavItem ---
        for item in nav_items:
            button_row = self._build_button_row(item)
            layout.addWidget(button_row)

        layout.addStretch()  # pushes everything above upward, footer stays at bottom

        footer = QLabel("Team WebGoats · Group C14")
        footer.setStyleSheet("color: #8b93a7; font-size: 10px; padding: 8px 16px;")
        layout.addWidget(footer)

        # Highlight the first button by default, like most apps opening
        # to a "Home" or "Dashboard" screen.
        if nav_items:
            self._set_checked(nav_items[0].key)

    def _build_button_row(self, item: NavItem) -> QWidget:
        """Builds one row: the nav button, plus an optional badge label."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        button = make_nav_button(item.label, item.icon)
        button.setEnabled(item.enabled)
        # "lambda" here just means: when clicked, run self._on_clicked(item.key)
        button.clicked.connect(lambda checked, key=item.key: self._on_clicked(key))
        row_layout.addWidget(button, stretch=1)

        if item.badge:
            row_layout.addWidget(self._build_badge(item.badge))

        self.buttons[item.key] = button
        return row

    @staticmethod
    def _build_badge(text: str) -> QLabel:
        badge = QLabel(text)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedHeight(18)
        badge.setMinimumWidth(18)
        badge.setStyleSheet(
            "background-color: #3ddc9733; color: #3ddc97; border: 1px solid #3ddc9788; "
            "border-radius: 9px; font-size: 10px; font-weight: 700; padding: 0px 6px; margin-right: 10px;"
        )
        return badge

    def _on_clicked(self, key: str):
        self._set_checked(key)
        self.navigation_requested.emit(key)  # tells the outside world "this key was clicked"

    def _set_checked(self, key: str):
        """Makes only the clicked button look 'active'; un-highlights the rest."""
        for button_key, button in self.buttons.items():
            button.setChecked(button_key == key)

    def set_active(self, key: str):
        """Call this from outside if you need to highlight a button
        WITHOUT it counting as a click (e.g. when the app first opens)."""
        if key in self.buttons:
            self._set_checked(key)

    def set_badge(self, key: str, text: Optional[str]):
        """Update a badge later, e.g. to show a live count of findings.
        Pass text=None to remove the badge."""
        for item in self.nav_items:
            if item.key == key:
                item.badge = text
        # Simplest way to reflect the change: nothing fancy needed yet —
        # this is a placeholder you can build out once you need it live.

    def set_enabled(self, key: str, enabled: bool):
        """Lock or unlock a button at runtime, e.g. keep 'Active Scan'
        disabled until the user confirms authorisation in Settings."""
        if key in self.buttons:
            self.buttons[key].setEnabled(enabled)
