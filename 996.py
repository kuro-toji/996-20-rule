#!/usr/bin/env python3
"""
996 Protocol — Deep Work Timer
================================
Rules:
  996  → Work hard. Count down 12 hours. No wasted time.
  20-20-20 → Every 20 min, look 20 ft away for 20 sec.

Features:
  - 12-hour countdown timer with 20-20-20 eye protection
  - Clipboard notes auto-capture (remember important snippets)
  - Auto-save every 5 seconds + on all state changes
  - Streak tracking with weekly view
  - System tray support with minimize-to-tray
  - Dark/Light theme toggle
  - Keyboard shortcuts for all actions

Usage:
  pip install PyQt5
  python 996.py

Data saved to: ~/.996protocol/data.json
GitHub: https://github.com/kuro-toji/996-20-rule
"""

import sys
import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QProgressBar,
        QDialog,
        QSystemTrayIcon,
        QMenu,
        QMessageBox,
        QFrame,
        QGridLayout,
        QAction,
    )
    from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
    from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
    from PyQt6.QtGui import QFont, QColor, QPalette, QKeyEvent, QPainter, QBrush

    PyQt6 = True
except ImportError:
    try:
        from PyQt5.QtWidgets import (
            QApplication,
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTextEdit,
            QProgressBar,
            QDialog,
            QSystemTrayIcon,
            QMenu,
            QMessageBox,
            QFrame,
            QGridLayout,
            QAction,
        )
        from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
        from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
        from PyQt5.QtGui import QFont, QColor, QPalette, QKeyEvent, QPainter, QBrush

        PyQt6 = False
    except ImportError:
        print("PyQt5 or PyQt6 is required. Install with: pip install PyQt5")
        sys.exit(1)


DATA_DIR = Path.home() / ".996protocol"
DATA_FILE = DATA_DIR / "data.json"
CLIPBOARD_FILE = DATA_DIR / "clipboard_notes.json"


# ============================================================
# CLIPBOARD NOTES SYSTEM
# ============================================================
# Auto-capture clipboard content, store snippets with timestamps
# Supports manual add, auto-capture, and history browsing

class ClipboardMonitor:
    """Monitor system clipboard and store important snippets."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.last_content = ""
        self.notes = []
        self.load_notes()
        
    def load_notes(self):
        """Load clipboard notes from file."""
        if CLIPBOARD_FILE.exists():
            try:
                with open(CLIPBOARD_FILE, "r") as f:
                    self.notes = json.load(f)
            except:
                self.notes = []
    
    def save_notes(self):
        """Save clipboard notes to file."""
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)
        with open(CLIPBOARD_FILE, "w") as f:
            json.dump(self.notes[-100:], f, indent=2)  # Keep last 100 notes
    
    def capture_clipboard(self, text):
        """Capture and store clipboard content."""
        if not text or text.strip() == "" or text == self.last_content:
            return
        
        self.last_content = text
        note = {
            "content": text[:500],  # Limit to 500 chars
            "timestamp": datetime.now().isoformat(),
            "tags": self._extract_tags(text)
        }
        
        # Avoid duplicates (check last 10)
        for existing in self.notes[-10:]:
            if existing["content"][:100] == note["content"][:100]:
                return
        
        self.notes.append(note)
        self.save_notes()
        return note
    
    def _extract_tags(self, text):
        """Extract tags from text (URLs, code blocks, etc)."""
        tags = []
        if text.startswith("http"):
            tags.append("url")
        if any(lang in text.lower() for lang in ["function", "def ", "class ", "const ", "let "]):
            tags.append("code")
        if len(text) < 50:
            tags.append("short")
        return tags
    
    def add_manual_note(self, content):
        """Manually add a note."""
        note = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tags": ["manual"]
        }
        self.notes.append(note)
        self.save_notes()
        return note
    
    def get_recent_notes(self, limit=10):
        """Get recent notes."""
        return self.notes[-limit:][::-1]
    
    def delete_note(self, index):
        """Delete a note by index (from end)."""
        if 0 <= index < len(self.notes):
            del self.notes[-(index + 1)]
            self.save_notes()
    
    def clear_all(self):
        """Clear all clipboard notes."""
        self.notes = []
        self.save_notes()


# ============================================================
# SECTION 1: 20-20-20 EYE PROTECTION SYSTEM
# ============================================================
# 20-minute timer triggers fullscreen overlay, 20-second countdown
# Unskippable for first 10 seconds

class EyeBreakOverlay(QWidget):
    dismiss_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.countdown = 20
        self.can_dismiss = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.label1 = QLabel("EYE BREAK")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label1.setStyleSheet(
            "color: #8b7cf8; font-size: 16px; letter-spacing: 4px; font-weight: bold;"
        )

        self.label2 = QLabel("Look 20 feet away")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label2.setStyleSheet("color: white; font-size: 32px; font-weight: medium;")

        self.label3 = QLabel("Relax your focus completely")
        self.label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label3.setStyleSheet("color: #8a8a96; font-size: 14px;")

        self.countdown_label = QLabel("20")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet(
            "color: white; font-size: 120px; font-family: monospace;"
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(20)
        self.progress_bar.setValue(20)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #8b7cf8;
            }
        """)

        self.dismiss_label = QLabel("Press any key or click to dismiss")
        self.dismiss_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dismiss_label.setStyleSheet("color: #555; font-size: 12px;")
        self.dismiss_label.setVisible(False)

        layout.addWidget(self.label1)
        layout.addSpacing(20)
        layout.addWidget(self.label2)
        layout.addSpacing(8)
        layout.addWidget(self.label3)
        layout.addSpacing(40)
        layout.addWidget(self.countdown_label)
        layout.addSpacing(40)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(32)
        layout.addWidget(self.dismiss_label)

        self.setStyleSheet("background-color: #0a0a0a;")
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.countdown -= 1
        self.countdown_label.setText(str(self.countdown))
        self.progress_bar.setValue(self.countdown)

        if self.countdown <= 10:
            self.can_dismiss = True
            self.dismiss_label.setVisible(True)

        if self.countdown <= 0:
            self.timer.stop()
            self.dismiss_signal.emit()
            self.close()

    def keyPressEvent(self, event):
        if self.can_dismiss:
            self.dismiss_signal.emit()
            self.close()
        else:
            pass

    def mousePressEvent(self, event):
        if self.can_dismiss:
            self.dismiss_signal.emit()
            self.close()
        else:
            pass


# ============================================================
# SECTION 2: MAIN TIMER (996 COUNTDOWN)
# ============================================================
# Large countdown timer, 4 control buttons, status bar, progress bar

class Protocol996(QWidget):
    def __init__(self):
        super().__init__()

        self.state = "idle"
        self.remaining_seconds = 12 * 3600
        self.eye_timer_seconds = 0
        self.eye_breaks_today = 0
        self.stop_cycles = 0
        self.worked_seconds_today = 0
        self.last_mode = None
        self.eye_protection_enabled = False
        self.overlay = None
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.theme = "dark"
        self.always_on_top = False
        self.tray_icon = None

        self.clipboard_notes = ClipboardMonitor(self)
        self.load_data()

        # Real-time clock timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        # Main session timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)

        # Note auto-save timer
        self.note_timer = QTimer()
        self.note_timer.setSingleShot(True)
        self.note_timer.timeout.connect(self.save_note)

        self.setup_ui()
        self.apply_theme()
        self.center_on_screen()
        self.setup_clipboard_monitor()
        self.update_clock() # Initial call

    def update_clock(self):
        """Update the real-time clock display."""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        if hasattr(self, 'clock_label'):
            self.clock_label.setText(current_time)

    def setup_clipboard_monitor(self):
        """Setup periodic clipboard check."""
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(3000)  # Check every 3 seconds
    
    def check_clipboard(self):
        """Check clipboard for new content."""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text and len(text) > 10:  # Ignore very short clips
                note = self.clipboard_notes.capture_clipboard(text)
                if note:
                    self.refresh_clipboard_display()
        except:
            pass
    
    def center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def setup_ui(self):
        self.setWindowTitle("996 Protocol")
        self.setMinimumSize(420, 780)
        self.resize(460, 820)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ============================================================
        # HEADER: Title + Clock + Always on top toggle
        # ============================================================
        header_layout = QHBoxLayout()
        title_label = QLabel("996 Protocol")
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #1fbe82; letter-spacing: 1px;")
        
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setStyleSheet("font-size: 18px; font-family: monospace; font-weight: bold; color: #8a8a96; margin-left: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.clock_label)
        header_layout.addStretch()
        
        self.always_on_top_btn = QPushButton("📌")
        self.always_on_top_btn.setFixedSize(32, 32)
        self.always_on_top_btn.setToolTip("Always on top")
        self.always_on_top_btn.clicked.connect(self.toggle_always_on_top)
        self.always_on_top_btn.setStyleSheet("border: none; background: transparent; font-size: 16px;")
        header_layout.addWidget(self.always_on_top_btn)

        main_layout.addLayout(header_layout)

        # ============================================================
        # TIMER CARD
        # ============================================================
        timer_card = QFrame()
        timer_card.setObjectName("timerCard")
        timer_layout = QVBoxLayout()
        timer_layout.setContentsMargins(15, 20, 15, 20)
        timer_layout.setSpacing(10)

        self.timer_label = QLabel("12:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 64px; font-family: monospace; font-weight: 800; color: #f0f0f0;")
        timer_layout.addWidget(self.timer_label)

        self.status_label = QLabel("Status: Idle ⏹")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #8a8a96;")
        timer_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(12 * 3600)
        self.progress_bar.setValue(12 * 3600)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        timer_layout.addWidget(self.progress_bar)

        timer_card.setLayout(timer_layout)
        main_layout.addWidget(timer_card)

        # ============================================================
        # CONTROLS CARD (2x2 Grid)
        # ============================================================
        controls_card = QFrame()
        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(10)

        self.btn_start_2020 = QPushButton("▶ Start 20-20-20")
        self.btn_start_focus = QPushButton("▶ Focus Mode")
        self.btn_stop = QPushButton("⏸ Stop Session")
        self.btn_end_day = QPushButton("🏁 End Day")

        for btn in [self.btn_start_2020, self.btn_start_focus, self.btn_stop, self.btn_end_day]:
            btn.setMinimumHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_start_2020.clicked.connect(self.start_with_eye_protection)
        self.btn_start_focus.clicked.connect(self.start_focus_mode)
        self.btn_stop.clicked.connect(self.stop_session)
        self.btn_end_day.clicked.connect(self.end_day)

        controls_layout.addWidget(self.btn_start_2020, 0, 0)
        controls_layout.addWidget(self.btn_start_focus, 0, 1)
        controls_layout.addWidget(self.btn_stop, 1, 0)
        controls_layout.addWidget(self.btn_end_day, 1, 1)

        controls_card.setLayout(controls_layout)
        main_layout.addWidget(controls_card)

        # ============================================================
        # CLIPBOARD CARD
        # ============================================================
        clipboard_card = QFrame()
        clipboard_layout = QVBoxLayout()
        clipboard_layout.setSpacing(10)
        clipboard_layout.setContentsMargins(15, 15, 15, 15)
        
        clipboard_header = QHBoxLayout()
        clipboard_title = QLabel("📋 CLIPBOARD NOTES")
        clipboard_title.setStyleSheet("font-size: 10px; font-weight: 800; letter-spacing: 1.5px; color: #666;")
        clipboard_header.addWidget(clipboard_title)
        clipboard_header.addStretch()
        
        self.add_note_btn = QPushButton("+ Add")
        self.add_note_btn.setFixedSize(54, 24)
        self.add_note_btn.clicked.connect(self.show_add_note_dialog)
        self.add_note_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        clipboard_header.addWidget(self.add_note_btn)
        
        clipboard_layout.addLayout(clipboard_header)
        
        self.clipboard_list = QVBoxLayout()
        self.clipboard_list.setSpacing(6)
        self.refresh_clipboard_display()
        
        clipboard_layout.addLayout(self.clipboard_list)
        clipboard_card.setLayout(clipboard_layout)
        main_layout.addWidget(clipboard_card)

        # ============================================================
        # DAILY DASHBOARD CARD
        # ============================================================
        dashboard_card = QFrame()
        dashboard_layout = QVBoxLayout()
        dashboard_layout.setContentsMargins(15, 15, 15, 15)
        dashboard_layout.setSpacing(12)

        self.dashboard_label = QLabel(f"TODAY — {self.get_formatted_date().upper()}")
        self.dashboard_label.setStyleSheet("font-size: 10px; font-weight: 800; letter-spacing: 1.5px; color: #666;")
        dashboard_layout.addWidget(self.dashboard_label)

        # Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        # Time Stats
        time_frame = QFrame()
        time_frame.setStyleSheet("background: transparent; border: none;")
        time_vbox = QVBoxLayout(time_frame)
        time_vbox.setContentsMargins(0, 0, 0, 0)
        time_vbox.setSpacing(2)
        time_lbl = QLabel("TIME WORKED")
        time_lbl.setStyleSheet("font-size: 9px; color: #8a8a96; font-weight: bold;")
        self.time_worked_label = QLabel("00:00:00")
        self.time_worked_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #1fbe82;")
        time_vbox.addWidget(time_lbl)
        time_vbox.addWidget(self.time_worked_label)
        
        # Break Stats
        break_frame = QFrame()
        break_frame.setStyleSheet("background: transparent; border: none;")
        break_vbox = QVBoxLayout(break_frame)
        break_vbox.setContentsMargins(0, 0, 0, 0)
        break_vbox.setSpacing(2)
        break_lbl = QLabel("EYE BREAKS")
        break_lbl.setStyleSheet("font-size: 9px; color: #8a8a96; font-weight: bold;")
        self.breaks_count_label = QLabel("0")
        self.breaks_count_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #8b7cf8;")
        break_vbox.addWidget(break_lbl)
        break_vbox.addWidget(self.breaks_count_label)

        stats_layout.addWidget(time_frame)
        stats_layout.addWidget(break_frame)
        dashboard_layout.addLayout(stats_layout)

        # Note Area
        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText("📝 Write what you did today...")
        self.note_text.setMinimumHeight(70)
        self.note_text.setMaximumHeight(80)
        self.note_text.textChanged.connect(self.on_note_changed)
        dashboard_layout.addWidget(self.note_text)

        # Streak Row
        streak_vbox = QVBoxLayout()
        streak_vbox.setSpacing(6)
        streak_title = QLabel("WEEKLY PROGRESS")
        streak_title.setStyleSheet("font-size: 9px; font-weight: bold; color: #666; letter-spacing: 1px;")
        streak_vbox.addWidget(streak_title)

        self.streak_layout = QHBoxLayout()
        self.streak_layout.setSpacing(8)
        self.streak_squares = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in day_names:
            container = QVBoxLayout()
            container.setSpacing(4)
            square = QFrame()
            square.setFixedSize(32, 32)
            square.setStyleSheet("background-color: #2a2a2e; border-radius: 6px;")
            container.addWidget(square, 0, Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(day[0])
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
            container.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
            self.streak_layout.addLayout(container)
            self.streak_squares.append(square)
        
        streak_vbox.addLayout(self.streak_layout)
        dashboard_layout.addLayout(streak_vbox)

        dashboard_card.setLayout(dashboard_layout)
        main_layout.addWidget(dashboard_card)

        # ============================================================
        # FOOTER
        # ============================================================
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.theme_btn = QPushButton("🌙 Dark")
        self.theme_btn.setFixedSize(80, 28)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setStyleSheet("font-size: 11px; padding: 0; background: #2a2a2e; color: #a0a0a0; border-radius: 4px;")
        footer_layout.addWidget(self.theme_btn)
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

        self.load_today_data()
        self.update_streak_display()
        self.update_buttons_state()
    
    def refresh_clipboard_display(self):
        """Refresh the clipboard notes list display."""
        while self.clipboard_list.count():
            child = self.clipboard_list.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        notes = self.clipboard_notes.get_recent_notes(5)
        if not notes:
            empty_label = QLabel("📎 No notes yet. Copy something to capture.")
            empty_label.setStyleSheet("font-size: 11px; color: #555; padding: 10px;")
            self.clipboard_list.addWidget(empty_label)
        else:
            for i, note in enumerate(notes):
                note_widget = self.create_clipboard_note_widget(note, i)
                self.clipboard_list.addWidget(note_widget)
    
    def create_clipboard_note_widget(self, note, index):
        """Create a single clipboard note widget."""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Content
        content = note["content"][:70] + ("..." if len(note["content"]) > 70 else "")
        content_label = QLabel(content)
        content_label.setStyleSheet("font-size: 11px; color: #a0a0a0;")
        content_label.setWordWrap(False)
        content_label.setToolTip(note["content"][:200])
        layout.addWidget(content_label, 1)
        
        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(26, 26)
        copy_btn.setStyleSheet("border: none; background: transparent; font-size: 11px;")
        copy_btn.clicked.connect(lambda: self.copy_note(note["content"]))
        copy_btn.setToolTip("Copy to clipboard")
        layout.addWidget(copy_btn)
        
        # Delete button
        del_btn = QPushButton("×")
        del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px; color: #555;")
        del_btn.clicked.connect(lambda: self.delete_clipboard_note(index))
        del_btn.setToolTip("Delete note")
        layout.addWidget(del_btn)
        
        widget.setLayout(layout)
        return widget
    
    def copy_note(self, content):
        """Copy a note to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
    
    def delete_clipboard_note(self, index):
        """Delete a clipboard note."""
        self.clipboard_notes.delete_note(index)
        self.refresh_clipboard_display()
    
    def show_add_note_dialog(self):
        """Show dialog to add a manual note."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Note")
        dialog.setFixedSize(400, 180)
        dialog.setStyleSheet("QDialog { background-color: #1e1e21; }")
        
        layout = QVBoxLayout()
        
        label = QLabel("Enter note content:")
        label.setStyleSheet("color: #f0f0f0;")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Type your note here...")
        text_edit.setMinimumHeight(80)
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #333; color: #f0f0f0; padding: 8px 16px;")
        cancel_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_manual_note(text_edit.toPlainText(), dialog))
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_manual_note(self, content, dialog):
        """Save a manual note."""
        if content.strip():
            self.clipboard_notes.add_manual_note(content.strip())
            self.refresh_clipboard_display()
        dialog.close()
    
    def get_formatted_date(self):
        return datetime.now().strftime("%A, %d %B %Y")

    def get_today_key(self):
        return date.today().isoformat()

    def timer_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.worked_seconds_today += 1
            self.update_timer_display()

        if self.eye_protection_enabled:
            self.eye_timer_seconds += 1
            if self.eye_timer_seconds >= 1200:
                self.trigger_eye_break()

        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.show_day_complete()

    def update_timer_display(self):
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.progress_bar.setValue(self.remaining_seconds)

        if self.tray_icon:
            if self.remaining_seconds > 0:
                remaining_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.tray_icon.setToolTip(f"996 Protocol - {remaining_str} remaining")

    def update_buttons_state(self):
        """Update button states based on current state."""
        if self.state == "running":
            self.btn_start_2020.setText("⟳ Running...")
            self.btn_start_focus.setText("⟳ Running (focus)...")
            self.btn_start_2020.setEnabled(False)
            self.btn_start_focus.setEnabled(False)
            self.progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #1fbe82; }"
            )
        elif self.state == "paused":
            self.btn_start_2020.setText("▶ Resume 20-20-20")
            self.btn_start_focus.setText("▶ Resume (focus)")
            self.btn_start_2020.setEnabled(True)
            self.btn_start_focus.setEnabled(True)
            self.progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #f0a830; }"
            )
        else:
            self.btn_start_2020.setText("▶ Start 20-20-20")
            self.btn_start_focus.setText("▶ Start (focus mode)")
            self.btn_start_2020.setEnabled(True)
            self.btn_start_focus.setEnabled(True)
            self.progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #1fbe82; }"
            )

    def start_with_eye_protection(self):
        if self.state == "paused" and self.last_mode == "eye_protection":
            # Resume from pause
            self.state = "running"
            self.timer.start(1000)
            self.status_label.setText("Status: Running ✓")
            self.status_label.setStyleSheet("color: #1fbe82; font-weight: bold;")
            self.auto_save_timer.start(5000)
            self.save_data()
            self.update_buttons_state()
            return
        
        self.state = "running"
        self.eye_protection_enabled = True
        self.last_mode = "eye_protection"
        self.timer.start(1000)
        self.status_label.setText("Status: Running ✓")
        self.status_label.setStyleSheet("color: #1fbe82; font-weight: bold;")
        self.progress_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #1fbe82; }"
        )
        self.auto_save_timer.start(5000)
        self.save_data()
        self.update_buttons_state()

    def start_focus_mode(self):
        if self.state == "paused" and self.last_mode == "focus":
            # Resume from pause
            self.state = "running"
            self.timer.start(1000)
            self.status_label.setText("Status: Running (focus) ✓")
            self.status_label.setStyleSheet("color: #1fbe82; font-weight: bold;")
            self.auto_save_timer.start(5000)
            self.save_data()
            self.update_buttons_state()
            return
        
        self.state = "running"
        self.eye_protection_enabled = False
        self.last_mode = "focus"
        self.timer.start(1000)
        self.status_label.setText("Status: Running (focus) ✓")
        self.status_label.setStyleSheet("color: #1fbe82; font-weight: bold;")
        self.progress_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #1fbe82; }"
        )
        self.auto_save_timer.start(5000)
        self.save_data()
        self.update_buttons_state()

    def stop_session(self):
        self.timer.stop()
        self.auto_save_timer.stop()
        self.state = "paused"
        self.status_label.setText("Status: Paused ⏸")
        self.status_label.setStyleSheet("color: #f0a830; font-weight: bold;")
        self.stop_cycles += 1
        self.save_data()  # Immediate save on stop
        self.update_buttons_state()

    def end_day(self):
        self.timer.stop()
        self.auto_save_timer.stop()

        self.save_session()

        dialog = QDialog(self)
        dialog.setWindowTitle("End of Day")
        dialog.setFixedSize(400, 280)
        dialog.setStyleSheet("QDialog { background-color: #1e1e21; }")
        
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("🎉 Day Complete!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1fbe82;")
        layout.addWidget(title)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        date_label = QLabel(f"📅 Date: {self.get_formatted_date()}")
        date_label.setStyleSheet("color: #a0a0a0;")
        
        worked_label = QLabel(f"⏱ Time worked: {self.format_time(self.worked_seconds_today)}")
        worked_label.setStyleSheet("color: #1fbe82; font-size: 16px; font-weight: bold;")
        
        breaks_label = QLabel(f"👁 Eye breaks: {self.eye_breaks_today}")
        breaks_label.setStyleSheet("color: #8b7cf8;")
        
        cycles_label = QLabel(f"⏸ Stop/resume cycles: {self.stop_cycles}")
        cycles_label.setStyleSheet("color: #a0a0a0;")
        
        info_layout.addWidget(date_label)
        info_layout.addWidget(worked_label)
        info_layout.addWidget(breaks_label)
        info_layout.addWidget(cycles_label)
        layout.addLayout(info_layout)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #1fbe82; color: #0e0e0f; padding: 10px 20px; font-weight: bold;")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

        self.reset_day()
        self.save_data()

    def reset_day(self):
        self.state = "idle"
        self.remaining_seconds = 12 * 3600
        self.eye_timer_seconds = 0
        self.eye_breaks_today = 0
        self.stop_cycles = 0
        self.worked_seconds_today = 0
        self.eye_protection_enabled = False
        self.last_mode = None

        self.timer_label.setText("12:00:00")
        self.progress_bar.setValue(12 * 3600)
        self.status_label.setText("Status: Idle ⏹")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.progress_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #1fbe82; }"
        )

        self.time_worked_label.setText("00:00:00")
        self.breaks_count_label.setText("0")
        self.update_buttons_state()
        self.refresh_clipboard_display()
        
        # Clear today's clipboard notes on new day
        self.clipboard_notes.clear_all()

    def trigger_eye_break(self):
        self.timer.stop()

        self.overlay = EyeBreakOverlay()
        self.overlay.dismiss_signal.connect(self.on_eye_break_dismissed)
        self.overlay.showFullScreen()

    def on_eye_break_dismissed(self):
        self.overlay = None
        self.eye_breaks_today += 1
        self.breaks_count_label.setText(str(self.eye_breaks_today))

        if self.state == "running":
            self.eye_timer_seconds = 0
            self.timer.start(1000)

    def show_day_complete(self):
        if sys.platform == "win32":
            import winsound
            winsound.Beep(440, 500)
        
        self.status_label.setText("🎉 Day complete!")
        self.status_label.setStyleSheet("color: #1fbe82; font-weight: bold; font-size: 18px;")

        dialog = QDialog(self)
        dialog.setWindowTitle("Day Complete")
        dialog.setStyleSheet("QDialog { background-color: #1e1e21; }")
        layout = QVBoxLayout()
        
        title = QLabel("🎉 Day Complete!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1fbe82;")
        layout.addWidget(title)
        
        msg = QLabel("Great work! You completed the 996 session.")
        msg.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(msg)
        
        close_btn = QPushButton("OK")
        close_btn.setStyleSheet("background-color: #1fbe82; color: #0e0e0f; padding: 10px 20px;")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def on_note_changed(self):
        self.note_timer.start(2000)

    def save_note(self):
        self.save_data()

    # ============================================================
    # SECTION 3: DATA PERSISTENCE
    # ============================================================
    # JSON save/load to ~/.996protocol/data.json, auto-save triggers, load on startup

    def load_data(self):
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)

        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r") as f:
                    self.data = json.load(f)
            except:
                self.data = self.get_default_data()
        else:
            self.data = self.get_default_data()

    def get_default_data(self):
        return {
            "sessions": {},
            "streak": {},
            "settings": {
                "theme": "dark",
                "always_on_top": False,
                "eye_protection_default": True,
            },
        }

    def save_data(self):
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)

        self.data["settings"]["theme"] = self.theme
        self.data["settings"]["always_on_top"] = self.always_on_top

        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def auto_save(self):
        self.save_data()

    def save_session(self):
        today = self.get_today_key()
        self.data["sessions"][today] = {
            "worked_seconds": self.worked_seconds_today,
            "eye_breaks": self.eye_breaks_today,
            "stop_cycles": self.stop_cycles,
            "note": self.note_text.toPlainText(),
            "completed": self.remaining_seconds <= 0,
        }

        if self.worked_seconds_today >= 14400:  # 4 hours
            self.data["streak"][today] = True

        self.save_data()
        self.update_streak_display()

    def load_today_data(self):
        today = self.get_today_key()
        if today in self.data.get("sessions", {}):
            session = self.data["sessions"][today]
            self.worked_seconds_today = session.get("worked_seconds", 0)
            self.eye_breaks_today = session.get("eye_breaks", 0)
            self.stop_cycles = session.get("stop_cycles", 0)
            self.note_text.setPlainText(session.get("note", ""))

            self.time_worked_label.setText(self.format_time(self.worked_seconds_today))
            self.breaks_count_label.setText(str(self.eye_breaks_today))

        self.theme = self.data.get("settings", {}).get("theme", "dark")
        self.always_on_top = self.data.get("settings", {}).get("always_on_top", False)

    def update_streak_display(self):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_str = day.isoformat()
            square = self.streak_squares[i]

            if day_str in self.data.get("streak", {}) and self.data["streak"][day_str]:
                square.setStyleSheet("background-color: #1fbe82; border: none; border-radius: 6px;")
            else:
                square.setStyleSheet("background-color: #2a2a2e; border: none; border-radius: 6px;")

            if day == today:
                square.setStyleSheet(square.styleSheet() + " border: 2px solid #1fbe82;")

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()
        self.theme_btn.setText("☀️ Light" if self.theme == "light" else "🌙 Dark")
        self.save_data()

    def apply_theme(self):
        if self.theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #0c0c0d;
                    color: #e0e0e0;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                QFrame {
                    background-color: #161618;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                }
                QFrame#timerCard {
                    background-color: #1a1a1c;
                    border: 1px solid rgba(31, 190, 130, 0.2);
                }
                QTextEdit {
                    background-color: #0c0c0d;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: #d1d1d1;
                    font-size: 13px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #1fbe82;
                    color: #0c0c0d;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2fd692;
                }
                QPushButton:pressed {
                    background-color: #1aa671;
                }
                QPushButton:disabled {
                    background-color: #2a2a2e;
                    color: #555;
                }
                QLabel {
                    color: #e0e0e0;
                    border: none;
                    background: transparent;
                }
                QProgressBar {
                    background-color: #2a2a2e;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #1fbe82;
                    border-radius: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    color: #1a1a1a;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid rgba(0, 0, 0, 0.06);
                    border-radius: 12px;
                }
                QFrame#timerCard {
                    background-color: #ffffff;
                    border: 1px solid rgba(31, 190, 130, 0.3);
                }
                QTextEdit {
                    background-color: #fcfcfc;
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    border-radius: 8px;
                    color: #2a2a2a;
                    font-size: 13px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #1fbe82;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2fd692;
                }
                QPushButton:pressed {
                    background-color: #1aa671;
                }
                QPushButton:disabled {
                    background-color: #e9ecef;
                    color: #adb5bd;
                }
                QLabel {
                    color: #1a1a1a;
                    border: none;
                    background: transparent;
                }
                QProgressBar {
                    background-color: #e9ecef;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #1fbe82;
                    border-radius: 2px;
                }
            """)

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self.save_data()
        
        if self.always_on_top:
            self.always_on_top_btn.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #1fbe82;")
        else:
            self.always_on_top_btn.setStyleSheet("border: none; background: transparent; font-size: 16px;")

    # ============================================================
    # SECTION 4: KEYBOARD SHORTCUTS
    # ============================================================
    # Ctrl+S stop, Ctrl+R resume, Ctrl+E end day, Ctrl+T toggle always-on-top, Ctrl+Q quit

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.stop_session()
                return
            elif event.key() == Qt.Key_R:
                if self.last_mode == "eye_protection":
                    self.start_with_eye_protection()
                elif self.last_mode == "focus":
                    self.start_focus_mode()
                return
            elif event.key() == Qt.Key_E:
                self.end_day()
                return
            elif event.key() == Qt.Key_T:
                self.toggle_always_on_top()
                return
            elif event.key() == Qt.Key_Q:
                self.close()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.state == "running":
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Session Running")
            dialog.setText("Session is running. End day and quit?")
            dialog.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            dialog.button(QMessageBox.Yes).setText("End day & quit")
            dialog.button(QMessageBox.No).setText("Just minimize")

            result = dialog.exec()

            if result == QMessageBox.Yes:
                self.end_day()
                event.accept()
            elif result == QMessageBox.No:
                event.ignore()
                self.hide()
                if self.tray_icon:
                    self.tray_icon.show()
            else:
                event.ignore()
        else:
            self.save_data()
            event.accept()

    # ============================================================
    # SECTION 5: SYSTEM TRAY
    # ============================================================
    # Minimize to tray, right-click menu (Show, Stop session, End day, Quit)

    def setup_system_tray(self):
        """Setup system tray icon with menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("996 Protocol - Idle")

        menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        stop_action = QAction("Stop session", self)
        stop_action.triggered.connect(self.stop_session)
        menu.addAction(stop_action)

        end_action = QAction("End day", self)
        end_action.triggered.connect(self.end_day)
        menu.addAction(end_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.show)
        self.tray_icon.show()

    def setup_tray(self):
        """Legacy alias for setup_system_tray."""
        self.setup_system_tray()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("996 Protocol")

    window = Protocol996()
    window.setup_tray()
    window.show()

    sys.exit(app.exec())