import openai_translate_app_utils
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

translations = {
    "Hello": "Bonjour",
    "learn": "apprendre",
    "Title": "Titre",
}

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        phrase_1 = ["phrase_1_guess_space", "phrase_1_word_translation", "phrase_1_guess",
            "phrase_1", "phrase_1_guess_word", "phrase_1_random_word_1", "phrase_1_random_word_2"
        ]

        phrase_2 = ["phrase_2_word", "phrase_2_word_translation", "phrase_2", "phrase_2_translation"]

        data = request.get_json()
        original_text = data.get("text", "")

        translated_text = translations.get(original_text, original_text)

        return jsonify({"translatedText": translated_text})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred during translation"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30032)
