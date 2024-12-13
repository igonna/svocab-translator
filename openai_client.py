import re
from openai import OpenAI
import httpx
import psycopg2
import loc_lib.file_to_text as file_to_text
import sys
import os
import loc_lib.text_to_words as text_to_words
import colorama
from colorama import Back
import time
import psycopg2.pool
import threading
import openai_utils


colorama.init(autoreset=True)

# db_conn = psycopg2.connect(
#   dbname="svocab_ai_translations",
#   user="svocab_ai_translator",
#   password="12345",
# )

# db_cur = db_conn.cursor()


arguments = sys.argv[1:]

if len(arguments) != 1:
    print(Back.RED + "arguments count is not 1")
    exit(1)

input_file = os.path.expanduser(arguments[0])
src_lang = file_to_text.get_file_name_without_extension(input_file)


class WordPhraseData:
  def __init__(self, src_lang, src_word, dst_lang, dst_word, phrase):
    self.src_lang = src_lang
    self.src_word = src_word
    self.dst_lang = dst_lang
    self.dst_word = dst_word
    self.phrase = phrase

def add_phrase_to_db(db_conn, db_cur, word_phrase_data: WordPhraseData):
  sql = """
    INSERT INTO words_phrase (src_lang, src_word, dst_lang, dst_word, phrase)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (src_lang, src_word, dst_lang) DO UPDATE
    SET phrase = EXCLUDED.phrase, dst_word= EXCLUDED.dst_word
  """
  data = (word_phrase_data.src_lang, word_phrase_data.src_word, word_phrase_data.dst_lang, word_phrase_data.dst_word, word_phrase_data.phrase)
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
  
  
def add_disabled_word_to_db(db_conn, db_cur, src_lang, src_word):
  sql = """
    INSERT INTO disabled_word (src_lang, src_word)
    VALUES (%s, %s)
    ON CONFLICT (src_lang, src_word) DO UPDATE
    SET count = disabled_word.count + 1
  """

  data = (src_lang, src_word)
  db_cur.execute(sql, data)
  db_conn.commit()
  
def remove_disabled_word_from_db(db_conn, db_cur, src_lang, src_word):
  sql = """
    DELETE FROM disabled_word WHERE src_lang=%s AND src_word=%s
  """

  data = (src_lang, src_word)
  db_cur.execute(sql, data)
  db_conn.commit()

def get_disabled_word_count(db_cur, src_lang, src_word):
  sql = """
  SELECT count FROM disabled_word
  WHERE src_lang = %s AND src_word = %s;
  """
  
  data = (src_lang, src_word)
  db_cur.execute(sql, data)
  result = db_cur.fetchone()
  
  if result is None:
    return 0
  else:
    return result[0]


def get_word_phrase_from_db(db_cur, dst_lang, src_lang, src_word):
  sql = """
    SELECT src_lang, src_word, dst_lang, dst_word, phrase
    FROM words_phrase
    WHERE src_lang = %s AND dst_lang = %s AND src_word = %s
    LIMIT 1
  """

  # print(sql)
  data = (src_lang, dst_lang, src_word)
  db_cur.execute(sql, data)
  row = db_cur.fetchone()

  if row is None:
    return None
  
  return WordPhraseData(row[0], row[1], row[2], row[3], row[4])

def is_all_langs_for_word_in_db(db_cur, langs, src_lang, src_word):
  exists_count = 0
  for dst_lang in langs:
    result = get_word_phrase_from_db(db_cur, dst_lang, src_lang, src_word)
    if result is not None:
      exists_count += 1
  return exists_count == len(langs)


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

def crop_first_and_last_quote(s):
  if s.startswith("'"):
    s = s[1:]
  if s.endswith("'"):
    s = s[:-1]
  return s
  
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

def capitalize_first_char(s):
    if len(s) > 0:
        return s[0].upper() + s[1:]
    else:
        return s

def process_word_phrase_prompt_result(db_conn, db_cur, src_lang, src_word, prompt_result) -> list[WordPhraseData]:
  src_word = src_word.lower()
  src_phrase = ''
  prompt_lines = prompt_result.split('\n')

  word_phrase_list = []
  langs_already_in_list = set()

  for index, line in enumerate(prompt_lines):
    line_len = len(line)
    if line_len == 0:
      continue
    
    line_lang = openai_utils.replace_line_lang_if_wrong(openai_utils.get_lang_code_from_line(line).lower())
    line_content_parts = openai_utils.extract_phrases_from_line(line)
    line_content_parts_count = len(line_content_parts)

    if line_content_parts_count < 1 or line_content_parts_count > 2:
      raise ValueError("content not valid")

    if line_lang == src_lang:
      if index != 0:
        raise ValueError("src content not valid")
      else:
        src_phrase = crop_first_and_last_quote(line_content_parts[0])
        src_phrase = crop_period(src_phrase)
        if len(src_phrase) == 0:
          raise ValueError("not valid phrase len")

        if not is_phrase_legal(src_phrase, src_lang):
          raise ValueError("not valid phrase = illegal")

        src_phrase_words = text_to_words.text_to_words_1(src_phrase.lower(), src_lang)
        if src_lang != 'zh':
          if src_word not in src_phrase_words:
            add_disabled_word_to_db(db_conn, db_cur, src_lang, src_word)
            raise ValueError(f"ai identified word as not valid, or phrase not contains a word: {src_word}")
        
        if src_lang in langs_already_in_list:
          raise ValueError("duplicate languages")
        
        langs_already_in_list.add(src_lang)
        
        word_phrase_list.append(WordPhraseData(src_lang, src_word, src_lang, src_word, phrase=capitalize_first_char(src_phrase)))
    else:
      if index == 0:
        raise ValueError("dst content not valid")
      else:
        dst_phrase = crop_first_and_last_quote(line_content_parts[0])
        dst_phrase = crop_period(dst_phrase)
        dst_word = line_content_parts[1].lower()
        if len(dst_phrase) == 0 or len(dst_word) == 0:
          raise ValueError("not valid phrase or word len")
        if not is_word_legal(dst_word):
          raise ValueError("not valid word")
        
        if not is_phrase_legal(dst_phrase, line_lang):
          raise ValueError("not valid phrase = illegal")
        
        line_lang = openai_utils.verify_or_replace_lang(line_lang)
        
        if len(line_lang) != 2:
          raise ValueError("not valid language length")
        
        if line_lang in langs_already_in_list:
          raise ValueError("duplicate languages")
        
        langs_already_in_list.add(line_lang)
        
        word_phrase_list.append(WordPhraseData(src_lang, src_word, line_lang, dst_word, phrase=capitalize_first_char(dst_phrase)))
  remove_disabled_word_from_db(db_conn, db_cur, src_lang, src_word)
  return word_phrase_list


# OpenAI 2.0
def openai_get_word_phrase(src_lang, src_word, target_lang):
  system_prompt = "I give you a word in '', you must create phrase in " + src_lang + " language with it, and translate this phrase to " + target_lang + " language and also exclude word translation from this phrase, output should look like " + src_lang + ": {phrase in braces} and for each language one row lang:{phrase in braces}; {translated word in braces}"
  messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": src_word}
  ]

  # client = OpenAI()
  
  client = OpenAI(timeout=httpx.Timeout(15.0, read=5.0, write=10.0, connect=3.0))


  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
  )

  return completion.choices[0].message.content

# OpenAI
def openai_get_phrases_and_words(src_lang, src_word, target_langs):
  system_prompt = "I give you a word in '', you must create phrase in " + src_lang + " language with it, and translate this phrase to each language [" + target_langs + "] and also translate word for each language, output should look like " + src_lang + ": {phrase in braces} and for each language one row lang:{phrase in braces}; {translated word in braces}"
  messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": src_word}
  ]

  # client = OpenAI()
  
  client = OpenAI(timeout=httpx.Timeout(15.0, read=5.0, write=10.0, connect=3.0))


  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
  )

  return completion.choices[0].message.content


periods = ['。', '.']


class ExceptionOpenAI(Exception):
    pass

error_count = 0
success_count = 0
process_lock = threading.Lock()

def process_words(db_conn, db_cur, words, src_lang, langs):
  global success_count
  global error_count
  # for src_lang in langs:
  #   if src_lang != 'es':
  #     continue

  target_langs_array = [lang for lang in langs if lang != src_lang]
  current_prompt_target_langs = ', '.join(target_langs_array)

  for src_word in words:
    skip = is_all_langs_for_word_in_db(db_cur, langs, src_lang, src_word)
    
    if get_disabled_word_count(db_cur, src_lang, src_word) > 1:
      skip = True
    
    if skip:
      # print("-- already exists (skip) word: ", src_word)
      continue

    prompt_response = ''
    
    try:
      prompt_response = openai_get_phrases_and_words(openai_utils.replace_lang_for_ai(src_lang), src_word, current_prompt_target_langs)
    except Exception as e:
      raise ExceptionOpenAI(e)
    
    print(prompt_response)
    prompt_parsed_status = False

    try:
      result_word_phrases = process_word_phrase_prompt_result(db_conn, db_cur, src_lang, src_word, prompt_response)
      prompt_parsed_status = len(result_word_phrases) == len(langs)
      
      if prompt_parsed_status:
        for wp in result_word_phrases:
          if wp.phrase[-1] in periods:
            wp.phrase = wp.phrase[:-1]
          add_phrase_to_db(db_conn, db_cur, wp)
        print(Back.GREEN + "PROCESS SUCCESSFULL")
        with process_lock:
          success_count += 1
    except psycopg2.Error as e:
      print("Database Execution happened:", e)
      db_conn.rollback()
      with process_lock:
        error_count += 1
    except Exception as e:
      print(Back.RED + 'process failed: ', e)
      prompt_parsed_status = False
      with process_lock:
          error_count += 1

    try:
      add_prompt_result_to_db(db_conn, db_cur, src_lang, src_word, current_prompt_target_langs, prompt_response, prompt_parsed_status)
    except psycopg2.Error as e:
      print("Database Execution happened:", e)
      db_conn.rollback()
      # exit(1)


target_langs_to_translate_langs = {
  'en': {'es', 'pt', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'tr', 'ab'},
  'es': {'en', 'pt', 'fr', 'it', 'ru', 'zh'},
  'fr': {'en', 'es', 'pt', 'de', 'it', 'ru', 'zh', 'ja', 'ab'},
  'de': {'en', 'es', 'pt', 'fr', 'it', 'ru', 'tr', 'ab'},
  'ja': {'en', 'zh'},
  'ko': {'en', 'zh', 'ja'},
  'it': {'en', 'es', 'pt', 'fr', 'de', 'zh'},
  'hi': {'en'},
  'zh': {'en', 'ja'},
  'pt': {'en', 'es', 'fr'},
  'ru': {'en', 'es', 'tr'},
  'ab': {'en'}
}

langs = ['en', 'es', 'it', 'pt', 'fr', 'de', 'ru', 'zh']

words = file_to_text.read_text_file(input_file).lower().split('\n')
print("words count: ", len(words))

conn_params = {
  'dbname':'svocab_ai_translations',
  'user':'svocab_ai_translator',
  'password':'12345'
}

pool_len = 20

open_ai_error_counter = 0
lock = threading.Lock()

def process_words_th(conn_params, words, src_lang, langs):
  global open_ai_error_counter
  global success_count
  global error_count
  

  conn = psycopg2.connect(**conn_params)

  try:
    with conn.cursor() as cur:
      process_words(conn, cur, words, src_lang, langs)
      print("finished---")
  except ExceptionOpenAI as e:
    print(Back.RED + "open ai exception: ", "(", open_ai_error_counter, ")", e)
    print(f"success count: {success_count}; error count: {error_count}")
    os._exit(1)

    # with lock:
    #   open_ai_error_counter += 1

    # if open_ai_error_counter > pool_len * 0.4:
    #   print("success count: ", success_count)
    #   print("error count: ", error_count)
    #   os._exit(1)
    
    # conn.close()
    # sys.exit(1)
  except Exception as e:
    print(Back.RED + "got error: ", e)
  finally:
    conn.close()

def main():

  chunk_size = len(words) // pool_len
  chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
  
  threads = []
  for chunk in chunks:
      t = threading.Thread(target=process_words_th, args=(conn_params, chunk, src_lang, langs))
      threads.append(t)
      t.start()

  for t in threads:
      t.join()

  # with multiprocessing.Pool(processes=pool_len) as pool:
  #   pool.starmap(process_words_th, [(conn_params, chunk, langs) for chunk in chunks])

if __name__ == "__main__":
  main()




# # Close the cursor and connection for postgresql
# db_cur.close()
# db_conn.close()




