
import yfinance as yf
import pandas as pd
import datetime
import pytz
import warnings
import os
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import mplfinance as mpf

# --- 全域設定 ---
warnings.filterwarnings("ignore")
TZ = pytz.timezone('Asia/Taipei')

# --- 股票群組設定 ---
STOCK_GROUPS = [
    {
        "title": "<<美股主要指數>>",
        "symbols": ["^VIX", "^GSPC", "^SOX", "^IXIC", "^DJI", "^NYFANG", "^N225", "^XAU"],
        "description": "VIX:恐慌指數, GSPC:標普, SOX:費半, IXIC:納斯達克, DJI:道瓊, NYFNAG:尖牙, N225:日經, XAU:黃金現貨"
    },
    {
        "title": "<<台股ETF>>",
        "symbols": ["00770.TW", "00924.TW", "00757.TW", "006208.TW", "00631L.TW", "2330.TW", "00733.TW", "00661.TW"],
        "description": "包含主要台股ETF及台積電"
    },
    {
        "title": "<<債券ETF>>",
        "symbols": ["HYG", "00937B.TWO", "00725B.TWO", "00679B.TWO", "00687B.TWO", "00719B.TWO"],
        "description": "HYG:高收益公司債, 00937B(群益BBB20Y), 00725B(國泰BBB10Y), 00679B(元大美債20Y), 00687B(國泰美債20Y), 00719B(元大美債1-3Y)"
    }
]

# --- 資料獲取 ---
def get_stock_data(symbols, start_date, end_date):
    """抓取多支股票的資料"""
    data = {}
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                print(f"警告：無法獲取 {symbol} 的有效資料，將跳過。")
                continue
            
            # 處理 yfinance 可能回傳的 MultiIndex 欄位
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            df = df[~df.index.duplicated(keep='first')]
            data[symbol] = df
        except Exception as e:
            print(f"抓取 {symbol} 資料時發生錯誤: {e}")
    return data

# --- 技術指標計算 ---
def calculate_all_indicators(df):
    """計算所有需要的技術指標"""
    df = df.copy()
    # KD
    low_min = df['Low'].rolling(window=9, min_periods=1).min()
    high_max = df['High'].rolling(window=9, min_periods=1).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    
    # BIAS
    for period in [5, 20, 60]:
        ma = df['Close'].rolling(window=period).mean()
        df[f'BIAS_{period}'] = ((df['Close'] - ma) / ma) * 100
        
    # DMI
    df['+DM'] = df['High'].diff().clip(lower=0)
    df['-DM'] = -df['Low'].diff().clip(upper=0)
    tr = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['TR'] = tr.rolling(window=14).sum()
    df['+DI'] = 100 * (df['+DM'].rolling(window=14).sum() / df['TR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=14).sum() / df['TR'])
    dx = abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = (dx * 100).rolling(window=14).mean()

    # Change & Volume
    df['Change %'] = df['Close'].pct_change() * 100
    df['Volume Change %'] = (df['Volume'] / df['Volume'].rolling(window=20).mean() * 100).fillna(0)
    
    # Moving Averages
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['20MA'] = df['Close'].rolling(window=20).mean()
    df['60MA'] = df['Close'].rolling(window=60).mean()
    
    return df

# --- HTML 與繪圖 ---
def get_value_style(value, high, low):
    """根據閾值返回顏色"""
    if pd.isna(value): return ""
    if value > high: return "color:red;"
    if value < low: return "color:green;"
    return ""

def format_data_row(symbol, latest, prev):
    """格式化單行HTML表格資料"""
    def get_scalar(data, key):
        val = data.get(key)
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return val if pd.notna(val) else 0.0

    change_pct = get_scalar(latest, "Change %")
    close = get_scalar(latest, "Close")
    vol_change = get_scalar(latest, "Volume Change %")
    k = get_scalar(latest, "K")
    d = get_scalar(latest, "D")
    bias5 = get_scalar(latest, "BIAS_5")
    bias20 = get_scalar(latest, "BIAS_20")
    bias60 = get_scalar(latest, "BIAS_60")
    adx = get_scalar(latest, "ADX")
    plus_di = get_scalar(latest, "+DI")
    minus_di = get_scalar(latest, "-DI")

    return [
        symbol,
        f'<span style="{get_value_style(change_pct, 0, 0)}">{close:.2f}</span>',
        f'<span style="{get_value_style(change_pct, 0, 0)}">{change_pct:.2f}%</span>',
        f'<span style="{get_value_style(vol_change, 100, 50)}">{vol_change:.1f}%</span>',
        f'<span style="{get_value_style(k, 80, 20)}">{k:.1f}</span>',
        f'<span style="{get_value_style(d, 80, 20)}">{d:.1f}</span>',
        f'<span style="{get_value_style(bias5, 4, -4)}">{bias5:.1f}</span>',
        f'<span style="{get_value_style(bias20, 7, -7)}">{bias20:.1f}</span>',
        f'<span style="{get_value_style(bias60, 15, -15)}">{bias60:.1f}</span>',
        f'<span style="{get_value_style(adx, 25, 0)}">{adx:.1f}</span>',
        f'<span style="{get_value_style(plus_di, minus_di, float("-inf"))}">{plus_di:.1f}</span>',
        f'<span style="{get_value_style(minus_di, plus_di, float("-inf"))}">{minus_di:.1f}</span>',
    ]

def create_ma_plot_base64(df, symbol):
    """建立K線圖(含MA與成交量)並返回Base64字串"""
    # 定義自訂樣式：紅漲綠跌 (Taiwan Style)
    mc = mpf.make_marketcolors(up='r', down='g', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', gridaxis='both')

    buf = BytesIO()
    
    # 繪製 K 線圖、均線 (5, 20, 60) 與成交量
    try:
        mpf.plot(df, type='candle', mav=(5, 20, 60), volume=True, 
                 style=s, figsize=(10, 5), 
                 savefig=dict(fname=buf, format='png', bbox_inches='tight', pad_inches=0.1),
                 ylabel='', ylabel_lower='',
                 xrotation=30,
                 datetime_format='%Y-%m-%d',
                 tight_layout=True)
        
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        print(f"繪製 {symbol} K線圖時發生錯誤: {e}")
        return None

def create_yield_curve_plot_base64():
    """建立美國公債殖利率曲線圖並返回Base64字串"""
    print("  - 正在產生美國公債殖利率圖表...")
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=10*365)
        
        print(f"    - 抓取 ^TNX 資料從 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        ten_year_df = yf.download("^TNX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        print(f"    - ^TNX 資料獲取完畢，共 {len(ten_year_df)} 筆。")

        print(f"    - 抓取 ^IRX 資料從 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        three_month_df = yf.download("^IRX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        print(f"    - ^IRX 資料獲取完畢，共 {len(three_month_df)} 筆。")

        if ten_year_df.empty or three_month_df.empty:
            print("警告：無法獲取公債殖利率資料，將跳過圖表產生。")
            if ten_year_df.empty:
                print("    - ^TNX 資料為空。")
            if three_month_df.empty:
                print("    - ^IRX 資料為空。")
            return None

        print("    - 正在繪製殖利率圖表...")
        plt.figure(figsize=(10, 2.25)) # 調整圖表高度
        plt.plot(ten_year_df.index, ten_year_df['Close'], label='10-Year Treasury Yield (^TNX)', color='blue', linewidth=1.0)
        plt.plot(three_month_df.index, three_month_df['Close'], label='3-Month Treasury Yield (^IRX)', color='red', linewidth=1.0)
        
        plt.title('US Treasury Yield Curve (10Y vs 3M)', fontsize=14)
        plt.ylabel('Yield (%)', fontsize=10)
        plt.legend(fontsize=9, loc='upper left')
        plt.grid(True, which='both', linestyle='--', linewidth=0.4)
        plt.xticks(rotation=30, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        plt.tight_layout(pad=0.5)
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close()
        print("    - 殖利率圖表繪製完畢。")
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"產生殖利率圖表時發生錯誤: {e}")
        return None

def generate_html_report(report_data, date_str, yield_curve_plot_b64=None):
    """生成最終的HTML報告"""
    tables_html = ""
    plots_html = ""

    for group_data in report_data:
        tables_html += f"<h2>{group_data['title']}</h2>"
        if group_data['description']:
            tables_html += f"<p>{group_data['description']}</p>"
        tables_html += group_data['table_html']
        
        plots_html += f"<h2>{group_data['title']} - K線圖</h2>" # Add a title for the plots section of each group
        plots_html += '<div class="plots-grid">'
        for symbol, b64_plot in group_data['plots'].items():
            plots_html += f'''
            <div class="plot-container">
                <h3>{symbol}</h3>
                <img src="data:image/png;base64,{b64_plot}" alt="{symbol} Plot">
            </div>
            '''
        plots_html += '</div>'

    content_html = tables_html + plots_html

    if yield_curve_plot_b64:
        print("  - 正在將殖利率圖表加入HTML報告...")
        content_html += f'''
        <h2>美國長短期國庫券殖利率 (10年)</h2>
        <div class="yield-plot-container">
             <img src="data:image/png;base64,{yield_curve_plot_b64}" alt="Yield Curve Plot">
        </div>
        '''
        print("  - 殖利率圖表已成功加入HTML。")

    html_template = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>綜合技術分析報告</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 15px; background-color: #f9f9f9; color: #333; }}
            h1 {{ text-align: center; color: #1a237e; margin-bottom: 15px; font-size: 24px; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 3px; margin-top: 25px; margin-bottom: 10px; font-size: 18px; }}
            h3 {{ text-align: center; color: #444; margin: 5px 0; font-size: 14px; font-weight: bold; }}
            p {{ color: #555; font-size: 13px; margin-top: 0; margin-bottom: 10px; }}
            table {{ font-size: 13px; border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ padding: 4px 6px; text-align: center; border: 1px solid #ddd; }}
            th {{ background-color: #e8eaf6; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f7f7f7; }}
            .plots-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 15px; margin-top: 20px; }}
            .plot-container {{ border: 1px solid #ddd; border-radius: 6px; padding: 10px; background-color: #fff; page-break-inside: avoid; }}
            .yield-plot-container {{ border: 1px solid #ddd; border-radius: 6px; padding: 10px; background-color: #fff; margin-top: 20px; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <h1>綜合技術分析報告 - {date_str}</h1>
        {content_html}
    <div id="text-analysis-report"></div>
    </body>
    </html>
    """
    filename = f"etf_tech_analysis_{date_str.replace('-', '')}.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"報告已成功生成：{os.path.abspath(filename)}")
    except IOError as e:
        print(f"寫入檔案時發生錯誤: {e}")

# --- 主程式 ---
def main():
    """主執行函式"""
    utc_now = datetime.datetime.utcnow()
    start_date = utc_now - datetime.timedelta(days=250)
    current_date_str = utc_now.astimezone(TZ).strftime('%Y-%m-%d')
    
    report_data = []
    table_columns = ["代碼", "價格", "漲跌%", "成交量%", "K9", "D9", "BIAS5", "BIAS20", "BIAS60", "ADX", "+DI", "-DI"]

    for group in STOCK_GROUPS:
        print(f"--- 正在處理群組: {group['title']} ---")
        stock_data = get_stock_data(group["symbols"], start_date, utc_now)
        
        if not stock_data:
            print(f"群組 {group['title']} 沒有可處理的資料。")
            continue

        table_rows = []
        plots = {}
        for symbol, df in stock_data.items():
            print(f"  - 計算指標: {symbol}")
            df_indicators = calculate_all_indicators(df)
            
            if df_indicators.empty or len(df_indicators) < 2:
                print(f"  - 跳過 {symbol}，指標計算後資料不足。")
                continue

            latest = df_indicators.iloc[-1]
            prev = df_indicators.iloc[-2]
            table_rows.append(format_data_row(symbol, latest, prev))
            
            print(f"  - 產生圖表: {symbol}")
            plots[symbol] = create_ma_plot_base64(df_indicators.tail(120), symbol)

        if not table_rows:
            continue
        
        df_result = pd.DataFrame(table_rows, columns=table_columns)
        
        report_data.append({
            "title": group['title'],
            "description": group['description'],
            "table_html": df_result.to_html(index=False, escape=False, justify="center"),
            "plots": plots
        })

    yield_curve_plot = create_yield_curve_plot_base64()

    if report_data:
        generate_html_report(report_data, current_date_str, yield_curve_plot)
    else:
        print("沒有任何資料可生成報告。")

if __name__ == "__main__":
    main()
