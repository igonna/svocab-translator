import loc_lib.file_to_text as file_to_text
import sys
from colorama import Back
import os
import json
import psycopg2
import colorama
import openai_translate_app_utils
import concurrent.futures

colorama.init(autoreset=True)

arguments = sys.argv[1:]

# get arguments && verify that valid paths
if len(arguments) != 1:
    print(Back.RED + "give me path to your project root")
    exit(1)

path_to_root = arguments[0]

l10n_exists = os.path.isdir(os.path.join(path_to_root, 'l10n'))
lib_exists = os.path.isdir(os.path.join(path_to_root, 'lib'))

if not l10n_exists or not lib_exists:
    print(Back.RED + "not valid path, root not contains l10n or lib directories")
    exit(1)

language_codes_file = os.path.expanduser(path_to_root) + '/lib/main.dart'
phrases_file = os.path.expanduser(path_to_root) + '/l10n/app_en.arb'
output_dir = os.path.expanduser(path_to_root) + '/l10n'

# extract phrases && language codes && get special_phrases_variables
phrases = {}
try:
    phrases = json.loads(file_to_text.read_text_file(phrases_file))
except Exception as e:
    print(f"Phrases parse error: {e}")
    exit(1)

language_codes = []
try:
    language_codes = openai_translate_app_utils.extract_language_codes_from_file(language_codes_file)
except Exception as e:
    print(f"Exctract language codes error: {e}")
    exit(1)
    
special_phrases_variables = openai_translate_app_utils.extract_special_phrases_variables(phrases)

# translate all phrases
src_lang_code = 'en'

src_phrases_count = len(phrases)

problematic_langs_count = {}
def increase_problematic_lang_count(lang_code):
    if lang_code in problematic_langs_count:
        problematic_langs_count[lang_code] += 1
    else:
        problematic_langs_count[lang_code] = 1

def create_language_file(dst_lang_code, db_conn, db_cur):
    dst_lang_name = openai_translate_app_utils.get_language_name(dst_lang_code)

    translated_phrase_count = 0
    dst_phrases = {}
    for phrase_key in phrases:
        src_phrase = phrases[phrase_key]
        phrase_info = openai_translate_app_utils.get_phrase_info(phrase_key, src_phrase, special_phrases_variables)
        
        if not phrase_info.is_phrase_for_translation:
            dst_phrases[phrase_key] = phrases[phrase_key]
            continue

        # preferred phrase
        preferred_phrase_translation_db = openai_translate_app_utils.get_preferred_phrase_from_db(db_cur, dst_lang_code, src_lang_code, src_phrase)

        if preferred_phrase_translation_db is not None:
            dst_phrases[phrase_key] = preferred_phrase_translation_db
            translated_phrase_count += 1
            continue

        # default phrase
        phrase_translation_db = openai_translate_app_utils.get_phrase_from_db(db_cur, dst_lang_code, src_lang_code, src_phrase)

        if phrase_translation_db is not None:
            dst_phrases[phrase_key] = phrase_translation_db
            translated_phrase_count += 1
            continue

        # generation required
        max_retry = 4
        retry_count = 0
        max_lang_errors = 2
        translated_phrase = ''
        was_not_valid_lang_error = False
        while(retry_count < max_retry and translated_phrase == ''):
            prompt_result = ''
            if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.DEFAULT:
                prompt_result = openai_translate_app_utils.openai_default_phrase_translation(src_phrase, dst_lang_name)
            elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.VARIABLE:
                prompt_result = openai_translate_app_utils.openai_variable_phrase_translation(src_phrase, dst_lang_name)
            elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.PLURAL:
                prompt_result = openai_translate_app_utils.openai_plural_phrase_translation(src_phrase, dst_lang_name)
            elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.NOT_TRANSLATION_NAME:
                prompt_result = openai_translate_app_utils.openai_not_translation_name_phrase_translation(src_phrase, phrase_info, dst_lang_name)

            print(f"prompt result: {prompt_result}")
            translated_phrase = openai_translate_app_utils.extract_phrase_from_prompt(prompt_result)
            print(f"translated phrase: {translated_phrase}")
            translated_phrase = openai_translate_app_utils.make_dst_phrase_look_the_same(src_phrase, translated_phrase)            
            translated_phrase = openai_translate_app_utils.double_single_quotes(translated_phrase)
            
            if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.NOT_TRANSLATION_NAME:
                translated_phrase = openai_translate_app_utils.make_dst_not_translation_names_phrase_look_the_same(translated_phrase, phrase_info)

            dst_phrase_info = openai_translate_app_utils.get_phrase_info(phrase_key, translated_phrase, special_phrases_variables)

            # verify that phrase valid
            try:
                if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.NOT_TRANSLATION_NAME:
                    if openai_translate_app_utils.is_entire_phrase_not_translation(src_phrase):
                        pass
                    elif not openai_translate_app_utils.local_server_is_phrase_language_valid(translated_phrase, phrase_info, dst_lang_code):
                        increase_problematic_lang_count(dst_lang_code)
                        print(problematic_langs_count)
                        raise Exception("translated phrase language not valid")
                elif not openai_translate_app_utils.local_server_is_phrase_language_valid(translated_phrase, phrase_info, dst_lang_code):
                    increase_problematic_lang_count(dst_lang_code)
                    print(problematic_langs_count)
                    raise Exception("translated phrase language not valid")

                if phrase_info.phrase_variables != dst_phrase_info.phrase_variables:
                    raise Exception("variables not the same")

                if phrase_info.phrase_type != dst_phrase_info.phrase_type:
                    raise Exception(f"phrase type not the same {phrase_info.phrase_type} to {dst_phrase_info.phrase_type}")

                if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.DEFAULT:
                    if retry_count > 1 and was_not_valid_lang_error:
                        pass
                    else:
                        phrase_of_lang = openai_translate_app_utils.openai_default_phrase_is_of_lang(src_phrase, translated_phrase, dst_lang_name)
                        if not phrase_of_lang:
                            was_not_valid_lang_error = True
                            raise Exception("openai phrase lang not valid")  
                elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.NOT_TRANSLATION_NAME:
                    if retry_count > 1 and was_not_valid_lang_error or openai_translate_app_utils.is_entire_phrase_not_translation(src_phrase):
                        pass
                    else:
                        phrase_of_lang = openai_translate_app_utils.openai_default_phrase_is_of_lang(src_phrase, translated_phrase, dst_lang_name)
                        if not phrase_of_lang:
                            was_not_valid_lang_error = True
                            raise Exception("openai phrase lang not valid")

                    if not openai_translate_app_utils.is_not_translation_phrase_valid(translated_phrase, phrase_info):
                        raise Exception("not translation phrase not valid")
                elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.PLURAL:
                    if retry_count > 1 and was_not_valid_lang_error:
                        pass
                    else:
                        phrase_of_lang = openai_translate_app_utils.openai_plural_phrase_is_of_lang(src_phrase, translated_phrase, dst_lang_name)
                        if not phrase_of_lang:
                            was_not_valid_lang_error = True
                            raise Exception("openai phrase lang not valid")

                    if not openai_translate_app_utils.is_plural_phrase_valid(translated_phrase, phrase_info.phrase_variables):
                        raise Exception("plural phrase not valid")
                elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.VARIABLE:
                    if retry_count > 1 and was_not_valid_lang_error:
                        pass
                    else:
                        phrase_of_lang = openai_translate_app_utils.openai_variable_phrase_is_of_lang(src_phrase, translated_phrase, dst_lang_name)
                        if not phrase_of_lang:
                            was_not_valid_lang_error = True
                            raise Exception("openai phrase lang not valid")

                    if not openai_translate_app_utils.is_variable_phrase_valid(translated_phrase, phrase_info.phrase_variables):
                        raise Exception("variable phrase not valid")

            except Exception as e:
                print(Back.YELLOW + f"Retrying: \n\tsrc_phrase ({src_lang_code}): {src_phrase};\n\tdst_phrase ({dst_lang_code}): {translated_phrase};\n\treason: {e};\n\tprompt: {prompt_result};")
                retry_count += 1
                translated_phrase = ''

        translation_valid = translated_phrase != ''
        if translation_valid:
            # add phrase to db
            openai_translate_app_utils.add_phrase_to_db(
                db_conn,
                db_cur,
                openai_translate_app_utils.PhraseData(src_lang_code, src_phrase, dst_lang_code, translated_phrase)
            )

            dst_phrases[phrase_key] = translated_phrase
            print(Back.GREEN + f"Done: \n\tsrc_phrase ({src_lang_code}): {src_phrase};\n\tdst_phrase ({dst_lang_code}): {translated_phrase};\n\tprompt: {prompt_result};")
        else:
            print(Back.RED + f"failed to translate src_phrase: {phrases[phrase_key]}")
    
    dst_phrases_count = len(dst_phrases)
    if src_phrases_count != dst_phrases_count:
        print(Back.RED + f"Not enough translations for {dst_lang_code}, {dst_phrases_count}/{src_phrases_count}")
    else:
        filename = f"app_{dst_lang_code}.arb"
        with open(output_dir + '/' + filename, 'w') as f:
            json.dump(dst_phrases, f, ensure_ascii=False, indent=2)


def process_language_code(dst_lang_code):
    if dst_lang_code == src_lang_code:
        return

    db_conn = psycopg2.connect(
        dbname="svocab_ai_translations",
        user="svocab_ai_translator",
        password="12345",
    )

    db_cur = db_conn.cursor()
    
    create_language_file(dst_lang_code, db_conn, db_cur)


with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = {executor.submit(process_language_code, code) for code in language_codes}

    for future in concurrent.futures.as_completed(futures):
        try:
            future.result()
        except Exception as e:
            if "no results to fetch" not in e:
                print(Back.RED + f"Error processing language code: {e}")