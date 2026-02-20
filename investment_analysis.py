import yfinance as yf
import pandas as pd
import datetime
import pytz
import warnings
import os
import base64
import shutil
from io import BytesIO
import matplotlib.pyplot as plt
import mplfinance as mpf
import json
import sys
from jinja2 import Environment, FileSystemLoader

# --- 全域設定 ---
warnings.filterwarnings("ignore")
TZ = pytz.timezone('Asia/Taipei')
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "report_template.html"

# --- 讀取設定檔 ---
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        STOCK_GROUPS = config.get("stock_groups", [])
        KEY_INDICATORS = config.get("key_indicators", [])
        SYMBOL_NAME_MAP = config.get("symbol_name_map", {})
        INVERSE_SYMBOLS = config.get("inverse_symbols", ["^VIX"])
        PARAMS = config.get("parameters", {})
        
        # 提取參數並提供預設值
        KD_WINDOW = PARAMS.get("kd_window", 9)
        BIAS_PERIODS = PARAMS.get("bias_periods", [5, 20, 60])
        DMI_WINDOW = PARAMS.get("dmi_window", 14)
        RSI_WINDOW = PARAMS.get("rsi_window", 14)
        MA_PERIODS = PARAMS.get("ma_periods", [5, 20, 60])
        VOL_MA_WINDOW = PARAMS.get("volume_ma_window", 20)
        HISTORY_DAYS = PARAMS.get("history_days", 250)
        PLOT_DAYS = PARAMS.get("plot_days", 120)
        AI_ANALYSIS_DAYS = PARAMS.get("ai_analysis_days", 60)
        
        TREND_PARAMS = PARAMS.get("trend_thresholds", {"bias_signal_period": 20, "bias_threshold": 0})
        COLOR_THRESHOLDS = PARAMS.get("color_thresholds", {})

except FileNotFoundError:
    print(f"[Error] 錯誤：找不到設定檔 {CONFIG_FILE}。")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"[Error] 錯誤：設定檔 {CONFIG_FILE} 格式不正確。")
    sys.exit(1)
except Exception as e:
    print(f"[Error] 讀取設定檔時發生未預期的錯誤: {e}")
    sys.exit(1)

# --- 資料獲取 ---
def get_stock_data(symbols, start_date, end_date):
    """抓取多支股票的資料"""
    data = {}
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                print(f"[Warning] 警告：無法獲取 {symbol} 的有效資料，將跳過。")
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            df = df[~df.index.duplicated(keep='first')]
            data[symbol] = df
        except Exception as e:
            print(f"[Error] 抓取 {symbol} 資料時發生錯誤: {e}")
    return data

def get_fundamental_data(symbol):
    """抓取個股基本面資料"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        data = {
            "symbol": symbol,
            "name": SYMBOL_NAME_MAP.get(symbol, symbol),
            "pe_trailing": info.get('trailingPE'),
            "pe_forward": info.get('forwardPE'),
            "pb_ratio": info.get('priceToBook'),
            "peg_ratio": info.get('pegRatio'),
            "roe": info.get('returnOnEquity'),
            "gross_margin": info.get('grossMargins'),
            "operating_margin": info.get('operatingMargins'),
            "dividend_yield": info.get('dividendYield'),
            "payout_ratio": info.get('payoutRatio'),
            "free_cashflow": info.get('freeCashflow'),
            "debt_to_equity": info.get('debtToEquity'),
            "sector": info.get('sector'),
            "industry": info.get('industry')
        }
        return data
    except Exception as e:
        print(f"[Warning] 無法獲取 {symbol} 的基本面資料: {e}")
        return None

# --- 技術指標計算 ---
def calculate_all_indicators(df):
    """計算所有需要的技術指標"""
    df = df.copy()
    
    # KD 計算
    low_min = df['Low'].rolling(window=KD_WINDOW, min_periods=1).min()
    high_max = df['High'].rolling(window=KD_WINDOW, min_periods=1).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    
    # RSI 計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=RSI_WINDOW).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_WINDOW).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD 計算
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    
    # 乖離率 (BIAS)
    for period in BIAS_PERIODS:
        ma = df['Close'].rolling(window=period).mean()
        df[f'BIAS_{period}'] = ((df['Close'] - ma) / ma) * 100
        
    # DMI 指標
    df['+DM'] = df['High'].diff().clip(lower=0)
    df['-DM'] = -df['Low'].diff().clip(upper=0)
    tr = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['TR'] = tr.rolling(window=DMI_WINDOW).sum()
    df['+DI'] = 100 * (df['+DM'].rolling(window=DMI_WINDOW).sum() / df['TR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=DMI_WINDOW).sum() / df['TR'])
    dx = abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = (dx * 100).rolling(window=DMI_WINDOW).mean()

    # 量價相關
    df['Change %'] = df['Close'].pct_change() * 100
    df['Volume Change %'] = (df['Volume'] / df['Volume'].rolling(window=VOL_MA_WINDOW).mean() * 100).fillna(0)
    
    # 均線
    for ma_period in MA_PERIODS:
        df[f'{ma_period}MA'] = df['Close'].rolling(window=ma_period).mean()
    
    return df

# --- HTML 樣式與輔助函式 ---

def determine_trend(k, d, bias_signal_val):
    """簡易趨勢判斷"""
    signal, style_class = "資料不足", "neutral"
    if k is None or d is None or bias_signal_val is None:
        return signal, style_class

    threshold = TREND_PARAMS.get("bias_threshold", 0)
    if k > d and bias_signal_val > threshold:
        signal, style_class = "多頭排列", "bullish-strong"
    elif k > d and bias_signal_val < threshold:
        signal, style_class = "反彈", "bullish-weak"
    elif k < d and bias_signal_val < threshold:
        signal, style_class = "空頭修正", "bearish-strong"
    elif k < d and bias_signal_val > threshold:
        signal, style_class = "回檔整理", "bearish-weak"
        
    return signal, style_class

def get_color_class(value, high=0, low=0, inverse=False):
    """返回 CSS class"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if not inverse:
        if value > high: return "text-up"
        if value < low: return "text-down"
    else:
        if value > high: return "text-down"
        if value < low: return "text-up"
    return ""

def format_data_row(symbol, latest, prev):
    """格式化單行 HTML 表格資料"""
    def get_scalar(data, key):
        val = data.get(key)
        if isinstance(val, pd.Series): val = val.iloc[0]
        return val if pd.notna(val) else None

    def fmt_num(val, fmt="{:.1f}", fallback="N/A"):
        return fmt.format(val) if val is not None else fallback

    change_pct = get_scalar(latest, "Change %")
    close = get_scalar(latest, "Close")
    vol_change = get_scalar(latest, "Volume Change %")
    k, d = get_scalar(latest, "K"), get_scalar(latest, "D")
    
    bias_signal_period = TREND_PARAMS.get("bias_signal_period", 20)
    bias_signal_val = get_scalar(latest, f"BIAS_{bias_signal_period}")
    trend_signal, trend_class = determine_trend(k, d, bias_signal_val)
    
    is_inverse = symbol in INVERSE_SYMBOLS or any(inv in symbol for inv in ["VIX", "Inverse", "Short"])
    display_name = SYMBOL_NAME_MAP.get(symbol, symbol)
    symbol_html = f"<div>{display_name}</div><div style='font-size: 11px; color: #888;'>{symbol}</div>"

    ct = COLOR_THRESHOLDS
    def make_td(val, high, low, inv=False, fmt="{:.1f}"):
        cls = get_color_class(val, high, low, inv)
        return f'<td class="number-cell {cls}">{fmt_num(val, fmt)}</td>'

    rows = f"""
    <tr>
      <td class="symbol-cell">{symbol_html}</td>
      <td class="number-cell {get_color_class(change_pct, 0, 0, is_inverse)}"><strong>{fmt_num(close, "{:,.2f}")}</strong></td>
      <td class="number-cell {get_color_class(change_pct, 0, 0, is_inverse)}">{fmt_num(change_pct, "{:+.2f}%")}</td>
      <td class="trend-cell"><span class="badge {trend_class}">{trend_signal}</span></td>
      {make_td(vol_change, ct.get("vol_high", 100), ct.get("vol_low", 50))}
      {make_td(k, ct.get("kd_high", 80), ct.get("kd_low", 20))}
      {make_td(d, ct.get("kd_high", 80), ct.get("kd_low", 20))}
    """
    for period in BIAS_PERIODS:
        val = get_scalar(latest, f"BIAS_{period}")
        rows += make_td(val, ct.get(f"bias{period}_high", 0), ct.get(f"bias{period}_low", 0))
        
    adx, plus_di, minus_di = get_scalar(latest, "ADX"), get_scalar(latest, "+DI"), get_scalar(latest, "-DI")
    rows += make_td(adx, ct.get("adx_high", 25), 0)
    rows += make_td(plus_di, minus_di if minus_di is not None else 0, float("-inf"))
    rows += make_td(minus_di, plus_di if plus_di is not None else 0, float("-inf"))
    rows += "</tr>"
    return rows

def create_ma_plot_base64(df, symbol, title=None):
    """建立K線圖(含MA與成交量)並返回Base64字串"""
    mc = mpf.make_marketcolors(up='#e53935', down='#43a047', edge='inherit', wick='inherit', volume='in', inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, gridstyle=':', gridcolor='#e0e0e0', facecolor='white')
    buf = BytesIO()
    try:
        mpf.plot(df, type='candle', mav=tuple(MA_PERIODS), volume=True, style=s, figsize=(10, 6), 
                 savefig=dict(fname=buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100),
                 ylabel='', ylabel_lower='', xrotation=0, datetime_format='%m-%d', tight_layout=True, panel_ratios=(4,1))
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        print(f"[Error] 繪製 {symbol} K線圖時發生錯誤: {e}"); return None

def create_yield_curve_plot_base64():
    """建立美國公債殖利率曲線圖並返回Base64字串及最新數據"""
    print("  - 正在產生美國公債殖利率圖表...")
    yield_data = {}
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=5*365)
        t_3m = yf.download("^IRX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        t_10y = yf.download("^TNX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        t_30y = yf.download("^TYX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        if t_3m.empty or t_10y.empty or t_30y.empty: return None, {}
        yield_data = {'3M': float(t_3m['Close'].iloc[-1]), '10Y': float(t_10y['Close'].iloc[-1]), '30Y': float(t_30y['Close'].iloc[-1])}
        plt.style.use('bmh'); plt.figure(figsize=(12, 6))
        plt.plot(t_3m.index, t_3m['Close'], label='3-Month (^IRX)', color='#e53935', linewidth=1.2, alpha=0.8)
        plt.plot(t_10y.index, t_10y['Close'], label='10-Year (^TNX)', color='#1976d2', linewidth=1.5)
        plt.plot(t_30y.index, t_30y['Close'], label='30-Year (^TYX)', color='#8e24aa', linewidth=1.5)
        plt.ylabel('Yield (%)'); plt.legend(loc='upper left', frameon=True, facecolor='white'); plt.grid(True, linestyle='--', alpha=0.7)
        buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=100); plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8'), yield_data
    except Exception as e:
        print(f"[Error] 產生殖利率圖表時發生錯誤: {e}"); return None, {}

def generate_html_report(report_data, date_str, summary_html, yield_curve_plot_b64=None, fundamental_data=None, yield_data=None, market_data=None):
    """使用 Jinja2 生成 HTML 報告"""
    fundamental_json = json.dumps(fundamental_data, ensure_ascii=False, indent=2) if fundamental_data else "{}"
    yield_json = json.dumps(yield_data, ensure_ascii=False, indent=2) if yield_data else "{}"
    market_json = json.dumps(market_data, ensure_ascii=False, indent=0) if market_data else "{}"
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    try:
        template = env.get_template(TEMPLATE_FILE)
        render_vars = {
            "date_str": date_str, "summary_html": summary_html, "report_data": report_data,
            "kd_window": KD_WINDOW, "bias_periods": BIAS_PERIODS, "fundamental_json": fundamental_json,
            "yield_json": yield_json, "market_json": market_json, "yield_curve_plot_b64": yield_curve_plot_b64, "yield_data": yield_data
        }
        html_output = template.render(**render_vars)
        filename = f"report/invest_analysis_{date_str.replace('-', '')}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f: f.write(html_output)
        
        # 複製一份為 index.html 至根目錄，以便 GitHub Pages 發佈
        root_index_filename = "index.html"
        shutil.copy2(filename, root_index_filename)
        
        # 同時保留 report/index.html 
        report_index_filename = os.path.join(os.path.dirname(filename), "index.html")
        shutil.copy2(filename, report_index_filename)
        
        print(f"[Success] 報告已成功生成：{os.path.abspath(filename)}")
        print(f"[Info] 已同步更新最新報告至根目錄：{os.path.abspath(root_index_filename)}")
    except Exception as e: print(f"[Error] 生成 HTML 報告時發生錯誤: {e}")

def process_stock_group(group, start_date, utc_now):
    """處理單個股票群組"""
    stock_data = get_stock_data(group["symbols"], start_date, utc_now)
    if not stock_data: return None
    
    # 獲取最後交易日 (取群組內第一個標的為準)
    first_symbol = group["symbols"][0]
    last_trading_date = "N/A"
    is_closed = False
    
    if first_symbol in stock_data:
        last_dt = stock_data[first_symbol].index[-1]
        last_trading_date = last_dt.strftime('%Y-%m-%d')
        
        # 判斷是否為休市 (簡單邏輯：若最後交易日早於 utc_now 的當天日期，且當天是週一至週五)
        current_date = utc_now.astimezone(TZ).date()
        if last_dt.date() < current_date and current_date.weekday() < 5:
            is_closed = True

    group_res = {
        "title": group['title'], 
        "section_id": "", 
        "table_rows": "", 
        "plots": {},
        "last_trading_date": last_trading_date,
        "is_closed": is_closed
    }
    if "美股" in group['title']: group_res["section_id"] = "us-stocks"
    elif "台股" in group['title']: group_res["section_id"] = "tw-stocks"
    elif "債券" in group['title']: group_res["section_id"] = "bonds"
    else: group_res["section_id"] = f"group-{abs(hash(group['title']))}"
    summary_items, market_data, fundamental_data = [], {}, []
    for symbol, df in stock_data.items():
        print(f"  - 分析: {symbol}")
        df_indicators = calculate_all_indicators(df)
        if df_indicators.empty or len(df_indicators) < 2: continue
        latest, prev = df_indicators.iloc[-1], df_indicators.iloc[-2]
        group_res["table_rows"] += format_data_row(symbol, latest, prev)
        display_name = SYMBOL_NAME_MAP.get(symbol, symbol)
        group_res["plots"][display_name] = create_ma_plot_base64(df_indicators.tail(PLOT_DAYS), symbol, display_name)
        if symbol in KEY_INDICATORS: summary_items.append({'symbol': display_name, 'close': latest['Close'], 'change': latest['Change %'], 'orig_symbol': symbol})
        recent_df = df_indicators.tail(AI_ANALYSIS_DAYS).copy().reset_index()
        recent_df['Date'] = recent_df['Date'].dt.strftime('%Y-%m-%d')
        cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'MACD', 'MACD_Hist'] + [f'{p}MA' for p in MA_PERIODS] + ['K', 'D']
        market_data[display_name] = recent_df[[c for c in cols if c in recent_df.columns]].to_dict(orient='records')
        if not symbol.startswith('^'):
            f_data = get_fundamental_data(symbol)
            if f_data: fundamental_data.append(f_data)
    return group_res, summary_items, market_data, fundamental_data

def main():
    """主執行函式"""
    utc_now = datetime.datetime.utcnow()
    start_date = utc_now - datetime.timedelta(days=HISTORY_DAYS)
    current_date_str = utc_now.astimezone(TZ).strftime('%Y-%m-%d')
    all_report_data, all_summary_items, all_fundamental_data, all_market_data = [], [], [], {}
    print(f"[Info] 開始執行分析工作... ({current_date_str})")
    for group in STOCK_GROUPS:
        print(f"\n--- 正在處理群組: {group['title']} ---")
        res = process_stock_group(group, start_date, utc_now)
        if res:
            g_res, s_items, m_data, f_data = res
            all_report_data.append(g_res); all_summary_items.extend(s_items)
            all_market_data.update(m_data); all_fundamental_data.extend(f_data)
    summary_html = ""
    for key in KEY_INDICATORS:
        item = next((i for i in all_summary_items if i['orig_symbol'] == key), None)
        if item:
            is_inv = item['orig_symbol'] in INVERSE_SYMBOLS or any(x in item['orig_symbol'] for x in ["VIX", "Inverse", "Short"])
            cls = get_color_class(item['change'], 0, 0, inverse=is_inv)
            icon = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "-"
            summary_html += f'<div class="summary-card"><div class="summary-title">{item["symbol"]}</div><div class="summary-price">{item["close"]:.2f}</div><div class="summary-change {cls}">{icon} {item["change"]:.2f}%</div></div>'
    yield_plot, yield_data = create_yield_curve_plot_base64()
    if all_report_data: generate_html_report(all_report_data, current_date_str, summary_html, yield_plot, all_fundamental_data, yield_data, all_market_data)
    else: print("[Error] 沒有任何資料可生成報告。")

if __name__ == "__main__":
    main()
