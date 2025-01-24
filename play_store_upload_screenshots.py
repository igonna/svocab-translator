#!/usr/bin/python

import sys
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import os
from collections import defaultdict
import hashlib
import openai_translate_app_utils
import psycopg2

directory_path = "/Users/c/Documents/a_screenshots_2/"

language_screenshots = defaultdict(list)

for filename in os.listdir(directory_path):
    if filename.endswith(".png"):
        parts = filename.split("_")
        if len(parts) >= 3:
            number = int(parts[0])
            language_code = parts[-1].split(".")[0]
            full_path = os.path.join(directory_path, filename)
            language_screenshots[language_code].append((number, full_path))

for language, files in language_screenshots.items():
    language_screenshots[language] = [f[1] for f in sorted(files, key=lambda x: x[0])]

language_screenshots = dict(language_screenshots)

for lang, files in language_screenshots.items():
    if len(files) != 8:
        print("some of files is wrong")
        exit(1)

TRACK = 'alpha'

app_name_p1 = 'svocab: '
app_name_p2 = 'Learn any words'
app_name_p2_shorter = 'Learn words'
app_name_max_len = 30

title_src = app_name_p1 + app_name_p2

short_description_src = 'Learn any words and improve your vocabulary, create generated topics'
short_description_shorter_src = 'Learn any words and improve your vocabulary'
short_description_even_shorter_src = 'Improve your vocabulary'

short_description_max_len = 80

long_description_src = 'Learn languages: English, Spanish, French, German, Chinese, Japanese, Italian, Portuguese, Russian, Korean, Arabic, Dutch, Swedish, Turkish, Hindi, Norwegian, Greek, Polish, Vietnamese, Indonesian, Danish, Thai, Ukrainian, Persian, Czech, Finnish, Romanian, Swahili, Hungarian, Catalan, Bangla, Icelandic, Malay, Serbian, Croatian, Armenian, Georgian, Albanian, Bosnian, Slovak, Slovenian, Lithuanian, Latvian, Estonian, Macedonian, Tamil, Telugu, Urdu, Marathi, Gujarati, Malayalam, Kazakh, Mongolian, Burmese, Amharic, Kannada, Somali, Bulgarian, Punjabi'
long_description_max_len = 4000

SERVICE_ACCOUNT_FILE = 'secrets/svocab_publish.json'
PACKAGE_NAME = 'com.svocab.svocab'

play_console_supported_localizations = {
    'af', 'sq', 'am', 'ar', 'hy-AM', 'az-AZ', 'bn-BD', 'eu-ES', 'be', 'bg', 'my-MM', 'ca', 'zh-HK', 'zh-CN', 
    'zh-TW', 'hr', 'cs-CZ', 'da-DK', 'nl-NL', 'en-AU', 'en-CA', 'en-US', 'en-GB', 'en-IN', 'en-SG', 'en-ZA', 
    'et', 'fil', 'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'ka-GE', 'de-DE', 'el-GR', 'gu', 'iw-IL', 'hi-IN', 
    'hu-HU', 'is-IS', 'id', 'it-IT', 'ja-JP', 'kn-IN', 'kk', 'km-KH', 'ko-KR', 'ky-KG', 'lo-LA', 'lv', 
    'lt', 'mk-MK', 'ms-MY', 'ms', 'ml-IN', 'mr-IN', 'mn-MN', 'ne-NP', 'no-NO', 'fa', 'fa-AE', 'fa-AF', 
    'fa-IR', 'pl-PL', 'pt-BR', 'pt-PT', 'pa', 'ro', 'rm', 'ru-RU', 'sr', 'si-LK', 'sk', 'sl', 'es-419', 
    'es-ES', 'es-US', 'sw', 'sv-SE', 'ta-IN', 'te-IN', 'th', 'tr-TR', 'uk', 'ur', 'vi', 'zu'
}

play_console_supported_localizations_only_popular = {
    'af', 'sq', 'am', 'ar', 'hy-AM', 'az-AZ', 'bn-BD', 'eu-ES', 'be', 'bg', 'my-MM', 'ca', 'zh-CN', 'hr', 'cs-CZ', 'da-DK', 
    'nl-NL', 'en-US', 'et', 'fil', 'fi-FI', 'fr-FR', 'gl-ES', 'ka-GE', 'de-DE', 'el-GR', 'gu', 'iw-IL', 'hi-IN', 'hu-HU', 
    'is-IS', 'id', 'it-IT', 'ja-JP', 'kn-IN', 'kk', 'km-KH', 'ko-KR', 'ky-KG', 'lo-LA', 'lv', 'lt', 'mk-MK', 'ms-MY', 
    'ml-IN', 'mr-IN', 'mn-MN', 'ne-NP', 'no-NO', 'fa', 'fa-IR', 'pl-PL', 'pt-BR', 'pa', 'ro', 'rm', 'ru-RU', 'sr', 
    'si-LK', 'sk', 'sl', 'es-ES', 'sw', 'sv-SE', 'ta-IN', 'te-IN', 'th', 'tr-TR', 'uk', 'ur', 'vi', 'zu'
}

def get_localizations(lang_code):
    localizations = {loc for loc in play_console_supported_localizations if loc.startswith(lang_code)}
    return localizations

def get_popular_localization(lang_code):
    localizations = [loc for loc in play_console_supported_localizations_only_popular if loc.startswith(lang_code)]
    return localizations[0] if localizations else None

def create_edit_session(service):
    edit_request = service.edits().insert(body={}, packageName=PACKAGE_NAME)
    result = edit_request.execute()
    return result['id']

def commit_edit(service, edit_id):
    commit_request = service.edits().commit(editId=edit_id, packageName=PACKAGE_NAME).execute()

def update_listing(service, edit_id, lang_code, title, short_description, long_description):
    listing_response = service.edits().listings().update(
        editId=edit_id, packageName=PACKAGE_NAME, language=lang_code,
        body={
            'title': title,
            'shortDescription': short_description,
            'fullDescription': long_description
    }).execute()
    
def is_listing_updated(service, edit_id, lang_code, new_title, new_short_description, new_long_description):
    try:
        response = service.edits().listings().get(
            editId=edit_id,
            packageName=PACKAGE_NAME,
            language=lang_code
        ).execute()

        title = response.get('title', '')
        short_description = response.get('shortDescription', '')
        long_description = response.get('fullDescription', '')

        if title == new_title and short_description == new_short_description and long_description == new_long_description:
            return True
        return False
    except Exception as e:
        return False

def get_sha1_of_file(file_path):
    sha1_hash = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha1_hash.update(chunk)
    return sha1_hash.hexdigest()

def is_screenshots_uploaded(service, edit_id, lang_code, screenshots_files):
    try:
        screenshots_sha1 = set()
        for screenshot_file in screenshots_files:
            screenshots_sha1.add(get_sha1_of_file(screenshot_file))

        response = service.edits().images().list(
            editId=edit_id,
            packageName=PACKAGE_NAME,
            language=lang_code,
            imageType='phoneScreenshots'
        ).execute()

        uploaded_sha1 = {os.path.basename(img['sha1']) for img in response.get('images', [])}

        return screenshots_sha1.issubset(uploaded_sha1)
    except Exception as e:
        print(f"Error fetching uploaded screenshots: {e}")
        return False

def remove_screenshots(service, edit_id, lang_code):
    delete_response = service.edits().images().deleteall(
        editId=edit_id,
        packageName=PACKAGE_NAME,
        language=lang_code,
        imageType='phoneScreenshots'
    ).execute()

def upload_screenshots(service, edit_id, lang_code, screenshots_to_upload):
    for screenshot_file in screenshots_to_upload:
        media_body = MediaFileUpload(screenshot_file, mimetype='image/png')
        upload_response = service.edits().images().upload(
            editId=edit_id,
            packageName=PACKAGE_NAME,
            language=lang_code,
            imageType='phoneScreenshots',
            media_body=media_body
        ).execute()

# translate generic
def translate_text(db_conn, db_cur, src_text, lang_code, translation_logic):
    src_lang_code = 'en'
    phrase_translation_db = openai_translate_app_utils.get_phrase_from_db(db_cur, lang_code, src_lang_code, src_text)

    if phrase_translation_db is not None:
        return phrase_translation_db
    
    translated_text = ''

    retry_count = 0
    max_retry_count = 12
    while translated_text == '' and retry_count < max_retry_count:
        try:
            dst_lang_name = openai_translate_app_utils.get_language_name(lang_code)
            translated_text = translation_logic(src_text, dst_lang_name)

            openai_translate_app_utils.add_phrase_to_db(
                db_conn,
                db_cur,
                openai_translate_app_utils.PhraseData(src_lang_code, src_text, lang_code, translated_text)
            )
            
            return translated_text
        except Exception as e:
            print(f"Retrying: got an exception: '{e}' for ({lang_code}) '{src_text}'")
            retry_count += 1

    raise Exception(f"failed to translate text ({lang_code}): {src_text}")

# translation app title
def openai_title_translation(src_title, dst_lang):
    prompt = 'translate this play store part of ai generation app title "' + src_title + '" in formal and form to ' + dst_lang + ' maximum length is 22 symbols, output this only as json {"translated_title": ""}'
    return openai_translate_app_utils.openai_prompt_exec(prompt)

def openai_is_description_translation_valid(src_description, dst_description, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' ' + dst_description + ' a possible close translation for English ' + src_description + ', output only yes or no'
    result = openai_translate_app_utils.openai_prompt_exec(prompt)
    return 'yes' in result.lower()


def openai_is_title_translation_valid(src_description, dst_description, dst_lang_name):
    prompt = 'is ' + dst_lang_name + ' title ' + dst_description + ' a possible close translation for English ' + src_description + ', output only yes or no'
    result = openai_translate_app_utils.openai_prompt_exec(prompt)
    return 'yes' in result.lower()

def title_translation_logic(src_text, dst_lang_name):
    prompt_result = openai_title_translation(src_text, dst_lang_name)
    extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_title')
    translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)

    if len(translated_text) > 22 or len(translated_text) == 0:
        src_text = app_name_p2_shorter
        prompt_result = openai_title_translation(src_text, dst_lang_name)
        extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_title')
        translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)

        if len(translated_text) > 22 or len(translated_text) == 0:
            print(f"text: '{translated_text}', len: '{len(translated_text)}'")
            raise Exception("not valid length")
        
    print(src_text)
    print(translated_text)

    is_valid = openai_is_title_translation_valid(src_text, translated_text, dst_lang_name)
    if not is_valid:
        raise Exception("openai title translation not valid")
    return translated_text

# translation app short description
def openai_short_description_translation(src_description, dst_lang):
    prompt = 'translate this play store short description of ai generation app "' + src_description + '" in formal form to ' + dst_lang + ' maximum length is 80 symbols, output this only as json {"translated_description": ""}'
    return openai_translate_app_utils.openai_prompt_exec(prompt)

def short_description_translation_logic(src_text, dst_lang_name):
    prompt_result = openai_short_description_translation(src_text, dst_lang_name)
    extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_description')
    translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)

    if len(translated_text) > 80 or len(translated_text) == 0:
        src_text = short_description_shorter_src
        prompt_result = openai_short_description_translation(src_text, dst_lang_name)
        extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_description')
        translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)
        print(f"text: '{translated_text}', len: '{len(translated_text)}'")

        if len(translated_text) > 80 or len(translated_text) == 0:
            src_text = short_description_even_shorter_src
            prompt_result = openai_short_description_translation(src_text, dst_lang_name)
            extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_description')
            translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)
            print(f"text: '{translated_text}', len: '{len(translated_text)}'")
            if len(translated_text) > 80 or len(translated_text) == 0:
                print(f"text: '{translated_text}', len: '{len(translated_text)}'")
                raise Exception(f"not valid length: {len(translated_text)}")

    is_valid = openai_is_description_translation_valid(src_text, translated_text, dst_lang_name)
    if not is_valid:
        print(f"dst_phrase: {translated_text}")
        raise Exception("openai translation not valid")
    return translated_text

def openai_long_description_translation(src_description, dst_lang):
    prompt = 'translate this play store long description of ai generation app "' + src_description + '" in formal form to ' + dst_lang + ', output this only as json {"translated_description": ""}'
    return openai_translate_app_utils.openai_prompt_exec(prompt)

def long_description_translation_logic(src_text, dst_lang_name):
    prompt_result = openai_long_description_translation(src_text, dst_lang_name)
    extracted_text = openai_translate_app_utils.extract_phrase_from_prompt_by_key(prompt_result, 'translated_description')
    translated_text = openai_translate_app_utils.remove_periods_from_end(extracted_text)

    if len(translated_text) > 4000 or len(translated_text) == 0:
        raise Exception(f"not valid length: {len(translated_text)}")

    is_valid = openai_is_description_translation_valid(src_text, translated_text, dst_lang_name)
    if not is_valid:
        print(f"dst_phrase: {translated_text}")
        raise Exception("openai translation not valid")
    return translated_text

# translation app long description

def get_prepared_listings_texts():
    titles = {}
    short_descriptions = {}
    long_descriptions = {}

    db_conn = psycopg2.connect(
        dbname="svocab_ai_translations",
        user="svocab_ai_translator",
        password="12345",
    )

    db_cur = db_conn.cursor()
    
    for lang_code in language_screenshots:
        # if lang_code != 'ru':
        #     continue
        if lang_code == 'en':
            titles[lang_code] = title_src
            short_descriptions[lang_code] = short_description_src
            long_descriptions[lang_code] = long_description_src
        else:
            titles[lang_code] = app_name_p1 + translate_text(
                db_conn=db_conn,
                db_cur=db_cur,
                src_text=app_name_p2,
                lang_code=lang_code,
                translation_logic=title_translation_logic
            )

            short_descriptions[lang_code] = translate_text(
                db_conn=db_conn,
                db_cur=db_cur,
                src_text=short_description_src,
                lang_code=lang_code,
                translation_logic=short_description_translation_logic
            )

            long_descriptions[lang_code] = translate_text(
                db_conn=db_conn,
                db_cur=db_cur,
                src_text=long_description_src,
                lang_code=lang_code,
                translation_logic=long_description_translation_logic
            )

            # print(f'({lang_code}) title: {titles[lang_code]}')
            # print(f'({lang_code}) short_description: {short_descriptions[lang_code]}')
            # print(f'({lang_code}) long_description: {long_descriptions[lang_code]}')
            # print('')
            continue

    return titles, short_descriptions, long_descriptions


def main():
    SCOPES = ['https://www.googleapis.com/auth/androidpublisher']

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('androidpublisher', 'v3', credentials=credentials)

    try:
        print(f"languages count: {len(language_screenshots)}")
        
        titles, short_descriptions, long_descriptions = get_prepared_listings_texts()
        # exit(0)
        
        changes_to_commit = 8
        changes_made = 0
        edit_id = ''
        

        for lang_code in language_screenshots:
            # if lang_code != 'ru':
            #     continue
            localization_code = get_popular_localization(lang_code)

            if localization_code is None:
                print(f"localization code is none: {lang_code}")
                continue
            
            if edit_id == '':
                edit_id = create_edit_session(service)
                print(f"new_edit_id: {edit_id}")

            listing_updated = is_listing_updated(service, edit_id, localization_code, titles[lang_code], short_descriptions[lang_code], long_descriptions[lang_code])
            if not listing_updated:
                print(f"updating listing for ({lang_code})")
                update_listing(service, edit_id, localization_code, titles[lang_code], short_descriptions[lang_code], long_descriptions[lang_code])
                changes_made += 1

            screenshot_files = language_screenshots[lang_code]
            screenshots_uploaded = is_screenshots_uploaded(service, edit_id, localization_code, screenshot_files)

            if not screenshots_uploaded:
                print(f"uploading screenshots for ({lang_code})")
                remove_screenshots(service, edit_id, localization_code)
                upload_screenshots(service, edit_id, localization_code, screenshot_files)
                changes_made += 1
    
        if edit_id != '' and changes_made > 0:
            commit_edit(service, edit_id)
            print('commit made')

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()