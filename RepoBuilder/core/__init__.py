"""Repo Intelligence Platform — core framework.

Foundation utilities used by B1–B6 phases (not implemented here):
stack detection, file scanning, shell execution, JSON persistence, markdown reports.
"""
from core.api_server import create_app
from core.dashboard_data_builder import DashboardBuildResult, DashboardDataBuilder
from core.rust_builder import RustBuilder, RustBuildResult
from core.node_builder import NodeBuilder, NodeBuildResult
from core.fastapi_builder import FastAPIBuilder, FastAPIBuildResult
from core.file_scanner import FileRecord, FileScanner, ScanResult
from core.graph_engine import GraphEngine, GraphModel
from core.inventory_agent import InventoryAgent, InventoryItem, InventoryResult
from core.json_writer import JsonWriter, read_json
from core.route_agent import RouteAgent, RouteDiscoveryResult, RouteRecord
from core.test_agent import TestAgent, TestAgentResult, TestExecutionResult
from core.report_generator import ReportGenerator, ReportSection
from core.shell_executor import ShellExecutor, ShellResult
from core.stack_detector import DetectedStack, StackDetector, StackProfile

__all__ = [
    "DetectedStack",
    "create_app",
    "DashboardBuildResult",
    "DashboardDataBuilder",
    "FastAPIBuilder",
    "FastAPIBuildResult",
    "FileRecord",
    "FileScanner",
    "GraphEngine",
    "GraphModel",
    "InventoryAgent",
    "InventoryItem",
    "InventoryResult",
    "JsonWriter",
    "NodeBuilder",
    "NodeBuildResult",
    "RouteAgent",
    "RouteDiscoveryResult",
    "RouteRecord",
    "RustBuilder",
    "RustBuildResult",
    "TestAgent",
    "TestAgentResult",
    "TestExecutionResult",
    "ReportGenerator",
    "ReportSection",
    "ScanResult",
    "ShellExecutor",
    "ShellResult",
    "StackDetector",
    "StackProfile",
    "read_json",
]
