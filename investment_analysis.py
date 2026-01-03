# @title
import yfinance as yf
import pandas as pd
import datetime
import pytz
import warnings
import os

# 忽略所有警告訊息
warnings.filterwarnings("ignore")

# 設定台灣時區
tz = pytz.timezone('Asia/Taipei')

# --- 設定股票群組 ---
STOCK_GROUPS = [
    {
        "title": "&lt;&lt;美股主要指數&gt;&gt;",
        "symbols": ["^VIX", "^GSPC", "^SOX", "^IXIC", "^DJI", "^NYFANG", "^N225", "^XAU"],
        "description": "VIX:恐慌指數, GSPC:標普, SOX:費半, IXIC:納斯達克, DJI:道瓊, NYFNAG:尖牙, N225:日經, XAU:黃金"
    },
    {
        "title": "&lt;&lt;台股ETF&gt;&gt;",
        "symbols": ["00770.TW", "00924.TW", "00757.TW", "006208.TW", "00631L.TW", "2330.TW", "00733.TW", "00661.TW"],
        "description": ""
    },
    {
        "title": "&lt;&lt;美債ETF&gt;&gt;",
        "symbols": ["HYG", "00937B.TWO", "00725B.TWO", "00679B.TWO", "00687B.TWO", "00719B.TWO"],
        "description": "00937B(群益BBB20Y)，00725B(國泰BBB10Y),00679B(元大美債20Y)，00687B(國泰美債20Y)，00719B(元大美債1-3Y)"
    }
]

# --- 資料獲取 ---
def get_stock_data(symbols, start_date, end_date):
    """抓取股票資料，並處理可能的錯誤"""
    data = {}
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty:
                print(f"警告：無法獲取 {symbol} 的資料，將跳過。")
                continue
            if len(df) < 2:
                print(f"警告：{symbol} 的資料不足以進行分析，將跳過。")
                continue
            data[symbol] = df
        except Exception as e:
            print(f"抓取 {symbol} 資料時發生錯誤: {e}")
    return data

# --- 技術指標計算 ---
def calculate_kd(df, n=9, k_period=3, d_period=3):
    low_min = df['Low'].rolling(window=n, min_periods=1).min()
    high_max = df['High'].rolling(window=n, min_periods=1).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=(k_period - 1), adjust=False).mean()
    df['D'] = df['K'].ewm(com=(d_period - 1), adjust=False).mean()
    return df

def calculate_bias(df, period):
    ma = df['Close'].rolling(window=period).mean()
    return ((df['Close'] - ma) / ma) * 100

def calculate_dmi(df, period=14):
    df['+DM'] = df['High'].diff().clip(lower=0)
    df['-DM'] = -df['Low'].diff().clip(upper=0)
    tr = pd.concat([df['High'] - df['Low'],
                    abs(df['High'] - df['Close'].shift()),
                    abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['TR'] = tr.rolling(window=period).sum()
    df['+DI'] = 100 * (df['+DM'].rolling(window=period).sum() / df['TR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=period).sum() / df['TR'])
    dx = abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']) * 100
    df['ADX'] = dx.rolling(window=period).mean()
    return df

def calculate_indicators(df):
    """計算所有需要的技術指標"""
    df['Change %'] = df['Close'].pct_change() * 100
    df = calculate_kd(df, n=9)
    df['BIAS_5'] = calculate_bias(df, 5)
    df['BIAS_20'] = calculate_bias(df, 20)
    df['BIAS_60'] = calculate_bias(df, 60)
    df = calculate_dmi(df, period=14)
    df['Volume Change %'] = (df['Volume'] / df['Volume'].rolling(window=20).mean() * 100).fillna(0)
    return df

# --- HTML 格式化 ---
def arrow(value, previous_value):
    """返回增減箭頭符號"""
    return "▲" if value > previous_value else ("▼" if value < previous_value else "")

def determine_color(value, thresholds):
    """根據閾值確定顏色"""
    if value > thresholds.get('high', float('inf')):
        return "red"
    elif value < thresholds.get('low', float('-inf')):
        return "green"
    return "black"

def format_data_row(symbol, latest_data, previous_data):
    """格式化單行資料以用於HTML表格"""
    # 安全地提取數值
    def get_scalar(series, key):
        val = series.get(key, 0)
        return val.item() if isinstance(val, (pd.Series, pd.Index)) else val

    close_price = get_scalar(latest_data, 'Close')
    change_pct = get_scalar(latest_data, 'Change %')
    volume_change = get_scalar(latest_data, 'Volume Change %')
    k_value = get_scalar(latest_data, 'K')
    d_value = get_scalar(latest_data, 'D')
    bias_5 = get_scalar(latest_data, 'BIAS_5')
    bias_20 = get_scalar(latest_data, 'BIAS_20')
    bias_60 = get_scalar(latest_data, 'BIAS_60')
    adx = get_scalar(latest_data, 'ADX')
    plus_di = get_scalar(latest_data, '+DI')
    minus_di = get_scalar(latest_data, '-DI')

    # 返回格式化後的資料行
    return [
        symbol,
        f'<span style="color:{determine_color(change_pct, {"high": 0, "low": 0})}">{close_price:.2f}</span>',
        f'<span style="color:{determine_color(change_pct, {"high": 0, "low": 0})}">{change_pct:.2f}%</span>',
        f'<span style="color:{determine_color(volume_change, {"high": 99, "low": 50})}">{volume_change:.2f}%{arrow(volume_change, get_scalar(previous_data, "Volume Change %"))}</span>',
        f'<span style="color:{determine_color(k_value, {"high": 80, "low": 20})}">{k_value:.2f} {arrow(k_value, get_scalar(previous_data, "K"))}</span>',
        f'<span style="color:{determine_color(d_value, {"high": 80, "low": 20})}">{d_value:.2f} {arrow(d_value, get_scalar(previous_data, "D"))}</span>',
        f'<span style="color:{determine_color(bias_5, {"high": 4, "low": -4})}">{bias_5:.2f} {arrow(bias_5, get_scalar(previous_data, "BIAS_5"))}</span>',
        f'<span style="color:{determine_color(bias_20, {"high": 7, "low": -7})}">{bias_20:.2f} {arrow(bias_20, get_scalar(previous_data, "BIAS_20"))}</span>',
        f'<span style="color:{determine_color(bias_60, {"high": 20, "low": -20})}">{bias_60:.2f} {arrow(bias_60, get_scalar(previous_data, "BIAS_60"))}</span>',
        f'<span style="color:{determine_color(adx, {"high": 25, "low": 0})}">{adx:.2f} {arrow(adx, get_scalar(previous_data, "ADX"))}</span>',
        f'<span style="color:{determine_color(plus_di, {"high": minus_di})}">{plus_di:.2f} {arrow(plus_di, get_scalar(previous_data, "+DI"))}</span>',
        f'<span style="color:{determine_color(minus_di, {"high": plus_di})}">{minus_di:.2f} {arrow(minus_di, get_scalar(previous_data, "-DI"))}</span>',
    ]

def generate_html_report(all_groups_html, date_str):
    """生成完整的HTML報告檔案"""
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ETF 技術指標分析</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 5px;}}
            p {{ color: #34495e; }}
            table {{ font-size: 13px; border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            th, td {{ padding: 4px 8px; text-align: center; line-height: 1.2; border: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>ETF 技術指標分析 - {date_str}</h1>
        {''.join(all_groups_html)}
    </body>
    </html>
    """
    filename = f"etf_analysis_{date_str.replace('-', '')}.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"報告已成功生成：{os.path.abspath(filename)}")
    except IOError as e:
        print(f"寫入檔案時發生錯誤: {e}")

# --- 主程式 ---
def main():
    """主執行函式"""
    utc_now = datetime.datetime.utcnow()
    start_date = utc_now - datetime.timedelta(days=100)
    current_date_str = utc_now.astimezone(tz).strftime('%Y-%m-%d')

    all_groups_html = []
    columns = ["Code", "Price", "Pri(%)", "Vol(%)", "K9", "D9", "BIAS5", "BIAS20", "BIAS60", "ADX", "+DI", "-DI"]

    for group in STOCK_GROUPS:
        print(f"--- 正在處理: {group['title']} ---")
        stock_data = get_stock_data(group["symbols"], start_date, utc_now)
        
        if not stock_data:
            print(f"群組 {group['title']} 沒有可處理的資料。")
            continue

        data_rows = []
        for symbol, df in stock_data.items():
            df_indicators = calculate_indicators(df)
            latest_data = df_indicators.iloc[-1]
            previous_data = df_indicators.iloc[-2]
            data_rows.append(format_data_row(symbol, latest_data, previous_data))

        if not data_rows:
            continue

        df_result = pd.DataFrame(data_rows, columns=columns)
        html_table = df_result.to_html(index=False, escape=False, justify="center")
        
        group_html = f"<h2>{group['title']}</h2>"
        if group['description']:
            group_html += f"<p>{group['description']}</p>"
        group_html += html_table
        all_groups_html.append(group_html)

    if all_groups_html:
        generate_html_report(all_groups_html, current_date_str)
    else:
        print("沒有任何資料可生成報告。")

if __name__ == "__main__":
    main()