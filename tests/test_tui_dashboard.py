import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from rich.panel import Panel
from rich.layout import Layout
from auditor.application.tui_dashboard import AuditorDashboard

def test_tui_layout_generation():
    dash = AuditorDashboard()
    layout = dash.make_layout()
    
    assert isinstance(layout, Layout)
    assert isinstance(layout["header"], Layout)
    assert isinstance(layout["main"], Layout)
    assert isinstance(layout["footer"], Layout)
    assert isinstance(layout["hw"], Layout)
    assert isinstance(layout["queue"], Layout)

def test_generate_header():
    dash = AuditorDashboard()
    header_panel = dash.generate_header()
    assert isinstance(header_panel, Panel)
    
    from rich.console import Console
    console = Console()
    with console.capture() as capture:
        console.print(header_panel)
    assert "AUDITOR.NEXT" in capture.get()

def test_generate_hardware_metrics():
    dash = AuditorDashboard()
    
    with patch("psutil.cpu_percent", return_value=45.0), \
         patch("psutil.virtual_memory") as mock_ram:
        mock_ram.return_value.percent = 60.0
        
        panel = dash.generate_hardware_metrics()
        assert isinstance(panel, Panel)
        
        from rich.console import Console
        console = Console()
        with console.capture() as capture:
            console.print(panel)
        rendered = capture.get()
        assert "CPU Load" in rendered
        assert "45" in rendered
        assert "60" in rendered

@pytest.mark.asyncio
async def test_generate_queue_metrics():
    dash = AuditorDashboard()
    
    mock_connect = AsyncMock()
    mock_size = AsyncMock(return_value=12)
    mock_disconnect = AsyncMock()
    
    dash.queue.connect = mock_connect
    dash.queue.get_queue_size = mock_size
    dash.queue.disconnect = mock_disconnect
    
    panel = await dash.generate_queue_metrics()
    assert isinstance(panel, Panel)
    
    from rich.console import Console
    console = Console()
    with console.capture() as capture:
        console.print(panel)
    rendered = capture.get()
    assert "Pending Tasks" in rendered
    assert "12" in rendered
    
    mock_connect.assert_called_once()
    mock_size.assert_called_once()
    mock_disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_generate_queue_metrics_exception():
    dash = AuditorDashboard()
    # Mock connect to throw exception
    dash.queue.connect = AsyncMock(side_effect=RuntimeError("Redis down"))
    panel = await dash.generate_queue_metrics()
    assert isinstance(panel, Panel)
    
    from rich.console import Console
    console = Console()
    with console.capture() as capture:
        console.print(panel)
    rendered = capture.get()
    assert "ERR" in rendered

@pytest.mark.asyncio
async def test_tui_dashboard_run():
    dash = AuditorDashboard()
    
    # Mock internal methods of run loop
    dash.generate_hardware_metrics = MagicMock()
    dash.generate_queue_metrics = AsyncMock()
    
    # Mock Live and mock sleep to break loop by raising KeyboardInterrupt
    call_count = 0
    def mock_sleep_impl(sec):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            raise KeyboardInterrupt()
            
    with patch("auditor.application.tui_dashboard.Live") as mock_live, \
         patch("time.sleep", side_effect=mock_sleep_impl):
        with pytest.raises(KeyboardInterrupt):
            await dash.run()
        assert mock_live.called

def test_tui_dashboard_path_reconciliation():
    import sys
    import importlib
    import os
    orig_path = sys.path.copy()
    try:
        # Remove any path containing Web_Accessibility_Auditor to simulate running from outside
        sys.path = [p for p in sys.path if "Web_Accessibility_Auditor" not in p and p != ""]
        import auditor.application.tui_dashboard
        importlib.reload(auditor.application.tui_dashboard)
    finally:
        sys.path = orig_path
