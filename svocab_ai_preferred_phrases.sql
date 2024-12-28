-- greek-el
insert into preferred_app_phrases (src_lang, dst_lang, src_phrase, dst_phrase)
values ('en', 'el', 'Get Plus', 'Αποκτήστε Plus') on conflict do nothing;

-- russian-ru
insert into preferred_app_phrases (src_lang, dst_lang, src_phrase, dst_phrase)
values ('en', 'ru', 'By first appearance', 'По первому появлению'),
('en', 'ru', 'Link profile with', 'Связать профиль с'),
('en', 'ru', 'Yes, rate it now', 'Да, оценить сейчас'),
('en', 'ru', 'Your learning sequence is empty', 'Ваша последовательность изучения пуста')
on conflict do nothing;