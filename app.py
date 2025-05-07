from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

model = genai.GenerativeModel('gemini-2.0-flash')

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

def generate_response(user_input):
    if not user_input:
        return {'error': 'Chưa có đầu vào'}

    try:
        system_prompt = (
            "Bạn là chuyên gia về du lịch. Bạn chỉ trả lời các câu hỏi liên quan đến du lịch."
            " Nếu như tôi kêu bạn xưng em với tôi bạn phải xưng như vậy.\n"
        )
        history_text = ""
        for i in chat_history:
            history_text += f"User: {i['user']}\n"
            history_text += f"Bot: {i['bot']}\n"
        full_prompt = system_prompt + history_text + f"Người dùng: {user_input}\nBot:"
        response = model.generate_content(full_prompt)
        bot_reply = response.text.strip()

        chat_history.append({
            'user': user_input,
            'bot': bot_reply,
        })
        save_history()
        return {'response': bot_reply}
    except Exception as e:
        return {'error': str(e)}

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
