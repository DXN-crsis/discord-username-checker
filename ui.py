"""
Professional PyQt6 UI for SHOTER — Anthropic-grade Discord Username Engine.
Dark theme, live sparkline, engine telemetry, one-click claim.
"""

import time
from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QPainterPath, QBrush,
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSpinBox, QComboBox, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSplitter, QFrame, QFileDialog, QApplication, QScrollArea,
    QSizePolicy,
)

from engine import CheckerWorker, ClaimThread


# ═══════════════════════════════════════════════════════════════════════
#  Palette
# ═══════════════════════════════════════════════════════════════════════

class C:
    BG_DARKEST = "#0b0b1a"
    BG_DARK    = "#0f0f23"
    BG_MID     = "#16213e"
    BG_CARD    = "#1a1a2e"
    BG_INPUT   = "#1e1e36"
    BORDER     = "#2d2d52"
    TEXT       = "#dcddde"
    TEXT_DIM   = "#8e9297"
    TEXT_MUTED = "#5c5e66"
    BLURPLE    = "#5865F2"
    BLURPLE_H  = "#4752C4"
    BLURPLE_P  = "#3C45A5"
    GREEN      = "#57F287"
    GREEN_DIM  = "#2d7d46"
    RED        = "#ED4245"
    RED_DIM    = "#8b2022"
    YELLOW     = "#FEE75C"
    ORANGE     = "#F0A030"
    CYAN       = "#00D4AA"
    WHITE      = "#FFFFFF"


# ═══════════════════════════════════════════════════════════════════════
#  Stylesheet
# ═══════════════════════════════════════════════════════════════════════

STYLESHEET = f"""
QMainWindow, QWidget#central {{ background-color: {C.BG_DARK}; }}

QLabel {{ color: {C.TEXT}; font-size: 13px; }}
QLabel#header {{ font-size: 28px; font-weight: 800; color: {C.WHITE}; letter-spacing: 3px; }}
QLabel#subtitle {{ font-size: 11px; color: {C.TEXT_DIM}; letter-spacing: 1px; }}
QLabel#availableTag {{
    background-color: {C.GREEN_DIM}; color: {C.GREEN};
    border-radius: 6px; padding: 5px 12px; font-weight: 700; font-size: 13px;
}}
QLabel#engineLabel {{
    color: {C.TEXT_MUTED}; font-size: 11px; font-family: "Consolas","Fira Code",monospace;
}}

QPushButton {{
    border: none; border-radius: 8px; padding: 10px 24px;
    font-weight: 700; font-size: 13px; color: {C.WHITE};
}}
QPushButton#startBtn {{
    background-color: {C.GREEN}; color: {C.BG_DARKEST};
    min-width: 140px; font-size: 14px; padding: 12px 28px;
}}
QPushButton#startBtn:hover {{ background-color: #45d972; }}
QPushButton#startBtn:pressed {{ background-color: #3ac462; }}
QPushButton#startBtn:disabled {{ background-color: {C.TEXT_MUTED}; color: {C.BG_DARK}; }}

QPushButton#stopBtn {{ background-color: {C.RED}; min-width: 100px; }}
QPushButton#stopBtn:hover {{ background-color: #d93638; }}
QPushButton#stopBtn:disabled {{ background-color: {C.TEXT_MUTED}; color: {C.BG_DARK}; }}

QPushButton#exportBtn {{ background-color: {C.BLURPLE}; }}
QPushButton#exportBtn:hover {{ background-color: {C.BLURPLE_H}; }}

QPushButton#clearBtn {{
    background-color: transparent; border: 1px solid {C.BORDER}; color: {C.TEXT_DIM};
}}
QPushButton#clearBtn:hover {{ border-color: {C.TEXT_DIM}; color: {C.TEXT}; }}

QPushButton#claimBtn {{
    background-color: {C.CYAN}; color: {C.BG_DARKEST};
    padding: 3px 10px; font-size: 11px; border-radius: 4px; font-weight: 800;
}}
QPushButton#claimBtn:hover {{ background-color: #00b893; }}

QSpinBox, QComboBox, QLineEdit {{
    background-color: {C.BG_INPUT}; border: 1px solid {C.BORDER};
    border-radius: 6px; color: {C.TEXT}; padding: 7px 10px;
    font-size: 13px; min-height: 20px;
}}
QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{ border-color: {C.BLURPLE}; }}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox QAbstractItemView {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
    color: {C.TEXT}; selection-background-color: {C.BLURPLE};
}}
QSpinBox::up-button, QSpinBox::down-button {{ border: none; width: 16px; }}

QTableWidget {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
    border-radius: 8px; gridline-color: {C.BORDER};
    color: {C.TEXT}; font-size: 12px; selection-background-color: {C.BLURPLE};
}}
QTableWidget::item {{ padding: 6px 8px; border-bottom: 1px solid {C.BORDER}; }}
QHeaderView::section {{
    background-color: {C.BG_MID}; color: {C.TEXT_DIM}; border: none;
    border-bottom: 2px solid {C.BORDER}; padding: 8px 10px;
    font-weight: 700; font-size: 11px;
}}
QScrollBar:vertical {{
    background: {C.BG_DARKEST}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C.TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QGroupBox {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
    border-radius: 10px; margin-top: 14px; padding: 18px 14px 10px 14px;
    font-weight: 700; font-size: 12px; color: {C.TEXT_DIM};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 14px; padding: 0 6px; color: {C.TEXT_DIM};
}}

QTextEdit {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
    border-radius: 8px; color: {C.TEXT};
    font-family: "Consolas","Fira Code",monospace; font-size: 12px; padding: 8px;
}}
"""


# ═══════════════════════════════════════════════════════════════════════
#  Sparkline — live throughput chart
# ═══════════════════════════════════════════════════════════════════════

class Sparkline(QWidget):
    """Custom-painted rolling line chart with translucent fill."""

    def __init__(self, color: str = C.BLURPLE, max_pts: int = 80, parent=None):
        super().__init__(parent)
        self._data: List[float] = []
        self._max = max_pts
        self._color = QColor(color)
        self.setMinimumHeight(44)
        self.setMaximumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def push(self, value: float):
        self._data.append(value)
        if len(self._data) > self._max:
            self._data.pop(0)
        self.update()

    def paintEvent(self, _event):
        if len(self._data) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad = 2
        mx = max(self._data) or 1

        pts: List[QPointF] = []
        for i, v in enumerate(self._data):
            x = pad + i / max(self._max - 1, 1) * (w - 2 * pad)
            y = h - pad - (v / mx) * (h - 2 * pad)
            pts.append(QPointF(x, y))

        # Line
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        p.setPen(QPen(self._color, 2))
        p.drawPath(path)

        # Fill
        fill = QPainterPath(path)
        fill.lineTo(QPointF(pts[-1].x(), h))
        fill.lineTo(QPointF(pts[0].x(), h))
        fill.closeSubpath()
        fc = QColor(self._color)
        fc.setAlpha(35)
        p.fillPath(fill, QBrush(fc))
        p.end()


# ═══════════════════════════════════════════════════════════════════════
#  Stat card
# ═══════════════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, label: str, initial: str = "0", color: str = C.WHITE):
        super().__init__()
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {C.BG_CARD}; border: 1px solid {C.BORDER};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(1)

        self._val = QLabel(initial)
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {color};"
        )
        self._name = QLabel(label.upper())
        self._name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name.setStyleSheet(
            f"font-size: 10px; font-weight: 600; color: {C.TEXT_DIM}; letter-spacing: 1px;"
        )
        lay.addWidget(self._val)
        lay.addWidget(self._name)

    def set(self, v: str):
        self._val.setText(v)


# ═══════════════════════════════════════════════════════════════════════
#  Main window
# ═══════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    MAX_ROWS = 400

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHOTER")
        self.setMinimumSize(1000, 740)
        self.resize(1060, 830)

        self._worker: Optional[CheckerWorker] = None
        self._claim_threads: List[ClaimThread] = []
        self._available: List[str] = []
        self._results: List[tuple] = []
        self._rps_history: List[float] = []

        self._build()
        self._wire()

    # ── Build ────────────────────────────────────────────────────────

    def _build(self):
        cw = QWidget()
        cw.setObjectName("central")
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(22, 18, 22, 14)
        root.setSpacing(12)

        root.addLayout(self._mk_header())
        root.addWidget(self._mk_config())

        # Stats + sparkline
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.s_checked  = StatCard("Checked",  "0", C.BLURPLE)
        self.s_found    = StatCard("Found",    "0", C.GREEN)
        self.s_errors   = StatCard("Errors",   "0", C.RED)
        self.s_rate     = StatCard("Rate /s",  "0", C.ORANGE)
        for c in (self.s_checked, self.s_found, self.s_errors, self.s_rate):
            stats_row.addWidget(c)
        self.sparkline = Sparkline(C.BLURPLE, 80)
        stats_row.addWidget(self.sparkline, stretch=1)
        root.addLayout(stats_row)

        # Engine telemetry bar
        self.engine_label = QLabel("")
        self.engine_label.setObjectName("engineLabel")
        root.addWidget(self.engine_label)

        # Splitter: table / available
        sp = QSplitter(Qt.Orientation.Vertical)
        sp.setStyleSheet("QSplitter::handle { background: transparent; height: 5px; }")
        sp.addWidget(self._mk_table())
        sp.addWidget(self._mk_available())
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 1)
        root.addWidget(sp, stretch=1)

        root.addWidget(self._mk_log())

    def _mk_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(10)
        t = QLabel("SHOTER")
        t.setObjectName("header")
        h.addWidget(t)
        s = QLabel("Anthropic-Grade Discord Username Engine")
        s.setObjectName("subtitle")
        s.setAlignment(Qt.AlignmentFlag.AlignBottom)
        h.addWidget(s)
        h.addStretch()

        self.btn_start  = QPushButton("START")
        self.btn_start.setObjectName("startBtn")
        self.btn_stop   = QPushButton("STOP")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_export = QPushButton("EXPORT")
        self.btn_export.setObjectName("exportBtn")
        self.btn_clear  = QPushButton("CLEAR")
        self.btn_clear.setObjectName("clearBtn")
        for b in (self.btn_start, self.btn_stop, self.btn_export, self.btn_clear):
            h.addWidget(b)
        return h

    def _mk_config(self) -> QGroupBox:
        g = QGroupBox("ENGINE CONFIGURATION")
        gl = QGridLayout(g)
        gl.setSpacing(10)

        gl.addWidget(QLabel("Concurrency"), 0, 0)
        self.spin_conc = QSpinBox()
        self.spin_conc.setRange(2, 200)
        self.spin_conc.setValue(30)
        self.spin_conc.setToolTip("Initial AIMD window size (auto-adjusts)")
        gl.addWidget(self.spin_conc, 0, 1)

        gl.addWidget(QLabel("Mode"), 0, 2)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Smart (random + speculative)", "Exhaustive (all combos)"])
        gl.addWidget(self.combo_mode, 0, 3)

        gl.addWidget(QLabel("Min Len"), 0, 4)
        self.spin_min = QSpinBox()
        self.spin_min.setRange(2, 6)
        self.spin_min.setValue(3)
        gl.addWidget(self.spin_min, 0, 5)

        gl.addWidget(QLabel("Max Len"), 0, 6)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(2, 6)
        self.spin_max.setValue(4)
        gl.addWidget(self.spin_max, 0, 7)

        gl.addWidget(QLabel("Token (optional)"), 1, 0)
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText(
            "Leave empty = unauthenticated mode  |  Paste user token to enable CLAIM"
        )
        self.input_token.setEchoMode(QLineEdit.EchoMode.Password)
        gl.addWidget(self.input_token, 1, 1, 1, 7)
        return g

    def _mk_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Username", "Status", "Time (ms)", "Timestamp"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 200)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        return self.table

    def _mk_available(self) -> QGroupBox:
        g = QGroupBox("AVAILABLE USERNAMES")
        lay = QVBoxLayout(g)
        lay.setContentsMargins(10, 14, 10, 10)

        # Scroll area for tags
        self._avail_scroll = QScrollArea()
        self._avail_scroll.setWidgetResizable(True)
        self._avail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._avail_scroll.setStyleSheet("background: transparent;")

        self._avail_widget = QWidget()
        self._avail_layout = QHBoxLayout(self._avail_widget)
        self._avail_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._avail_layout.setSpacing(8)
        self._avail_layout.setContentsMargins(0, 0, 0, 0)

        self._avail_ph = QLabel("Found usernames will appear here...")
        self._avail_ph.setStyleSheet(f"color: {C.TEXT_MUTED}; font-style: italic;")
        self._avail_layout.addWidget(self._avail_ph)

        self._avail_scroll.setWidget(self._avail_widget)
        lay.addWidget(self._avail_scroll)
        return g

    def _mk_log(self) -> QTextEdit:
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(90)
        self.log_box.setPlaceholderText("Engine log...")
        return self.log_box

    # ── Wire ─────────────────────────────────────────────────────────

    def _wire(self):
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_clear.clicked.connect(self._on_clear)

    # ── Actions ──────────────────────────────────────────────────────

    def _on_start(self):
        tok = self.input_token.text().strip() or None
        conc = self.spin_conc.value()
        mn = self.spin_min.value()
        mx = max(mn, self.spin_max.value())
        self.spin_max.setValue(mx)
        mode = "smart" if self.combo_mode.currentIndex() == 0 else "exhaustive"

        self._worker = CheckerWorker(
            token=tok, concurrency=conc,
            min_len=mn, max_len=mx, mode=mode,
        )
        self._worker.username_result.connect(self._on_result)
        self._worker.stats_update.connect(self._on_stats)
        self._worker.engine_status.connect(self._on_engine)
        self._worker.log.connect(self._on_log)
        self._worker.done.connect(self._on_done)

        self._toggle(True)
        self._worker.start()
        self._on_log("Engine started")

    def _on_stop(self):
        if self._worker and self._worker.running:
            self._worker.stop()
            self._on_log("Stopping...")

    def _on_done(self):
        self._toggle(False)
        self._on_log("Engine stopped")
        if self._worker:
            t = time.time() - self._worker._t0 if self._worker._t0 else 1
            r = self._worker._checked / max(t, 0.001)
            self.s_checked.set(f"{self._worker._checked:,}")
            self.s_found.set(f"{self._worker._available:,}")
            self.s_errors.set(f"{self._worker._errors:,}")
            self.s_rate.set(f"{r:.1f}")

    def _toggle(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        for w in (self.spin_conc, self.combo_mode, self.spin_min,
                  self.spin_max, self.input_token):
            w.setEnabled(not running)

    # ── Result handler ───────────────────────────────────────────────

    def _on_result(self, name: str, avail: object, ms: float):
        now = datetime.now().strftime("%H:%M:%S")

        if avail is True:
            txt, clr = "AVAILABLE", C.GREEN
            self._available.append(name)
            self._add_tag(name)
        elif avail is False:
            txt, clr = "TAKEN", C.RED
        else:
            txt, clr = "ERROR", C.YELLOW

        self._results.append((name, txt, ms, now))

        # Insert at top
        self.table.insertRow(0)

        it_name = QTableWidgetItem(name)
        it_name.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        if avail is True:
            it_name.setForeground(QColor(C.GREEN))
        self.table.setItem(0, 0, it_name)

        it_st = QTableWidgetItem(txt)
        it_st.setForeground(QColor(clr))
        it_st.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        it_st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 1, it_st)

        it_ms = QTableWidgetItem(f"{ms:.0f}")
        it_ms.setForeground(QColor(C.TEXT_DIM))
        it_ms.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 2, it_ms)

        it_ts = QTableWidgetItem(now)
        it_ts.setForeground(QColor(C.TEXT_MUTED))
        it_ts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 3, it_ts)

        while self.table.rowCount() > self.MAX_ROWS:
            self.table.removeRow(self.table.rowCount() - 1)

    # ── Stats handler ────────────────────────────────────────────────

    def _on_stats(self, checked: int, found: int, errors: int, rps: float):
        self.s_checked.set(f"{checked:,}")
        self.s_found.set(f"{found:,}")
        self.s_errors.set(f"{errors:,}")
        self.s_rate.set(f"{rps:.1f}")
        self.sparkline.push(rps)

    # ── Engine telemetry ─────────────────────────────────────────────

    def _on_engine(self, aimd: int, budget: int, fp_health: list):
        dots = ""
        for h in fp_health:
            if h > 60:
                dots += f"<span style='color:{C.GREEN}'>●</span>"
            elif h > 20:
                dots += f"<span style='color:{C.YELLOW}'>●</span>"
            else:
                dots += f"<span style='color:{C.RED}'>●</span>"
        self.engine_label.setText(
            f"AIMD concurrency: <b>{aimd}</b>  |  "
            f"Budget: <b>{budget:,}</b>/9,500  |  "
            f"Fingerprints: {dots}"
        )

    # ── Log ──────────────────────────────────────────────────────────

    def _on_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(
            f"<span style='color:{C.TEXT_DIM}'>[{ts}]</span> {msg}"
        )

    # ── Available tags + claim ───────────────────────────────────────

    def _add_tag(self, name: str):
        if self._avail_ph:
            self._avail_ph.hide()
            self._avail_ph = None

        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        tag = QLabel(name)
        tag.setObjectName("availableTag")
        tag.setCursor(Qt.CursorShape.PointingHandCursor)
        tag.setToolTip("Click to copy")
        tag.mousePressEvent = lambda _e, u=name: self._copy(u)
        row.addWidget(tag)

        # Claim button (visible only when token is provided)
        if self.input_token.text().strip():
            btn = QPushButton("CLAIM")
            btn.setObjectName("claimBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c=False, u=name: self._claim(u))
            row.addWidget(btn)

        self._avail_layout.addWidget(container)

    def _copy(self, name: str):
        QApplication.clipboard().setText(name)
        self._on_log(f"Copied <b>{name}</b> to clipboard")

    def _claim(self, name: str):
        tok = self.input_token.text().strip()
        if not tok:
            self._on_log("Cannot claim — no token provided")
            return
        self._on_log(f"Claiming <b>{name}</b>...")
        ct = ClaimThread(name, tok)
        ct.result.connect(self._on_claim_result)
        self._claim_threads.append(ct)
        ct.start()

    def _on_claim_result(self, name: str, ok: bool, msg: str):
        if ok:
            self._on_log(f"<span style='color:{C.GREEN}'>CLAIMED <b>{name}</b>!</span>")
        else:
            self._on_log(f"<span style='color:{C.RED}'>Claim failed ({name}): {msg}</span>")

    # ── Export / Clear ───────────────────────────────────────────────

    def _on_export(self):
        if not self._available:
            self._on_log("Nothing to export")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "available_usernames.txt", "Text (*.txt)"
        )
        if path:
            with open(path, "w") as f:
                for n in self._available:
                    f.write(n + "\n")
            self._on_log(f"Exported {len(self._available)} usernames → {path}")

    def _on_clear(self):
        self.table.setRowCount(0)
        self._results.clear()
        self._available.clear()

        while self._avail_layout.count():
            it = self._avail_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        self._avail_ph = QLabel("Found usernames will appear here...")
        self._avail_ph.setStyleSheet(f"color: {C.TEXT_MUTED}; font-style: italic;")
        self._avail_layout.addWidget(self._avail_ph)

        for card in (self.s_checked, self.s_found, self.s_errors, self.s_rate):
            card.set("0")
        self.engine_label.setText("")
        self._on_log("Cleared")

    # ── Cleanup ──────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._worker and self._worker.running:
            self._worker.stop()
            self._worker.wait(3000)
        event.accept()
