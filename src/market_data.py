from datetime import datetime, timezone

import pandas as pd
import yfinance as yf


def _safe_number(value):
    """Return float value where possible, otherwise None."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def _calculate_return(current_price, earlier_price):
    """Calculate percentage return between two prices."""
    current = _safe_number(current_price)
    earlier = _safe_number(earlier_price)

    if current is None or earlier is None or earlier == 0:
        return None

    return ((current / earlier) - 1) * 100


def fetch_market_snapshot(asx_ticker):
    """
    Fetch recent daily market history for an ASX-listed company.

    Market data are used as a research input only.
    Fundamental and financing evidence remains sourced separately.
    """

    yahoo_ticker = f"{asx_ticker}.AX"

    ticker = yf.Ticker(yahoo_ticker)

    history = ticker.history(
        period="6mo",
        interval="1d",
        auto_adjust=False,
    )

    if history is None or history.empty:
        raise ValueError(
            f"No market history returned for {yahoo_ticker}"
        )

    history = history.copy()

    required_columns = {"Close", "Volume"}

    if not required_columns.issubset(history.columns):
        raise ValueError(
            f"Required price/volume columns missing for {yahoo_ticker}"
        )

    history = history[
        history["Close"].notna()
        & history["Volume"].notna()
    ].copy()

    if history.empty:
        raise ValueError(
            f"No usable market observations for {yahoo_ticker}"
        )


    # ------------------------------------------------------------
    # LATEST MARKET OBSERVATION
    # ------------------------------------------------------------

    latest = history.iloc[-1]

    latest_price = float(latest["Close"])

    latest_market_date = history.index[-1].date().isoformat()


    # ------------------------------------------------------------
    # 20-DAY LIQUIDITY
    # ------------------------------------------------------------

    last_20 = history.tail(20).copy()

    last_20["daily_value_traded"] = (
        last_20["Close"] * last_20["Volume"]
    )

    avg_daily_volume_20d = float(
        last_20["Volume"].mean()
    )

    avg_daily_value_traded_20d_aud_m = float(
        last_20["daily_value_traded"].mean()
        / 1_000_000
    )


    # ------------------------------------------------------------
    # PRICE PERFORMANCE
    # ------------------------------------------------------------

    one_month_return_pct = None
    three_month_return_pct = None

    if len(history) >= 22:
        one_month_return_pct = _calculate_return(
            latest_price,
            history.iloc[-22]["Close"],
        )

    if len(history) >= 64:
        three_month_return_pct = _calculate_return(
            latest_price,
            history.iloc[-64]["Close"],
        )


    # ------------------------------------------------------------
    # OBSERVATION COVERAGE
    # ------------------------------------------------------------

    trading_days_available = int(len(history))


    return {
        "ticker": asx_ticker.upper(),
        "yahoo_ticker": yahoo_ticker,
        "latest_market_date": latest_market_date,
        "latest_price_aud": round(latest_price, 6),
        "avg_daily_volume_20d": round(
            avg_daily_volume_20d,
            2,
        ),
        "avg_daily_value_traded_20d_aud_m": round(
            avg_daily_value_traded_20d_aud_m,
            6,
        ),
        "return_1m_pct": (
            round(one_month_return_pct, 2)
            if one_month_return_pct is not None
            else None
        ),
        "return_3m_pct": (
            round(three_month_return_pct, 2)
            if three_month_return_pct is not None
            else None
        ),
        "trading_days_available": trading_days_available,
        "refreshed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "market_data_source": "Yahoo Finance via yfinance",
        "refresh_status": "SUCCESS",
        "refresh_error": None,
    }
