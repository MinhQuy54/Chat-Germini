from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import os
import psycopg2

# Cấu hình Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Kết nối Database (Railway)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Khởi tạo Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Chọn model Gemini
model = genai.GenerativeModel('gemini-2.0-flash')

# Lưu lịch sử chat vào file
HISTORY_FILE = 'chat_history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history():
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

chat_history = load_history()

# Hàm lấy tất cả dữ liệu từ các bảng
def get_all_data():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()

        db_summary = ""

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")  # Lấy 10 dòng mẫu
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]

            db_summary += f"\nBảng: {table_name}\n"
            db_summary += f"Cột: {', '.join(colnames)}\n"
            for row in rows:
                db_summary += f"{dict(zip(colnames, row))}\n"

        cursor.close()
        conn.close()
        return db_summary
    except Exception as e:
        return f"Lỗi lấy dữ liệu: {e}"

# Sinh câu trả lời từ Gemini + dữ liệu DB
def generate_response(user_input):
    if not user_input:
        return {'error': 'Chưa có đầu vào'}

    try:
        db_context = get_all_data()
        system_prompt = (
            "Bạn là chuyên gia dữ liệu du lịch. Dưới đây là dữ liệu từ hệ thống:\n"
            f"{db_context}\n"
            "Dựa trên dữ liệu trên, hãy trả lời câu hỏi của người dùng.\n"
        )

        full_prompt = system_prompt + f"Người dùng: {user_input}\nBot:"
        response = model.generate_content(full_prompt)
        bot_reply = response.text.strip()

        chat_history.append({'user': user_input, 'bot': bot_reply})
        save_history()
        return {'response': bot_reply}
    except Exception as e:
        return {'error': str(e)}

# API endpoints
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('question')
    response = generate_response(user_input)
    return jsonify(response)

@app.route('/history', methods=['GET'])
def history():
    return jsonify(chat_history)

@app.route('/clear', methods=['POST'])
def clear_history():
    global chat_history
    chat_history = []
    save_history()
    return jsonify({'message': 'Lịch sử đã xóa thành công.'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
