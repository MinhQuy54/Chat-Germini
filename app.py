from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

genai.configure(api_key="AIzaSyBlp5eDl0PAq7ANPYIkfcQlcHylhiBJ_DA")

app = Flask(__name__)

CORS(app, resources={r"/chat": {"origins": "*"}})

model = genai.GenerativeModel('gemini-2.0-flash')

chat_history = []
def generate_response(user_input):
    if not user_input:
        return {'error': 'Chưa có đầu vào'}

    try:
        system_prompt = "Bạn là chuyên gia về du lịch. Bạn chỉ trả lời các câu hỏi liên quan đến du lịch.Nếu như tôi kêu bạn xưng em với tôi bạn phải xưng như vậy.'\n"
        history_text = ""
        for i in chat_history:
            history_text += f"User: {i['user']}\n"
            history_text += f"Bot: {i['bot']}\n"
        full_prompt = system_prompt + history_text + f"Người dùng: {user_input}\nBot:"
        response = model.generate_content(full_prompt)
        bot_reply = response.text.strip()

        chat_history.append({
            'user': user_input,
            'bot': bot_reply
        })
        return {'response': bot_reply}
        # response = model.generate_content(full_prompt)
        # return {'response': response.text}
    except Exception as e:
        return {'error': str(e)}

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('question')
    response = generate_response(user_input)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
