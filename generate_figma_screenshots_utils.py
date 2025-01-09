import openai_translate_app_utils
import json

# database start
class WordPhrasePair:
    def __init__(self, src_lang, dst_lang, src_word, dst_word, src_phrase, dst_phrase):
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.src_word = src_word
        self.dst_word = dst_word
        self.src_phrase = src_phrase
        self.dst_phrase = dst_phrase

def add_word_phrase_to_db(db_conn, db_cur, word_phrase_data: WordPhrasePair):
    sql = """
        INSERT INTO word_phrase_pair (src_lang, dst_lang, src_word, dst_word, src_phrase, dst_phrase)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (src_lang, dst_lang, src_word, dst_word) DO NOTHING
    """
    data = (word_phrase_data.src_lang, word_phrase_data.dst_lang, word_phrase_data.src_word, word_phrase_data.dst_word, word_phrase_data.src_phrase, word_phrase_data.dst_phrase)
    db_cur.execute(sql, data)
    db_conn.commit()

def get_word_phrase_from_db(db_cur, dst_lang, src_lang, src_phrase, src_word):
    sql = """
        SELECT dst_word, dst_phrase
        FROM word_phrase_pair
        WHERE src_lang = %s AND dst_lang = %s AND src_phrase = %s AND src_word = %s
        LIMIT 1
    """

    data = (src_lang, dst_lang, src_phrase, src_word)
    db_cur.execute(sql, data)
    row = db_cur.fetchone()

    if row is None:
        return None

    return row[1], row[0]

def is_word_phrase_pair_contains_words(src_phrase: str, src_word: str, dst_phrase: str, dst_word: str):
    if src_word.lower() not in src_phrase.lower():
        return False

    if dst_word.lower() not in dst_phrase.lower():
        return False

    return True

def openai_translate_phrase_and_exclude_word_translation(src_lang, dst_lang, src_phrase, src_word):
    prompt = 'translate this ' + src_lang + ' phrase "' + src_phrase + '" in formal way to ' + dst_lang
    prompt = prompt + ' and extract "' + src_word + '" word translation from translated phrase, output this only as json {"translated_phrase": "", "extracted_word_translation": ""}'
    return openai_translate_app_utils.openai_prompt_exec(prompt)

# const std::string prompt = std::string("generate ") + src_lang_name + " meaningful phrase from word '" 
#     + src_word + "' and translate this phrase to " + dst_lang_name + " and extract word translation from phrase,"
#     + " output this only as csv \"" + src_lang_name + " phrase\" ; \"" + dst_lang_name + " phrase\" ; \"extracted '" + src_word + "' word translation from " + dst_lang_name + " phrase\"";


def openai_is_phrase_translation_valid(src_phrase, dst_phrase, src_lang_name, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' phrase "' + dst_phrase + '" a possible translation for ' + src_lang_name + ' phrase "' + src_phrase + '", output only yes or no'
    result = openai_translate_app_utils.openai_prompt_exec(prompt)
    return 'yes' in result.lower()

# prompt extraction
def extract_word_phrase_from_prompt(prompt):
    try:
        clean_prompt = prompt.strip("```json ").strip("```")
        json_object = json.loads(clean_prompt)
        extracted_phrase = json_object.get("translated_phrase", "")
        if extracted_phrase == "":
            return None

        extracted_word_translation = json_object.get("extracted_word_translation", "")
        if extracted_word_translation == "":
            return None

        if "translated_phrase" in extracted_phrase or "translated phrase" in extracted_phrase:
            return None

        if "translated_phrase" in extracted_word_translation or "translated phrase" in extracted_word_translation:
            return None

        if "extracted_word_translation" in extracted_phrase or "excluded word translation" in extracted_phrase:
            return None

        if "extracted_word_translation" in extracted_word_translation or "excluded word translation" in extracted_word_translation:
            return None

        return extracted_phrase, extracted_word_translation
    except:
        return None
