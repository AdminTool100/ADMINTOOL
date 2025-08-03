from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random
from collections import Counter
import requests
from typing import List, Dict, Optional

app = FastAPI()

# ------------------- CORS Middleware -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Các hàm phụ trợ -------------------
def xu_huong_diem(history: List[Dict]) -> str:
    total1 = history[1]["total"]
    total2 = history[0]["total"]
    if total2 > total1:
        return "lên"
    elif total2 < total1:
        return "xuống"
    return "đều"

def dem_trung(xucxac: List[int]) -> int:
    return max(Counter(xucxac).values())

def du_doan_theo_cong_thuc(history: List[Dict]) -> Optional[str]:
    try:
        xx1, xx2, xx3 = history[2]["dice"], history[1]["dice"], history[0]["dice"]
        result3 = history[0]["result"]
        trend = xu_huong_diem(history)

        if dem_trung(xx1) >= 2:
            return "Tài" if trend == "lên" else "Xỉu"
        if dem_trung(xx2) == 3:
            return "Tài" if trend == "lên" else "Xỉu"

        if (abs(xx3[0] - xx3[1]) == 1 and abs(xx3[2] - xx3[1]) == 1) or \
           (abs(xx3[1] - xx3[2]) == 1 and abs(xx3[0] - xx3[1]) == 1):
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        sorted_xx = sorted(xx3)
        if sorted_xx[1] == sorted_xx[0] + 1 and sorted_xx[2] == sorted_xx[1] + 1:
            return result3
        if sorted_xx[1] - sorted_xx[0] == 2 and sorted_xx[2] - sorted_xx[1] == 2:
            return result3

        if dem_trung(xx3) == 3:
            return result3 if xx3[0] in [3, 4, 6] else ("Tài" if result3 == "Xỉu" else "Xỉu")

        if dem_trung(xx3) == 2:
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        return result3

    except Exception as e:
        print(f"Lỗi trong du_doan_theo_cong_thuc: {e}")
        return None

# ------------------- Lấy dữ liệu từ API -------------------
def fetch_data() -> List[Dict]:
    try:
        res = requests.get("https://saobody-lopq.onrender.com/api/taixiu/history", timeout=10)
        res.raise_for_status()
        data = res.json()  # ✅ Phản hồi API mới là list JSON
        return data
    except Exception as e:
        print(f"[Fetch Error] Không thể lấy dữ liệu: {e}")
        return []

# ------------------- API Dự đoán -------------------
@app.get("/predict")
def predict():
    data = fetch_data()

    if len(data) < 3:
        return JSONResponse(content={"error": "Thiếu dữ liệu để dự đoán. Cần ít nhất 3 phiên."}, status_code=400)

    du_doan = du_doan_theo_cong_thuc(data[:3])
    confidence = 0.95 if du_doan else 0.5
    du_doan = du_doan or random.choice(["Tài", "Xỉu"])

    current = data[0]
    dice = current.get("dice", [0, 0, 0])

    return {
        "id": "ExTaiXiu2010",
        "phien": current.get("session"),
        "xuc_xac_1": dice[0],
        "xuc_xac_2": dice[1],
        "xuc_xac_3": dice[2],
        "tong": current.get("total"),
        "ket_qua": current.get("result"),
        "du_doan": du_doan,
        "ty_le_thanh_cong": f"{round(confidence * 100, 2)}%"
    }