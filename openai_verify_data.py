import re
import psycopg2
import loc_lib.text_to_words as text_to_words

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
    
    
class NewWordPhraseData:
  def __init__(self, src_lang, src_word, dst_lang, dst_word, phrase):
    self.src_lang = src_lang
    self.src_word = src_word
    self.dst_lang = dst_lang
    self.dst_word = dst_word
    self.phrase = phrase

def get_word_phrases_from_db(db_cur) -> list[NewWordPhraseData]:
    sql = """SELECT src_lang, src_word, dst_lang, dst_word, phrase FROM words_phrase"""

    db_cur.execute(sql)

    rows = db_cur.fetchall()

    word_phrase_list = []


    for row in rows:
        # print(row[0] + ' --- ' + row[1] + ' --- ' + row[2] + ' --- ' + row[3])
        word_phrase = NewWordPhraseData(row[0], row[1], row[2], row[3], row[4])        
        word_phrase_list.append(word_phrase)
    
    return word_phrase_list



def word_phrase_to_str(word_phrase: WordPhraseData):
   return word_phrase.lang + '* *' + word_phrase.word_en_key + '* *' + word_phrase.word + '* *' + word_phrase.phrase + '*'



def add_new_phrase_to_db(db_conn, db_cur, word_phrase_data: NewWordPhraseData):
  sql = """
    INSERT INTO words_phrase (src_lang, src_word, dst_lang, dst_word, phrase)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (src_lang, src_word, dst_lang, dst_word) DO UPDATE
    SET phrase = EXCLUDED.phrase
  """
  data = (word_phrase_data.src_lang, word_phrase_data.src_word, word_phrase_data.dst_lang, word_phrase_data.dst_word, word_phrase_data.phrase)
  db_cur.execute(sql, data)
  db_conn.commit()


not_valid_word_en_keys = set()

count_phrases = 0
total_count_phrases = 0

word_phrases = get_word_phrases_from_db(db_cur)

def capitalize_first_char(s):
    if len(s) > 0:
        return s[0].upper() + s[1:]
    else:
        return s
    
    
# def add_phrase_to_db(db_conn, db_cur, word_phrase_data: WordPhraseData):
#   sql = """
#     INSERT INTO words_phrase (lang, word_en_key, word, phrase)
#     VALUES (%s, %s, %s, %s)
#     ON CONFLICT (lang, word_en_key, word) DO UPDATE
#     SET phrase = EXCLUDED.phrase
#   """
#   data = (word_phrase_data.lang, word_phrase_data.word_en_key, word_phrase_data.word, word_phrase_data.phrase)
#   db_cur.execute(sql, data)
#   db_conn.commit()

for word_phrase in word_phrases:
  if word_phrase.src_lang == word_phrase.dst_lang:
    continue
  if word_phrase.src_word == word_phrase.dst_word:
    continue
  if text_to_words.text_contain_word(word_phrase.dst_lang, word_phrase.phrase, word_phrase.dst_word):
    print(word_phrase.phrase, ' **** ', word_phrase.dst_word)
    total_count_phrases += 1
    
  
  
  # add_new_phrase_to_db(db_conn, db_cur, dt)
  # words = text_to_words.text_to_words_1(word_phrase.phrase.lower(), word_phrase.lang)
  # if word_phrase.word not in words:
  #   print(word_phrase.phrase, ' *** ', word_phrase.word)
  #   print(words.keys())
  #   print()
  #   count_phrases += 1
  #   not_valid_word_en_keys.add(word_phrase.word_en_key)

  #   count_phrases += 1

    # crop_period(word_phrase.phrase)
    # if word_phrase.word in word_phrase.phrase:
    #     count_substr += 1




# phrase = 'I did my homework'

# print(phrase)
# print(text_to_words.text_to_words_1(phrase.lower(), 'en').keys())

# print(total_count_phrases)
print(total_count_phrases)

# print(not_valid_word_en_keys)


# print(len(not_valid_word_en_keys))
# print(unique_not_alphas)




# def delete_word_en_keys(db_cur, db_conn, word_en_key):
#     sql_delete_row = "DELETE FROM words_phrase WHERE word_en_key = %s"
#     db_cur.execute(sql_delete_row, (word_en_key,))
#     db_conn.commit()
    
# for not_valid_word in not_valid_word_en_keys:
#     delete_word_en_keys(db_cur, db_conn, not_valid_word)


db_cur.close()
db_conn.close()