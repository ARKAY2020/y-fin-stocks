# A simple Flask app for Vercel's serverless function.
# This code will be placed in the `api` directory as `filter.py`.

from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import time # Import the time module here

# The Flask application object must be named 'app' for Vercel to work.
app = Flask(__name__)

# Sample stock list for the Indian market (NSE)
# .NS suffix is mandatory for NSE stocks.
STOCK_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFC.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'BHARTIARTL.NS', 'ASIANPAINT.NS', 'BAJFINANCE.NS',
    'AXISBANK.NS'
]

# --- Stock Filter Logic Functions ---
# These are the same functions from your previous script.
# They are self-contained and ready to be used by the API endpoint.

def get_intraday_breakout_stocks(stock_list):
    """
    Filters for intraday breakout stocks.
    Finds stocks where the 5-minute price is above a short WMA and has increased volume.
    """
    filtered_stocks = []
    for ticker_symbol in stock_list:
        try:
            # Yfinance को थ्रॉटल होने से रोकने के लिए 1 सेकंड का इंतज़ार करें
            time.sleep(1) 
            data = yf.download(ticker_symbol, period='5d', interval='5m', prepost=False, progress=False)
            if data.empty or len(data) < 20:
                continue

            data['WMA'] = data['Close'].rolling(window=15).apply(lambda x: (x * pd.Series(range(1, 16))).sum() / (pd.Series(range(1, 16))).sum(), raw=True)
            data['Average_Volume'] = data['Volume'].rolling(window=30).mean()
            
            latest_row = data.iloc[-1]
            previous_row = data.iloc[-2]

            if (latest_row['Close'] > latest_row['WMA'] and
                previous_row['Close'] <= latest_row['WMA'] and
                latest_row['Volume'] > latest_row['Average_Volume'] * 1.5):
                
                filtered_stocks.append(ticker_symbol)

        except Exception as e:
            print(f"Error fetching {ticker_symbol} for Intraday: {e}")
            continue
    return filtered_stocks

def get_swing_trading_stocks(stock_list):
    """
    Filters for swing trading stocks.
    Finds stocks where the 20-day EMA is crossing above the 50-day EMA (Golden Cross).
    """
    filtered_stocks = []
    for ticker_symbol in stock_list:
        try:
            # Yfinance को थ्रॉटल होने से रोकने के लिए 1 सेकंड का इंतज़ार करें
            time.sleep(1)
            data = yf.download(ticker_symbol, period='100d', interval='1d', prepost=False, progress=False)
            if data.empty or len(data) < 50:
                continue
            
            data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
            data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

            latest_row = data.iloc[-1]
            previous_row = data.iloc[-2]

            if (latest_row['EMA20'] > latest_row['EMA50'] and
                previous_row['EMA20'] <= previous_row['EMA50']):
                
                filtered_stocks.append(ticker_symbol)

        except Exception as e:
            print(f"Error fetching {ticker_symbol} for Swing: {e}")
            continue
    return filtered_stocks

def get_long_term_stocks(stock_list):
    """
    Filters for long-term investment stocks.
    Finds stocks where the weekly closing price is above the 200-week EMA.
    """
    filtered_stocks = []
    for ticker_symbol in stock_list:
        try:
            # Yfinance को थ्रॉटल होने से रोकने के लिए 1 सेकंड का इंतज़ार करें
            time.sleep(1)
            data = yf.download(ticker_symbol, period='5y', interval='1wk', prepost=False, progress=False)
            if data.empty or len(data) < 200:
                continue
            
            data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
            
            if data.iloc[-1]['Close'] > data.iloc[-1]['EMA200']:
                filtered_stocks.append(ticker_symbol)

        except Exception as e:
            print(f"Error fetching {ticker_symbol} for Long Term: {e}")
            continue
    return filtered_stocks

def get_consolidation_breakout_stocks(stock_list):
    """
    Filters for stocks with a consolidation breakout pattern.
    Finds stocks that have been in a narrow range and then broke out with high volume.
    """
    filtered_stocks = []
    for ticker_symbol in stock_list:
        try:
            # Yfinance को थ्रॉटल होने से रोकने के लिए 1 सेकंड का इंतज़ार करें
            time.sleep(1)
            data = yf.download(ticker_symbol, period='100d', interval='1d', prepost=False, progress=False)
            if data.empty or len(data) < 50:
                continue
            
            recent_data = data.iloc[-30:]
            
            price_range = recent_data['High'].max() - recent_data['Low'].min()
            percentage_range = (price_range / recent_data['Close'].iloc[0]) * 100
            
            latest_row = data.iloc[-1]
            breakout_condition = latest_row['Close'] > recent_data['High'].max() * 0.99
            volume_condition = latest_row['Volume'] > recent_data['Volume'].mean() * 2

            if percentage_range < 5 and breakout_condition and volume_condition:
                filtered_stocks.append(ticker_symbol)

        except Exception as e:
            print(f"Error fetching {ticker_symbol} for Chart Pattern: {e}")
            continue
    return filtered_stocks

# --- API Endpoint ---
# This route will be accessible at /api/filter from your Vercel URL
@app.route('/api/filter', methods=['GET'])
def filter_stocks():
    filter_type = request.args.get('type')
    
    if filter_type == 'intraday':
        results = get_intraday_breakout_stocks(STOCK_LIST)
    elif filter_type == 'swing':
        results = get_swing_trading_stocks(STOCK_LIST)
    elif filter_type == 'longterm':
        results = get_long_term_stocks(STOCK_LIST)
    elif filter_type == 'chartpattern':
        results = get_consolidation_breakout_stocks(STOCK_LIST)
    else:
        return jsonify({"error": "Invalid filter type"}), 400
        
    return jsonify(results)
