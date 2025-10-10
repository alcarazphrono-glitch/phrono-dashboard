import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_price_data(tickers, period_years=3):
    """
    Download daily adjusted close price data for a list of tickers over the last `period_years`.
    
    Args:
        tickers (list of str): List of ticker symbols.
        period_years (int): Number of years of historical data to fetch (default: 3).
    
    Returns:
        pd.DataFrame: DataFrame with Date as index and tickers as columns, containing adjusted closing prices.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=period_years * 365)
    
    # Download data
    data = yf.download(
        tickers=tickers,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        progress=False,
        group_by='ticker',
        auto_adjust=True
    )
    
    # Extract adjusted close prices for all tickers
    if len(tickers) == 1:
        # yfinance returns a series if only one ticker
        close_prices = data['Adj Close'].to_frame()
        close_prices.columns = tickers
    else:
        close_prices = pd.DataFrame({
            ticker: data[ticker]['Adj Close']
            for ticker in tickers
        })
    
    # Handle missing values: forward-fill then back-fill as fallback
    close_prices = close_prices.ffill().bfill()
    
    # Drop rows where all tickers are still missing (rare)
    close_prices = close_prices.dropna(how='all')
    
    return close_prices

def prepare_for_log_returns(df):
    """
    Prepare a DataFrame of closing prices for log return calculations.
    Ensures no non-positive prices and handles missing values.
    
    Args:
        df (pd.DataFrame): DataFrame of closing prices.
    
    Returns:
        pd.DataFrame: Cleaned DataFrame ready for log return calculation.
    """
    # Remove non-positive prices (cannot compute log)
    df = df[(df > 0).all(axis=1)]
    # Optionally, could drop rows with any missing values
    df = df.dropna(how='any')
    return df

# Example usage:
# tickers = ["AAPL", "MSFT", "GOOG"]
# prices = download_price_data(tickers)
# prices_clean = prepare_for_log_returns(prices)