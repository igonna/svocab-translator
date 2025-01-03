import openai_translate_app_utils
from flask import Flask, request, jsonify
from flask_cors import CORS
from colorama import Back
import colorama
import psycopg2
import traceback

colorama.init(autoreset=True)

app = Flask(__name__)
CORS(app)

special_phrases_variables = {}

def translate_phrase(src_phrase, src_lang_code, dst_lang_code, db_conn, db_cur):
    phrase_info = openai_translate_app_utils.get_phrase_info('', src_phrase, special_phrases_variables)
    dst_lang_name = openai_translate_app_utils.get_language_name(dst_lang_code)

    # default phrase
    phrase_translation_db = openai_translate_app_utils.get_phrase_from_db(db_cur, dst_lang_code, src_lang_code, src_phrase)

    if phrase_translation_db is not None:
        return phrase_translation_db

    # generation required
    max_retry = 4
    retry_count = 0
    max_lang_errors = 2
    translated_phrase = ''
    was_not_valid_lang_error = False
    while(retry_count < max_retry and translated_phrase == ''):
        prompt_result = ''
        if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.DEFAULT:
            prompt_result = openai_translate_app_utils.openai_default_phrase_translation(src_phrase, dst_lang_name)

        print(f"prompt result: {prompt_result}")
        translated_phrase = openai_translate_app_utils.extract_phrase_from_prompt(prompt_result)
        print(f"translated phrase: {translated_phrase}")
        translated_phrase = openai_translate_app_utils.make_dst_phrase_look_the_same(src_phrase, translated_phrase)            
        translated_phrase = openai_translate_app_utils.double_single_quotes(translated_phrase)
        
        if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.NOT_TRANSLATION_NAME:
            translated_phrase = openai_translate_app_utils.make_dst_not_translation_names_phrase_look_the_same(translated_phrase, phrase_info)

        dst_phrase_info = openai_translate_app_utils.get_phrase_info('', translated_phrase, special_phrases_variables)

        # verify that phrase valid
        try:
            if phrase_info.phrase_type != dst_phrase_info.phrase_type:
                raise Exception(f"phrase type not the same {phrase_info.phrase_type} to {dst_phrase_info.phrase_type}")

            if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.DEFAULT:
                if retry_count > 1 and was_not_valid_lang_error:
                    pass
                else:
                    phrase_of_lang = openai_translate_app_utils.openai_default_phrase_is_of_lang(src_phrase, translated_phrase, dst_lang_name)
                    if not phrase_of_lang:
                        was_not_valid_lang_error = True
                        raise Exception("openai phrase lang not valid")

        except Exception as e:
            print(Back.YELLOW + f"Retrying: \n\tsrc_phrase ({src_lang_code}): {src_phrase};\n\tdst_phrase ({dst_lang_code}): {translated_phrase};\n\treason: {e};\n\tprompt: {prompt_result};")
            retry_count += 1
            translated_phrase = ''

    translation_valid = translated_phrase != ''
    if translation_valid:
        # add phrase to db
        openai_translate_app_utils.add_phrase_to_db(
            db_conn,
            db_cur,
            openai_translate_app_utils.PhraseData(src_lang_code, src_phrase, dst_lang_code, translated_phrase)
        )
        
        print(Back.GREEN + f"Done: \n\tsrc_phrase ({src_lang_code}): {src_phrase};\n\tdst_phrase ({dst_lang_code}): {translated_phrase};\n\tprompt: {prompt_result};")
        return translated_phrase
    else:
        print(Back.RED + f"failed to translate src_phrase: {src_phrase}")

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        original_text = data.get("text", "")
        dst_lang_code = data.get("dst_lang", "")
        src_lang_code = data.get("src_lang", "")

        print(f"src_lang: {src_lang_code}, dst_lang: {dst_lang_code}, original_text: {original_text}")
        
        if dst_lang_code == '' or src_lang_code == '':
            raise Exception("not valid language length")

        if dst_lang_code == src_lang_code:
            return jsonify({"translatedText": original_text})

        db_conn = psycopg2.connect(
            dbname="svocab_ai_translations",
            user="svocab_ai_translator",
            password="12345",
        )

        db_cur = db_conn.cursor()
        
        try:
            translated_phrase = translate_phrase(original_text, src_lang_code, dst_lang_code, db_conn, db_cur)
        except Exception as e:
            print(f"got exception: {e}")
            traceback.print_exc()
            raise

        print(f"translated_text: {translated_phrase}")

        return jsonify({"translatedText": translated_phrase})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred during translation"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30032)
