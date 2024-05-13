-- db_name = svocab_ai_translations
-- db_user = svocab_ai_translator
-- db_password = 12345

-- CREATE TABLE words_phrase (
--     lang CHAR(2) NOT NULL,
--     word_en_key TEXT NOT NULL,
--     word TEXT NOT NULL,
--     phrase TEXT NOT NULL,
--     PRIMARY KEY (lang, word_en_key, word)
-- );




-- CREATE TABLE words_phrase (
--     src_lang CHAR(2) NOT NULL,
--     src_word TEXT NOT NULL,
--     dst_lang CHAR(2) NOT NULL,
--     dst_word TEXT NOT NULL,
--     phrase TEXT NOT NULL,
--     PRIMARY KEY (src_lang, src_word, dst_lang)
-- );



SELECT src_word, dst_lang, COUNT(*)
FROM words_phrase
WHERE dst_lang IN ('sp', 'es')
GROUP BY src_word, dst_lang
HAVING COUNT(*) > 1;

-- Create a temporary table to hold duplicates
CREATE TEMP TABLE temp_duplicates AS
SELECT src_word, dst_lang, COUNT(*) as duplicate_count
FROM words_phrase
WHERE src_lang IN ('sp', 'es')
GROUP BY src_word, dst_lang
HAVING COUNT(*) > 1;

SELECT * FROM temp_duplicates;




CREATE EXTENSION IF NOT EXISTS hstore;

CREATE TABLE phrase_packs (
    id SERIAL PRIMARY KEY,
    lang_phrase hstore,
    lang_word hstore
);

CREATE TABLE words (
    lang CHAR(2) NOT NULL,
    word TEXT NOT NULL,
    phrase_pack_id INT NOT NULL REFERENCES phrase_packs(id),
    PRIMARY KEY (lang, word, phrase_pack_id)
);

CREATE TABLE prompt_response (
    src_lang CHAR(2) NOT NULL,
    src_word TEXT NOT NULL,
    target_langs TEXT NOT NULL,
    prompt_response TEXT NOT NULL,
    process_success BOOLEAN NOT NULL,
    PRIMARY KEY (src_lang, src_word, target_langs)
);