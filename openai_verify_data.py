import re
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

def get_word_phrases_from_db(db_cur) -> list[WordPhraseData]:
    sql = """SELECT lang, word_en_key, word, phrase
        FROM words_phrase"""

    db_cur.execute(sql)

    rows = db_cur.fetchall()

    word_phrase_list = []


    for row in rows:
        # print(row[0] + ' --- ' + row[1] + ' --- ' + row[2] + ' --- ' + row[3])
        word_phrase = WordPhraseData(row[0], row[1], row[2], row[3])
        word_phrase_list.append(word_phrase)
    
    return word_phrase_list


word_phrases = get_word_phrases_from_db(db_cur)

def word_phrase_to_str(word_phrase: WordPhraseData):
   return word_phrase.lang + '* *' + word_phrase.word_en_key + '* *' + word_phrase.word + '* *' + word_phrase.phrase + '*'



unique_not_alphas = set()
def update_not_alphas(s):
    for char in s:
        if not char.isalpha():
            unique_not_alphas.add(char)


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

not_valid_word_en_keys = set()

count_rows = 0
count_substr = 0
for word_phrase in word_phrases:
    count_rows += 1
    if word_phrase.word in word_phrase.phrase:
        count_substr += 1
    # update_not_alphas(word_phrase.phrase)
    # if not is_word_legal(word_phrase.word):
    #     not_valid_word_en_keys.add(word_phrase.word_en_key)
    #     continue
    
    # if not is_phrase_legal(word_phrase.phrase, word_phrase.lang):
    #     not_valid_word_en_keys.add(word_phrase.word_en_key)
    #     print(word_phrase_to_str(word_phrase))

print(count_rows)
print(count_substr)


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