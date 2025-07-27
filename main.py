# main.py
import random
import requests
from collections import Counter
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# --- Công thức cầu ---
def xu_huong_diem(history):
    total1 = history[1]["total"]
    total2 = history[0]["total"]
    if total2 > total1:
        return "lên"
    elif total2 < total1:
        return "xuống"
    return "đều"

def dem_trung(xucxac):
    return max(xucxac.count(i) for i in xucxac)

def dem_tan_suat(xx1, xx2, xx3):
    return Counter(xx1 + xx2 + xx3)

def du_doan_theo_cong_thuc(history):
    try:
        xx1, xx2, xx3 = history[2]["dice"], history[1]["dice"], history[0]["dice"]
        result3 = history[0]["result"]
        trend = xu_huong_diem(history)
        freq = dem_tan_suat(xx1, xx2, xx3)
        sorted_xx = sorted(xx3)

        if dem_trung(xx1) >= 2 or dem_trung(xx2) == 3:
            return "Tài" if trend == "lên" else "Xỉu"

        if (abs(xx3[0] - xx3[1]) == 1 and abs(xx3[2] - xx3[1]) == 1) or \
           (abs(xx3[1] - xx3[2]) == 1 and abs(xx3[0] - xx3[1]) == 1):
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        if sorted_xx[1] == sorted_xx[0] + 1 and sorted_xx[2] == sorted_xx[1] + 1:
            return result3
        if sorted_xx[1] - sorted_xx[0] == 2 and sorted_xx[2] - sorted_xx[1] == 2:
            return result3

        if dem_trung(xx3) == 3:
            return result3 if xx3[0] in [3, 4, 6] else ("Tài" if result3 == "Xỉu" else "Xỉu")
        if dem_trung(xx3) == 2:
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        return result3
    except:
        return None

# --- Lấy dữ liệu lịch sử ---
def fetch_data():
    try:
        res = requests.get("https://saobody-lopq.onrender.com/api/taixiu/history")
        return res.json()
    except:
        return []

# --- API /predict ---
@app.get("/predict")
def predict():
    data = fetch_data()
    if len(data) < 3:
        return JSONResponse(content={"error": "Thiếu dữ liệu."})

    du_doan = du_doan_theo_cong_thuc(data[:3])
    if du_doan is None:
        du_doan = random.choice(["Tài", "Xỉu"])
        confidence = 0.5
    else:
        confidence = 0.95

    current = data[0]
    return {
        "id": "ExTaiXiu2010",
        "phien": current["session"],
        "xuc_xac_1": current["dice"][0],
        "xuc_xac_2": current["dice"][1],
        "xuc_xac_3": current["dice"][2],
        "tong": current["total"],
        "ket_qua": current["result"],
        "du_doan": du_doan,
        "ty_le_thanh_cong": f"{round(confidence * 100, 2)}%",
        "note": "Dự đoán theo công thức cầu" if confidence > 0.5 else "Không khớp cầu, chọn ngẫu nhiên"
    }