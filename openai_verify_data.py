# import re
# import psycopg2
# import loc_lib.text_to_words as text_to_words

# db_conn = psycopg2.connect(
#   dbname="svocab_ai_translations",
#   user="svocab_ai_translator",
#   password="12345",
# )

# db_cur = db_conn.cursor()

# class WordPhraseData:
#   def __init__(self, lang, word_en_key, word, phrase):
#     self.lang = lang
#     self.word_en_key = word_en_key
#     self.word = word
#     self.phrase = phrase
    
    
# class NewWordPhraseData:
#   def __init__(self, src_lang, src_word, dst_lang, dst_word, phrase):
#     self.src_lang = src_lang
#     self.src_word = src_word
#     self.dst_lang = dst_lang
#     self.dst_word = dst_word
#     self.phrase = phrase

# def get_word_phrases_from_db(db_cur) -> list[NewWordPhraseData]:
#     sql = """SELECT src_lang, src_word, dst_lang, dst_word, phrase FROM words_phrase"""

#     db_cur.execute(sql)

#     rows = db_cur.fetchall()

#     word_phrase_list = []


#     for row in rows:
#         # print(row[0] + ' --- ' + row[1] + ' --- ' + row[2] + ' --- ' + row[3])
#         word_phrase = NewWordPhraseData(row[0], row[1], row[2], row[3], row[4])        
#         word_phrase_list.append(word_phrase)
    
#     return word_phrase_list



# def word_phrase_to_str(word_phrase: WordPhraseData):
#    return word_phrase.lang + '* *' + word_phrase.word_en_key + '* *' + word_phrase.word + '* *' + word_phrase.phrase + '*'



# def add_new_phrase_to_db(db_conn, db_cur, word_phrase_data: NewWordPhraseData):
#   sql = """
#     INSERT INTO words_phrase (src_lang, src_word, dst_lang, dst_word, phrase)
#     VALUES (%s, %s, %s, %s, %s)
#     ON CONFLICT (src_lang, src_word, dst_lang, dst_word) DO UPDATE
#     SET phrase = EXCLUDED.phrase
#   """
#   data = (word_phrase_data.src_lang, word_phrase_data.src_word, word_phrase_data.dst_lang, word_phrase_data.dst_word, word_phrase_data.phrase)
#   db_cur.execute(sql, data)
#   db_conn.commit()
  
  
# def get_duplicates_db(db_conn, db_cur):
#   sql = """SELECT src_word, dst_lang, COUNT(*)
#     FROM words_phrase
#     WHERE src_lang IN ('sp', 'es')
#     GROUP BY src_word, dst_lang
#     HAVING COUNT(*) > 1;
#   """
#   db_cur.execute(sql)
#   results = db_cur.fetchall()
#   duplicates = [(row[0], row[1]) for row in results]

#   return duplicates


# not_valid_word_en_keys = set()

# count_phrases = 0
# total_count_phrases = 0

# word_phrases = get_word_phrases_from_db(db_cur)

# def capitalize_first_char(s):
#     if len(s) > 0:
#         return s[0].upper() + s[1:]
#     else:
#         return s
    


# # def add_new_phrase_to_db(db_conn, db_cur, word_phrase_data: NewWordPhraseData):
# #   sql = """
# #     INSERT INTO words_phrase (src_lang, src_word, dst_lang, dst_word, phrase)
# #     VALUES (%s, %s, %s, %s, %s)
# #     ON CONFLICT (src_lang, src_word, dst_lang, dst_word) DO UPDATE
# #     SET phrase = EXCLUDED.phrase
# #   """
# #   data = (word_phrase_data.src_lang, word_phrase_data.src_word, word_phrase_data.dst_lang, word_phrase_data.dst_word, word_phrase_data.phrase)
# #   db_cur.execute(sql, data)
# #   db_conn.commit()
  
    
# # def remove_duplicate_db(db_conn, db_cur, duplicate_src_word):
# #   sql = """
# #     DELETE FROM words_phrase where src_lang = 'sp' and src_word=%s
# #   """
# #   data = (duplicate_src_word,)

# #   db_cur.execute(sql, data)
# #   db_conn.commit()


# # duplicates = get_duplicates_db(db_conn, db_cur)
# # print(len(duplicates))

# # for duplicate in duplicates:
# #   # print(duplicate)
# #   remove_duplicate_db(db_conn, db_cur, duplicate[0])
# #   # break



# # def add_phrase_to_db(db_conn, db_cur, word_phrase_data: WordPhraseData):
# #   sql = """
# #     INSERT INTO words_phrase (lang, word_en_key, word, phrase)
# #     VALUES (%s, %s, %s, %s)
# #     ON CONFLICT (lang, word_en_key, word) DO UPDATE
# #     SET phrase = EXCLUDED.phrase
# #   """
# #   data = (word_phrase_data.lang, word_phrase_data.word_en_key, word_phrase_data.word, word_phrase_data.phrase)
# #   db_cur.execute(sql, data)
# #   db_conn.commit()

# def is_word_in_db(db_cur, word, lang):
#   query = "SELECT 1 FROM words_phrase WHERE src_lang=%s and src_word = %s LIMIT 1"
#   data = (word, lang)
#   db_cur.execute(query, data)
#   result = db_cur.fetchone()
#   return result

# for word_phrase in word_phrases:
#   if word_phrase.src_lang == word_phrase.dst_lang:
#     continue
  
#   if text_to_words.text_contain_word(word_phrase.dst_lang, word_phrase.phrase, word_phrase.dst_word):
#     if is_word_in_db(db_cur, word_phrase.dst_word, word_phrase.dst_lang):
#       continue
#     # print(word_phrase.phrase, ' **** ', word_phrase.dst_word)
#     total_count_phrases += 1
    
  
  
#   # add_new_phrase_to_db(db_conn, db_cur, dt)
#   # words = text_to_words.text_to_words_1(word_phrase.phrase.lower(), word_phrase.lang)
#   # if word_phrase.word not in words:
#   #   print(word_phrase.phrase, ' *** ', word_phrase.word)
#   #   print(words.keys())
#   #   print()
#   #   count_phrases += 1
#   #   not_valid_word_en_keys.add(word_phrase.word_en_key)

#   #   count_phrases += 1

#     # crop_period(word_phrase.phrase)
#     # if word_phrase.word in word_phrase.phrase:
#     #     count_substr += 1




# # phrase = 'I did my homework'

# # print(phrase)
# # print(text_to_words.text_to_words_1(phrase.lower(), 'en').keys())

# # print(total_count_phrases)
# print(total_count_phrases)

# # print(not_valid_word_en_keys)


# # print(len(not_valid_word_en_keys))
# # print(unique_not_alphas)




# # def delete_word_en_keys(db_cur, db_conn, word_en_key):
# #     sql_delete_row = "DELETE FROM words_phrase WHERE word_en_key = %s"
# #     db_cur.execute(sql_delete_row, (word_en_key,))
# #     db_conn.commit()
    
# # for not_valid_word in not_valid_word_en_keys:
# #     delete_word_en_keys(db_cur, db_conn, not_valid_word)


# db_cur.close()
# db_conn.close()



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

def add_word_phrase_pair_to_db(db_conn, db_cur, src_lang, dst_lang, src_word, dst_word, src_phrase, dst_phrase):
  sql = """
    INSERT INTO word_phrase_pair (src_lang, dst_lang, src_word, dst_word, src_phrase, dst_phrase)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (src_lang, dst_lang, src_word, dst_word) DO NOTHING
  """
  data = (src_lang, dst_lang, src_word, dst_word, src_phrase, dst_phrase)
  db_cur.execute(sql, data)
  db_conn.commit()

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

def get_src_word_phrase(words_phrases, src_lang) -> LangWordPhrase:
  for word_phrase in words_phrases:
    if word_phrase.lang == src_lang:
      return word_phrase
  return None

counter = 0
counter_per_lang = {}
counter_per_matches = {}
total_added = 0
total_skipped = 0

for index, src_word in enumerate(src_words):
  words_phrases = get_words_phrases_from_db(translations_db_cur, src_lang, src_word)
  src_word_phrase = get_src_word_phrase(words_phrases, src_lang)
  
  if src_word_phrase is None:
    total_skipped += 1
    print("errorr -- -- -- - ")
    continue
  
  # if len(words_phrases) != dst_langs_len:
  #   continue

  current_words_phrases_len = len(words_phrases) - 1

  current_crossing = 0
  for word_phrase in words_phrases:
    if word_phrase.lang == src_lang:
      continue
    phrase_words = text_to_words.get_words_from_text(word_phrase.phrase, word_phrase.lang)
    
    if word_phrase.phrase == src_word_phrase.phrase:
      total_skipped += 1
      continue
      
    if word_phrase.word in phrase_words:
      add_word_phrase_pair_to_db(translations_db_conn,
        translations_db_cur,
        src_lang,
        word_phrase.lang,
        src_word,
        word_phrase.word,
        src_word_phrase.phrase,
        word_phrase.phrase
      )
      total_added += 1
      current_crossing += 1
      if word_phrase.lang not in counter_per_lang:
        counter_per_lang[word_phrase.lang] = 1
      else:
        counter_per_lang[word_phrase.lang] += 1

  if current_crossing in counter_per_matches:
    counter_per_matches[current_crossing] += 1
  else:
    counter_per_matches[current_crossing] = 1

print("total words: ", len(src_words))
for lang_key in counter_per_lang.keys():
  print("containes word in phrase for lang (" + lang_key + ") total: ", counter_per_lang[lang_key])
  
for match_key in sorted(counter_per_matches.keys()):
  print("contains word in langs matches count (" + str(match_key) + ") total: ", counter_per_matches[match_key])
  
print("total skipped: ", total_skipped)
print("total added: ", total_added)

# crop last symbols
# for dst_lang in dst_langs:
#   for index, _ in enumerate(langs_topics[dst_lang]):
#     langs_topics[dst_lang][index] = langs_topics[dst_lang][index][:-1]

# for lang in langs_topics.keys():
#   file_to_text.write_text_to_file('/Users/c/Documents/test_output_dir/' + lang + '0.txt', langs_topics[lang][0])
  
  
# for lang in langs_topics.keys():
#   file_to_text.write_text_to_file('/Users/c/Documents/test_output_dir/' + lang + '1.txt', langs_topics[lang][1])