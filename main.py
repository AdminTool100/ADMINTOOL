import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


class Phien:
    def __init__(self, dice, total, result):
        self.dice = dice
        self.total = total
        self.result = result


def du_doan_theo_cong_thuc_moi(history_raw):
    if len(history_raw) < 3:
        return None

    history = [
        Phien(item["dice"], item["total"], item["result"])
        for item in history_raw
    ]

    p3, p2, p1 = history[-3], history[-2], history[-1]

    # Công thức 1
    if p2.dice[0] == p2.dice[1]:
        if p2.dice[2] < p3.dice[2]:
            return "Xỉu"
        elif p2.dice[2] > p3.dice[2]:
            return "Tài"

    # Công thức 2
    if p2.dice[0] == p2.dice[2]:
        if p2.dice[1] < p3.dice[1]:
            return "Tài"
        elif p2.dice[1] > p3.dice[1] and p2.dice[2] > p3.dice[2]:
            return "Xỉu"

    # Công thức 3
    if p2.dice[1] == p2.dice[2]:
        if p2.dice[0] < p3.dice[0]:
            return "Tài"
        elif p2.dice[0] > p3.dice[0]:
            return "Tài"

    # Công thức 4 + 5
    sorted_dice = sorted(p2.dice)
    if abs(sorted_dice[0] - sorted_dice[1]) == 1 and abs(sorted_dice[2] - sorted_dice[1]) > 1:
        return "Tài" if p2.result == "Xỉu" else "Xỉu"
    if abs(sorted_dice[1] - sorted_dice[2]) == 1 and abs(sorted_dice[0] - sorted_dice[1]) > 1:
        return "Tài" if p2.result == "Xỉu" else "Xỉu"
    if (abs(sorted_dice[0] - sorted_dice[1]) == 1 and abs(sorted_dice[2] - sorted_dice[1]) > 1) or \
       (abs(sorted_dice[1] - sorted_dice[2]) == 1 and abs(sorted_dice[0] - sorted_dice[1]) > 1):
        return p2.result

    # Công thức 6: Bão
    if p2.dice[0] == p2.dice[1] == p2.dice[2]:
        if p2.dice[0] in [1, 3]:
            return "Tài" if p2.result == "Xỉu" else "Xỉu"
        else:
            return p2.result

    # Công thức 7: 3 số cách đều
    if sorted(p2.dice) in ([1, 3, 5], [2, 4, 6]):
        return "Tài" if p2.result == "Xỉu" else "Xỉu"

    # Công thức 8: 3 số liên tiếp
    seq = sorted(p2.dice)
    if seq == [1, 2, 3]:
        return "Xỉu"
    elif seq == [2, 3, 4]:
        return "Xỉu"
    elif seq == [3, 4, 5]:
        return "Tài"
    elif seq == [4, 5, 6]:
        return "Xỉu"

    # Công thức 9: cầu kép điểm
    count_same_total = 1
    for i in range(len(history) - 2, 0, -1):
        if history[i].total == history[i-1].total:
            count_same_total += 1
        else:
            break
    if count_same_total in [3, 4, 6, 9]:
        return "Tài" if p2.result == "Xỉu" else "Xỉu"
    elif count_same_total in [5, 7, 8, 10]:
        return p2.result
    elif count_same_total in [11, 13, 14, 16, 18]:
        return "Tài"
    elif count_same_total in [12, 15, 17]:
        return "Xỉu"

    # Công thức 10: cầu 1-1 hoặc bệt
    last3 = [p3.result, p2.result, p1.result]
    if last3[0] != last3[1] and last3[0] == last3[2]:
        return last3[0]  # theo cầu 1-1
    count_bet = 1
    for i in range(len(history) - 1, 0, -1):
        if history[i].result == history[i-1].result:
            count_bet += 1
        else:
            break
    if count_bet >= 4:
        return history[-1].result

    # Không khớp công thức nào → theo phiên trước
    return p2.result


@app.get("/")
def predict():
    try:
        response = requests.get("https://saolo-binhtool.onrender.com/api/taixiu/history")
        response.raise_for_status()

        raw_text = response.text.strip()
        raw_lines = raw_text.splitlines()

        try:
            history = [json.loads(line) for line in raw_lines if line.strip()][:100]
        except Exception as e:
            return JSONResponse(content={"detail": f"Lỗi phân tích JSON: {str(e)}"})

        if len(history) < 3:
            return JSONResponse(content={"detail": "Không đủ dữ liệu để phân tích theo công thức"})

        current = history[0]
        next_session = current["session"] + 1

        du_doan = du_doan_theo_cong_thuc_moi(history[:10])

        return {
            "current_session": current["session"],
            "current_result": current["result"],
            "current_dice": current["dice"],
            "current_total": current["total"],
            "next_session": next_session,
            "du_doan": du_doan,
            "Te_le": "@ExTaiXiu2010"
        }

    except Exception as e:
        return JSONResponse(content={"detail": f"Lỗi xử lý dự đoán: {str(e)}"})