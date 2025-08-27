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

    def get_stock_data(self, symbol, period, interval):
        # हम यहाँ सीधे Yahoo Finance के बजाय NSE की वेबसाइट से डेटा लाने का प्रयास करेंगे
        try:
            # यह एक सामान्य NSE API का URL है, लेकिन यह बदल सकता है।
            url = f"https://www.nseindia.com/api/chart-databy-symbol?symbol={symbol}&resolution=15" # 15-minute interval
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() # HTTP एरर के लिए जाँच करें
            data = response.json()
            
            # यदि डेटा मिलता है, तो इसे एक pandas डेटाफ़्रेम में बदलें
            candles = data['g']
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df.set_index('Timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol} from NSE: {e}")
            return pd.DataFrame()

    def run_intraday_filter(self):
        # यहाँ आप NSE स्टॉक सिंबल की अपनी सूची जोड़ सकते हैं।
        stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"] # NSE सिंबल में '.NS' नहीं है
        filtered_stocks = []

        for stock in stocks:
            df = self.get_stock_data(stock, None, None) # period and interval are handled in get_stock_data
            
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
