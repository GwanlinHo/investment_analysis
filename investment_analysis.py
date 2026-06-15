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
import requests

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
except Exception as e:
    print(f"[Error] 讀取設定檔失敗: {e}"); sys.exit(1)

# --- 資料獲取 ---
def get_stock_data(symbols, start_date):
    """回傳 (data, failed)：data 為成功取得的 {symbol: df}，failed 為 yfinance 與
    FinMind 皆無法取得的標的清單 (供上層做資料完整性把關)。"""
    data, failed = {}, []
    for symbol in symbols:
        df = None
        try:
            df = yf.download(symbol, start=start_date, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                df = None
            else:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
                df = df[~df.index.duplicated(keep='first')]
                # 台股標的：以 FinMind 補 Yahoo 回補延遲所缺的最新交易日 (美股標的不受影響)
                df = fill_latest_from_finmind(symbol, df, start_date)
        except Exception as e:
            print(f"[Error] {symbol} yfinance 抓取失敗: {e}"); df = None
        # yfinance 完全失敗時，台股標的改用 FinMind 全量抓取作為備援
        if df is None:
            fid = _to_finmind_id(symbol)
            if fid is not None:
                try:
                    fm = _fetch_finmind_df(fid, start_date)
                    if fm is not None and len(fm) >= 2:
                        print(f"    [FinMind] {symbol} yfinance 失敗，改用 FinMind 全量抓取 ({len(fm)} 筆)")
                        df = fm
                except Exception as e:
                    print(f"    [FinMind] {symbol} 全量抓取失敗: {e}")
        if df is not None and not df.empty:
            data[symbol] = df
        else:
            failed.append(symbol)
            print(f"[Missing] {symbol} yfinance 與 FinMind 皆無法取得資料")
    return data, failed

def _to_finmind_id(symbol):
    """將 Yahoo 代號轉為 FinMind data_id；非台股標的回傳 None。"""
    if symbol == "^TWII": return "TAIEX"
    if symbol.endswith(".TWO"): return symbol[:-4]
    if symbol.endswith(".TW"): return symbol[:-3]
    return None

def _fetch_finmind_df(fid, start_date):
    """抓 FinMind TaiwanStockPrice，回傳標準 OHLCV DataFrame (DatetimeIndex)；失敗或無資料回 None。"""
    params = {"dataset": "TaiwanStockPrice", "data_id": fid, "start_date": start_date.strftime('%Y-%m-%d')}
    resp = requests.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=15)
    if resp.status_code != 200: return None
    data = resp.json().get("data", [])
    if not data: return None
    fm = pd.DataFrame(data)
    fm['date'] = pd.to_datetime(fm['date'])
    fm = fm.set_index('date').sort_index().rename(
        columns={'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'})
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    fm = fm[[c for c in cols if c in fm.columns]]
    return fm if not fm.empty else None

def fill_latest_from_finmind(symbol, df, start_date):
    """以 FinMind 補 Yahoo 對台股回補延遲所缺的最新交易日資料。

    Yahoo 對台股 ETF/指數的當日收盤常延遲跨日回補 (Close 為 NaN)，導致報表呈現
    前一交易日的過期數據。FinMind (本土源) 對台股 ETF、指數的當日收盤齊全且與
    Yahoo 指數值一致，故用其原始 OHLC 補上 Yahoo 缺漏的列。

    補值僅作用於「Yahoo 缺漏的日期」(該日不存在或 Close 為 NaN)，不覆蓋既有有效值；
    且 auto_adjust 還原價在近期 ≈ 原始價 (落差為 0)，補在序列尾端口徑一致，漲跌幅與
    技術指標皆正確。FinMind 取得失敗時原樣返回，由表頭基準日與逐列標註機制防呆。
    """
    fid = _to_finmind_id(symbol)
    if fid is None: return df
    try:
        fm = _fetch_finmind_df(fid, start_date)
        if fm is None: return df
        filled = 0
        for dt, row in fm.iterrows():
            if dt not in df.index or pd.isna(df.loc[dt].get('Close')):
                for c in fm.columns: df.loc[dt, c] = row[c]
                filled += 1
        if filled: print(f"    [FinMind] {symbol} 補入 {filled} 個交易日 (Yahoo 缺漏)")
        return df.sort_index()
    except Exception as e:
        print(f"    [FinMind] {symbol} 補值略過: {e}")
        return df

def fetch_tw_institutional_data(symbol, start_date):
    clean_symbol = symbol.split('.')[0]
    if not clean_symbol.isdigit(): return None
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": clean_symbol, "start_date": start_date.strftime('%Y-%m-%d')}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            if not data: return None
            df_inst = pd.DataFrame(data)
            df_inst['date'] = pd.to_datetime(df_inst['date'])
            df_inst['buy_sell'] = df_inst['buy'] - df_inst['sell']
            return df_inst.pivot_table(index='date', columns='name', values='buy_sell', aggfunc='sum').fillna(0)
    except: return None
    return None

def get_fundamental_data(symbol):
    try:
        ticker = yf.Ticker(symbol); info = ticker.info
        return {
            "symbol": symbol, "name": SYMBOL_NAME_MAP.get(symbol, symbol),
            "short_percent": info.get('shortPercentOfFloat'), "short_ratio": info.get('shortRatio')
        }
    except: return None

# --- 技術指標計算 ---
def calculate_all_indicators(df):
    df = df.copy()
    low_min = df['Low'].rolling(window=KD_WINDOW).min(); high_max = df['High'].rolling(window=KD_WINDOW).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean(); df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    delta = df['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=RSI_WINDOW).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_WINDOW).mean(); df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean(); exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2; df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean(); df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    for period in BIAS_PERIODS:
        ma = df['Close'].rolling(window=period).mean(); df[f'BIAS_{period}'] = ((df['Close'] - ma) / ma) * 100
    df['+DM'] = df['High'].diff().clip(lower=0); df['-DM'] = -df['Low'].diff().clip(upper=0)
    tr = pd.concat([df['High'] - df['Low'], abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['TR'] = tr.rolling(window=DMI_WINDOW).sum()
    df['+DI'] = 100 * (df['+DM'].rolling(window=DMI_WINDOW).sum() / df['TR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=DMI_WINDOW).sum() / df['TR'])
    dx = abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']); df['ADX'] = (dx * 100).rolling(window=DMI_WINDOW).mean()
    df['Change %'] = df['Close'].pct_change() * 100
    df['Volume Change %'] = (df['Volume'] / df['Volume'].rolling(window=VOL_MA_WINDOW).mean() * 100).fillna(0)
    for ma_period in MA_PERIODS: df[f'{ma_period}MA'] = df['Close'].rolling(window=ma_period).mean()
    return df

# --- 輔助函式 ---
def get_color_class(value, high=0, low=0, inverse=False):
    if value is None or (isinstance(value, float) and pd.isna(value)): return ""
    if not inverse:
        if value > high: return "text-up"; 
        if value < low: return "text-down"
    else:
        if value > high: return "text-down"; 
        if value < low: return "text-up"
    return ""

def format_na_row(symbol, show_chips=True, show_vol=True):
    """缺失標的的佔位列：保留標的名稱，所有數值欄位顯示 n/a，明確標示為 API 無資料，
    讓使用者一眼辨識某次數據異常是資料源取不到，而非真實數值。欄位順序須與 format_data_row 一致。"""
    sym_html = (f"<div>{SYMBOL_NAME_MAP.get(symbol, symbol)}</div>"
                f"<div style='font-size: 11px; color: #888;'>{symbol}</div>"
                f"<div style='font-size: 10px; color: #e74c3c;'>[!] API 無資料</div>")
    na = "<td class='number-cell'>n/a</td>"
    row = f"<tr><td class='symbol-cell'>{sym_html}</td>"
    row += na + na + "<td class='trend-cell'>n/a</td>"   # 收盤、漲跌%、訊號
    if show_vol: row += na                               # 量比
    if show_chips: row += na + na                        # 籌碼/空單兩欄
    row += na + na                                       # K、D
    for _ in BIAS_PERIODS: row += na                     # 各期乖離率
    row += na + na + na                                  # ADX、+DI、-DI
    row += "</tr>"
    return row

def format_data_row(symbol, latest, prev, inst_df=None, fund_data=None, show_chips=True, show_vol=True, ref_date=None):
    def get_scalar(data, key): val = data.get(key); return val if pd.notna(val) else None
    def fmt_num(val, fmt="{:.1f}", fallback="-"): return fmt.format(val) if val is not None else fallback
    change_pct = get_scalar(latest, "Change %"); close = get_scalar(latest, "Close"); vol_change = get_scalar(latest, "Volume Change %")
    k, d = get_scalar(latest, "K"), get_scalar(latest, "D"); bias_val = get_scalar(latest, f"BIAS_{TREND_PARAMS.get('bias_signal_period', 20)}")
    signal, style = "資料不足", "neutral"; th = TREND_PARAMS.get("bias_threshold", 0)
    if k and d and bias_val is not None:
        if k > d and bias_val > th: signal, style = "多頭排列", "bullish-strong"
        elif k > d and bias_val < th: signal, style = "反彈", "bullish-weak"
        elif k < d and bias_val < th: signal, style = "空頭修正", "bearish-strong"
        elif k < d and bias_val > th: signal, style = "回檔整理", "bearish-weak"
    is_inverse = symbol in INVERSE_SYMBOLS or any(inv in symbol for inv in ["VIX", "Inverse", "Short"])
    # 若該標的的實際數據日與群組基準交易日不一致 (例如尾端 NaN 導致退回前一交易日)，
    # 明確標註該列真正反映的資料日期，避免靜默呈現過期數據而誤導。
    date_note = ""
    row_date = getattr(latest, 'name', None)
    if ref_date is not None and row_date is not None:
        try:
            if row_date.normalize() != ref_date.normalize():
                date_note = f"<div style='font-size: 10px; color: #e67e22;'>[!] 資料 {row_date.strftime('%m/%d')}</div>"
        except Exception: pass
    sym_html = f"<div>{SYMBOL_NAME_MAP.get(symbol, symbol)}</div><div style='font-size: 11px; color: #888;'>{symbol}</div>{date_note}"
    ct = COLOR_THRESHOLDS
    row = f"<tr><td class='symbol-cell'>{sym_html}</td>"
    row += f"<td class='number-cell {get_color_class(change_pct, 0, 0, is_inverse)}'><strong>{fmt_num(close, '{:,.2f}')}</strong></td>"
    row += f"<td class='number-cell {get_color_class(change_pct, 0, 0, is_inverse)}'>{fmt_num(change_pct, '{:+.2f}%')}</td>"
    row += f"<td class='trend-cell'><span class='badge {style}'>{signal}</span></td>"
    if show_vol: row += f"<td class='number-cell {get_color_class(vol_change, ct.get('vol_high', 100), ct.get('vol_low', 50))}'>{fmt_num(vol_change)}</td>"
    if show_chips:
        if inst_df is not None and not inst_df.empty:
            l_inst = inst_df.iloc[-1]
            row += f"<td class='number-cell'>{fmt_num(l_inst.get('Foreign_Investor', 0), '{:+,.0f}')}</td><td class='number-cell'>{fmt_num(l_inst.get('Investment_Trust', 0), '{:+,.0f}')}</td>"
        elif fund_data and fund_data.get('short_percent') is not None:
            row += f"<td class='number-cell {get_color_class(fund_data.get('short_percent')*100, 15, 5, True)}'>{fmt_num(fund_data.get('short_percent')*100, '{:.1f}%')}</td><td class='number-cell {get_color_class(fund_data.get('short_ratio'), 5, 2, True)}'>{fmt_num(fund_data.get('short_ratio'))}</td>"
        else: row += "<td>-</td><td>-</td>"
    row += f"<td class='number-cell {get_color_class(k, 80, 20)}'>{fmt_num(k)}</td><td class='number-cell {get_color_class(d, 80, 20)}'>{fmt_num(d)}</td>"
    for p in BIAS_PERIODS: row += f"<td class='number-cell {get_color_class(get_scalar(latest, f'BIAS_{p}'), ct.get(f'bias{p}_high', 0), ct.get(f'bias{p}_low', 0))}'>{fmt_num(get_scalar(latest, f'BIAS_{p}'))}</td>"
    adx, pdi, mdi = get_scalar(latest, "ADX"), get_scalar(latest, "+DI"), get_scalar(latest, "-DI")
    row += f"<td class='number-cell'>{fmt_num(adx)}</td><td class='number-cell {get_color_class(pdi, mdi if mdi else 0, -1)}'>{fmt_num(pdi)}</td><td class='number-cell {get_color_class(mdi, pdi if pdi else 0, -1)}'>{fmt_num(mdi)}</td>"
    row += "</tr>"
    return row

def create_ma_plot_base64(df, symbol, inst_df=None, show_extra=True):
    df = df.copy(); apds = []
    # 檢查是否真的有成交量資料，若無成交量則強制不顯示副圖
    if show_extra and df['Volume'].sum() > 0:
        vol_colors = ['#e53935' if c >= o else '#43a047' for c, o in zip(df['Close'], df['Open'])]
        apds.append(mpf.make_addplot(df['Volume'], type='bar', panel=1, color=vol_colors, ylabel='Vol', y_on_right=False))
        if inst_df is not None and not inst_df.empty:
            ia = inst_df.reindex(df.index).fillna(0)
            if 'Investment_Trust' in ia.columns: apds.append(mpf.make_addplot(ia['Investment_Trust'].cumsum(), panel=2, color='#e53935', width=1.5, ylabel='Flow'))
            if 'Foreign_Investor' in ia.columns: apds.append(mpf.make_addplot(ia['Foreign_Investor'].cumsum(), panel=2, color='#1976d2', width=1.0, alpha=0.8))
            dealer_cols = [c for c in ia.columns if 'Dealer' in c]
            if dealer_cols: apds.append(mpf.make_addplot(ia[dealer_cols].sum(axis=1).cumsum(), panel=2, color='#43a047', width=1.0, alpha=0.6))
        else:
            df['OBV'] = (df['Volume'] * (~df['Close'].diff().le(0) * 2 - 1)).cumsum()
            apds.append(mpf.make_addplot(df['OBV'], panel=2, color='#455a64', width=1.5, ylabel='OBV'))
    
    mc = mpf.make_marketcolors(up='#e53935', down='#43a047', edge='inherit', wick='inherit', volume='in', inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, gridstyle=':', gridcolor='#e0e0e0', facecolor='white')
    buf = BytesIO()
    try:
        kwargs = {'type': 'candle', 'mav': tuple(MA_PERIODS), 'volume': False, 'style': s, 'figsize': (10, 8 if apds else 6), 'ylabel': '', 'ylabel_lower': '', 'xrotation': 0, 'datetime_format': '%m-%d', 'tight_layout': True, 'savefig': dict(fname=buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100)}
        if apds: kwargs['addplot'] = apds; kwargs['panel_ratios'] = (5, 1, 1)
        mpf.plot(df, **kwargs)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except: return None

def create_yield_curve_plot_base64():
    try:
        end_date = datetime.datetime.now(); start_date = end_date - datetime.timedelta(days=5*365)
        t_3m = yf.download("^IRX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        t_10y = yf.download("^TNX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        t_30y = yf.download("^TYX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        if t_3m.empty or t_10y.empty or t_30y.empty: return None, {}
        yield_data = {'3M': float(t_3m['Close'].iloc[-1]), '10Y': float(t_10y['Close'].iloc[-1]), '30Y': float(t_30y['Close'].iloc[-1])}
        plt.style.use('bmh'); plt.figure(figsize=(12, 6)); plt.plot(t_3m.index, t_3m['Close'], label='3M', color='#e53935'); plt.plot(t_10y.index, t_10y['Close'], label='10Y', color='#1976d2'); plt.plot(t_30y.index, t_30y['Close'], label='30Y', color='#8e24aa'); plt.ylabel('Yield (%)'); plt.legend(); plt.grid(True)
        buf = BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=100); plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8'), yield_data
    except: return None, {}

def process_stock_group(group, start_date, utc_now):
    stock_data, failed = get_stock_data(group["symbols"], start_date)
    if not stock_data and not failed: return None
    
    # 群組基準交易日：取各標的「最後有效數據日」(排除尾端 NaN) 的最大值，代表本報告
    # 涵蓋到的最新交易日。關鍵在於必須以 dropna 後的有效日計算，而非含 NaN 的
    # df.index[-1]；尚未回補最新日的標的 (有效日落後者) 會在 format_data_row 逐列標註其
    # 實際資料日，避免靜默呈現過期數據而與表頭日期錯位。
    valid_last_dates = []
    for df in stock_data.values():
        dfv = df.dropna(subset=['Close']) if 'Close' in df.columns else df.dropna(how='all')
        if not dfv.empty: valid_last_dates.append(dfv.index[-1])
    ref_date_obj = max(valid_last_dates) if valid_last_dates else None
    last_date = ref_date_obj.strftime('%Y-%m-%d') if ref_date_obj else "N/A"
    
    is_closed = utc_now.replace(tzinfo=pytz.utc).astimezone(TZ).weekday() >= 5
    is_idx_group = "指數" in group['title'] or "債券" in group['title']
    ch1, ch2 = (None, None) if is_idx_group else ("籌碼1", "籌碼2")
    if not is_idx_group:
        if "美股" in group['title']: ch1, ch2 = "空單%", "補空天數"
        elif "台股" in group['title']: ch1, ch2 = "外資(張)", "投信(張)"
    g_res = {"title": group['title'], "section_id": group.get('section_id', f"s-{abs(hash(group['title']))}"), "table_rows": "", "plots": {}, "last_trading_date": last_date, "is_closed": is_closed, "chip_header_1": ch1, "chip_header_2": ch2, "show_vol": not is_idx_group}
    if "美股" in group['title']: g_res["section_id"] = "us-stocks"
    elif "台股" in group['title']: g_res["section_id"] = "tw-stocks"
    elif "債券" in group['title']: g_res["section_id"] = "bonds"
    summary, market, fundamental, missing = [], {}, [], []
    # 完全無法取得資料的標的 (yfinance 與 FinMind 皆失敗)：列為缺失並產生 n/a 佔位列
    for symbol in failed:
        missing.append(symbol)
        g_res["table_rows"] += format_na_row(symbol, show_chips=not is_idx_group, show_vol=not is_idx_group)
    for symbol, df in stock_data.items():
        print(f"  - 分析: {symbol}")
        df_ind = calculate_all_indicators(df)

        # 缺失判定採「絕對標準」，不可用「落後群組基準日」判定：週末/跨市場時段，群組內
        # 持續交易或時區領先的商品 (黃金期貨 GC=F、日經 ^N225) 會把群組 max 拉高，導致
        # 正常休市的股票指數被誤判缺失而誤觸發中止 (每週一早晨必中)。
        # 缺失 = 完全無有效收盤，或最新資料距執行日超過 STALE_DAYS 個日曆日 (長期停更，
        # 涵蓋一般週末與短連假)。僅落後群組基準但在期限內者不計缺失，由逐列日期標註誠實呈現。
        STALE_DAYS = 5
        df_valid = df_ind.dropna(subset=['Close'])
        run_date = utc_now.astimezone(TZ).date()
        is_stale = (not df_valid.empty) and (run_date - df_valid.index[-1].date()).days > STALE_DAYS
        if df_valid.empty or is_stale:
            missing.append(symbol)
            g_res["table_rows"] += format_na_row(symbol, show_chips=not is_idx_group, show_vol=not is_idx_group)
            continue
        latest = df_valid.iloc[-1]
        prev = df_valid.iloc[-2] if len(df_valid) > 1 else latest
        
        inst_df = fetch_tw_institutional_data(symbol, start_date) if (".TW" in symbol or ".TWO" in symbol) else None
        f_data = get_fundamental_data(symbol) if not symbol.startswith('^') else None
        if f_data: fundamental.append(f_data)
        # 表格顯示邏輯：指數群組不顯示量比與籌碼
        g_res["table_rows"] += format_data_row(symbol, latest, prev, inst_df, f_data, show_chips=not is_idx_group, show_vol=not is_idx_group, ref_date=ref_date_obj)
        disp_name = SYMBOL_NAME_MAP.get(symbol, symbol)
        # 圖表顯示邏輯：不論群組，只要標的有成交量就嘗試繪製副圖
        g_res["plots"][disp_name] = create_ma_plot_base64(df_ind.tail(PLOT_DAYS), symbol, inst_df, show_extra=True)
        if symbol in KEY_INDICATORS: summary.append({'symbol': disp_name, 'close': latest['Close'], 'change': latest['Change %'], 'orig_symbol': symbol})
        rd = df_ind.tail(AI_ANALYSIS_DAYS).copy().reset_index(); rd.rename(columns={rd.columns[0]: 'Date'}, inplace=True); rd['Date'] = rd['Date'].dt.strftime('%Y-%m-%d')
        market[disp_name] = rd.to_dict(orient='records')
        if inst_df is not None:
            ir = inst_df.reindex(df_ind.index).tail(AI_ANALYSIS_DAYS).reset_index(); ir.rename(columns={ir.columns[0]: 'date'}, inplace=True); ir['date'] = ir['date'].dt.strftime('%Y-%m-%d')
            market[disp_name + "_institutional"] = ir.to_dict(orient='records')
    return g_res, summary, market, fundamental, missing

def save_to_json(fundamental, yield_data, market, summary, filename="technical_data.json"):
    data = {
        "fundamental": fundamental,
        "yield": yield_data,
        "market": market,
        "summary": summary,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    utc_now = datetime.datetime.now(datetime.timezone.utc); start_date = utc_now - datetime.timedelta(days=HISTORY_DAYS)
    all_rep, all_sum, all_fun, all_mkt, all_missing = [], [], [], {}, []
    for group in STOCK_GROUPS:
        print(f"\n--- 正在處理群組: {group['title']} ---")
        res = process_stock_group(group, start_date, utc_now)
        if res: gr, si, md, fd, ms = res; all_rep.append(gr); all_sum.extend(si); all_mkt.update(md); all_fun.extend(fd); all_missing.extend(ms)
    # 資料完整性關卡：缺失標的達 3 個(含)以上 → 中止，不產生報告、不更新 technical_data.json，
    # 從源頭杜絕殘缺資料被後續工作流上傳；保留前一份完整報告。缺 0~2 個則於報表標示 n/a 後照常產生。
    if len(all_missing) >= 3:
        print(f"\n[ABORT] 資料完整性不足：{len(all_missing)} 個標的無法取得最近交易日資料"
              f" (yfinance 與 FinMind 皆失敗)：{all_missing}")
        print("[ABORT] 已取消本次報告產生與更新，保留前一份報告。請檢查資料源 API 狀態。")
        sys.exit(2)
    if all_missing:
        print(f"[WARN] {len(all_missing)} 個標的資料缺失，已於報表標示 n/a：{all_missing}")
    sum_html = ""
    for key in KEY_INDICATORS:
        item = next((i for i in all_sum if i['orig_symbol'] == key), None)
        if item:
            is_inv = item['orig_symbol'] in INVERSE_SYMBOLS or any(x in item['orig_symbol'] for x in ["VIX", "Inverse", "Short"])
            cls = get_color_class(item['change'], 0, 0, is_inv); icon = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "-"
            sum_html += f'<div class="summary-card"><div class="summary-title">{item["symbol"]}</div><div class="summary-price">{item["close"]:.2f}</div><div class="summary-change {cls}">{icon} {item["change"]:.2f}%</div></div>'
    y_plot, y_data = create_yield_curve_plot_base64()
    if all_rep:
        save_to_json(all_fun, y_data, all_mkt, all_sum)
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR)); tpl = env.get_template(TEMPLATE_FILE)
        html = tpl.render(
            date_str=utc_now.astimezone(TZ).strftime('%Y-%m-%d'), 
            summary_html=sum_html, 
            report_data=all_rep, 
            kd_window=KD_WINDOW, 
            bias_periods=BIAS_PERIODS, 
            yield_curve_plot_b64=y_plot, 
            yield_data=y_data,
            fundamental_json=all_fun,
            yield_json=y_data,
            market_json=all_mkt
        )
        os.makedirs("report", exist_ok=True); fname = f"report/invest_analysis_{utc_now.astimezone(TZ).strftime('%Y%m%d')}.html"; open(fname, 'w', encoding='utf-8').write(html); shutil.copy2(fname, "index.html"); print("[Success] 分析完成")

if __name__ == "__main__": main()
