# ui/killchain_view.py
# Kill chain / relationship graph – purely visual, no exploit logic

from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel, QPlainTextEdit
from PyQt6.QtCore import Qt
from typing import List

import matplotlib
matplotlib.use("QtAgg")  # ensure Qt backend

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import networkx as nx

from core.findings import findings_store
from core.killchain_store import killchain_store


class KillChainView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.asset_filter = QComboBox()
        self.asset_filter.addItem("All Assets", None)
        self.asset_filter.currentIndexChanged.connect(self.rebuild_graph)

        self.phase_filter = QComboBox()
        self.phase_filter.addItem("All Phases", None)
        self.phase_filter.currentIndexChanged.connect(self.rebuild_graph)

        self.severity_filter = QComboBox()
        self.severity_filter.addItem("All Severities", None)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            self.severity_filter.addItem(sev, sev)
        self.severity_filter.currentIndexChanged.connect(self.rebuild_graph)

        self.refresh_btn = QPushButton("Refresh Graph")
        self.refresh_btn.clicked.connect(self.rebuild_graph)

        controls.addWidget(QLabel("Asset:"))
        controls.addWidget(self.asset_filter)
        controls.addWidget(QLabel("Phase:"))
        controls.addWidget(self.phase_filter)
        controls.addWidget(QLabel("Severity:"))
        controls.addWidget(self.severity_filter)
        controls.addStretch()
        controls.addWidget(self.refresh_btn)

        layout.addLayout(controls)

        self.fig = Figure(facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, stretch=1)

        self.graph = nx.DiGraph()
        self._edges_cache: List[dict] = []

        self.summary_box = QPlainTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setStyleSheet("QPlainTextEdit{background:#101010; color:#f0f0f0; padding:8px;}")
        layout.addWidget(QLabel("Edge Summary"))
        layout.addWidget(self.summary_box)

        self.rebuild_graph()
        killchain_store.edges_changed.connect(self.rebuild_graph)
        findings_store.findings_changed.connect(self.rebuild_graph)

    def rebuild_graph(self):
        self.graph.clear()

        edges = killchain_store.get_all()
        findings = findings_store.get_all()

        if edges:
            self._update_filter_options(edges)
            self._build_from_edges(edges)
        elif findings:
            self._build_from_findings(findings)
            self.summary_box.setPlainText("Graph is derived from raw findings (no correlated edges).")
        else:
            self._draw_empty()
            self.summary_box.setPlainText("No findings available.")

    def _build_from_edges(self, edges: list[dict]):
        self.graph.clear()
        asset_filter = self.asset_filter.currentData()
        phase_filter = self.phase_filter.currentData()
        severity_filter = self.severity_filter.currentData()
        filtered: List[dict] = []

        for edge in edges:
            source = edge.get("source", "unknown")
            target = edge.get("target", "issue")
            severity = str(edge.get("severity", "INFO")).upper()
            kind = "behavior" if str(target).startswith("behavior") or str(target).startswith("recon-phase") else "issue"
            phase = edge.get("edge_type") or ",".join(edge.get("families", []))

            if asset_filter and source != asset_filter:
                continue
            if severity_filter and severity != severity_filter:
                continue
            if phase_filter and (phase_filter not in (phase or "")):
                continue

            self.graph.add_node(source, kind="asset")
            self.graph.add_node(target, kind=kind, severity=severity)
            self.graph.add_edge(
                source,
                target,
                label=edge.get("label") or edge.get("signal") or edge.get("edge_type", ""),
                phase=phase,
            )
            filtered.append(edge)

        self._edges_cache = filtered
        self._draw_graph()
        self._update_summary(filtered)

    def _build_from_findings(self, findings):
        self.graph.clear()

        for f in findings:
            target = f["target"]
            tool = f["tool"]
            vtype = f["type"]
            severity = f["severity"]

            target_node = f"TARGET: {target}"
            tool_node = f"TOOL: {tool}"
            vuln_node = f"{vtype} ({severity})"

            self.graph.add_node(target_node, kind="target")
            self.graph.add_node(tool_node, kind="tool")
            self.graph.add_node(vuln_node, kind="vuln", severity=severity)

            self.graph.add_edge(tool_node, vuln_node)
            self.graph.add_edge(vuln_node, target_node)

        self._draw_graph()
        self._update_summary([])

    def _draw_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#1e1e1e")
        ax.text(
            0.5, 0.5,
            "No findings yet.\nRun a scan first.",
            color="white",
            ha="center", va="center",
            fontsize=14,
            transform=ax.transAxes,
        )
        ax.axis("off")
        self.canvas.draw()

    def _draw_graph(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#1e1e1e")

        pos = nx.spring_layout(self.graph, seed=42, k=0.8)

        node_colors = []
        for n, data in self.graph.nodes(data=True):
            kind = data.get("kind", "")
            if kind in ("target", "asset"):
                node_colors.append("#4b8b3b")
            elif kind == "tool":
                node_colors.append("#357abd")
            elif kind == "behavior":
                node_colors.append("#8e44ad")
            else:
                sev = data.get("severity", "")
                if sev in ("HIGH", "CRITICAL"):
                    node_colors.append("#c0392b")
                elif sev == "MEDIUM":
                    node_colors.append("#d68910")
                else:
                    node_colors.append("#7f8c8d")

        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=2200,
            font_size=9,
            font_weight="bold",
            edge_color="#aaaaaa",
            arrows=True,
            ax=ax,
        )

        legend = (
            "Legend:\n"
            "Green=Asset  Blue=Tool  Purple=Behavioral/TLS Phases\n"
            "Red/Amber/Gray=Issues by severity"
        )
        ax.text(
            0.02, 0.02,
            legend,
            transform=ax.transAxes,
            fontsize=8,
            color="#bbbbbb",
            va="bottom",
        )

        self.canvas.draw()

    def _update_filter_options(self, edges: List[dict]):
        assets = sorted({edge.get("source", "unknown") for edge in edges})
        phases = sorted({edge.get("edge_type") or "Generic" for edge in edges})
        self._repopulate_combo(self.asset_filter, assets, "All Assets")
        self._repopulate_combo(self.phase_filter, phases, "All Phases")

    def _repopulate_combo(self, combo: QComboBox, values: List[str], label: str):
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(label, None)
        for value in values:
            combo.addItem(value, value)
        index = combo.findData(current) if current else 0
        if index == -1:
            index = 0
        combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _update_summary(self, edges: List[dict]):
        if not edges:
            self.summary_box.setPlainText("No edges match the current filters.")
            return
        lines = []
        for edge in edges[:20]:
            lines.append(
                f"{edge.get('source')} → {edge.get('target')} | {edge.get('severity')} | {edge.get('label') or edge.get('signal')}"
            )
        if len(edges) > 20:
            lines.append(f"… {len(edges) - 20} more edges")
        self.summary_box.setPlainText("\n".join(lines))
