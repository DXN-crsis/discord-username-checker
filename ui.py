"""
Professional PyQt6 UI for Shoter — Discord Username Checker.
Dark theme inspired by Discord's design language.
"""

import os
import time
from datetime import datetime
from typing import List

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QPalette, QFontDatabase
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSpinBox, QComboBox, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSplitter, QFrame, QFileDialog, QApplication, QGraphicsDropShadowEffect,
)

from checker import CheckerWorker


# ═══════════════════════════════════════════════════════════════════════
#  Colour palette (Discord-inspired)
# ═══════════════════════════════════════════════════════════════════════

class C:
    BG_DARKEST  = "#0b0b1a"
    BG_DARK     = "#0f0f23"
    BG_MID      = "#16213e"
    BG_CARD     = "#1a1a2e"
    BG_INPUT    = "#1e1e36"
    BORDER      = "#2d2d52"
    TEXT        = "#dcddde"
    TEXT_DIM    = "#8e9297"
    TEXT_MUTED  = "#5c5e66"
    BLURPLE     = "#5865F2"
    BLURPLE_H   = "#4752C4"
    BLURPLE_P   = "#3C45A5"
    GREEN       = "#57F287"
    GREEN_DIM   = "#2d7d46"
    RED         = "#ED4245"
    RED_DIM     = "#8b2022"
    YELLOW      = "#FEE75C"
    ORANGE      = "#F0A030"
    WHITE       = "#FFFFFF"


# ═══════════════════════════════════════════════════════════════════════
#  Global stylesheet
# ═══════════════════════════════════════════════════════════════════════

STYLESHEET = f"""
/* ── Base ──────────────────────────────────────────── */

QMainWindow, QWidget#central {{
    background-color: {C.BG_DARK};
}}

QLabel {{
    color: {C.TEXT};
    font-size: 13px;
}}

QLabel#header {{
    font-size: 26px;
    font-weight: 800;
    color: {C.WHITE};
    letter-spacing: 2px;
}}

QLabel#subtitle {{
    font-size: 12px;
    color: {C.TEXT_DIM};
}}

QLabel#statValue {{
    font-size: 22px;
    font-weight: 700;
    color: {C.WHITE};
}}

QLabel#statLabel {{
    font-size: 11px;
    color: {C.TEXT_DIM};
    text-transform: uppercase;
}}

QLabel#availableTag {{
    background-color: {C.GREEN_DIM};
    color: {C.GREEN};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: 13px;
}}

/* ── Buttons ───────────────────────────────────────── */

QPushButton {{
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 700;
    font-size: 13px;
    color: {C.WHITE};
}}

QPushButton#startBtn {{
    background-color: {C.GREEN};
    color: {C.BG_DARKEST};
    min-width: 160px;
    font-size: 14px;
    padding: 12px 32px;
}}
QPushButton#startBtn:hover {{ background-color: #45d972; }}
QPushButton#startBtn:pressed {{ background-color: #3ac462; }}
QPushButton#startBtn:disabled {{ background-color: {C.TEXT_MUTED}; }}

QPushButton#stopBtn {{
    background-color: {C.RED};
    min-width: 120px;
}}
QPushButton#stopBtn:hover {{ background-color: #d93638; }}
QPushButton#stopBtn:pressed {{ background-color: #c12b2d; }}
QPushButton#stopBtn:disabled {{ background-color: {C.TEXT_MUTED}; }}

QPushButton#exportBtn {{
    background-color: {C.BLURPLE};
    min-width: 120px;
}}
QPushButton#exportBtn:hover {{ background-color: {C.BLURPLE_H}; }}
QPushButton#exportBtn:pressed {{ background-color: {C.BLURPLE_P}; }}

QPushButton#clearBtn {{
    background-color: transparent;
    border: 1px solid {C.BORDER};
    color: {C.TEXT_DIM};
}}
QPushButton#clearBtn:hover {{ border-color: {C.TEXT_DIM}; color: {C.TEXT}; }}

/* ── Inputs ────────────────────────────────────────── */

QSpinBox, QComboBox, QLineEdit {{
    background-color: {C.BG_INPUT};
    border: 1px solid {C.BORDER};
    border-radius: 6px;
    color: {C.TEXT};
    padding: 7px 10px;
    font-size: 13px;
    min-height: 20px;
}}

QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
    border-color: {C.BLURPLE};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER};
    color: {C.TEXT};
    selection-background-color: {C.BLURPLE};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    width: 16px;
}}

/* ── Table ─────────────────────────────────────────── */

QTableWidget {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    gridline-color: {C.BORDER};
    color: {C.TEXT};
    font-size: 12px;
    selection-background-color: {C.BLURPLE};
}}

QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {C.BORDER};
}}

QHeaderView::section {{
    background-color: {C.BG_MID};
    color: {C.TEXT_DIM};
    border: none;
    border-bottom: 2px solid {C.BORDER};
    padding: 8px 10px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
}}

QScrollBar:vertical {{
    background: {C.BG_DARKEST};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C.TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

/* ── Cards / Groups ────────────────────────────────── */

QGroupBox {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 18px 14px 10px 14px;
    font-weight: 700;
    font-size: 12px;
    color: {C.TEXT_DIM};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {C.TEXT_DIM};
}}

/* ── Log / TextEdit ────────────────────────────────── */

QTextEdit {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    color: {C.TEXT};
    font-family: "Consolas", "Fira Code", monospace;
    font-size: 12px;
    padding: 8px;
}}

/* ── Frame separators ──────────────────────────────── */

QFrame#separator {{
    background-color: {C.BORDER};
    max-height: 1px;
}}
"""


# ═══════════════════════════════════════════════════════════════════════
#  Stat card widget
# ═══════════════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, label: str, initial: str = "0", color: str = C.WHITE):
        super().__init__()
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {C.BG_CARD};
                border: 1px solid {C.BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel(initial)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {color};")

        self.name_label = QLabel(label.upper())
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {C.TEXT_DIM}; letter-spacing: 1px;")

        layout.addWidget(self.value_label)
        layout.addWidget(self.name_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


# ═══════════════════════════════════════════════════════════════════════
#  Main window
# ═══════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    MAX_TABLE_ROWS = 500  # Keep table performant

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHOTER")
        self.setMinimumSize(960, 720)
        self.resize(1020, 800)

        self._worker: CheckerWorker | None = None
        self._available_names: List[str] = []
        self._all_results: List[tuple] = []

        self._build_ui()
        self._connect_signals()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # Header
        root.addLayout(self._make_header())

        # Config + Buttons
        root.addWidget(self._make_config())

        # Stats bar
        root.addLayout(self._make_stats())

        # Splitter: results table | available list
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; height: 6px; }")

        splitter.addWidget(self._make_table())
        splitter.addWidget(self._make_available_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, stretch=1)

        # Log bar
        root.addWidget(self._make_log())

    def _make_header(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(12)

        title = QLabel("SHOTER")
        title.setObjectName("header")
        lay.addWidget(title)

        sub = QLabel("Discord Username Checker")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignBottom)
        lay.addWidget(sub)

        lay.addStretch()

        # Action buttons
        self.btn_start = QPushButton("START")
        self.btn_start.setObjectName("startBtn")
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_export = QPushButton("EXPORT")
        self.btn_export.setObjectName("exportBtn")
        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.setObjectName("clearBtn")

        for btn in (self.btn_start, self.btn_stop, self.btn_export, self.btn_clear):
            lay.addWidget(btn)

        return lay

    def _make_config(self) -> QGroupBox:
        grp = QGroupBox("CONFIGURATION")
        grid = QGridLayout(grp)
        grid.setSpacing(10)

        # Row 0
        grid.addWidget(QLabel("Workers"), 0, 0)
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 200)
        self.spin_workers.setValue(50)
        grid.addWidget(self.spin_workers, 0, 1)

        grid.addWidget(QLabel("Mode"), 0, 2)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Random", "Exhaustive"])
        grid.addWidget(self.combo_mode, 0, 3)

        grid.addWidget(QLabel("Min Length"), 0, 4)
        self.spin_min = QSpinBox()
        self.spin_min.setRange(2, 6)
        self.spin_min.setValue(2)
        grid.addWidget(self.spin_min, 0, 5)

        grid.addWidget(QLabel("Max Length"), 0, 6)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(2, 6)
        self.spin_max.setValue(4)
        grid.addWidget(self.spin_max, 0, 7)

        # Row 1
        grid.addWidget(QLabel("Token (optional)"), 1, 0)
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Leave empty for unauthenticated mode (recommended)")
        self.input_token.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(self.input_token, 1, 1, 1, 7)

        return grp

    def _make_stats(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(12)

        self.stat_checked = StatCard("Checked", "0", C.BLURPLE)
        self.stat_available = StatCard("Available", "0", C.GREEN)
        self.stat_errors = StatCard("Errors", "0", C.RED)
        self.stat_rate = StatCard("Rate /s", "0", C.ORANGE)

        for card in (self.stat_checked, self.stat_available, self.stat_errors, self.stat_rate):
            lay.addWidget(card)

        return lay

    def _make_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Username", "Status", "Time (ms)", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 200)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        return self.table

    def _make_available_panel(self) -> QGroupBox:
        grp = QGroupBox("AVAILABLE USERNAMES")
        lay = QVBoxLayout(grp)
        lay.setContentsMargins(10, 14, 10, 10)

        self.available_area = QWidget()
        self.available_layout = QHBoxLayout(self.available_area)
        self.available_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.available_layout.setSpacing(8)
        self.available_layout.setContentsMargins(0, 0, 0, 0)

        self.available_placeholder = QLabel("Found usernames will appear here...")
        self.available_placeholder.setStyleSheet(f"color: {C.TEXT_MUTED}; font-style: italic;")
        self.available_layout.addWidget(self.available_placeholder)

        lay.addWidget(self.available_area)
        return grp

    def _make_log(self) -> QTextEdit:
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(80)
        self.log_box.setPlaceholderText("Logs...")
        return self.log_box

    # ── Signal wiring ────────────────────────────────────────────────

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_clear.clicked.connect(self._on_clear)

    # ── Actions ──────────────────────────────────────────────────────

    def _on_start(self):
        token = self.input_token.text().strip() or None
        workers = self.spin_workers.value()
        min_len = self.spin_min.value()
        max_len = self.spin_max.value()
        mode = "random" if self.combo_mode.currentIndex() == 0 else "exhaustive"

        if max_len < min_len:
            max_len = min_len
            self.spin_max.setValue(max_len)

        self._worker = CheckerWorker(
            token=token,
            concurrency=workers,
            min_len=min_len,
            max_len=max_len,
            mode=mode,
        )

        self._worker.username_result.connect(self._on_result)
        self._worker.stats_update.connect(self._on_stats)
        self._worker.log.connect(self._on_log)
        self._worker.done.connect(self._on_done)

        self._set_running(True)
        self._worker.start()
        self._on_log("Checker started")

    def _on_stop(self):
        if self._worker and self._worker.running:
            self._worker.stop()
            self._on_log("Stopping...")

    def _on_done(self):
        self._set_running(False)
        self._on_log("Checker stopped")
        # Final stats
        if self._worker:
            total = time.time() - self._worker._t0 if self._worker._t0 else 1
            rate = self._worker._checked / max(total, 0.001)
            self.stat_checked.set_value(f"{self._worker._checked:,}")
            self.stat_available.set_value(f"{self._worker._available:,}")
            self.stat_errors.set_value(f"{self._worker._errors:,}")
            self.stat_rate.set_value(f"{rate:.1f}")

    def _set_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.spin_workers.setEnabled(not running)
        self.combo_mode.setEnabled(not running)
        self.spin_min.setEnabled(not running)
        self.spin_max.setEnabled(not running)
        self.input_token.setEnabled(not running)

    def _on_result(self, username: str, available: object, elapsed_ms: float):
        now = datetime.now().strftime("%H:%M:%S")

        if available is True:
            status_text = "AVAILABLE"
            status_color = C.GREEN
            self._available_names.append(username)
            self._add_available_tag(username)
        elif available is False:
            status_text = "TAKEN"
            status_color = C.RED
        else:
            status_text = "ERROR"
            status_color = C.YELLOW

        self._all_results.append((username, status_text, elapsed_ms, now))

        # Add to table (insert at top)
        row = 0
        self.table.insertRow(row)

        # Username cell
        item_name = QTableWidgetItem(username)
        item_name.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        if available is True:
            item_name.setForeground(QColor(C.GREEN))
        self.table.setItem(row, 0, item_name)

        # Status cell
        item_status = QTableWidgetItem(status_text)
        item_status.setForeground(QColor(status_color))
        item_status.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, item_status)

        # Time cell
        item_time = QTableWidgetItem(f"{elapsed_ms:.0f}")
        item_time.setForeground(QColor(C.TEXT_DIM))
        item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, item_time)

        # Timestamp cell
        item_ts = QTableWidgetItem(now)
        item_ts.setForeground(QColor(C.TEXT_MUTED))
        item_ts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, item_ts)

        # Trim table for performance
        while self.table.rowCount() > self.MAX_TABLE_ROWS:
            self.table.removeRow(self.table.rowCount() - 1)

    def _on_stats(self, checked: int, available: int, errors: int, rate: float):
        self.stat_checked.set_value(f"{checked:,}")
        self.stat_available.set_value(f"{available:,}")
        self.stat_errors.set_value(f"{errors:,}")
        self.stat_rate.set_value(f"{rate:.1f}")

    def _on_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"<span style='color:{C.TEXT_DIM}'>[{ts}]</span> {msg}")

    def _add_available_tag(self, username: str):
        if self.available_placeholder:
            self.available_placeholder.hide()
            self.available_placeholder = None

        tag = QLabel(username)
        tag.setObjectName("availableTag")
        tag.setCursor(Qt.CursorShape.PointingHandCursor)
        tag.setToolTip("Click to copy")
        tag.mousePressEvent = lambda e, u=username: self._copy_username(u)
        self.available_layout.addWidget(tag)

    def _copy_username(self, username: str):
        QApplication.clipboard().setText(username)
        self._on_log(f"Copied <b>{username}</b> to clipboard")

    def _on_export(self):
        if not self._available_names:
            self._on_log("Nothing to export")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Available Usernames", "available_usernames.txt", "Text Files (*.txt)"
        )
        if path:
            with open(path, "w") as f:
                for name in self._available_names:
                    f.write(name + "\n")
            self._on_log(f"Exported {len(self._available_names)} usernames to {path}")

    def _on_clear(self):
        self.table.setRowCount(0)
        self._all_results.clear()
        self._available_names.clear()

        # Clear available tags
        while self.available_layout.count():
            item = self.available_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.available_placeholder = QLabel("Found usernames will appear here...")
        self.available_placeholder.setStyleSheet(f"color: {C.TEXT_MUTED}; font-style: italic;")
        self.available_layout.addWidget(self.available_placeholder)

        self.stat_checked.set_value("0")
        self.stat_available.set_value("0")
        self.stat_errors.set_value("0")
        self.stat_rate.set_value("0")

        self._on_log("Cleared all results")

    # ── Cleanup ──────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._worker and self._worker.running:
            self._worker.stop()
            self._worker.wait(3000)
        event.accept()
