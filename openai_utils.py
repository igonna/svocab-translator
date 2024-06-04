import re

def verify_or_replace_lang(lang):
  if lang == 'sp':
    lang = 'es'
  return lang

def replace_line_lang_if_wrong(lang):
  if lang == 'english':
    return 'en'
  if lang == 'italian':
    return 'it'
  if lang == 'spanish':
    return 'es'
  if lang == 'portuguese':
    return 'pt'
  if lang == 'french':
    return 'fr'
  if lang == 'german':
    return 'de'
  if lang == 'russian':
    return 'ru'
  if lang == 'chinese':
    return 'zh'
  return lang

def extract_phrases_from_line(line):
  pattern = r'\{(.*?)\}'
  matches = re.findall(pattern, line)
  phrases = [match.strip() for match in matches]
  return phrases

def replace_lang_for_ai(lang):
  if lang == 'it':
    return 'italian'
  return lang

def get_lang_code_from_line(line):
  return line.split(':')[0].strip('{')