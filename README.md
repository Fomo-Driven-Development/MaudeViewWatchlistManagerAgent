# MaudeView Watchlist Manager Agent

Go MCP server + Python A2A layer for managing TradingView watchlists and charts.

This is a reference implementation of the [MaudeView agent pattern](https://fomo-driven-development.github.io/MaudeViewTvDocs/building-agents/) — a thin client that wraps [MaudeViewTVCore](https://github.com/Fomo-Driven-Development/MaudeViewTVCore) REST endpoints as MCP tools. Fork it to build your own agent.

**[Full Documentation](https://fomo-driven-development.github.io/MaudeViewTvDocs/)** — architecture, quickstart, API reference, building agents.

## Tools (50)

### Watchlists (15)
- `list_watchlists` - List all watchlists
- `get_active_watchlist` - Get active watchlist
- `set_active_watchlist` - Set active watchlist
- `create_watchlist` - Create a new watchlist
- `get_watchlist` - Get watchlist details
- `rename_watchlist` - Rename a watchlist
- `delete_watchlist` - Delete a watchlist
- `add_watchlist_symbols` - Add symbols to a watchlist
- `remove_watchlist_symbols` - Remove symbols from a watchlist
- `flag_watchlist_symbol` - Flag/unflag a symbol
- `list_colored_watchlists` - List colored watchlists
- `set_color_list_symbols` - Replace color list symbols
- `append_color_list_symbols` - Add symbols to color list
- `remove_color_list_symbols` - Remove symbols from color list
- `bulk_remove_colored_symbols` - Remove symbols from all colors

### Charts (35)
- `list_charts` / `get_active_chart` - Chart listing and active info
- `get_symbol` / `set_symbol` / `get_symbol_info` - Symbol management
- `get_resolution` / `set_resolution` - Resolution control
- `get_chart_type` / `set_chart_type` - Chart type control
- `get_currency` / `set_currency` / `list_available_currencies` - Currency
- `get_unit` / `set_unit` / `list_available_units` - Units
- `zoom_chart` / `scroll_chart` / `reset_chart_view` / `go_to_date` - Navigation
- `get_visible_range` / `set_visible_range` / `set_timeframe` - Time range
- `reset_scales` / `undo_chart` / `redo_chart` - Actions
- `get_toggles` / `toggle_log_scale` / `toggle_auto_scale` / `toggle_extended_hours` - Toggles
- `execute_chart_action` / `list_chart_panes` - Introspection
- `next_chart` / `prev_chart` / `maximize_chart` / `activate_chart` - Multi-pane

## Setup

```bash
just setup
```

See the [Quick Start guide](https://fomo-driven-development.github.io/MaudeViewTvDocs/quickstart/) for the full walkthrough.

## Usage

```bash
just agent    # Interactive CLI
just a2a      # A2A server on :8100
just mcp      # Raw MCP server (stdio)
```
