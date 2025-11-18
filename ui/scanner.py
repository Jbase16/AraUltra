# ui/scanner.py
# Scanner with parallel execution, progress bar, timing,
# aggressive-mode toggle, and real-time colored log output.

from __future__ import annotations

import subprocess
import threading
import time

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QListWidget,
    QTextEdit,
    QProgressBar,
    QCheckBox,
)
from PyQt6.QtCore import pyqtSignal

from core.tools import (
    TOOLS,
    get_installed_tools,
    get_tool_command,
    tool_callback_factory,
)


class ScannerPanel(QWidget):
    # Signals to MainWindow
    scan_started = pyqtSignal(str)
    scan_finished = pyqtSignal(str)

    # Internal signals to ensure UI updates happen on the GUI thread
    log_event = pyqtSignal(str, str)
    progress_event = pyqtSignal(int, int)
    scan_complete_internal = pyqtSignal(str)

    # Internal UI-thread style signals are already handled via direct widgets in this design

    def __init__(self):
        super().__init__()

        self._scan_lock = threading.Lock()
        self._total_tools = 0
        self._completed_tools = 0
        self._current_target = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ---------------------------------------------------------
        # Target + button row
        # ---------------------------------------------------------
        row = QHBoxLayout()
        row.addWidget(QLabel("Target:"))

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. http://demo.testfire.net")
        row.addWidget(self.target_input)

        self.run_btn = QPushButton("Run Scan")
        self.run_btn.clicked.connect(self.start_scan)
        row.addWidget(self.run_btn)

        layout.addLayout(row)

        # ---------------------------------------------------------
        # Tool list
        # ---------------------------------------------------------
        self.tool_list = QListWidget()
        self.tool_list.setSelectionMode(self.tool_list.SelectionMode.MultiSelection)

        available = get_installed_tools()
        for name, tdef in available.items():
            label = tdef["label"]
            if tdef.get("aggressive"):
                display = f"{name} — {label} [AGGRESSIVE]"
            else:
                display = f"{name} — {label}"
            self.tool_list.addItem(display)

        layout.addWidget(self.tool_list)

        # ---------------------------------------------------------
        # Aggressive toggle
        # ---------------------------------------------------------
        aggr_row = QHBoxLayout()
        self.allow_aggressive = QCheckBox("Include aggressive tools")
        self.allow_aggressive.setChecked(False)
        aggr_row.addWidget(self.allow_aggressive)
        aggr_row.addStretch(1)
        layout.addLayout(aggr_row)

        # ---------------------------------------------------------
        # Progress + status
        # ---------------------------------------------------------
        p_row = QHBoxLayout()

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        p_row.addWidget(self.progress, stretch=1)

        self.status = QLabel("Idle.")
        p_row.addWidget(self.status)

        layout.addLayout(p_row)

        # ---------------------------------------------------------
        # Log box
        # ---------------------------------------------------------
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setAcceptRichText(True)
        self.log_box.setStyleSheet(
            "background: #0b0b0b; color: #c0ffc0; font-family: Menlo, monospace; font-size: 11px;"
        )
        layout.addWidget(self.log_box, stretch=2)

        self.log_event.connect(self._log_slot)
        self.progress_event.connect(self._apply_progress_update)
        self.scan_complete_internal.connect(self._on_scan_complete_ui)

        self._log_system("Scanner ready.")

    # =====================================================================
    # Public API: Start scan
    # =====================================================================
    def start_scan(self):
        target = self.target_input.text().strip()
        if not target:
            self._log_warn("No target supplied.")
            return

        selected_raw = [i.text() for i in self.tool_list.selectedItems()]
        if not selected_raw:
            self._log_warn("No tools selected.")
            return

        # Extract tool keys from "name — label" or "name — label [AGGRESSIVE]"
        selected = []
        for item in selected_raw:
            key = item.split(" — ")[0]
            selected.append(key)

        # Apply aggressive toggle
        filtered: list[str] = []
        for name in selected:
            tdef = TOOLS.get(name)
            if not tdef:
                self._log_error(f"Unknown tool selected: {name}")
                continue

            if tdef.get("aggressive") and not self.allow_aggressive.isChecked():
                self._log_warn(
                    f"Skipping {name}: aggressive and 'Include aggressive tools' is off."
                )
                continue

            filtered.append(name)

        if not filtered:
            self._log_warn("No tools to run after applying aggressive filter.")
            return

        self._current_target = target

        with self._scan_lock:
            self._total_tools = len(filtered)
            self._completed_tools = 0

        self.progress.setMaximum(self._total_tools)
        self.progress.setValue(0)

        self.run_btn.setEnabled(False)
        self.status.setText("Running…")
        self._log_system(
            f"=== Starting scan on {target} with {len(filtered)} tool(s) ==="
        )

        self.scan_started.emit(target)

        # Launch each tool in parallel
        for tool_name in filtered:
            t = threading.Thread(
                target=self._run_single_tool,
                args=(tool_name, target),
                daemon=True,
            )
            t.start()

    # =====================================================================
    # Worker: run a single tool (parallel, streaming output)
    # =====================================================================
    def _run_single_tool(self, tool_name: str, target: str):
        try:
            cmd = get_tool_command(tool_name, target)
        except Exception as e:
            self._log_error(f"[{tool_name}] Bad tool definition: {e}")
            self._increment_progress()
            return

        self._log_tool(tool_name, f"Running: {' '.join(cmd)}")

        callback = tool_callback_factory(tool_name)

        start = time.time()

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stdout_lines = []

            # Stream stdout line-by-line
            if proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    line = line.rstrip("\n")
                    stdout_lines.append(line)
                    if line:
                        self._log_tool(tool_name, line)

            proc.wait()

            stderr = ""
            if proc.stderr:
                stderr = proc.stderr.read() or ""

            if stderr.strip():
                for line in stderr.splitlines():
                    self._log_tool(tool_name, line, color="#ff8080")

            duration = time.time() - start

            callback(
                stdout="\n".join(stdout_lines),
                stderr=stderr,
                rc=proc.returncode,
                metadata={
                    "tool": tool_name,
                    "target": target,
                    "cmd": cmd,
                    "duration": duration,
                },
            )

            self._log_tool(
                tool_name,
                f"Finished in {duration:.1f}s (rc={proc.returncode})",
                color="#80b3ff",
            )

        except FileNotFoundError:
            self._log_error(f"[{tool_name}] Executable not found in PATH.")
        except Exception as e:
            self._log_error(f"[{tool_name}] Unexpected error: {e}")
        finally:
            self._increment_progress()

    # =====================================================================
    # Progress tracking (thread-safe)
    # =====================================================================
    def _increment_progress(self):
        with self._scan_lock:
            self._completed_tools += 1
            done = self._completed_tools
            total = self._total_tools

        self.progress_event.emit(done, total)

        if done == total and self._current_target is not None:
            self.scan_complete_internal.emit(self._current_target)

    def _apply_progress_update(self, done: int, total: int):
        self.progress.setMaximum(total if total > 0 else 1)
        self.progress.setValue(done)

        if total > 0:
            if done < total:
                self.status.setText(f"Running… {done}/{total} tool(s) finished.")
            else:
                self.status.setText(f"Completed {total} tool(s).")
        else:
            self.status.setText("Idle.")

    def _on_scan_complete_ui(self, target: str):
        self.scan_finished.emit(target)
        self._log_system(f"=== Scan complete for {target} ===")
        self.run_btn.setEnabled(True)

    # =====================================================================
    # Logging helpers
    # =====================================================================
    def _append_log_ui(self, html: str):
        self.log_box.append(html)
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _log(self, msg: str, color: str = "#c0ffc0"):
        self.log_event.emit(msg, color)

    def _log_slot(self, msg: str, color: str):
        html = f'<span style="color:{color}">{msg}</span>'
        self._append_log_ui(html)

    # External panels (e.g., MainWindow) can append directly via TaskRouter events.
    def append_log(self, text: str, color: str = "#c0ffc0"):
        self.log_event.emit(text, color)

    def _log_system(self, msg: str):
        self._log(f"[system] {msg}", color="#80b3ff")

    def _log_warn(self, msg: str):
        self._log(f"[warn] {msg}", color="#ffd480")

    def _log_error(self, msg: str):
        self._log(f"[error] {msg}", color="#ff8080")

    def _log_tool(self, tool: str, msg: str, color: str = "#c0ffc0"):
        self._log(f"[{tool}] {msg}", color=color)
