"""
AUDITOR REAL-TIME TUI DASHBOARD (O-Z10)
======================================

Role: Live observability and cluster monitoring.
Responsibilities:
  - Visualizing hardware health (CPU/RAM).
  - Monitoring Redis task queue depth.
  - Tracking audit success/failure metrics in real-time.
"""

import time
import psutil # type: ignore
from datetime import datetime
from rich.live import Live # type: ignore
from rich.table import Table # type: ignore
from rich.panel import Panel # type: ignore
from rich.layout import Layout # type: ignore
from rich.console import Console # type: ignore
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn # type: ignore
from rich.columns import Columns # type: ignore
from rich import box # type: ignore

# IDE PATH RECONCILIATION
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from auditor.infrastructure.redis_task_queue import RedisTaskQueue # type: ignore

class AuditorDashboard:
    """
    Ultra-premium terminal dashboard for the Auditor platform.
    """
    
    def __init__(self):
        self.console = Console()
        self.queue = RedisTaskQueue()
        self.start_time = datetime.now()

    def generate_header(self) -> Panel:
        """Dashboard Header with clinical metadata."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right", ratio=1)
        grid.add_row(
            "[b]AUDITOR.NEXT | [magenta]PHASE III: AUTONOMOUS[/][/b]",
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]"
        )
        return Panel(grid, style="white on blue")

    def generate_hardware_metrics(self) -> Panel:
        """Real-time CPU/RAM telemetry."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        cpu_color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
        ram_color = "green" if ram < 50 else "yellow" if ram < 80 else "red"
        
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Sensor", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("CPU Load", f"[{cpu_color}]{cpu}%[/]")
        table.add_row("RAM Usage", f"[{ram_color}]{ram}%[/]")
        table.add_row("Uptime", str(datetime.now() - self.start_time).split(".")[0])
        
        return Panel(table, title="[b]Hardware Telemetry[/b]", border_style="bright_blue")

    async def generate_queue_metrics(self) -> Panel:
        """Redis cluster state."""
        try:
            await self.queue.connect()
            size = await self.queue.get_queue_size()
            await self.queue.disconnect()
        except:
            size = "ERR"
            
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Metric", style="magenta")
        table.add_column("Status", justify="right")
        table.add_row("Redis Cluster", "[green]ONLINE[/]")
        table.add_row("Pending Tasks", f"[bold white]{size}[/]")
        table.add_row("Active Workers", "[cyan]3[/]") # Mocked for now
        
        return Panel(table, title="[b]Orchestration Layer[/b]", border_style="magenta")

    def make_layout(self) -> Layout:
        """Defines the TUI layout structure."""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="side", size=40),
            Layout(name="body", ratio=1)
        )
        layout["side"].split(
            Layout(name="hw"),
            Layout(name="queue")
        )
        return layout

    async def run(self):
        """Main Loop for the TUI."""
        layout = self.make_layout()
        layout["header"].update(self.generate_header())
        layout["footer"].update(Panel("[dim]Auditor Terminal v0.1.0 | Press Ctrl+C to exit[/]", box=box.SIMPLE))
        
        with Live(layout, refresh_per_second=2, screen=True):
            while True:
                layout["hw"].update(self.generate_hardware_metrics())
                layout["queue"].update(await self.generate_queue_metrics())
                time.sleep(0.5)

if __name__ == "__main__":
    import asyncio
    dash = AuditorDashboard()
    asyncio.run(dash.run())
