import re
from openai import OpenAI
import psycopg2
import loc_lib.file_to_text as file_to_text
import sys
import os
import loc_lib.text_to_words as text_to_words

# db_conn = psycopg2.connect(
#   dbname="svocab_ai_translations",
#   user="svocab_ai_translator",
#   password="12345",
# )

# db_cur = db_conn.cursor()


arguments = sys.argv[1:]

if len(arguments) != 1:
    print("arguments count is not 1")
    exit(1)

input_file = os.path.expanduser(arguments[0])




class WordPhraseData:
  def __init__(self, lang, word_en_key, word, phrase):
    self.lang = lang
    self.word_en_key = word_en_key
    self.word = word
    self.phrase = phrase

def add_phrase_to_db(db_conn, db_cur, word_phrase_data: WordPhraseData):
  sql = """
    INSERT INTO words_phrase (lang, word_en_key, word, phrase)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (lang, word_en_key, word) DO UPDATE
    SET phrase = EXCLUDED.phrase
  """
  data = (word_phrase_data.lang, word_phrase_data.word_en_key, word_phrase_data.word, word_phrase_data.phrase)
  db_cur.execute(sql, data)
  db_conn.commit()

def add_prompt_result_to_db(db_conn, db_cur, src_lang, src_word, target_langs, prompt_response, process_success_status):
  sql = """
    INSERT INTO prompt_response (src_lang, src_word, target_langs, prompt_response, process_success)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (src_lang, src_word, target_langs) DO UPDATE
    SET prompt_response = EXCLUDED.prompt_response, process_success = EXCLUDED.process_success
  """

  data = (src_lang, src_word, target_langs, prompt_response, process_success_status)
  db_cur.execute(sql, data)
  db_conn.commit()


def get_word_phrase_from_db(db_cur, lang, word, word_en_key=''):
  sql = """
    SELECT lang, word_en_key, word, phrase
    FROM words_phrase
    WHERE lang = %s AND """ + ("word = %s" if word_en_key == '' else "(word_en_key = %s OR word = %s)") + """
    LIMIT 1
  """

  # print(sql)
  data = (lang, word) if word_en_key == '' else (lang, word_en_key, word)
  db_cur.execute(sql, data)
  row = db_cur.fetchone()

  if row is None:
    return None
  
  return WordPhraseData(row[0], row[1], row[2], row[3])

def is_all_langs_for_word_in_db(db_cur, langs, word, word_en_key=''):
  exists_count = 0
  for lang in langs:
    result = get_word_phrase_from_db(db_cur, lang, word, word_en_key)
    if result is not None:
      exists_count += 1
  return exists_count == len(langs)


def get_lang_code_from_line(line):
  return line.split(':')[0].strip('{')

def extract_phrases_from_line(line):
  pattern = r'\{(.*?)\}'
  matches = re.findall(pattern, line)
  phrases = [match.strip() for match in matches]
  return phrases

def contains_only_alphabets(s):
  for char in s:
    if not char.isalpha():
      return False
  return True


def is_word_legal(word):
  if len(word) == 0:
    return False
  
  if word[0].isalpha() == False or word[-1].isalpha() == False:
    return False
  
  word_legal_not_alphas = {'-', '\'', ' '}
  
  legal_alphas_count = 0
  for char in word:
    if not char.isalpha():
      if char in word_legal_not_alphas:
        legal_alphas_count += 1
        if legal_alphas_count > 1:
          return False
      else:
        return False
  return True

def is_phrase_legal(phrase, lang):
  phrase_legal_not_alphas = {'!', '?', '.', '¿', '-', '\'', ' ', ',', '，', '！', '。', '？', '’', '—', '–'}
  
  if len(phrase) == 0:
    return False
  
  if not phrase[0].isalpha():
    return False
  
  prev_char = ''
  word_count = 0
  for char in phrase:
    if prev_char == ' ' and char == ' ':
      return False
        
    if char.isalpha():
      if prev_char == ' ' or prev_char == '':
        word_count += 1
    elif char not in phrase_legal_not_alphas:
      return False

    prev_char = char
      
  if word_count < 2 and lang != 'zh':
    return False
  
  return True

def crop_period(string):
  if string.endswith(".") or string.endswith("。"):
    return string[:-1]
  else:
    return string

def process_word_phrase_prompt_result(src_lang, src_word, prompt_result) -> list[WordPhraseData]:
  src_word = src_word.tolower()
  src_phrase = ''
  prompt_lines = prompt_result.split('\n')

  word_phrase_list = []

  for index, line in enumerate(prompt_lines):
    line_len = len(line)
    if line_len == 0:
      continue
    
    line_lang = get_lang_code_from_line(line).lower()
    line_content_parts = extract_phrases_from_line(line)
    line_content_parts_count = len(line_content_parts)

    if line_content_parts_count < 1 or line_content_parts_count > 2:
      raise ValueError("content not valid")

    if line_lang == src_lang:
      if index != 0:
        raise ValueError("src content not valid")
      else:
        src_phrase = crop_period(line_content_parts[0])
        if len(src_phrase) == 0:
          raise ValueError("not valid phrase len")

        if not is_phrase_legal(src_phrase, src_lang):
          raise ValueError("not valid phrase = illegal")
        
        word_phrase_list.append(WordPhraseData(src_lang, word_en_key=src_word, word=src_word, phrase=src_phrase))
        
        phrase_words = text_to_words.text_to_words_1(src_phrase.lower(), src_lang)
        if src_word not in phrase_words:
          raise ValueError("ai identified word as not valid, or phrase not contains it")
    else:
      if index == 0:
        raise ValueError("dst content not valid")
      else:
        dst_phrase = crop_period(line_content_parts[0])
        dst_word = line_content_parts[1].lower()
        if len(dst_phrase) == 0 or len(dst_word) == 0:
          raise ValueError("not valid phrase or word len")
        if not is_word_legal(dst_word):
          raise ValueError("not valid word")
        
        if not is_phrase_legal(dst_phrase, line_lang):
          raise ValueError("not valid phrase = illegal")
        
        word_phrase_list.append(WordPhraseData(line_lang, word_en_key=src_word, word=dst_word, phrase=dst_phrase))
        
  return word_phrase_list

# OpenAI
def openai_get_phrases_and_words(src_lang, src_word, target_langs):
  system_prompt = "I give you a word in '', you must create phrase in " + src_lang + " language with it, and translate this phrase to each language [" + target_langs + "] and also translate word for each language, output should look like " + src_lang + ": {phrase in braces} and for each language one row lang:{phrase in braces}; {translated word in braces}"
  messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": src_word}
  ]

  client = OpenAI()

  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
  )

  return completion.choices[0].message.content


periods = ['。', '.']

def process_words(db_conn, db_cur, words, langs):
  for src_lang in langs:
    if src_lang != 'en':
      continue

    target_langs_array = [lang for lang in langs if lang != src_lang]
    current_prompt_target_langs = ', '.join(target_langs_array)

    for src_word in words:
      skip = is_all_langs_for_word_in_db(db_cur, langs, src_word, src_word if src_lang == 'en' else '')
      if skip:
        # print("-- already exists (skip) word: ", src_word)
        continue

      prompt_response = openai_get_phrases_and_words(src_lang, src_word, current_prompt_target_langs)
      print(prompt_response)
      prompt_parsed_status = False

      try:
        result_word_phrases = process_word_phrase_prompt_result(src_lang, src_word, prompt_response)
        prompt_parsed_status = len(result_word_phrases) == len(langs)
        
        if prompt_parsed_status:
          for wp in result_word_phrases:
            if wp.phrase[-1] in periods:
              wp.phrase = wp.phrase[:-1]
            add_phrase_to_db(db_conn, db_cur, wp)
      except psycopg2.Error as e:
        print("Database Execution happened:", e)
        db_conn.rollback()
        # exit(1)
      except Exception as e:
        print('process failed: ', e)
        prompt_parsed_status = False

      try:
        add_prompt_result_to_db(db_conn, db_cur, src_lang, src_word, current_prompt_target_langs, prompt_response, prompt_parsed_status)
      except psycopg2.Error as e:
        print("Database Execution happened:", e)
        db_conn.rollback()
        # exit(1)


langs = ['en', 'sp', 'it', 'pt', 'fr', 'de', 'ru', 'zh']

words = file_to_text.read_text_file(input_file).lower().split('\n')

conn_params = {
  'dbname':'svocab_ai_translations',
  'user':'svocab_ai_translator',
  'password':'12345'
}


# def get_words_not_processed(db_cur):
#   words_not_processed = []
#   for src_lang in langs:
#     if src_lang != 'en':
#       continue
#     for src_word in words:
#       skip = is_all_langs_for_word_in_db(db_cur, langs, src_word, src_word if src_lang == 'en' else '')
#       if skip:
#         continue
#       words_not_processed.append(src_word)
#   return words_not_processed

import multiprocessing
import psycopg2.pool

def process_words_th(conn_params, words, langs):

  conn = psycopg2.connect(**conn_params)

  try:
    with conn.cursor() as cur:
      process_words(conn, cur, words, langs)
  finally:
    conn.close()

def main():
  pool_len = 90

  chunk_size = len(words) // pool_len
  chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]

  with multiprocessing.Pool(processes=pool_len) as pool:
    pool.starmap(process_words_th, [(conn_params, chunk, langs) for chunk in chunks])

if __name__ == "__main__":
  main()




# # Close the cursor and connection for postgresql
# db_cur.close()
# db_conn.close()




