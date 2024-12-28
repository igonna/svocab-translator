
import re
import pycountry
from enum import Enum
from dataclasses import dataclass, field
from typing import List
from openai import OpenAI
import httpx
from langdetect import detect
from langdetect import detect_langs
import json
import http.client


def extract_language_codes_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            dart_code = file.read()
        
        regex = r"List<String>\s+languageCodes\s+=\s+\[(.*?)\];"
        match = re.search(regex, dart_code, re.DOTALL)

        if match:
            codes_string = match.group(1)
            language_codes = re.findall(r"'(.*?)'", codes_string)
            return language_codes
        else:
            raise ValueError("No language codes found in the provided Dart file.")

    except FileNotFoundError:
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except ValueError as e:
        raise e
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def get_language_name(language_code):
    try:
        language = pycountry.languages.get(alpha_2=language_code)
        clean_name = re.sub(r'\s*\(.*?\)', '', language.name)
        return clean_name
    except AttributeError:
        return language_code


not_translation_names = ['Google', 'YouTube', 'Google Play']

class PhraseType(Enum):
    DEFAULT = "default"
    PLURAL = "plural"
    VARIABLE = "variable"
    NOT_TRANSLATION_NAME = "not_translation_name"

def is_phrase_contains_not_translation_name(phrase: str):
    result = False
    for name in not_translation_names:
        if name.lower() in phrase.lower():
            result = True
            break
    return result

def get_phrase_not_translation_names(phrase: str):
    phrase_not_translation_names = []
    for name in not_translation_names:
        if name.lower() in phrase.lower():
            phrase_not_translation_names.append(name)
    return phrase_not_translation_names

def get_phrase_without_not_translation_names(phrase: str):
    result_phrase = phrase.lower()
    for name in not_translation_names:
        name_parts = name.lower().split(' ')
        for name_part in name_parts:
            if name_part in result_phrase:
                result_phrase = result_phrase.replace(name_part, '')
    return result_phrase

def get_phrase_type(phrase):
    if re.search(r'\bplural\b', phrase) and re.search(r'[{}]', phrase):
        return PhraseType.PLURAL
    elif not re.search(r'\bplural\b', phrase) and re.search(r'[{}]', phrase):
        return PhraseType.VARIABLE
    elif is_phrase_contains_not_translation_name(phrase):
        return PhraseType.NOT_TRANSLATION_NAME
    else:
        return PhraseType.DEFAULT

def extract_special_phrases_variables(phrases):
    special_data = {}
    for key in phrases:
        if key[0] == '@':
            variables = []
            placeholders = phrases[key]["placeholders"]
            for variable_name in placeholders:
                variables.append(variable_name)
            special_data[key[1:]] = variables
    return special_data

@dataclass
class PhraseInfo:
    is_phrase_for_translation: bool = True
    phrase_type: PhraseType = PhraseType.DEFAULT
    start_non_alpha_symbol: str = ''
    end_non_alpha_symbol: str = ''
    phrase_variables: List[str] = field(default_factory=list)
    phrase_not_translation_names: List[str] = field(default_factory=list)

def get_phrase_info(phrase_key: str, phrase: str, special_phrases_variables) -> PhraseInfo:
    phrase_variables = []
    phrase_not_translation_names = []
    if phrase_key[0] == '@':
        return PhraseInfo(is_phrase_for_translation=False, phrase_variables=phrase_variables, phrase_not_translation_names=phrase_not_translation_names)

    phrase_type = get_phrase_type(phrase)

    if (phrase_type == PhraseType.VARIABLE or phrase_type == PhraseType.PLURAL) and phrase_key in special_phrases_variables:
        phrase_variables = special_phrases_variables[phrase_key]
        
    if phrase_type == PhraseType.NOT_TRANSLATION_NAME:
        phrase_not_translation_names = get_phrase_not_translation_names(phrase)

    start_non_alpha_symbol = ''
    if len(phrase) > 0 and not phrase[0].isalpha():
        start_non_alpha_symbol = phrase[0]

    end_non_alpha_symbol = ''
    if len(phrase) > 0 and not phrase[-1].isalpha():
        end_non_alpha_symbol = phrase[-1]

    return PhraseInfo(
        phrase_type=phrase_type,
        start_non_alpha_symbol=start_non_alpha_symbol,
        end_non_alpha_symbol=end_non_alpha_symbol,
        phrase_variables=phrase_variables,
        phrase_not_translation_names=phrase_not_translation_names
    )
    

# database start
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


def get_preferred_phrase_from_db(db_cur, dst_lang, src_lang, src_phrase):
    sql = """
        SELECT dst_phrase
        FROM preferred_app_phrases
        WHERE src_lang = %s AND dst_lang = %s AND src_phrase = %s
        LIMIT 1
    """

    data = (src_lang, dst_lang, src_phrase)
    db_cur.execute(sql, data)
    row = db_cur.fetchone()

    if row is None:
        return None

    return row[0]

def get_phrase_from_db(db_cur, dst_lang, src_lang, src_phrase):
    sql = """
        SELECT dst_phrase
        FROM app_phrases
        WHERE src_lang = %s AND dst_lang = %s AND src_phrase = %s
        LIMIT 1
    """

    data = (src_lang, dst_lang, src_phrase)
    db_cur.execute(sql, data)
    row = db_cur.fetchone()

    if row is None:
        return None

    return row[0]



def list_to_string(l):
    result = ''
    count = 0
    
    for i in l:
        if count > 0:
            result += ', '
        result += i
        count += 1
    
    return result


# OpenAI phrase translation
def openai_prompt_exec(prompt):
    messages = [
        {"role": "user", "content": prompt}
    ]

    client = OpenAI(timeout=httpx.Timeout(15.0, read=5.0, write=10.0, connect=3.0))

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    return completion.choices[0].message.content


def openai_default_phrase_translation(src_phrase, dst_lang):
    prompt = 'translate this English android app phrase "' + src_phrase + '" in formal way to ' + dst_lang + ', output this only as json {"translated_phrase": ""}'
    return openai_prompt_exec(prompt)

def openai_default_phrase_is_of_lang(src_phrase, dst_phrase, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' ' + dst_phrase + ' a possible translation for English ' + src_phrase + ', output only yes or no'
    result = openai_prompt_exec(prompt)
    return 'yes' in result.lower()


def openai_variable_phrase_translation(src_phrase, dst_lang):
    prompt = 'translate this English flutter app phrase with variables "' + src_phrase + '" in formal way to ' + dst_lang + ' with all variables remain the same, output this only as json {"translated_phrase": ""}'
    return openai_prompt_exec(prompt)

def openai_variable_phrase_is_of_lang(src_phrase, dst_phrase, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' "' + dst_phrase + '" a possible translation for English "' + src_phrase + '" with flutter variables, output only yes or no'
    result = openai_prompt_exec(prompt)
    return 'yes' in result.lower()


def openai_plural_phrase_translation(src_phrase, dst_lang):
    prompt = 'translate this English flutter app phrase with pluralization "' + src_phrase + '" in formal way to ' + dst_lang + ' with all variables remain the same, output this only as json {"translated_phrase": ""}'
    return openai_prompt_exec(prompt)

def openai_plural_phrase_is_of_lang(src_phrase, dst_phrase, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' "' + dst_phrase + '" a possible translation for English "' + src_phrase + '" with flutter pluralization variables, output only yes or no'
    result = openai_prompt_exec(prompt)
    return 'yes' in result.lower()


def is_entire_phrase_not_translation(phrase: str):
    result = False
    for name in not_translation_names:
        if phrase.lower() == name.lower():
            return True
    return result

def openai_not_translation_name_phrase_translation(src_phrase, phrase_info: PhraseInfo, dst_lang_name):
    if (is_entire_phrase_not_translation(src_phrase)):
        return json.dumps({"translated_phrase": src_phrase})

    what_to_not_translate = list_to_string(phrase_info.phrase_not_translation_names)
    prompt = 'translate this English android app phrase "' + src_phrase + '" in formal way to ' + dst_lang_name + ' but do not translate ' + what_to_not_translate + ', output this only as json {"translated_phrase": ""}'
    return openai_prompt_exec(prompt)

# prompt extraction
def extract_phrase_from_prompt(prompt):
    try:
        clean_prompt = prompt.strip("```json ").strip("```")
        json_object = json.loads(clean_prompt)
        extracted_phrase = json_object.get("translated_phrase", "")
        
        if "translated_phrase" in extracted_phrase or "translated phrase" in extracted_phrase:
            return ""

        return extracted_phrase
    except:
        return ""

def remove_periods_from_end(s):
    while s and s[-1] == '.':
        s = s[:-1]
    return s

def is_phrase_contains_braces(phrase: str):
    return phrase.count('{') > 0 and phrase.count('}') > 0

def is_phrase_braces_valid(phrase: str):
    if not is_phrase_contains_braces(phrase):
        return False

    return phrase.count('{') == phrase.count('}')

def is_plural_phrase_valid(phrase: str, variables):
    if not is_phrase_braces_valid(phrase):
        return False

    if 'plural' not in phrase:
        return False
    
    for variable in variables:
        if variable not in phrase:
            return False

    return True

def is_not_translation_phrase_valid(translated_phrase, phrase_info: PhraseInfo):
    result = True
    
    for name in phrase_info.phrase_not_translation_names:
        if name.lower() not in translated_phrase.lower():
            return False

    return result

def is_variable_phrase_valid(phrase: str, variables):
    if not is_phrase_braces_valid(phrase):
        return False
    
    for variable in variables:
        if variable not in phrase:
            return False

    return True

def double_single_quotes(phrase: str):
    return phrase.replace("'", "''")

def make_dst_phrase_look_the_same(src_phrase: str, dst_phrase: str):
    if src_phrase[0].isupper():
        dst_phrase = dst_phrase.capitalize()

    if src_phrase[-1] != '.':
        dst_phrase = remove_periods_from_end(dst_phrase)

    if src_phrase[-1] == ' ' and dst_phrase[-1] != ' ':
        dst_phrase += ' '
    return dst_phrase


def make_dst_not_translation_names_phrase_look_the_same(translated_phrase: str, phrase_info: PhraseInfo):
    for name in phrase_info.phrase_not_translation_names:
        translated_phrase = re.sub(re.escape(name), name, translated_phrase, flags=re.IGNORECASE)

    language_specific_not_translation_names_exception = {
        'یوٹیوب' : 'YouTube ',
        'यूट्यूब': 'YouTube ',
        'गुगल': 'Google ',
        'கூகிள்': 'Google ',
        'கூகுள்': 'Google ',
        'யூடியூப்': 'YouTube ',
        'গুগল': 'Google ',
        'ইউটিউব': 'YouTube ',
        'યુટ્યુબ': 'YouTube ',
        'ગૂગલ': 'Google ',
        'گوگل': 'Google ',
        'یوتیوب': 'YouTube',
        'గూగుల్': 'Google ',
        'యూట్యూబ్': 'YouTube ',
        'गूगल': 'Google ',
        'ഗൂഗിൾ': 'Google ',
        'ഗൂഗിളു': 'Google ',
        'യൂട്യൂബ്': 'YouTube ',
        'ಗೂಗಲ್': 'Google ',
        'ಗುಗಲ್ೊಂ': 'Google ',
        'ಯುಟ್ಯೂಬ್': 'YouTube '
    }

    for lang_exception in language_specific_not_translation_names_exception:
        if lang_exception in translated_phrase:
            translated_phrase = translated_phrase.replace(lang_exception, language_specific_not_translation_names_exception[lang_exception])
            translated_phrase = translated_phrase.replace('  ', ' ')

    return translated_phrase


def get_phrase_without_variables_and_plural(phrase, variables):
    words_to_remove = ['plural', 'other']
    words_to_remove = words_to_remove + variables
    for word_to_remove in words_to_remove:
        phrase = phrase.replace(word_to_remove,'')
    return phrase


def local_server_is_phrase_language_valid(phrase, phrase_info: PhraseInfo, lang_code):
    phrase_without_variables = get_phrase_without_variables_and_plural(phrase, phrase_info.phrase_variables)

    if phrase_info.phrase_type == PhraseType.NOT_TRANSLATION_NAME:
        phrase_without_variables = get_phrase_without_not_translation_names(phrase_without_variables)

    conn = http.client.HTTPConnection("localhost", 48499)
    headers = {'langCode': lang_code}
    data = phrase_without_variables.encode('utf-8')
    conn.request("POST", "/is_valid_phrase_langauge", body=data, headers=headers)

    response = conn.getresponse()
    
    if response.status not in (200, 422):
        raise Exception(f"something went wrong when calling local server, code: {response.status}")

    conn.close()
    return response.status == 200