from langdetect import detect_langs

def word_exists_in_language(word, language_code):
    try:
        # Detect the language of the word
        detected_languages = detect_langs(word)
        
        # Check if the detected language matches the specified language code
        for lang in detected_languages:
            if lang.lang == language_code:
                return True
    except:
        pass  # Handle exceptions gracefully
    
    return False

# Example usage
word = "hello"
language_code = "en"  # Language code for English
if word_exists_in_language(word, language_code):
    print(f"The word '{word}' exists in the language with code '{language_code}'")
else:
    print(f"The word '{word}' does not exist in the language with code '{language_code}'")