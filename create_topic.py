import re
import loc_lib.file_to_text as file_to_text
import sys
import os
import loc_lib.text_to_words as text_to_words
import psycopg2
import json

arguments = sys.argv[1:]

if len(arguments) != 1:
    print("arguments count is not 1")
    exit(1)
    
class LangWordPhrase:
  def __init__(self, lang, word, phrase):
    self.lang = lang
    self.word = word
    self.phrase = phrase


def get_words_phrases_from_db(db_cur, src_lang, src_word) -> list[LangWordPhrase]:
  sql = """
    SELECT dst_lang, dst_word, phrase
    FROM words_phrase
    WHERE src_lang = %s AND src_word = %s
  """

  data = (src_lang, src_word)
  db_cur.execute(sql, data)
  
  rows = db_cur.fetchall()

  result = []
  for row in rows:
    result.append(LangWordPhrase(row[0], row[1], row[2]))

  return result

def get_dst_langs(db_cur, src_lang):
  sql = """
    SELECT DISTINCT dst_lang
    FROM words_phrase
    WHERE src_lang = %s
  """

  data = (src_lang,)
  db_cur.execute(sql, data)
  rows = db_cur.fetchall()
  
  result = []
  for row in rows:
    result.append(row[0])
  return result


input_file_with_words = os.path.expanduser(arguments[0])


translations_db_conn = psycopg2.connect(
  dbname="svocab_ai_translations",
  user="svocab_ai_translator",
)

translations_db_cur = translations_db_conn.cursor()

# svocab database
def add_topic_to_svocab_db(db_cur, db_conn, topic_tag, translation_type, title_translations, supported_langs, popularity):
  sql = f"""INSERT INTO vocab_data.topics (topic_tag, translation_type, title_translations, supported_langs, popularity) 
  VALUES (%s, %s, %s, %s, %s)
  ON CONFLICT (topic_tag)
  DO UPDATE SET
    cur_version = vocab_data.topics.cur_version + 1,
    translation_type = EXCLUDED.translation_type,
    title_translations = EXCLUDED.title_translations,
    supported_langs = EXCLUDED.supported_langs,
    popularity = EXCLUDED.popularity;
  """
  data = (
    topic_tag,
    translation_type,
    json.dumps(title_translations),
    supported_langs,
    popularity
  )
  
  db_cur.execute(sql, data)
  db_conn.commit()

# svocab database
def add_topic_content_to_svocab_db(db_cur, db_conn, topic_tag, lang_tag, content_parts, content_parts_sizes):
  sql = f"""INSERT INTO vocab_data.topic_content (topic_tag, lang_tag, content_parts, content_parts_sizes) 
  VALUES (%s, %s, %s, %s)
  ON CONFLICT(topic_tag, lang_tag)
  DO UPDATE SET
    cur_version = vocab_data.topic_content.cur_version + 1,
    content_parts = EXCLUDED.content_parts,
    content_parts_sizes = EXCLUDED.content_parts_sizes;
  """
  data = (
    topic_tag,
    lang_tag,
    content_parts,
    content_parts_sizes
  )
  
  db_cur.execute(sql, data)
  db_conn.commit()

def add_topic_content_translation_to_svocab_db(db_cur, db_conn, topic_tag, lang_tag, lang_translation_tag, content_parts):
  sql = f"""INSERT INTO vocab_data.topic_content_translation (topic_tag, lang_tag, lang_translation_tag, content_parts) 
  VALUES (%s, %s, %s, %s)
  ON CONFLICT(topic_tag, lang_tag, lang_translation_tag)
  DO UPDATE SET
    cur_version = vocab_data.topic_content_translation.cur_version + 1,
    content_parts = EXCLUDED.content_parts;
  """
  data = (
    topic_tag,
    lang_tag,
    lang_translation_tag,
    content_parts
  )
  
  db_cur.execute(sql, data)
  db_conn.commit()


src_lang = file_to_text.get_file_name_without_extension(input_file_with_words)
src_words = file_to_text.read_text_file(input_file_with_words).lower().split('\n')

dst_langs = get_dst_langs(translations_db_cur, src_lang)
dst_langs_len = len(dst_langs)

langs_topics = {}
langs_topics_sizes = {}

topic_parts_count = 2

for dst_lang in dst_langs:
  langs_topics[dst_lang] = []
  langs_topics_sizes[dst_lang] = []
  for _ in range(topic_parts_count):
    langs_topics[dst_lang].append('')
    langs_topics_sizes[dst_lang].append(0)

free_part_size = round(len(src_words) * 0.35)

for index, src_word in enumerate(src_words):
  words_phrases = get_words_phrases_from_db(translations_db_cur, src_lang, src_word)
  if len(words_phrases) != dst_langs_len:
    continue

  for word_phrase in words_phrases:
    langs_topics[word_phrase.lang][0 if index < free_part_size else 1] += word_phrase.word + '/' + word_phrase.phrase + ';'
    langs_topics_sizes[word_phrase.lang][0 if index < free_part_size else 1] += 1

# crop last symbols
for dst_lang in dst_langs:
  for index, _ in enumerate(langs_topics[dst_lang]):
    langs_topics[dst_lang][index] = langs_topics[dst_lang][index][:-1]


  
topic_tag = 'popular_words'
translation_type='one-to-many'
title_translations = {
  "en": "Popular words",
}
supported_langs = dst_langs
popularity = 100

svocab_db_conn = psycopg2.connect(
  dbname="svocab",
  user="svocab_manager",
)

svocab_db_cur = svocab_db_conn.cursor()

add_topic_to_svocab_db(svocab_db_cur, svocab_db_conn, topic_tag, translation_type, title_translations, supported_langs, popularity)


for dst_lang in dst_langs:
  if dst_lang == src_lang:
    add_topic_content_to_svocab_db(svocab_db_cur, svocab_db_conn, topic_tag, dst_lang, langs_topics[dst_lang], langs_topics_sizes[dst_lang])
  else:
    add_topic_content_translation_to_svocab_db(svocab_db_cur, svocab_db_conn, topic_tag, src_lang, dst_lang, langs_topics[dst_lang])



# for lang in langs_topics.keys():
#   file_to_text.write_text_to_file('/Users/c/Documents/test_output_dir/' + lang + '0.txt', langs_topics[lang][0])
  
  
# for lang in langs_topics.keys():
#   file_to_text.write_text_to_file('/Users/c/Documents/test_output_dir/' + lang + '1.txt', langs_topics[lang][1])