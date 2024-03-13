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