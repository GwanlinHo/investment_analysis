import os
import json
import pytest
from investment_analysis import save_to_json
from update_report import load_from_json

def test_save_and_load_json(tmp_path):
    """測試資料儲存與讀取的完整性"""
    test_file = tmp_path / "test_data.json"
    
    # 建立假資料
    fundamental = [{"symbol": "TEST", "pe": 15}]
    yield_data = {"3M": 5.0, "10Y": 4.5}
    market = {"TEST": [{"Date": "2026-01-01", "Close": 100}]}
    summary = [{"symbol": "TEST", "change": 1.5}]
    
    # 測試儲存
    # 因為 save_to_json 內部沒法指定檔案路徑（除非我們修改它以支援路徑參數）
    # 我們這裡先用預設的 technical_data.json 並在完成後清理
    
    save_to_json(fundamental, yield_data, market, summary, filename=str(test_file))
    
    assert os.path.exists(test_file)
    
    # 測試讀取
    loaded_data = load_from_json(str(test_file))
    
    assert loaded_data is not None
    assert loaded_data["fundamental"] == fundamental
    assert loaded_data["yield"] == yield_data
    assert loaded_data["market"] == market
    assert loaded_data["summary"] == summary
    assert "last_updated" in loaded_data

def test_load_non_existent_file():
    """測試讀取不存在檔案的情況"""
    data = load_from_json("non_existent_file_xyz.json")
    assert data is None

def test_html_containment_reduction():
    """驗證 HTML 中不再包含原始 JSON 資料 (此測試需在執行過腳本後手動或透過 mock 驗證)"""
    # 這裡可以透過讀取最新的 index.html 並檢查是否還有 "{{ fundamental_json }}" 字樣
    # 但因為我們已经改了 template，這裡主要確認 script 標籤內是否為空 {}
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
            assert '<script id="fundamental-data" type="application/json">{}</script>' in content
