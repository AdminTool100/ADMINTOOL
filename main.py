import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Load công thức 8k và bảng quy tắc
with open("8k_cong_thuc.json", "r", encoding="utf-8") as f:
    cong_thuc = json.load(f)

with open("thuattoan.json", "r", encoding="utf-8") as f:
    thuattoan = json.load(f)

# ------------------- Lấy dữ liệu lịch sử -------------------
def fetch_data():
    try:
        res = requests.get("https://saobody-lopq.onrender.com/api/taixiu/history")
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data
    except:
        return []

# ------------------- Chuyển "Tài"/"Xỉu" thành "T"/"X" -------------------
def convert_to_tx(results):
    return ''.join(["T" if r.lower().strip() == "tài" else "X" for r in results])

# ------------------- Dự đoán theo công thức 8k -------------------
def predict_by_cong_thuc(history: str):
    for length in range(8, 2, -1):
        pattern = history[-length:]
        if pattern in cong_thuc:
            entry = cong_thuc[pattern]
            return {
                "du_doan": "Tài" if entry["next"] == "T" else "Xỉu",
                "confidence": entry["confidence"],
                "matched_pattern": pattern
            }
    return None

# ------------------- Dự đoán theo bảng thuattoan -------------------
def predict_by_thuattoan(history: str):
    for length in range(5, 0, -1):
        pattern = history[-length:]
        if pattern in thuattoan:
            result = thuattoan[pattern]
            return {
                "du_doan": result,
                "confidence": 60,
                "matched_pattern": pattern
            }
    return None

# ------------------- Trang chủ -------------------
@app.get("/")
def home():
    return {"message": "🎲 API Dự đoán Tài/Xỉu bằng Công thức thống kê đã sẵn sàng."}

# ------------------- API Dự đoán -------------------
@app.get("/predict")
def predict():
    data = fetch_data()
    if len(data) < 10:
        return JSONResponse(content={"error": "Không đủ dữ liệu để dự đoán"})

    data = sorted(data, key=lambda x: x["session"])  # sắp xếp tăng dần
    current = data[-1]
    current_session = current["session"]

    # Tạo chuỗi kết quả
    result_list = [item["result"] for item in data]
    history_str = convert_to_tx(result_list)

    # Dự đoán ưu tiên công thức 8k
    prediction = predict_by_cong_thuc(history_str) or predict_by_thuattoan(history_str)

    if not prediction:
        return JSONResponse(content={"error": "Không tìm được mẫu phù hợp để dự đoán"})

    return {
        "current_session": current_session,
        "dice": current["dice"],
        "total": current["total"],
        "result": current["result"],
        "next_session": current_session + 1,
        "du_doan": prediction["du_doan"],
        "confidence": f"{prediction['confidence']}%",
        "matched_pattern": prediction["matched_pattern"]
    }