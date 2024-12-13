
import re
import pycountry
from enum import Enum
from dataclasses import dataclass, field
from typing import List
from openai import OpenAI
import httpx


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


class PhraseType(Enum):
    DEFAULT = "default"
    PLURAL = "plural"
    VARIABLE = "variable"

def get_phrase_type(phrase):
    if re.search(r'\bplural\b', phrase) and re.search(r'[{}]', phrase):
        return PhraseType.PLURAL
    elif not re.search(r'\bplural\b', phrase) and re.search(r'[{}]', phrase):
        return PhraseType.VARIABLE
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

def get_phrase_info(phrase_key: str, phrase: str, special_phrases_variables) -> PhraseInfo:
    if phrase_key[0] == '@':
        return PhraseInfo(is_phrase_for_translation=False)

    phrase_type = get_phrase_type(phrase)

    phrase_variables = field(default_factory=list)
    if (phrase_type == PhraseType.VARIABLE or phrase_type == PhraseType.PLURAL) and phrase_key in special_phrases_variables:
        phrase_variables = special_phrases_variables[phrase_key]

    start_non_alpha_symbol = ''
    if not phrase[0].isalpha():
        start_non_alpha_symbol = phrase[0]

    end_non_alpha_symbol = ''
    if not phrase[-1].isalpha():
        end_non_alpha_symbol = phrase[-1]

    return PhraseInfo(
        phrase_type=phrase_type,
        start_non_alpha_symbol=start_non_alpha_symbol,
        end_non_alpha_symbol=end_non_alpha_symbol,
        phrase_variables=phrase_variables
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


def get_phrase_from_db(db_cur, dst_lang, src_lang, src_phrase):
  sql = """
    SELECT src_phrase
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
    prompt = 'This is flutter app phrase "' + src_phrase + '" translate it to ' + dst_lang + ' output only as "translated phrase"'
    return openai_prompt_exec(prompt)

def openai_variable_phrase_translation(src_phrase, dst_lang):
    prompt = 'This is flutter app phrase with variables "' + src_phrase + '" translate it to ' + dst_lang + ' with all variables remain the same, output only as "translated phrase"'
    return openai_prompt_exec(prompt)

def openai_plural_phrase_translation(src_phrase, dst_lang):
    prompt = 'This is flutter app phrase which uses pluralization "' + src_phrase + '" translate it to ' + dst_lang + '  with all variables remain the same, output only as "translated phrase"'
    return openai_prompt_exec(prompt)


# prompt extraction
def extract_phrase_from_prompt(prompt):
    return re.findall(r'"(.*?)"', prompt)

def contains_double_quotes(text):
    return '"' in text