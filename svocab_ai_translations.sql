-- db_name = svocab_ai_translations
-- db_user = svocab_ai_translator
-- db_password = 12345

CREATE TABLE words_phrase (
    lang CHAR(2) NOT NULL,
    word_en_key TEXT NOT NULL,
    word TEXT NOT NULL,
    phrase TEXT NOT NULL,
    PRIMARY KEY (lang, word_en_key, word)
);

-- CREATE TABLE words_phrase (
--     src_lang CHAR(2) NOT NULL,
--     src_word TEXT NOT NULL,
--     dst_lang CHAR(2) NOT NULL,
--     dst_word TEXT NOT NULL,
--     phrase TEXT NOT NULL,
--     phrase_contains_dst_word BOOLEAN NOT NULL,
-- );

-- en princess ru принцесса 'Принцесса катается на лошади' True


--  en   | princess       | princess                  | The princess is riding a horse
--  sp   | princess       | princesa                  | La princesa está montando un caballo
--  it   | princess       | principessa               | La principessa sta cavalcando un cavallo
--  pt   | princess       | princesa                  | A princesa está montando um cavalo
--  fr   | princess       | princesse                 | La princesse est en train de chevaucher un cheval
--  de   | princess       | prinzessin                | Die Prinzessin reitet auf einem Pferd
--  ru   | princess       | принцесса                 | Принцесса катается на лошади
--  zh   | princess       | 公主                      | 公主正在骑马


CREATE TABLE prompt_response (
    src_lang CHAR(2) NOT NULL,
    src_word TEXT NOT NULL,
    target_langs TEXT NOT NULL,
    prompt_response TEXT NOT NULL,
    process_success BOOLEAN NOT NULL,
    PRIMARY KEY (src_lang, src_word, target_langs)
);

CREATE TABLE process_stats (
    process_success INT DEFAULT 0,
    process_failure INT DEFAULT 0,
    already_exists INT DEFAULT 0
);