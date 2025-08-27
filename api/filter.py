# इस स्क्रिप्ट को Vercel पर एक सर्वरलेस फ़ंक्शन के रूप में चलाने के लिए बनाया गया है।
# यह भारतीय बाज़ार के स्टॉक्स को फ़िल्टर करता है।

from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, HTTPServer
import json
import pandas as pd
from datetime import datetime, timedelta
import pandas_datareader.data as web

# यह Vercel के लिए एक कस्टम HTTP हैंडलर है।
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS हेडर सेट करें
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # URL से 'type' पैरामीटर प्राप्त करें
        query_params = self.path.split('?')
        filter_type = 'intraday'
        if len(query_params) > 1:
            params = dict(param.split('=') for param in query_params[1].split('&'))
            if 'type' in params:
                filter_type = params['type']
        
        # फ़िल्टर टाइप के आधार पर फ़ंक्शन चलाएँ
        if filter_type == 'intraday':
            results = self.run_intraday_filter()
        elif filter_type == 'swing':
            results = self.run_swing_filter()
        elif filter_type == 'longterm':
            results = self.run_longterm_filter()
        elif filter_type == 'chartpattern':
            results = self.run_chart_pattern_filter()
        else:
            results = ["अज्ञात फ़िल्टर प्रकार"]

        # JSON में परिणाम भेजें
        self.wfile.write(json.dumps(results).encode('utf-8'))

    def get_stock_data(self, symbol, start_date, end_date):
        try:
            # DataReader का उपयोग करके Yahoo Finance से डेटा प्राप्त करें
            df = web.DataReader(symbol, 'yahoo', start_date, end_date)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def run_intraday_filter(self):
        # यहाँ आप NSE स्टॉक सिंबल की अपनी सूची जोड़ सकते हैं।
        # उदाहरण के लिए, मैंने कुछ लोकप्रिय भारतीय स्टॉक्स जोड़े हैं।
        stocks = ["RELIANCE.NS", "TCS.NS", "HDFC.NS", "INFY.NS", "ICICIBANK.NS"]
        filtered_stocks = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7) # पिछले 7 दिनों का डेटा

        for stock in stocks:
            df = self.get_stock_data(stock, start_date, end_date)
            if df is not None and len(df) > 1:
                # 5 मिनट के WMA और वॉल्यूम ब्रेकआउट की जाँच करें
                # यह एक सरलीकृत उदाहरण है, वास्तविक इंट्राडे रणनीति को अधिक जटिल डेटा की आवश्यकता होगी।
                latest_close = df['Close'].iloc[-1]
                latest_open = df['Open'].iloc[-1]
                latest_volume = df['Volume'].iloc[-1]
                
                # बुलिश कैंडल की जाँच
                is_bullish = latest_close > latest_open
                
                # वॉल्यूम ब्रेकआउट की जाँच (पिछले 5 दिनों के औसत वॉल्यूम से 1.5 गुना अधिक)
                if len(df) >= 5:
                    avg_volume = df['Volume'].iloc[-6:-1].mean()
                    is_volume_breakout = latest_volume > avg_volume * 1.5
                else:
                    is_volume_breakout = False
                
                if is_bullish and is_volume_breakout:
                    filtered_stocks.append(stock)
        return filtered_stocks

    def run_swing_filter(self):
        # स्विंग ट्रेडिंग के लिए लॉजिक यहाँ डालें।
        return ["स्विंग ट्रेडिंग फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

    def run_longterm_filter(self):
        # लॉन्ग-टर्म निवेश के लिए लॉजिक यहाँ डालें।
        return ["लॉन्ग टर्म निवेश फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

    def run_chart_pattern_filter(self):
        # चार्ट पैटर्न के लिए लॉजिक यहाँ डालें।
        return ["चार्ट पैटर्न फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

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

