# यह स्क्रिप्ट Vercel पर एक सर्वरलेस फ़ंक्शन के रूप में चलने के लिए बनाई गई है।
# यह भारतीय बाज़ार के स्टॉक्स को फ़िल्टर करता है।

from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import yfinance as yf
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
        try:
            # yfinance का उपयोग करके डेटा प्राप्त करें
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame() # अगर कोई एरर आता है, तो एक खाली डेटाफ़्रेम वापस करें

    def run_intraday_filter(self):
        # यहाँ आप NSE स्टॉक सिंबल की अपनी सूची जोड़ सकते हैं।
        # उदाहरण के लिए, मैंने कुछ लोकप्रिय भारतीय स्टॉक्स जोड़े हैं।
        # ध्यान दें: yfinance के लिए NSE सिंबल में '.NS' लगाना ज़रूरी है।
        stocks = ["RELIANCE.NS", "TCS.NS", "HDFC.NS", "INFY.NS", "ICICIBANK.NS"]
        filtered_stocks = []

        # इंट्राडे के लिए 1 दिन का डेटा 5 मिनट के अंतराल पर
        period = "1d"
        interval = "5m"

        for stock in stocks:
            df = self.get_stock_data(stock, period, interval)
            # जाँच करें कि डेटाफ़्रेम खाली तो नहीं है
            if not df.empty and len(df) > 1:
                # 5 मिनट के WMA और वॉल्यूम ब्रेकआउट की जाँच करें
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
