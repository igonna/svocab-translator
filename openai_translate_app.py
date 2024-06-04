import loc_lib.file_to_text as file_to_text
import sys
from colorama import Back
import os
import json
from openai import OpenAI
import httpx
import psycopg2
import re
import openai_utils
import colorama

colorama.init(autoreset=True)

arguments = sys.argv[1:]

if len(arguments) != 1:
    print(Back.RED + "arguments count is not 1")
    exit(1)

input_file = os.path.expanduser(arguments[0])
phrases = json.loads(file_to_text.read_text_file(input_file))
output_dir = os.path.dirname(os.path.expanduser(arguments[0]))

# OpenAI
def openai_get_phrase_translations(src_lang, src_phrase, target_langs):
    input_phrase = '\'' + src_phrase + '\''
    system_prompt = "I give you a phrase for application inside '' in " + src_lang + " language, you must translate this phrase as professional to [" + target_langs + "] and output should look like for each language one row lang:{phrase in braces}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_phrase}
    ]

    client = OpenAI(timeout=httpx.Timeout(15.0, read=5.0, write=10.0, connect=3.0))

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    return completion.choices[0].message.content


src_lang = 'en'
langs = ['en', 'es', 'it', 'pt', 'fr', 'de', 'ru', 'zh']

target_langs_array = [lang for lang in langs if lang != src_lang]
current_prompt_target_langs = ', '.join(target_langs_array)


class PhraseData:
    def __init__(self, src_lang, src_phrase, dst_lang, dst_phrase):
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.src_phrase = src_phrase
        self.dst_phrase = dst_phrase

def add_phrase_to_db(db_conn, db_cur, phrase_data: PhraseData):
  sql = """
    INSERT INTO app_phrases (src_lang, dst_lang, src_phrase, dst_phrase)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (src_lang, dst_lang, src_phrase) DO UPDATE
    SET dst_phrase = EXCLUDED.dst_phrase
  """
  data = (phrase_data.src_lang, phrase_data.dst_lang, phrase_data.src_phrase, phrase_data.dst_phrase)
  db_cur.execute(sql, data)
  db_conn.commit()

def get_phrase_from_db(db_cur, dst_lang, src_lang, src_phrase):
  sql = """
    SELECT src_lang, dst_lang, src_phrase, dst_phrase
    FROM app_phrases
    WHERE src_lang = %s AND dst_lang = %s AND src_phrase = %s
    LIMIT 1
  """

  data = (src_lang, dst_lang, src_phrase)
  db_cur.execute(sql, data)
  row = db_cur.fetchone()

  if row is None:
    return None
  
  return (dst_lang, row[3])

def get_all_phrases_from_db(db_cur, src_lang, langs, src_phrase):
    result = []
    for lang in langs:
        result.append(get_phrase_from_db(db_cur, lang, src_lang, src_phrase))
    return result


def is_all_phrases_in_db(db_cur, langs, src_lang, src_phrase):
    for lang in langs:
        if get_phrase_from_db(db_cur, lang, src_lang, src_phrase) is None:
            return False
    return True

def strip_non_alpha(s):
    start = 0
    while start < len(s) and not s[start].isalpha():
        start += 1

    end = len(s) - 1
    while end >= 0 and not s[end].isalpha() and s[end] not in ['?', '.', '!']:
        end -= 1

    return s[start:end + 1]


db_conn = psycopg2.connect(
  dbname="svocab_ai_translations",
  user="svocab_ai_translator",
  password="12345",
)

db_cur = db_conn.cursor()


def extract_after_colon(s):
    colon_pos = s.find(':')
    if colon_pos != -1:
        return s[colon_pos + 1:].strip()
    return s

def get_data_from_prompt(prompt):
    result = []
    lines = prompt.split('\n')
    
    for line in lines:
        lang_code = openai_utils.replace_line_lang_if_wrong(openai_utils.get_lang_code_from_line(line.lower()))
        if lang_code is None:
            continue
        if len(lang_code) != 2:
            continue
        
        phrase = strip_non_alpha(extract_after_colon(line))
        if len(phrase) > 0:
            result.append((lang_code, phrase))
    return result


result = {}

for lang in langs:
    if lang == src_lang:
        continue
    result[lang] = {}

for phrase_key, phrase in phrases.items():
    try:
        print("\nsrc_phrase:", phrase)
        add_phrase_to_db(db_conn, db_cur, PhraseData(src_lang, phrase, src_lang, phrase))
        
        lang_phrases = []
        
        if is_all_phrases_in_db(db_cur, langs, src_lang, phrase):
            lang_phrases = get_all_phrases_from_db(db_cur, src_lang, target_langs_array, phrase)
        else:
            prompt_result = openai_get_phrase_translations(openai_utils.replace_lang_for_ai(src_lang), phrase, current_prompt_target_langs)
            lang_phrases = get_data_from_prompt(prompt_result)
            print(prompt_result)
            
            if len(lang_phrases) != len(target_langs_array):
                print(Back.RED + "langs len not valid")
                continue
            
            for lang_phrase in lang_phrases:
                add_phrase_to_db(db_conn, db_cur, PhraseData(src_lang, phrase, lang_phrase[0], lang_phrase[1]))
            

        if len(lang_phrases) != len(target_langs_array):
            print(Back.RED + "langs len not valid")
            continue
            
        for lang_phrase in lang_phrases:
            result[lang_phrase[0]][phrase_key] = lang_phrase[1].replace("'", "\'\'")
            
    except Exception as e:
        print(Back.RED + "exception happened: ", e)
        

for lang, data in result.items():
    print("Locale(\"" + lang + "\"),")
    filename = f"app_{lang}.arb"
    with open(output_dir + '/' + filename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)