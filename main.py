import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# ------------------- Load công thức từ file -------------------
with open("8k_cong_thuc.json", "r", encoding="utf-8") as f:
    cong_thuc = json.load(f)

with open("thuattoan.json", "r", encoding="utf-8") as f:
    thuattoan = json.load(f)

# ------------------- Hàm lấy dữ liệu lịch sử từ API -------------------
def fetch_data():
    try:
        res = requests.get("https://saobody-lopq.onrender.com/api/taixiu/history")
        res.raise_for_status()

        # ✅ FIX lỗi JSONDecodeError bằng cách xử lý JSON Lines
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data
    except Exception as e:
        print("❌ Lỗi khi lấy dữ liệu:", e)
        return []

# ------------------- Chuyển kết quả Tài/Xỉu thành T/X -------------------
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

# ------------------- Dự đoán theo bảng thuật toán -------------------
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

# ------------------- API chính: /predict -------------------
@app.get("/predict")
def predict():
    data = fetch_data()
    if len(data) < 10:
        return JSONResponse(content={"error": "Không đủ dữ liệu để dự đoán."})

    # Sắp xếp tăng dần theo session để lấy phiên mới nhất
    data = sorted(data, key=lambda x: x["session"])
    current = data[-1]  # phiên mới nhất
    current_session = current["session"]

    # Tạo chuỗi lịch sử T/X
    result_list = [item["result"] for item in data]
    history_str = convert_to_tx(result_list)

    # Dự đoán theo công thức (ưu tiên 8k, sau đó fallback)
    prediction = predict_by_cong_thuc(history_str) or predict_by_thuattoan(history_str)

    if not prediction:
        return JSONResponse(content={"error": "Không tìm được mẫu phù hợp để dự đoán."})

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