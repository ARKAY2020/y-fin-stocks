# यह स्क्रिप्ट Vercel पर एक सर्वरलेस फ़ंक्शन के रूप में चलने के लिए बनाई गई है।
# यह भारतीय बाज़ार के स्टॉक्स को फ़िल्टर करता है।

from http.server import BaseHTTPRequestHandler
import json
import requests
import pandas as pd
from datetime import datetime, timedelta

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

    def get_stock_data(self, symbol, period="1mo", interval="1d"):
        # Alpha Vantage API का उपयोग करें (NSE के लिए .NS जोड़ें)
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_{interval.upper()}&symbol={symbol}.NSWPK5SOY3Z9NO8KBM"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # HTTP एरर के लिए जाँच करें
            data = response.json()

            # डेटा को pandas डेटाफ़्रेम में बदलें
            if interval == "1d":
                time_series = data.get('Time Series (Daily)', {})
            elif interval == "1wk":
                time_series = data.get('Weekly Adjusted Time Series', {})
            else:
                time_series = {}

            if not time_series:
                print(f"No data found for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame.from_dict(time_series, orient='index')
            df = df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            })
            df['Timestamp'] = pd.to_datetime(df.index)
            df.set_index('Timestamp', inplace=True)
            df = df.astype(float)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def run_intraday_filter(self):
        stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        filtered_stocks = []

        for stock in stocks:
            df = self.get_stock_data(stock, period="1d", interval="15min")  # 15-minute data
            if not df.empty and len(df) > 1:
                latest_close = df['Close'].iloc[-1]
                latest_open = df['Open'].iloc[-1]
                latest_volume = df['Volume'].iloc[-1]
                
                # बुलिश कैंडल की जाँच
                is_bullish = latest_close > latest_open
                
                # वॉल्यूम ब्रेकआउट की जाँच (पिछले 5 कैंडल के औसत वॉल्यूम से 1.5 गुना अधिक)
                if len(df) > 5:
                    avg_volume = df['Volume'].iloc[-6:-1].mean()
                    is_volume_breakout = latest_volume > avg_volume * 1.5
                else:
                    is_volume_breakout = False
                
                if is_bullish and is_volume_breakout:
                    filtered_stocks.append(stock)
        return filtered_stocks if filtered_stocks else ["इंट्राडे फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

    def run_swing_filter(self):
        # स्विंग ट्रेडिंग के लिए लॉजिक (स्थायी रूप से 1 सप्ताह का डेटा)
        stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        filtered_stocks = []

        for stock in stocks:
            df = self.get_stock_data(stock, period="1wk", interval="1d")
            if not df.empty and len(df) > 5:
                latest_close = df['Close'].iloc[-1]
                prev_close = df['Close'].iloc[-2]
                if latest_close > prev_close * 1.02:  # 2% ऊपर
                    filtered_stocks.append(stock)
        return filtered_stocks if filtered_stocks else ["स्विंग ट्रेडिंग फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

    def run_longterm_filter(self):
        # लॉन्ग-टर्म निवेश के लिए लॉजिक (1 साल का डेटा)
        stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        filtered_stocks = []

        for stock in stocks:
            df = self.get_stock_data(stock, period="1y", interval="1wk")
            if not df.empty and len(df) > 20:
                wma = df['Close'].rolling(window=20, weights=range(1, 21)).mean().iloc[-1]
                latest_close = df['Close'].iloc[-1]
                avg_volume = df['Volume'].mean()
                if latest_close > wma * 1.05 and avg_volume > 100000:  # 5% WMA ऊपर और न्यूनतम वॉल्यूम
                    filtered_stocks.append(stock)
        return filtered_stocks if filtered_stocks else ["लॉंग टर्म निवेश फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

    def run_chart_pattern_filter(self):
        # चार्ट पैटर्न के लिए लॉजिक (स्थायी रूप से सरल पैटर्न)
        stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        filtered_stocks = []

        for stock in stocks:
            df = self.get_stock_data(stock, period="1mo", interval="1d")
            if not df.empty and len(df) > 10:
                highs = df['High'].rolling(window=5).max()
                lows = df['Low'].rolling(window=5).min()
                if df['Close'].iloc[-1] > highs.iloc[-2] and df['Volume'].iloc[-1] > df['Volume'].mean():
                    filtered_stocks.append(stock)
        return filtered_stocks if filtered_stocks else ["चार्ट पैटर्न फ़िल्टर के लिए कोई स्टॉक नहीं मिला।"]

