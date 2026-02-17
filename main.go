package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Fatal(".env file is required: ", err)
	}

	addr := os.Getenv("CONTROLLER_BIND_ADDR")
	if addr == "" {
		log.Fatal("CONTROLLER_BIND_ADDR must be set in .env")
	}
	baseURL := "http://" + addr
	client := &http.Client{}

	server := mcp.NewServer(&mcp.Implementation{
		Name:    "maudeview-watchlist-manager",
		Version: "1.0.0",
	}, nil)

	// ─── Watchlist Tools ─────────────────────────────────────────────

	type ListWatchlistsInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_watchlists",
		Description: "List all watchlists",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ ListWatchlistsInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, "/api/v1/watchlists", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetActiveWatchlistInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_active_watchlist",
		Description: "Get the currently active watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ GetActiveWatchlistInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, "/api/v1/watchlists/active", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetActiveWatchlistInput struct {
		ID string `json:"id" jsonschema:"Watchlist ID to set as active"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_active_watchlist",
		Description: "Set the active watchlist by ID",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetActiveWatchlistInput) (*mcp.CallToolResult, any, error) {
		payload := map[string]string{"id": args.ID}
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, "/api/v1/watchlists/active", payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type CreateWatchlistInput struct {
		Name string `json:"name" jsonschema:"Name for the new watchlist"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "create_watchlist",
		Description: "Create a new watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args CreateWatchlistInput) (*mcp.CallToolResult, any, error) {
		payload := map[string]string{"name": args.Name}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/watchlists", payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetWatchlistInput struct {
		WatchlistID string `json:"watchlist_id" jsonschema:"Watchlist ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_watchlist",
		Description: "Get watchlist details by ID",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetWatchlistInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s", args.WatchlistID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type RenameWatchlistInput struct {
		WatchlistID string `json:"watchlist_id" jsonschema:"Watchlist ID"`
		Name        string `json:"name" jsonschema:"New name for the watchlist"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "rename_watchlist",
		Description: "Rename a watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args RenameWatchlistInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s", args.WatchlistID)
		payload := map[string]string{"name": args.Name}
		body, err := doAPI(ctx, client, baseURL, http.MethodPatch, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type DeleteWatchlistInput struct {
		WatchlistID string `json:"watchlist_id" jsonschema:"Watchlist ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "delete_watchlist",
		Description: "Delete a watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args DeleteWatchlistInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s", args.WatchlistID)
		body, err := doAPI(ctx, client, baseURL, http.MethodDelete, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type AddWatchlistSymbolsInput struct {
		WatchlistID string   `json:"watchlist_id" jsonschema:"Watchlist ID"`
		Symbols     []string `json:"symbols" jsonschema:"Symbols to add, e.g. [\"NASDAQ:AAPL\", \"NYSE:MSFT\"]"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "add_watchlist_symbols",
		Description: "Add symbols to a watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args AddWatchlistSymbolsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s/symbols", args.WatchlistID)
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type RemoveWatchlistSymbolsInput struct {
		WatchlistID string   `json:"watchlist_id" jsonschema:"Watchlist ID"`
		Symbols     []string `json:"symbols" jsonschema:"Symbols to remove"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "remove_watchlist_symbols",
		Description: "Remove symbols from a watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args RemoveWatchlistSymbolsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s/symbols", args.WatchlistID)
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodDelete, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type FlagWatchlistSymbolInput struct {
		WatchlistID string `json:"watchlist_id" jsonschema:"Watchlist ID"`
		Symbol      string `json:"symbol" jsonschema:"Symbol to flag/unflag"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "flag_watchlist_symbol",
		Description: "Flag or unflag a symbol in a watchlist",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args FlagWatchlistSymbolInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlist/%s/flag", args.WatchlistID)
		payload := map[string]string{"symbol": args.Symbol}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ListColoredWatchlistsInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_colored_watchlists",
		Description: "List colored watchlists",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ ListColoredWatchlistsInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, "/api/v1/watchlists/colored", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetColorListSymbolsInput struct {
		Color   string   `json:"color" jsonschema:"Color name"`
		Symbols []string `json:"symbols" jsonschema:"Symbols to set for this color"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_color_list_symbols",
		Description: "Replace all symbols in a color list",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetColorListSymbolsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlists/colored/%s", args.Color)
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type AppendColorListSymbolsInput struct {
		Color   string   `json:"color" jsonschema:"Color name"`
		Symbols []string `json:"symbols" jsonschema:"Symbols to add to this color"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "append_color_list_symbols",
		Description: "Add symbols to a color list",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args AppendColorListSymbolsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlists/colored/%s/append", args.Color)
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type RemoveColorListSymbolsInput struct {
		Color   string   `json:"color" jsonschema:"Color name"`
		Symbols []string `json:"symbols" jsonschema:"Symbols to remove from this color"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "remove_color_list_symbols",
		Description: "Remove symbols from a color list",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args RemoveColorListSymbolsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/watchlists/colored/%s/remove", args.Color)
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type BulkRemoveColoredSymbolsInput struct {
		Symbols []string `json:"symbols" jsonschema:"Symbols to remove from all colors"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "bulk_remove_colored_symbols",
		Description: "Remove symbols from all color lists",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args BulkRemoveColoredSymbolsInput) (*mcp.CallToolResult, any, error) {
		payload := map[string]any{"symbols": args.Symbols}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/watchlists/colored/bulk-remove", payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	// ─── Chart Tools ─────────────────────────────────────────────────

	type ListChartsInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_charts",
		Description: "List available TradingView chart IDs",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ ListChartsInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, "/api/v1/charts", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetActiveChartInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_active_chart",
		Description: "Get active chart info (count, active index)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ GetActiveChartInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, "/api/v1/charts/active", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetSymbolInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_symbol",
		Description: "Get the current ticker symbol on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetSymbolInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/symbol", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetSymbolInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Symbol  string `json:"symbol" jsonschema:"Ticker symbol, e.g. NASDAQ:AAPL"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_symbol",
		Description: "Change the ticker symbol on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetSymbolInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/symbol?symbol=%s", args.ChartID, args.Symbol)
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetSymbolInfoInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_symbol_info",
		Description: "Get extended symbol metadata",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetSymbolInfoInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/symbol/info", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetResolutionInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_resolution",
		Description: "Get the current chart resolution/timeframe",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetResolutionInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/resolution", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetResolutionInput struct {
		ChartID    string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Resolution string `json:"resolution" jsonschema:"Resolution, e.g. 1, 5, 15, 60, D, W, M"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_resolution",
		Description: "Set the chart resolution/timeframe",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetResolutionInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/resolution?resolution=%s", args.ChartID, args.Resolution)
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetChartTypeInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_chart_type",
		Description: "Get the chart type (candles, bars, line, etc.)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetChartTypeInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/chart-type", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetChartTypeInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Type    string `json:"type" jsonschema:"Chart type: candles, bars, line, area, etc."`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_chart_type",
		Description: "Set the chart type (candles, bars, line, etc.)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetChartTypeInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/chart-type?type=%s", args.ChartID, args.Type)
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetCurrencyInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_currency",
		Description: "Get the price denomination currency",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetCurrencyInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/currency", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetCurrencyInput struct {
		ChartID  string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Currency string `json:"currency" jsonschema:"Currency code, e.g. USD, EUR"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_currency",
		Description: "Set the price denomination currency",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetCurrencyInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/currency?currency=%s", args.ChartID, args.Currency)
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ListAvailableCurrenciesInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_available_currencies",
		Description: "List available currencies for a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ListAvailableCurrenciesInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/currency/available", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetUnitInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_unit",
		Description: "Get the display unit",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetUnitInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/unit", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetUnitInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Unit    string `json:"unit" jsonschema:"Display unit"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_unit",
		Description: "Set the display unit",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetUnitInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/unit?unit=%s", args.ChartID, args.Unit)
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ListAvailableUnitsInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_available_units",
		Description: "List available display units for a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ListAvailableUnitsInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/unit/available", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ZoomChartInput struct {
		ChartID   string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Direction string `json:"direction" jsonschema:"Zoom direction: in or out"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "zoom_chart",
		Description: "Zoom in or out on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ZoomChartInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/zoom", args.ChartID)
		payload := map[string]string{"direction": args.Direction}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ScrollChartInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Bars    int    `json:"bars" jsonschema:"Number of bars to scroll (positive=right, negative=left)"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "scroll_chart",
		Description: "Scroll chart by bar count",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ScrollChartInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/scroll", args.ChartID)
		payload := map[string]int{"bars": args.Bars}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ResetChartViewInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "reset_chart_view",
		Description: "Reset chart view (Alt+R)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResetChartViewInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/reset-view", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GoToDateInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Date    string `json:"date" jsonschema:"Date to navigate to"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "go_to_date",
		Description: "Navigate chart to a specific date",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GoToDateInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/go-to-date", args.ChartID)
		payload := map[string]string{"date": args.Date}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetVisibleRangeInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_visible_range",
		Description: "Get the visible time range on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetVisibleRangeInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/visible-range", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetVisibleRangeInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
		From    int64  `json:"from" jsonschema:"Start timestamp"`
		To      int64  `json:"to" jsonschema:"End timestamp"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_visible_range",
		Description: "Set the visible time range on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetVisibleRangeInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/visible-range", args.ChartID)
		payload := map[string]any{"from": args.From, "to": args.To}
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type SetTimeframeInput struct {
		ChartID   string `json:"chart_id" jsonschema:"TradingView chart ID"`
		Timeframe string `json:"timeframe" jsonschema:"Timeframe, e.g. 1D, 1W, 1M, 3M, 6M, YTD, 1Y, 5Y, ALL"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_timeframe",
		Description: "Set chart timeframe (1D, 1W, 1M, etc.)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args SetTimeframeInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/timeframe", args.ChartID)
		payload := map[string]string{"timeframe": args.Timeframe}
		body, err := doAPI(ctx, client, baseURL, http.MethodPut, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ResetScalesInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "reset_scales",
		Description: "Reset price scales on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ResetScalesInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/reset-scales", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type UndoChartInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "undo_chart",
		Description: "Undo last chart action (Ctrl+Z)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args UndoChartInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/undo", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type RedoChartInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "redo_chart",
		Description: "Redo last chart action (Ctrl+Y)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args RedoChartInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/redo", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type GetTogglesInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_toggles",
		Description: "Get toggle states (log, auto, extended)",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args GetTogglesInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/toggles", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ToggleLogScaleInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "toggle_log_scale",
		Description: "Toggle logarithmic scale on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ToggleLogScaleInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/toggles/log-scale", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ToggleAutoScaleInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "toggle_auto_scale",
		Description: "Toggle auto scale on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ToggleAutoScaleInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/toggles/auto-scale", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ToggleExtendedHoursInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "toggle_extended_hours",
		Description: "Toggle extended hours on a chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ToggleExtendedHoursInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/toggles/extended-hours", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ExecuteChartActionInput struct {
		ChartID  string `json:"chart_id" jsonschema:"TradingView chart ID"`
		ActionID string `json:"action_id" jsonschema:"Action ID to execute"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "execute_chart_action",
		Description: "Execute a chart action by ID",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ExecuteChartActionInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/action", args.ChartID)
		payload := map[string]string{"action_id": args.ActionID}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, path, payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ListChartPanesInput struct {
		ChartID string `json:"chart_id" jsonschema:"TradingView chart ID"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_chart_panes",
		Description: "List chart panes",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ListChartPanesInput) (*mcp.CallToolResult, any, error) {
		path := fmt.Sprintf("/api/v1/chart/%s/panes", args.ChartID)
		body, err := doAPI(ctx, client, baseURL, http.MethodGet, path, nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type NextChartInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "next_chart",
		Description: "Switch to the next chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ NextChartInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/chart/next", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type PrevChartInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "prev_chart",
		Description: "Switch to the previous chart",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ PrevChartInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/chart/prev", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type MaximizeChartInput struct{}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "maximize_chart",
		Description: "Toggle chart maximize",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ MaximizeChartInput) (*mcp.CallToolResult, any, error) {
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/chart/maximize", nil)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	type ActivateChartInput struct {
		Index int `json:"index" jsonschema:"Chart index to activate"`
	}
	mcp.AddTool(server, &mcp.Tool{
		Name:        "activate_chart",
		Description: "Set active chart by index",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args ActivateChartInput) (*mcp.CallToolResult, any, error) {
		payload := map[string]int{"index": args.Index}
		body, err := doAPI(ctx, client, baseURL, http.MethodPost, "/api/v1/chart/activate", payload)
		if err != nil {
			return errResult(err), nil, nil
		}
		return textResult(body), nil, nil
	})

	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatal(err)
	}
}

// doAPI makes an HTTP request to the tv_controller and returns the response body.
func doAPI(ctx context.Context, client *http.Client, baseURL, method, path string, body any) (json.RawMessage, error) {
	var bodyReader io.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("marshal request body: %w", err)
		}
		bodyReader = bytes.NewReader(data)
	}

	req, err := http.NewRequestWithContext(ctx, method, baseURL+path, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request %s %s: %w", method, path, err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("%s %s returned %d: %s", method, path, resp.StatusCode, string(respBody))
	}

	return json.RawMessage(respBody), nil
}

func textResult(data json.RawMessage) *mcp.CallToolResult {
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}
}

func errResult(err error) *mcp.CallToolResult {
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: err.Error()},
		},
		IsError: true,
	}
}
