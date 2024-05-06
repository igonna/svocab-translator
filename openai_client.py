import re
from openai import OpenAI
import psycopg2

db_conn = psycopg2.connect(
  dbname="svocab_ai_translations",
  user="svocab_ai_translator",
  password="12345",
)

db_cur = db_conn.cursor()

class WordPhraseData:
  def __init__(self, lang, word_en_key, word, phrase):
    self.lang = lang
    self.word_en_key = word_en_key
    self.word = word
    self.phrase = phrase

def add_phrase_to_db(word_phrase_data: WordPhraseData):
  sql = """
    INSERT INTO words_phrase (lang, word_en_key, word, phrase)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (lang, word_en_key, word) DO UPDATE
    SET phrase = EXCLUDED.phrase
  """
  data = (word_phrase_data.lang, word_phrase_data.word_en_key, word_phrase_data.word, word_phrase_data.phrase)
  db_cur.execute(sql, data)
  db_conn.commit()

def add_prompt_result_to_db(src_lang, src_word, target_langs, prompt_response, process_success_status):
  sql = """
    INSERT INTO prompt_response (src_lang, src_word, target_langs, prompt_response, process_success)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (src_lang, src_word, target_langs) DO UPDATE
    SET prompt_response = EXCLUDED.prompt_response, process_success = EXCLUDED.process_success
  """

  data = (src_lang, src_word, target_langs, prompt_response, process_success_status)
  db_cur.execute(sql, data)
  db_conn.commit()


def get_word_phrase_from_db(lang, word, word_en_key=''):
  sql = """
    SELECT lang, word_en_key, word, phrase
    FROM words_phrase
    WHERE lang = %s AND """ + ("word = %s" if word_en_key == '' else "(word_en_key = %s OR word = %s)") + """
    LIMIT 1
  """

  print(sql)
  data = (lang, word) if word_en_key == '' else (lang, word_en_key, word)
  db_cur.execute(sql, data)
  row = db_cur.fetchone()

  if row is None:
    return None
  
  return WordPhraseData(row[0], row[1], row[2], row[3])

def is_all_langs_for_word_in_db(langs, word, word_en_key=''):
  print(word_en_key)
  exists_count = 0
  for lang in langs:
    result = get_word_phrase_from_db(lang, word, word_en_key)
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

def process_word_phrase_prompt_result(src_lang, src_word, prompt_result) -> list[WordPhraseData]:
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
        src_phrase = line_content_parts[0]
        if len(src_phrase) == 0:
          raise ValueError("not valid phrase len")
        word_phrase_list.append(WordPhraseData(src_lang, word_en_key=src_word, word=src_word, phrase=src_phrase))
        # add_phrase_to_db(src_word, src_lang, src_word, src_phrase)
    else:
      if index == 0:
        raise ValueError("dst content not valid")
      else:
        dst_phrase = line_content_parts[0]
        dst_word = line_content_parts[1].lower()
        if len(dst_phrase) == 0 or len(dst_word) == 0:
          raise ValueError("not valid phrase or word len")
        word_phrase_list.append(WordPhraseData(line_lang, word_en_key=src_word, word=dst_word, phrase=dst_phrase))
        # add_phrase_to_db(src_word, line_lang, dst_word, dst_phrase)
  return word_phrase_list

# OpenAI
def openai_get_phrases_and_words(src_lang, src_word, target_langs):
  system_prompt = "I give you a word in '', you must create phrase in " + src_lang + " language with it, and translate this phrase to each language [" + target_langs + "] and also translate word for each language, output should look like " + src_lang + ": {phrase in braces} and for each language lang:{phrase in braces}; {translated word in braces}"
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


# prompt_response = '''en: {The princess is wearing a beautiful gown} 
# sp: {La princesa lleva un vestido hermoso}; {princesa} 
# it: {La principessa indossa un bellissimo abito}; {principessa} 
# pt: {A princesa está vestindo um lindo vestido}; {princesa} 
# fr: {La princesse porte une belle robe}; {princesse} 
# de: {Die Prinzessin trägt ein wunderschönes Kleid}; {Prinzessin} 
# ru: {Принцесса носит красивое платье}; {принцесса} 
# zh: {公主穿着一条漂亮的礼服}; {公主}'''

periods = ['。', '.']

langs = ['en', 'sp', 'it', 'pt', 'fr', 'de', 'ru', 'zh']
words = ['принцесса', 'курица']

for src_lang in langs:
  if src_lang != 'ru':
    continue

  target_langs_array = [lang for lang in langs if lang != src_lang]
  current_prompt_target_langs = ', '.join(target_langs_array)

  for src_word in words:
    skip = is_all_langs_for_word_in_db(langs, src_word, src_word if src_lang == 'en' else '')
    if skip:
      print("-- already exists (skip) word: ", src_word)
      continue

    prompt_response = openai_get_phrases_and_words(src_lang, src_word, current_prompt_target_langs)
    # print(prompt_response)
    prompt_parsed_status = False

    try:
      result_word_phrases = process_word_phrase_prompt_result(src_lang, src_word, prompt_response)
      prompt_parsed_status = len(result_word_phrases) == len(langs)
      
      if prompt_parsed_status:
        for wp in result_word_phrases:
          if wp.phrase[-1] in periods:
            wp.phrase = wp.phrase[:-1]
          add_phrase_to_db(wp)
    except psycopg2.Error as e:
      print("Database Execution happened:", e)
      exit(1)
    except:
      print('process failed')
      prompt_parsed_status = False

    try:
      add_prompt_result_to_db(src_lang, src_word, current_prompt_target_langs, prompt_response, prompt_parsed_status)
    except psycopg2.Error as e:
      print("Database Execution happened:", e)
      exit(1)


# Close the cursor and connection for postgresql
db_cur.close()
db_conn.close()