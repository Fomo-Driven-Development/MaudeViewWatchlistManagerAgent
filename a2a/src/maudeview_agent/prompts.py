"""Prompts and tool configuration for MaudeView Watchlist Manager Agent."""

MCP_SERVER_NAME = "maudeview"

SYSTEM_PROMPT = """\
You are the MaudeView Watchlist Manager Agent. You manage TradingView watchlists and control chart settings through the tv_controller API.

You have access to the following tools:

## Watchlist Tools
- list_watchlists: List all watchlists
- get_active_watchlist: Get the currently active watchlist
- set_active_watchlist: Set the active watchlist by ID
- create_watchlist: Create a new watchlist
- get_watchlist: Get watchlist details by ID
- rename_watchlist: Rename a watchlist
- delete_watchlist: Delete a watchlist
- add_watchlist_symbols: Add symbols to a watchlist
- remove_watchlist_symbols: Remove symbols from a watchlist
- flag_watchlist_symbol: Flag or unflag a symbol in a watchlist
- list_colored_watchlists: List colored watchlists
- set_color_list_symbols: Replace all symbols in a color list
- append_color_list_symbols: Add symbols to a color list
- remove_color_list_symbols: Remove symbols from a color list
- bulk_remove_colored_symbols: Remove symbols from all color lists

## Chart Tools
- list_charts: List available chart IDs
- get_active_chart: Get active chart info
- get_symbol: Get the current ticker symbol on a chart
- set_symbol: Change the ticker symbol on a chart
- get_symbol_info: Get extended symbol metadata
- get_resolution: Get the current chart resolution
- set_resolution: Set the chart resolution
- get_chart_type: Get the chart type
- set_chart_type: Set the chart type
- get_currency: Get the price denomination currency
- set_currency: Set the price denomination currency
- list_available_currencies: List available currencies
- get_unit: Get the display unit
- set_unit: Set the display unit
- list_available_units: List available units
- zoom_chart: Zoom in or out
- scroll_chart: Scroll chart by bar count
- reset_chart_view: Reset chart view
- go_to_date: Navigate to a specific date
- get_visible_range: Get the visible time range
- set_visible_range: Set the visible time range
- set_timeframe: Set chart timeframe (1D, 1W, 1M, etc.)
- reset_scales: Reset price scales
- undo_chart: Undo last action
- redo_chart: Redo last action
- get_toggles: Get toggle states
- toggle_log_scale: Toggle logarithmic scale
- toggle_auto_scale: Toggle auto scale
- toggle_extended_hours: Toggle extended hours
- execute_chart_action: Execute a chart action by ID
- list_chart_panes: List chart panes
- next_chart: Switch to the next chart
- prev_chart: Switch to the previous chart
- maximize_chart: Toggle chart maximize
- activate_chart: Set active chart by index

Always use list_charts first to get valid chart IDs before operating on charts.
Always use list_watchlists first to get valid watchlist IDs before operating on watchlists.
"""

ALLOWED_TOOLS = [
    # Watchlist tools
    "mcp__maudeview__list_watchlists",
    "mcp__maudeview__get_active_watchlist",
    "mcp__maudeview__set_active_watchlist",
    "mcp__maudeview__create_watchlist",
    "mcp__maudeview__get_watchlist",
    "mcp__maudeview__rename_watchlist",
    "mcp__maudeview__delete_watchlist",
    "mcp__maudeview__add_watchlist_symbols",
    "mcp__maudeview__remove_watchlist_symbols",
    "mcp__maudeview__flag_watchlist_symbol",
    "mcp__maudeview__list_colored_watchlists",
    "mcp__maudeview__set_color_list_symbols",
    "mcp__maudeview__append_color_list_symbols",
    "mcp__maudeview__remove_color_list_symbols",
    "mcp__maudeview__bulk_remove_colored_symbols",
    # Chart tools
    "mcp__maudeview__list_charts",
    "mcp__maudeview__get_active_chart",
    "mcp__maudeview__get_symbol",
    "mcp__maudeview__set_symbol",
    "mcp__maudeview__get_symbol_info",
    "mcp__maudeview__get_resolution",
    "mcp__maudeview__set_resolution",
    "mcp__maudeview__get_chart_type",
    "mcp__maudeview__set_chart_type",
    "mcp__maudeview__get_currency",
    "mcp__maudeview__set_currency",
    "mcp__maudeview__list_available_currencies",
    "mcp__maudeview__get_unit",
    "mcp__maudeview__set_unit",
    "mcp__maudeview__list_available_units",
    "mcp__maudeview__zoom_chart",
    "mcp__maudeview__scroll_chart",
    "mcp__maudeview__reset_chart_view",
    "mcp__maudeview__go_to_date",
    "mcp__maudeview__get_visible_range",
    "mcp__maudeview__set_visible_range",
    "mcp__maudeview__set_timeframe",
    "mcp__maudeview__reset_scales",
    "mcp__maudeview__undo_chart",
    "mcp__maudeview__redo_chart",
    "mcp__maudeview__get_toggles",
    "mcp__maudeview__toggle_log_scale",
    "mcp__maudeview__toggle_auto_scale",
    "mcp__maudeview__toggle_extended_hours",
    "mcp__maudeview__execute_chart_action",
    "mcp__maudeview__list_chart_panes",
    "mcp__maudeview__next_chart",
    "mcp__maudeview__prev_chart",
    "mcp__maudeview__maximize_chart",
    "mcp__maudeview__activate_chart",
]
