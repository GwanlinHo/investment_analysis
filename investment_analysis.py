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

import json

# --- 全域設定 ---
warnings.filterwarnings("ignore")
TZ = pytz.timezone('Asia/Taipei')

# --- 讀取設定檔 ---
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        STOCK_GROUPS = config.get("stock_groups", [])
        KEY_INDICATORS = config.get("key_indicators", [])
        SYMBOL_NAME_MAP = config.get("symbol_name_map", {})
except FileNotFoundError:
    print(f"[Error] 錯誤：找不到設定檔 {CONFIG_FILE}。")
    STOCK_GROUPS = []
    KEY_INDICATORS = []
    SYMBOL_NAME_MAP = {}
except json.JSONDecodeError:
    print(f"[Error] 錯誤：設定檔 {CONFIG_FILE} 格式不正確。")
    STOCK_GROUPS = []
    KEY_INDICATORS = []
    SYMBOL_NAME_MAP = {}
except Exception as e:
    print(f"[Error] 讀取設定檔時發生未預期的錯誤: {e}")
    STOCK_GROUPS = []
    KEY_INDICATORS = []
    SYMBOL_NAME_MAP = {}

# --- 資料獲取 ---
def get_stock_data(symbols, start_date, end_date):
    """抓取多支股票的資料"""
    data = {}
    for symbol in symbols:
        try:
            # yfinance download
            df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                print(f"[Warning] 警告：無法獲取 {symbol} 的有效資料，將跳過。")
                continue
            
            # 處理 yfinance 可能回傳的 MultiIndex 欄位
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
        
        # 提取關鍵指標，若無資料則為 None
        data = {
            "symbol": symbol,
            "name": SYMBOL_NAME_MAP.get(symbol, symbol),
            "pe_trailing": info.get('trailingPE'),
            "pe_forward": info.get('forwardPE'),
            "pb_ratio": info.get('priceToBook'),
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
    # KD
    low_min = df['Low'].rolling(window=9, min_periods=1).min()
    high_max = df['High'].rolling(window=9, min_periods=1).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    
    # BIAS (乖離率)
    for period in [5, 20, 60]:
        ma = df['Close'].rolling(window=period).mean()
        df[f'BIAS_{period}'] = ((df['Close'] - ma) / ma) * 100
        
    # DMI (動向指標)
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

# --- HTML 樣式與輔助函式 ---

def determine_trend(k, d, bias20, change_pct):
    """簡易趨勢判斷"""
    signal = ""
    style_class = "neutral"
    
    # 強勢多頭：K > D 且 月線乖離 > 0
    if k > d and bias20 > 0:
        signal = "多頭排列"
        style_class = "bullish-strong"
    # 弱勢反彈：K > D 但 月線乖離 < 0
    elif k > d and bias20 < 0:
        signal = "反彈"
        style_class = "bullish-weak"
    # 強勢空頭：K < D 且 月線乖離 < 0
    elif k < d and bias20 < 0:
        signal = "空頭修正"
        style_class = "bearish-strong"
    # 高檔拉回：K < D 但 月線乖離 > 0
    elif k < d and bias20 > 0:
        signal = "回檔整理"
        style_class = "bearish-weak"
        
    return signal, style_class

def get_color_class(value, high=0, low=0, inverse=False):
    """
    返回 CSS class
    inverse=True 用於 VIX 或反向指標 (跌是好的)
    預設: > high (Red/Up), < low (Green/Down)
    """
    if pd.isna(value): return ""
    
    if not inverse:
        if value > high: return "text-up"
        if value < low: return "text-down"
    else:
        if value > high: return "text-down" # 數值高是不好的
        if value < low: return "text-up"    # 數值低是好的
        
    return ""

def format_data_row(symbol, latest, prev):
    """格式化單行 HTML 表格資料"""
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
    
    trend_signal, trend_class = determine_trend(k, d, bias20, change_pct)
    
    # 判斷是否為 VIX 相關 (代碼含 VIX 或反向)
    is_inverse = "VIX" in symbol
    
    # 獲取顯示名稱
    display_name = SYMBOL_NAME_MAP.get(symbol, symbol)
    # 組合顯示 HTML: 中文名稱在上，代碼在下(小字)
    symbol_html = f"<div>{display_name}</div><div style='font-size: 11px; color: #888;'>{symbol}</div>"

    return f"""
    <tr>
      <td class="symbol-cell">{symbol_html}</td>
      <td class="number-cell {get_color_class(change_pct, 0, 0, is_inverse)}"><strong>{close:,.2f}</strong></td>
      <td class="number-cell {get_color_class(change_pct, 0, 0, is_inverse)}">{change_pct:+.2f}%</td>
      <td class="trend-cell"><span class="badge {trend_class}">{trend_signal}</span></td>
      <td class="number-cell {get_color_class(vol_change, 100, 50)}">{vol_change:.1f}%</td>
      <td class="number-cell {get_color_class(k, 80, 20)}">{k:.1f}</td>
      <td class="number-cell {get_color_class(d, 80, 20)}">{d:.1f}</td>
      <td class="number-cell {get_color_class(bias5, 3, -3)}">{bias5:.1f}</td>
      <td class="number-cell {get_color_class(bias20, 5, -5)}">{bias20:.1f}</td>
      <td class="number-cell {get_color_class(bias60, 10, -10)}">{bias60:.1f}</td>
      <td class="number-cell {get_color_class(adx, 25, 0)}">{adx:.1f}</td>
      <td class="number-cell {get_color_class(plus_di, minus_di, float("-inf"))}">{plus_di:.1f}</td>
      <td class="number-cell {get_color_class(minus_di, plus_di, float("-inf"))}">{minus_di:.1f}</td>
    </tr>
    """

def create_ma_plot_base64(df, symbol, title=None):
    """建立K線圖(含MA與成交量)並返回Base64字串"""
    # 定義自訂樣式：紅漲綠跌 (Taiwan Style), 背景白色
    mc = mpf.make_marketcolors(up='#e53935', down='#43a047', edge='inherit', wick='inherit', volume='in', inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc, gridstyle=':', gridcolor='#e0e0e0', facecolor='white')

    buf = BytesIO()
    
    # 如果沒有提供標題，就用代碼
    plot_title = title if title else symbol
    
    try:
        # 增加 dpi 提升清晰度
        # 注意: mpf.plot 的 title 參數有時會被 tight_layout 裁切，這裡我們不直接用 mpf 的 title，
        # 而是讓前端 HTML 負責顯示標題，圖表本身保持乾淨，或者僅在圖表內部顯示簡單資訊。
        # 但為了符合使用者需求，我們這裡不傳入 title 給 mpf (因為 HTML 已經有標題了)，
        # 這裡的修改主要是為了函式簽名的一致性，或者如果我們想在圖中加標題的話。
        # 實際上，我們在 HTML 的 chart-card 已經有顯示標題了。
        # 為了讓圖片更單純，我們保持原樣，但在 main 呼叫時會用到這個函式。
        
        mpf.plot(df, type='candle', mav=(5, 20, 60), volume=True, 
                 style=s, figsize=(10, 6), 
                 savefig=dict(fname=buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100),
                 ylabel='', ylabel_lower='',
                 xrotation=0,
                 datetime_format='%m-%d',
                 tight_layout=True,
                 panel_ratios=(4,1))
        
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        print(f"[Error] 繪製 {symbol} K線圖時發生錯誤: {e}")
        return None

def create_yield_curve_plot_base64():
    """建立美國公債殖利率曲線圖並返回Base64字串"""
    print("  - 正在產生美國公債殖利率圖表...")
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=5*365) # 5 years
        
        # 抓取三種殖利率
        three_month_df = yf.download("^IRX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        ten_year_df = yf.download("^TNX", start=start_date, end=end_date, progress=False, auto_adjust=True)
        thirty_year_df = yf.download("^TYX", start=start_date, end=end_date, progress=False, auto_adjust=True)

        if three_month_df.empty or ten_year_df.empty or thirty_year_df.empty:
            print("  [Warning] 無法獲取完整的殖利率資料。")
            return None

        # 使用 matplotlib 風格
        plt.style.use('bmh')
        plt.figure(figsize=(12, 6))
        
        # 繪製 3個月期 (短債)
        plt.plot(three_month_df.index, three_month_df['Close'], label='3-Month Yield (^IRX)', color='#e53935', linewidth=1.2, alpha=0.8)
        
        # 繪製 10年期 (中長債基準)
        plt.plot(ten_year_df.index, ten_year_df['Close'], label='10-Year Yield (^TNX)', color='#1976d2', linewidth=1.5)
        
        # 繪製 30年期 (長債)
        plt.plot(thirty_year_df.index, thirty_year_df['Close'], label='30-Year Yield (^TYX)', color='#8e24aa', linewidth=1.5)
        
        plt.ylabel('Yield (%)', fontsize=10)
        plt.legend(fontsize=9, loc='upper left', frameon=True, facecolor='white')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"[Error] 產生殖利率圖表時發生錯誤: {e}")
        return None

def generate_html_report(report_data, date_str, summary_data, yield_curve_plot_b64=None, fundamental_data=None):
    """生成最終的HTML報告"""
    
    # 將基本面數據轉換為 JSON 字串，嵌入 HTML 中供 AI 讀取
    fundamental_json = json.dumps(fundamental_data, ensure_ascii=False, indent=2) if fundamental_data else "{}"

    # 建構市場速覽 HTML
    summary_html = ""
    for item in summary_data:
        color_class = get_color_class(item['change'], 0, 0, inverse=("VIX" in item['symbol']))
        icon = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "-"
        summary_html += f'''
        <div class="summary-card">
            <div class="summary-title">{item['symbol']}</div>
            <div class="summary-price">{item['close']:.2f}</div>
            <div class="summary-change {color_class}">{icon} {item['change']:.2f}%</div>
        </div>
        '''

    content_html = ""
    for group_data in report_data:
        # Determine ID for navigation
        section_id = ""
        title = group_data['title']
        if "美股" in title:
            section_id = "us-stocks"
        elif "台股" in title:
            section_id = "tw-stocks"
        elif "債券" in title:
            section_id = "bonds"
        else:
            section_id = f"group-{abs(hash(title))}"

        # Group Title
        content_html += f'''
        <div id="{section_id}" class="group-section">
            <h2 class="group-title">{title}</h2>
            
            <!-- Table Card -->
            <div class="card table-card">
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>名稱</th>
                                <th>價格</th>
                                <th>漲跌%</th>
                                <th>技術訊號</th>
                                <th>量比%</th>
                                <th>K9</th>
                                <th>D9</th>
                                <th>5日乖離</th>
                                <th>20日乖離</th>
                                <th>60日乖離</th>
                                <th>ADX</th>
                                <th>+DI</th>
                                <th>-DI</th>
                            </tr>
                        </thead>
                        <tbody>
                            {group_data['table_rows']}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Charts Grid -->
            <h3 class="subsection-title">K線圖概覽</h3>
            <div class="charts-grid">
        '''
        
        for symbol, b64_plot in group_data['plots'].items():
            content_html += f'''
                <div class="card chart-card">
                    <div class="chart-header">{symbol}</div>
                    <img src="data:image/png;base64,{b64_plot}" alt="{symbol} Plot" loading="lazy">
                </div>
            '''
        content_html += '</div></div>'

    # Yield Curve Section
    if yield_curve_plot_b64:
        content_html += f'''
        <div id="macro-analysis" class="group-section">
            <h2 class="group-title">總體經濟指標</h2>
            <div class="card chart-card" style="max-width: 900px; margin: 0 auto;">
                 <div class="chart-header">美國長短期國庫券殖利率</div>
                 <img src="data:image/png;base64,{yield_curve_plot_b64}" alt="Yield Curve Plot">
            </div>
            
            <!-- Macro Data Section -->
            <div class="card" style="margin-top: 25px; padding: 20px;">
                <h3 class="subsection-title" style="margin-top: 0; margin-bottom: 20px;">美台重要經濟指標</h3>
                
                <div style="margin-bottom: 30px;">
                    <h4 style="color: #333; margin-bottom: 15px; border-left: 4px solid #1a237e; padding-left: 10px;"> 美國經濟指標</h4>
                    <div class="table-responsive">
                        <div id="us-macro-placeholder"></div>
                    </div>
                </div>

                <div>
                    <h4 style="color: #333; margin-bottom: 15px; border-left: 4px solid #2e7d32; padding-left: 10px;"> 台灣經濟指標</h4>
                    <div class="table-responsive">
                        <div id="tw-macro-placeholder"></div>
                    </div>
                </div>
            </div>
        </div>
        '''

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>投資技術分析日報 | {date_str}</title>
        <!-- 
        HIDDEN FUNDAMENTAL DATA FOR AI ANALYSIS
        The following JSON block contains fundamental data (PE, ROE, etc.) for the analyzed stocks.
        AI Agents should read this block to perform Value Investing analysis.
        -->
        <script id="fundamental-data" type="application/json">
        {fundamental_json}
        </script>
        <style>
            :root {{
                --bg-color: #f4f6f8;
                --text-primary: #333;
                --text-secondary: #666;
                --card-bg: #ffffff;
                --up-color: #e53935;
                --down-color: #43a047;
                --accent-color: #1a237e;
                --border-color: #e0e0e0;
            }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; background-color: var(--bg-color); color: var(--text-primary); line-height: 1.6; }}
            
            /* Container */
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            
            /* Header */
            header {{ text-align: center; margin-bottom: 30px; padding: 20px 0; }}
            h1 {{ margin: 0; color: var(--accent-color); font-size: 28px; font-weight: 700; letter-spacing: 1px; }}
            .date-tag {{ display: inline-block; background: #e8eaf6; color: var(--accent-color); padding: 4px 12px; border-radius: 20px; font-size: 14px; margin-top: 10px; font-weight: 500; }}

            /* Market Summary Bar */
            .summary-bar {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 40px; }}
            .summary-card {{ background: var(--card-bg); padding: 10px 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-bottom: 3px solid transparent; }}
            .summary-title {{ font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-bottom: 3px; }}
            .summary-price {{ font-size: 16px; font-weight: 800; color: var(--text-primary); }}
            .summary-change {{ font-size: 12px; font-weight: 600; margin-top: 2px; }}

            /* Common Utils */
            .text-up {{ color: var(--up-color); }}
            .text-down {{ color: var(--down-color); }}
            .card {{ background: var(--card-bg); border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 20px; margin-bottom: 25px; overflow: hidden; }}
            
            /* Group Section */
            .group-section {{ margin-bottom: 50px; }}
            .group-title {{ font-size: 22px; color: #2c3e50; border-left: 5px solid var(--accent-color); padding-left: 15px; margin-bottom: 8px; font-weight: 700; }}
            .group-desc {{ color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; padding-left: 20px; }}
            .subsection-title {{ text-align: center; font-size: 18px; color: var(--text-secondary); margin: 30px 0 20px; position: relative; }}
            .subsection-title:after {{ content: ''; display: block; width: 50px; height: 3px; background: #ddd; margin: 10px auto 0; }}

            /* Table Styles */
            .table-responsive {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; white-space: nowrap; }}
            th {{ background-color: #f8f9fa; color: #495057; font-weight: 600; padding: 8px 4px; text-align: right; border-bottom: 2px solid var(--border-color); }}
            th:first-child {{ text-align: left; }}
            th:nth-child(4) {{ text-align: center; width: 70px; }} /* Signal column center */
            td {{ padding: 8px 4px; border-bottom: 1px solid var(--border-color); text-align: right; }}
            td:first-child {{ text-align: left; font-weight: 600; color: var(--accent-color); }}
            tr:hover {{ background-color: #f1f3f5; }}
            
            /* Badges */
            .badge {{ padding: 4px 6px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; display: inline-block; min-width: 64px; text-align: center; }}
            .bullish-strong {{ background-color: #e53935; }}
            .bullish-weak {{ background-color: #ef9a9a; color: #b71c1c; }}
            .bearish-strong {{ background-color: #43a047; }}
            .bearish-weak {{ background-color: #a5d6a7; color: #1b5e20; }}
            .neutral {{ background-color: #9e9e9e; }}
            .trend-cell {{ text-align: center; }}

            /* Navigation & Back to Top */
            html {{ scroll-behavior: smooth; }}
            .nav-bar {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; flex-wrap: wrap; }}
            .nav-btn {{ background: #fff; border: 1px solid var(--accent-color); color: var(--accent-color); padding: 6px 14px; border-radius: 20px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all 0.2s; display: flex; align-items: center; gap: 5px; }}
            .nav-btn:hover {{ background: var(--accent-color); color: white; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .back-to-top {{ position: fixed; bottom: 30px; right: 30px; background: var(--accent-color); color: white; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: transform 0.2s; z-index: 1000; font-size: 20px; opacity: 0.9; }}
            .back-to-top:hover {{ transform: scale(1.1); opacity: 1; }}

            /* Charts Grid */
            .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 25px; }}
            .chart-card {{ padding: 15px; display: flex; flex-direction: column; align-items: center; }}
            .chart-header {{ width: 100%; text-align: left; font-weight: 700; font-size: 16px; margin-bottom: 10px; color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            img {{ max-width: 100%; height: auto; }}

            /* Text Analysis Section (Placeholder Styles) */
            #weekly-news-focus, #ai-analysis-report {{ margin-top: 40px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
            #weekly-news-focus h2, #ai-analysis-report h2 {{ color: var(--accent-color); border-bottom: 2px solid #eee; padding-bottom: 15px; margin-bottom: 25px; font-size: 24px; font-weight: 700; }}
            #weekly-news-focus h3, #ai-analysis-report h3 {{ color: #444; margin-top: 30px; font-size: 20px; margin-bottom: 15px; font-weight: 600; }}
            #weekly-news-focus p, #ai-analysis-report p {{ font-size: 16px; line-height: 1.8; color: #444; margin-bottom: 15px; }}
            #weekly-news-focus ul, #ai-analysis-report ul {{ padding-left: 20px; }}
            #weekly-news-focus li, #ai-analysis-report li {{ margin-bottom: 10px; color: #555; }}

            @media (max-width: 768px) {{
                .charts-grid {{ grid-template-columns: 1fr; }}
                .summary-bar {{ grid-template-columns: repeat(2, 1fr); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header id="top">
                <h1>綜合投資分析報告</h1>
                <div class="date-tag">{date_str}</div>
            </header>

            <div class="nav-bar">
                <a href="#us-stocks" class="nav-btn">美股</a>
                <a href="#tw-stocks" class="nav-btn">台股</a>
                <a href="#bonds" class="nav-btn">債券</a>
                <a href="#macro-analysis" class="nav-btn">總經資訊</a>
                <a href="#weekly-news-focus" class="nav-btn">財經焦點</a>
                <a href="#ai-analysis-report" class="nav-btn">AI分析</a>
            </div>

            <div class="summary-bar">
                {summary_html}
            </div>

            {content_html}

            <!-- AI Generated Content Will Be Injected Here -->
            <div id="weekly-news-focus"></div>
            <div id="ai-analysis-report"></div>

            <!-- Disclaimer Footer -->
            <footer style="text-align: center; margin-top: 50px; padding: 20px; color: #777; font-size: 12px; border-top: 1px solid #eee;">
                <p>[Warning] 免責聲明：本報告僅供研究參考，不構成任何投資建議。金融市場波動劇烈，投資人應自行評估風險並承擔投資結果。</p>
                <p>&copy; 2026 Investment Analysis Automation. Generated by AI.</p>
            </footer>
            
            <a href="#top" class="back-to-top" title="回到頁首">↑</a>
        </div>
    </body>
    </html>
    """
    filename = f"report/invest_analysis_{date_str.replace('-', '')}.html"
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"[Success] 報告已成功生成：{os.path.abspath(filename)}")
    except IOError as e:
        print(f"[Error] 寫入檔案時發生錯誤: {e}")

# --- 主程式 ---
def main():
    """主執行函式"""
    utc_now = datetime.datetime.utcnow()
    # 抓取足夠長的時間以計算 60MA
    start_date = utc_now - datetime.timedelta(days=250)
    current_date_str = utc_now.astimezone(TZ).strftime('%Y-%m-%d')
    
    report_data = []
    summary_data_list = []
    fundamental_data_list = [] # 儲存基本面數據

    print(f"[Info] 開始執行分析工作... ({current_date_str})")

    for group in STOCK_GROUPS:
        print(f"\n--- 正在處理群組: {group['title']} ---")
        stock_data = get_stock_data(group["symbols"], start_date, utc_now)
        
        if not stock_data:
            print(f"  [Warning] 群組 {group['title']} 沒有可處理的資料。")
            continue

        table_rows_html = ""
        plots = {}
        
        for symbol, df in stock_data.items():
            print(f"  - 分析: {symbol}")
            df_indicators = calculate_all_indicators(df)
            
            if df_indicators.empty or len(df_indicators) < 2:
                continue

            latest = df_indicators.iloc[-1]
            prev = df_indicators.iloc[-2]
            
            # 生成表格行
            table_rows_html += format_data_row(symbol, latest, prev)
            
            # 產生圖表
            display_name = SYMBOL_NAME_MAP.get(symbol, symbol)
            plots[display_name] = create_ma_plot_base64(df_indicators.tail(120), symbol, display_name)

            # 收集摘要數據
            if symbol in KEY_INDICATORS:
                summary_data_list.append({
                    'symbol': display_name,
                    'close': latest['Close'],
                    'change': latest['Change %']
                })
            
            # 抓取基本面數據 (非指數類)
            if not symbol.startswith('^'):
                f_data = get_fundamental_data(symbol)
                if f_data:
                    fundamental_data_list.append(f_data)
        
        if not table_rows_html:
            continue
        
        report_data.append({
            "title": group['title'],
            "description": group['description'],
            "table_rows": table_rows_html,
            "plots": plots
        })

    # 確保摘要數據按照設定的順序排列
    ordered_summary = []
    for key in KEY_INDICATORS:
        target_name = SYMBOL_NAME_MAP.get(key, key)
        for item in summary_data_list:
            if item['symbol'] == target_name:
                ordered_summary.append(item)
                break
    
    # 產生總經殖利率圖
    yield_curve_plot = create_yield_curve_plot_base64()

    if report_data:
        generate_html_report(report_data, current_date_str, ordered_summary, yield_curve_plot, fundamental_data_list)
    else:
        print("[Error] 沒有任何資料可生成報告。")

if __name__ == "__main__":
    main()