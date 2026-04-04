#!/usr/bin/env python3
"""
996 Protocol — Deep Work Timer
================================
Rules:
  996  → Work hard. Count down 12 hours. No wasted time.
  20-20-20 → Every 20 min, look 20 ft away for 20 sec.

Usage:
  pip install PyQt5
  python 996.py

Data saved to: ~/.996protocol/data.json
GitHub: https://github.com/kuro-toji/996-20-rule
"""

import sys
import os
import json
from datetime import datetime, date
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTextEdit, QProgressBar, QDialog, QSystemTrayIcon,
        QMenu, QMessageBox, QFrame, QGridLayout
    )
    from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
    from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QKeyEvent, QPainter, QBrush
    PyQt6 = True
except ImportError:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            QPushButton, QTextEdit, QProgressBar, QDialog, QSystemTrayIcon,
            QMenu, QMessageBox, QFrame, QGridLayout
        )
        from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QEvent
        from PyQt5.QtGui import QFont, QColor, QPalette, QAction, QKeyEvent, QPainter, QBrush
        PyQt6 = False
    except ImportError:
        print("PyQt5 or PyQt6 is required. Install with: pip install PyQt5")
        sys.exit(1)


DATA_DIR = Path.home() / ".996protocol"
DATA_FILE = DATA_DIR / "data.json"


# ============================================================
# SECTION 2: 20-20-20 EYE PROTECTION SYSTEM
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
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        self.label1 = QLabel("EYE BREAK")
        self.label1.setAlignment(Qt.AlignCenter)
        self.label1.setStyleSheet("color: #8b7cf8; font-size: 16px; letter-spacing: 4px; font-weight: bold;")
        
        self.label2 = QLabel("Look 20 feet away")
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet("color: white; font-size: 32px; font-weight: medium;")
        
        self.label3 = QLabel("Relax your focus completely")
        self.label3.setAlignment(Qt.AlignCenter)
        self.label3.setStyleSheet("color: #8a8a96; font-size: 14px;")
        
        self.countdown_label = QLabel("20")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: white; font-size: 120px; font-family: monospace;")
        
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
        self.dismiss_label.setAlignment(Qt.AlignCenter)
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
# SECTION 1: MAIN TIMER (996 COUNTDOWN)
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
        
        self.load_data()
        self.setup_ui()
        self.apply_theme()
        self.center_on_screen()
        
    def center_on_screen(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def setup_ui(self):
        self.setWindowTitle("996 Protocol")
        self.setMinimumSize(400, 600)
        self.resize(480, 720)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.always_on_top_btn = QPushButton("📌")
        self.always_on_top_btn.setFixedSize(30, 30)
        self.always_on_top_btn.setToolTip("Always on top")
        self.always_on_top_btn.clicked.connect(self.toggle_always_on_top)
        self.always_on_top_btn.setStyleSheet("border: none; background: transparent; font-size: 16px;")
        header_layout.addWidget(self.always_on_top_btn)
        
        main_layout.addLayout(header_layout)
        
        # ============================================================
        # SECTION 1: MAIN TIMER (996 COUNTDOWN)
        # ============================================================
        # Large countdown timer, 4 control buttons, status bar, progress bar
        
        self.timer_label = QLabel("12:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 72px; font-family: monospace; font-weight: bold;")
        main_layout.addWidget(self.timer_label)
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.btn_start_2020 = QPushButton("Start 20-20-20")
        self.btn_start_2020.setCursor(Qt.PointingHandCursor)
        self.btn_start_2020.clicked.connect(self.start_with_eye_protection)
        
        self.btn_start_focus = QPushButton("Start (no 20-20-20)")
        self.btn_start_focus.setCursor(Qt.PointingHandCursor)
        self.btn_start_focus.clicked.connect(self.start_focus_mode)
        
        self.btn_stop = QPushButton("Stop session")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_session)
        
        self.btn_end_day = QPushButton("End day")
        self.btn_end_day.setCursor(Qt.PointingHandCursor)
        self.btn_end_day.clicked.connect(self.end_day)
        
        for btn in [self.btn_start_2020, self.btn_start_focus, self.btn_stop, self.btn_end_day]:
            btn.setMinimumHeight(40)
        
        button_layout.addWidget(self.btn_start_2020)
        button_layout.addWidget(self.btn_start_focus)
        button_layout.addWidget(self.btn_stop)
        button_layout.addWidget(self.btn_end_day)
        
        main_layout.addLayout(button_layout)
        
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(12 * 3600)
        self.progress_bar.setValue(12 * 3600)
        self.progress_bar.setFixedHeight(4)
        main_layout.addWidget(self.progress_bar)
        
        self.eye_break_label = QLabel("Eye breaks today: 0")
        self.eye_break_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.eye_break_label)
        
        # ============================================================
        # SECTION 3: DAILY DASHBOARD
        # ============================================================
        # Date header, notes textarea, stat cards (time worked, eye breaks)
        
        self.dashboard_label = QLabel(f"Today — {self.get_formatted_date()}")
        self.dashboard_label.setStyleSheet("font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;")
        main_layout.addWidget(self.dashboard_label)
        
        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText("Write what you did today... (research, books read, tasks completed)")
        self.note_text.setMinimumHeight(120)
        self.note_text.textChanged.connect(self.on_note_changed)
        main_layout.addWidget(self.note_text)
        
        stats_layout = QHBoxLayout()
        
        time_card = QFrame()
        time_card.setFrameShape(QFrame.StyledPanel)
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("Time worked"))
        self.time_worked_label = QLabel("00:00:00")
        self.time_worked_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        time_layout.addWidget(self.time_worked_label)
        time_card.setLayout(time_layout)
        
        breaks_card = QFrame()
        breaks_card.setFrameShape(QFrame.StyledPanel)
        breaks_layout = QVBoxLayout()
        breaks_layout.addWidget(QLabel("Eye breaks"))
        self.breaks_count_label = QLabel("0")
        self.breaks_count_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        breaks_layout.addWidget(self.breaks_count_label)
        breaks_card.setLayout(breaks_layout)
        
        stats_layout.addWidget(time_card)
        stats_layout.addWidget(breaks_card)
        
        main_layout.addLayout(stats_layout)
        
        # ============================================================
        # SECTION 4: STREAK TRACKER
        # ============================================================
        # 7-day squares (Mon-Sun), green if 4+ hours worked
        
        streak_label = QLabel("This week")
        streak_label.setStyleSheet("font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;")
        main_layout.addWidget(streak_label)
        
        self.streak_layout = QHBoxLayout()
        self.streak_layout.setSpacing(8)
        self.streak_squares = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(day_names):
            square = QFrame()
            square.setFixedSize(40, 40)
            square.setStyleSheet("background-color: #333; border: none;")
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #8a8a96; font-size: 10px;")
            container = QVBoxLayout()
            container.setContentsMargins(0, 0, 0, 0)
            container.addWidget(square, 0, Qt.AlignCenter)
            container.addWidget(label, 0, Qt.AlignCenter)
            self.streak_layout.addLayout(container)
            self.streak_squares.append(square)
        
        main_layout.addLayout(self.streak_layout)
        
        # ============================================================
        # SECTION 5: UI DESIGN & THEMES
        # ============================================================
        # Dark/light mode toggle, button styling, colors
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        self.theme_btn = QPushButton("🌙 Dark" if self.theme == "light" else "☀️ Light")
        self.theme_btn.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_btn)
        main_layout.addLayout(theme_layout)
        
        self.setLayout(main_layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)
        
        self.load_today_data()
        self.update_streak_display()
        
        self.note_timer = QTimer()
        self.note_timer.setSingleShot(True)
        self.note_timer.timeout.connect(self.save_note)
        
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
    
    def start_with_eye_protection(self):
        self.state = "running"
        self.eye_protection_enabled = True
        self.last_mode = "eye_protection"
        self.timer.start(1000)
        self.btn_start_2020.setText("Running...")
        self.btn_start_focus.setText("Running (focus)...")
        self.btn_start_2020.setEnabled(False)
        self.btn_start_focus.setEnabled(False)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: #1fbe82;")
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #1fbe82; }")
        self.auto_save_timer.start(10000)
    
    def start_focus_mode(self):
        self.state = "running"
        self.eye_protection_enabled = False
        self.last_mode = "focus"
        self.timer.start(1000)
        self.btn_start_2020.setText("Running...")
        self.btn_start_focus.setText("Running (focus)...")
        self.btn_start_2020.setEnabled(False)
        self.btn_start_focus.setEnabled(False)
        self.status_label.setText("Status: Running (focus)")
        self.status_label.setStyleSheet("color: #1fbe82;")
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #1fbe82; }")
        self.auto_save_timer.start(10000)
    
    def stop_session(self):
        self.timer.stop()
        self.auto_save_timer.stop()
        self.state = "paused"
        self.btn_start_2020.setText("Start 20-20-20")
        self.btn_start_focus.setText("Start (no 20-20-20)")
        self.btn_start_2020.setEnabled(True)
        self.btn_start_focus.setEnabled(True)
        self.status_label.setText("Status: Paused")
        self.status_label.setStyleSheet("color: #f0a830;")
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #f0a830; }")
        self.stop_cycles += 1
        self.save_data()
    
    def end_day(self):
        self.timer.stop()
        self.auto_save_timer.stop()
        
        self.save_session()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("End of Day")
        dialog.setFixedSize(400, 300)
        layout = QVBoxLayout()
        
        title = QLabel("Day Complete")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        info = QLabel(f"Date: {self.get_formatted_date()}")
        layout.addWidget(info)
        
        worked = QLabel(f"Time worked: {self.format_time(self.worked_seconds_today)}")
        layout.addWidget(worked)
        
        breaks = QLabel(f"Eye breaks taken: {self.eye_breaks_today}")
        layout.addWidget(breaks)
        
        cycles = QLabel(f"Stop/resume cycles: {self.stop_cycles}")
        layout.addWidget(cycles)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
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
        
        self.timer_label.setText("12:00:00")
        self.progress_bar.setValue(12 * 3600)
        self.status_label.setText("Status: Idle")
        self.status_label.setStyleSheet("")
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #1fbe82; }")
        
        self.btn_start_2020.setText("Start 20-20-20")
        self.btn_start_focus.setText("Start (no 20-20-20)")
        self.btn_start_2020.setEnabled(True)
        self.btn_start_focus.setEnabled(True)
        
        self.eye_break_label.setText("Eye breaks today: 0")
        self.time_worked_label.setText("00:00:00")
        self.breaks_count_label.setText("0")
    
    def trigger_eye_break(self):
        self.timer.stop()
        
        self.overlay = EyeBreakOverlay()
        self.overlay.dismiss_signal.connect(self.on_eye_break_dismissed)
        self.overlay.showFullScreen()
    
    def on_eye_break_dismissed(self):
        self.overlay = None
        self.eye_breaks_today += 1
        self.eye_break_label.setText(f"Eye breaks today: {self.eye_breaks_today}")
        self.breaks_count_label.setText(str(self.eye_breaks_today))
        
        if self.state == "running":
            self.eye_timer_seconds = 0
            self.timer.start(1000)
    
    def show_day_complete(self):
        import winsound if sys.platform == "win32" else None
        self.status_label.setText("Day complete!")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Day Complete")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Day complete! Great work."))
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec_()
    
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
    # SECTION 6: DATA PERSISTENCE
    # ============================================================
    # JSON save/load to ~/.996protocol/data.json, auto-save triggers
    
    def load_data(self):
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)
        
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, 'r') as f:
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
                "eye_protection_default": True
            }
        }
    
    def save_data(self):
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)
        
        self.data["settings"]["theme"] = self.theme
        self.data["settings"]["always_on_top"] = self.always_on_top
        
        with open(DATA_FILE, 'w') as f:
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
            "completed": self.remaining_seconds <= 0
        }
        
        if self.worked_seconds_today >= 14400:
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
            self.eye_break_label.setText(f"Eye breaks today: {self.eye_breaks_today}")
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
                square.setStyleSheet("background-color: #1fbe82; border: none;")
            else:
                square.setStyleSheet("background-color: #333; border: none;")
            
            if day == today:
                square.setStyleSheet(square.styleSheet() + " border: 1px solid white;")
    
    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()
        self.theme_btn.setText("🌙 Dark" if self.theme == "light" else "☀️ Light")
        self.save_data()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #0e0e0f;
                    color: #f0f0f0;
                }
                QFrame {
                    background-color: #161618;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                }
                QTextEdit {
                    background-color: #1e1e21;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    color: #f0f0f0;
                    font-family: monospace;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: #1fbe82;
                    color: #0e0e0f;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: medium;
                }
                QPushButton:hover {
                    background-color: #2fd692;
                }
                QPushButton:disabled {
                    background-color: #333;
                    color: #666;
                }
                QLabel {
                    color: #f0f0f0;
                }
                QProgressBar {
                    background-color: #333;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #1fbe82;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f7;
                    color: #111111;
                }
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid rgba(0,0,0,0.1);
                    border-radius: 8px;
                }
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid rgba(0,0,0,0.1);
                    border-radius: 8px;
                    color: #111111;
                    font-family: monospace;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: #1fbe82;
                    color: #0e0e0f;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: medium;
                }
                QPushButton:hover {
                    background-color: #2fd692;
                }
                QPushButton:disabled {
                    background-color: #ddd;
                    color: #999;
                }
                QLabel {
                    color: #111111;
                }
                QProgressBar {
                    background-color: #ddd;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background-color: #1fbe82;
                }
            """)
    
    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self.save_data()
    
    def keyPressEvent(self, event):
        # ============================================================
        # SECTION 8: KEYBOARD SHORTCUTS
        # ============================================================
        # Ctrl+S stop, Ctrl+R resume, Ctrl+E end day, Ctrl+T toggle always-on-top, Ctrl+Q quit
        
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.stop_session()
            elif event.key() == Qt.Key_R:
                if self.last_mode == "eye_protection":
                    self.start_with_eye_protection()
                elif self.last_mode == "focus":
                    self.start_focus_mode()
            elif event.key() == Qt.Key_E:
                self.end_day()
            elif event.key() == Qt.Key_T:
                self.toggle_always_on_top()
            elif event.key() == Qt.Key_Q:
                self.close()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        if self.state == "running":
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Session Running")
            dialog.setText("Session is running. End day and quit?")
            dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            dialog.button(QMessageBox.Yes).setText("End day & quit")
            dialog.button(QMessageBox.No).setText("Just minimize")
            
            result = dialog.exec_()
            
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
    # SECTION 8: SYSTEM TRAY
    # ============================================================
    # Minimize to tray, right-click menu (Show, Stop session, End day, Quit)
    
    def setup_tray(self):
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


from datetime import timedelta

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("996 Protocol")
    
    window = Protocol996()
    window.setup_tray()
    window.show()
    
    sys.exit(app.exec_())