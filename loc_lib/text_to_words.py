import nltk
import os
import ssl

nltk_data_path = nltk.data.find('.')

if not os.path.exists(os.path.join(nltk_data_path, 'tokenizers/punkt')):
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

import jieba
import re
from konlpy.tag import Okt
# import nagisa


def _get_words_from_zh(text):
    words = jieba.cut(text)
    words = [word for word in words if re.match(r'^[\u4e00-\u9fa5]+$', word)]
    return words


one_len_words_by_language = {
    'en': ['a', 'i', 's'],
    'es': ['y', 'a', 'o'],
    'it': ['e', 'o', 'i'],
    'pt': ['e', 'o', 'a'],
    'fr': ['a', 'd'],
    'de': ['a', 'z'],
    'ru': ['и', 'в', 'я']
}

def _get_words_from_international(text, lang):
    clean_pattern = r'\b([^\w\'-])+\b'
    cleaned_text = re.sub(clean_pattern, ' ', text)
    pattern = r'\b(?:[А-Яа-яA-Za-z]+(?:[\'-]?[А-Яа-яA-Za-z]+)*)\b'
    words = re.findall(pattern, cleaned_text)
    words = [word for word in words if len(word) != 1 or word in one_len_words_by_language.get(lang, [])]
    return words

def _get_words_from_ko(text):
    okt = Okt()
    words = okt.morphs(text)
    words = [re.sub(r'[^가-힣]', '', word) for word in words]
    words = [word for word in words if word]
    return words

# def _get_words_from_ja(text):
#     doc = nagisa.tagging(text)
#     return doc.words


international_languages = ['en', 'es', 'it', 'pt', 'fr', 'de', 'ru']

def get_words_from_text(text, lang):
    if lang in international_languages:
        return _get_words_from_international(text.lower(), lang)
    elif lang == 'zh':
        return _get_words_from_zh(text)
    elif lang == 'ko':
        return _get_words_from_ko(text)
    
    


one_len_words_by_language = {
    'en': {'a', 'i'},
    'es': {'y', 'o', 'u'},
    'it': {'a', 'e', 'o'},
    'pt': {'a', 'e', 'o'},
    'fr': {'à', 'c', 'ù'},
    'de': {'a', 'u', 'o'},
    'ru': {'и', 'а', 'у'}
}


words_to_remove_by_language = {
    'en': {"the", "a", "an"},
    'es': {"el", "la", "los", "las", "un", "una", "unos", "unas"},
    'it': {"il", "la", "i", "le", "un", "una", "dei", "delle"},
    'pt': {"o", "a", "os", "as", "um", "uma", "uns", "umas"},
    'fr': {"le", "la", "les", "un", "une", "des"},
    'de': {"der", "die", "das", "die", "ein", "eine", "einen", "einem", "einer", "eines", "einige", "einigen", "einiger"},
}


continue_word_chars = {'—', '-','–'}
single_quotes_chars = {'\'', "'"}
new_line_char = '\n'

def clean_word(word):
    if len(word) <= 1:
        return word
    
    start = 0
    while start < len(word) and not word[start].isalpha():
        start += 1
    
    end = len(word) - 1
    while end >= 0 and not word[end].isalpha():
        end -= 1

    return word[start:end + 1]
    
def text_to_words_1(text, lang):
    text += ' '
    words_counts = {}
    add_word = lambda key: words_counts.update({key: words_counts.get(key, 0) + 1})
    
    current_word = ''
    prev_char = ''
    
    for char in text:
        if char.isalpha() or (char in single_quotes_chars and len(current_word) != 0) or char in continue_word_chars:
            current_word += char
        else:
            if len(current_word) != 0:
                if char == new_line_char and prev_char in continue_word_chars:
                    if current_word[-1] in continue_word_chars:
                        current_word[:-1]
                else:
                # if not (char == new_line_char and prev_char in continue_word_chars):
                    current_word = clean_word(current_word)
                    
                    if lang in words_to_remove_by_language:
                        if current_word in words_to_remove_by_language[lang]:
                            current_word = ''
                    
                    word_len = len(current_word)
                    if word_len != 0:
                        if word_len == 1:
                            if lang in one_len_words_by_language:
                                if current_word in one_len_words_by_language[lang]:
                                    add_word(current_word)                                    
                                current_word = ''
                            else:                                
                                add_word(current_word)
                                current_word = ''
                        else:
                            add_word(current_word)
                            current_word = ''
        prev_char = char
    return words_counts



def text_contain_word(lang, text, word):
    if lang == 'zh':
        return word in text
    
    words = text_to_words_1(text.lower(), lang)
  
    if word.lower() in words:
        return True
    
    return False