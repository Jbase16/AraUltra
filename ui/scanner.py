# ui/scanner_panel.py — Scanner panel with streaming output

from __future__ import annotations

import asyncio
import re
from collections import OrderedDict
from typing import Dict, List

from PyQt6.QtCore import pyqtSignal, Qt, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QApplication,
    QListWidget, QListWidgetItem
)

from core.scanner_engine import ScannerEngine
from core.findings import findings_store
from core.tools import TOOLS


class ScannerWorker(QThread):
    progress = pyqtSignal(str)        # Live output streaming
    done = pyqtSignal(str)            # When scan fully completes

    def __init__(self, target: str, selected_tools: list[str]):
        super().__init__()
        self.target = target
        self.engine = ScannerEngine()
        self._cancel_requested = False
        self.selected_tools = selected_tools

    def run(self):
        asyncio.run(self._run_scan())

    def request_cancel(self):
        self._cancel_requested = True

    async def _run_scan(self):
        try:
            async for line in self.engine.scan(self.target, self.selected_tools):
                if self._cancel_requested:
                    break
                self.progress.emit(line)
        except Exception as exc:  # pragma: no cover - defensive
            self.progress.emit(f"[scanner] ERROR: {exc}")
        finally:
            self.done.emit(self.target)


class ScannerPanel(QWidget):

    scan_started = pyqtSignal(str)
    scan_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # ------------------------------------------------------------------
        # Target field
        # ------------------------------------------------------------------
        row = QHBoxLayout()
        row.addWidget(QLabel("Target:", self))

        self.target_box = QLineEdit("https://example.com")
        row.addWidget(self.target_box)

        self.btn_scan = QPushButton("Start Scan")
        self.btn_scan.clicked.connect(self.start_scan)
        row.addWidget(self.btn_scan)

        layout.addLayout(row)

        # ------------------------------------------------------------------
        # Tool selection list
        # ------------------------------------------------------------------
        tools_row = QHBoxLayout()
        tools_row.setSpacing(8)
        tools_row.addWidget(QLabel("Tools:"))
        self.tools_list = QListWidget()
        self.tools_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        for name, meta in TOOLS.items():
            item = QListWidgetItem(f"{name} – {meta['label']}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setCheckState(Qt.CheckState.Checked)
            self.tools_list.addItem(item)
        self.tools_list.setMaximumHeight(180)
        tools_row.addWidget(self.tools_list)
        layout.addLayout(tools_row)

        # ------------------------------------------------------------------
        # Live tool status table
        # ------------------------------------------------------------------
        self.status_table = QTableWidget(0, 3)
        self.status_table.setHorizontalHeaderLabels(["Tool", "Status", "Last Message"])
        self.status_table.verticalHeader().setVisible(False)
        self.status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.status_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.status_table, stretch=1)

        # ------------------------------------------------------------------
        # Output console
        # ------------------------------------------------------------------
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #33ff33;
                font-family: Consolas, monospace;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.console)

        self.worker = None
        self.tool_status: "OrderedDict[str, Dict[str, str]]" = OrderedDict()
        self._installed_pattern = re.compile(r"^Installed tools:\s*(.+)$")
        self._running_pattern = re.compile(r"^--- Running ([^ ]+) ---$")
        self._exit_pattern = re.compile(r"^\[(.+?)\]\s+Exit code:\s+(\d+)")
        self._tool_prefix = re.compile(r"^\[([^\]]+)\]\s+(.*)$")

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._cleanup_worker)

    # ----------------------------------------------------------------------
    # Start scan
    # ----------------------------------------------------------------------
    def start_scan(self):
        target = self.target_box.text().strip()
        if not target:
            self._log("ERROR: No target provided.")
            return
        if self.worker and self.worker.isRunning():
            self._log("[scanner] Scan already running. Please wait for completion.")
            return

        selected = self._get_selected_tools()
        if not selected:
            self._log("[scanner] Please select at least one tool to run.")
            return

        self.console.clear()
        self._reset_status()

        self.worker = ScannerWorker(target, selected)
        self.worker.progress.connect(self._log)
        self.worker.done.connect(self._finish)
        self.btn_scan.setEnabled(False)

        self.scan_started.emit(target)
        self.worker.start()

    # ----------------------------------------------------------------------
    # Logging output
    # ----------------------------------------------------------------------
    def _log(self, text: str):
        self.console.append(text)
        self._interpret_status_line(text)

    # ----------------------------------------------------------------------
    # Scan finished
    # ----------------------------------------------------------------------
    def _finish(self, target: str):
        self.scan_finished.emit(target)
        self._log("\n[SCAN COMPLETE]\n")
        self.btn_scan.setEnabled(True)
        self.worker = None

    def _cleanup_worker(self):
        if self.worker and self.worker.isRunning():
            self.worker.request_cancel()
            self.worker.wait()
        self.worker = None
        self.btn_scan.setEnabled(True)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def _reset_status(self):
        self.tool_status.clear()
        self.status_table.setRowCount(0)

    def _set_tools(self, names: List[str]):
        self.tool_status = OrderedDict((name, {"status": "Pending", "message": ""}) for name in names)
        self.status_table.setRowCount(len(names))
        for row, name in enumerate(names):
            self.status_table.setItem(row, 0, QTableWidgetItem(name))
            self.status_table.setItem(row, 1, QTableWidgetItem("Pending"))
            self.status_table.setItem(row, 2, QTableWidgetItem(""))
        self.status_table.resizeColumnsToContents()

    def _update_status(self, tool: str, status: str, message: str = ""):
        if tool not in self.tool_status:
            self.tool_status[tool] = {"status": status, "message": message}
            row = self.status_table.rowCount()
            self.status_table.insertRow(row)
            self.status_table.setItem(row, 0, QTableWidgetItem(tool))
        else:
            self.tool_status[tool]["status"] = status
            if message:
                self.tool_status[tool]["message"] = message

        for row in range(self.status_table.rowCount()):
            name_item = self.status_table.item(row, 0)
            if name_item and name_item.text() == tool:
                status_item = self.status_table.item(row, 1)
                msg_item = self.status_table.item(row, 2)
                if not status_item:
                    status_item = QTableWidgetItem()
                    self.status_table.setItem(row, 1, status_item)
                if not msg_item:
                    msg_item = QTableWidgetItem()
                    self.status_table.setItem(row, 2, msg_item)
                status_item.setText(status)
                msg_item.setText(self.tool_status[tool]["message"])
                break

    def _interpret_status_line(self, text: str):
        if match := self._installed_pattern.match(text):
            tools = [name.strip() for name in match.group(1).split(",") if name.strip()]
            self._set_tools(tools)
            return

        if match := self._running_pattern.match(text):
            tool = match.group(1)
            self._update_status(tool, "Running", "Starting…")
            return

        if match := self._exit_pattern.match(text):
            tool, code = match.group(1), match.group(2)
            status = "Done" if code == "0" else f"Exit {code}"
            self._update_status(tool, status)
            return

        if match := self._tool_prefix.match(text):
            tool, msg = match.group(1), match.group(2)
            current_status = self.tool_status.get(tool, {}).get("status", "Running")
            self._update_status(tool, current_status, msg)

    def _get_selected_tools(self) -> List[str]:
        tools = []
        for i in range(self.tools_list.count()):
            item = self.tools_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                tools.append(item.data(Qt.ItemDataRole.UserRole))
        return tools
