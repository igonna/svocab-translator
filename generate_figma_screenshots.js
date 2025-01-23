// figma.currentPage.selection[0].clone()

await figma.loadAllPagesAsync();

const languages = {
	'en': ['es', 'fr'], 'es': ['en', 'fr'], 'fr': ['en', 'es'], 'de': ['en', 'fr'], 'zh': ['en', 'ja'], 'ja': ['en', 'ko'],
	'it': ['en', 'es'], 'pt': ['en', 'es'], 'ru': ['en', 'de'], 'ko': ['en', 'ja'], 'ar': ['en', 'fr'], 'nl': ['en', 'de'],
	'sv': ['en', 'de'], 'tr': ['en', 'de'], 'hi': ['en', 'ur'], 'no': ['en', 'de'], 'el': ['en', 'de'], 'pl': ['en', 'de'],
	'vi': ['en', 'zh'], 'id': ['en', 'zh'], 'da': ['en', 'de'], 'th': ['en', 'zh'], 'uk': ['en', 'pl'], 'fa': ['en', 'ar'],
	'cs': ['en', 'de'], 'fi': ['en', 'sv'], 'ro': ['en', 'it'], 'sw': ['en', 'fr'], 'hu': ['en', 'de'], 'ca': ['es', 'en'],
	'bn': ['en', 'hi'], 'is': ['en', 'da'], 'ms': ['en', 'zh'], 'sr': ['en', 'ru'], 'hr': ['en', 'de'], 'hy': ['ru', 'en'],
	'ka': ['ru', 'en'], 'sq': ['en', 'it'], 'bs': ['en', 'hr'], 'sk': ['en', 'cs'], 'sl': ['en', 'it'], 'lt': ['en', 'ru'],
	'lv': ['en', 'ru'], 'et': ['en', 'ru'], 'mk': ['en', 'bg'], 'ta': ['en', 'si'], 'te': ['en', 'hi'], 'ur': ['en', 'hi'],
	'mr': ['en', 'hi'], 'gu': ['en', 'hi'], 'ml': ['en', 'ta'], 'kk': ['ru', 'en'], 'mn': ['ru', 'en'], 'my': ['en', 'zh'],
	'tl': ['en', 'ja'], 'am': ['en', 'ar'], 'kn': ['en', 'hi'], 'so': ['en', 'ar'], 'bg': ['en', 'ru'], 'pa': ['en', 'hi']
};

const exception_fonts = {'hy': 'Noto Sans Armenian', 'my': 'Noto Sans Myanmar', 'am': 'Noto Sans Ethiopic', 'pa': 'Noto Sans Gurmukhi'};

const excluded_langs = new Set(['my']);

const targetComponentsNames = ["1_store_main", "2_store_simple_and_fast", "3_store_instant_feedback",
	"4_store_topic_generation", "5_store_statistics", "6_store_topics_mix", "7_store_multiple_languages",
	"8_store_dark_theme"
]

const allComponents = figma.root.findAll(node => node.type === 'COMPONENT');

const targetComponentsMap = {};
for (const component of allComponents) {
    if (targetComponentsNames.includes(component.name)) {
        targetComponentsMap[component.name] = component;
    }
}


const frame_with_all_components = figma.currentPage.findOne(node => node.type === 'FRAME' && node.name === 'frame_with_all_components');
const guess_word_frame_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_word_frame_comp');
const guess_text_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_text_comp');

const guess_word_frame_comp_2 = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_word_frame_comp_2');
const guess_text_comp_2 = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_text_comp_2');

const translation_word_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'translation_word_comp');
const translation_text_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'translation_text_comp');

async function translate_phrase(phrase, src_lang, dst_lang) {
	const response = await fetch('http://localhost:30032/translate', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			text: phrase,
			src_lang: src_lang,
			dst_lang: dst_lang
		})
	});

	if (!response.ok) {
		throw new Error("not valid response");
	}

	const data = await response.json();
	return data.translatedText || phrase;
}

async function translate_word_phrase(src_phrase, src_word, src_lang, dst_lang) {
	const response = await fetch('http://localhost:30032/translate_word_phrase', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			src_phrase: src_phrase,
			src_word: src_word,
			src_lang: src_lang,
			dst_lang: dst_lang
		})
	});

	if (!response.ok) {
		throw new Error("not valid response");
	}

	const data = await response.json();
	return { dst_phrase: data.dst_phrase, dst_word: data.dst_word };
}

async function translate_language(lang_code, dst_lang) {
	const response = await fetch('http://localhost:30032/get_language_name', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			lang_code: lang_code,
			translate_to: dst_lang
		})
	});

	if (!response.ok) {
		throw new Error("not valid response");
	}

	return (await response.json()).translatedLanguage || "Error";
}


const popular_langs = new Set(["lang_1", "lang_2"]);

const to_popular_lang_tags = new Set(["one_word", "text_source_content", "website_source_content"]);

const phrase_2_word_translation_text = "universe";

const phrase_1_text = "The book was published";
const phrase_1_word_text = "book";

const phrase_3_text = "Every dream is a step toward wonder";
const phrase_3_word_text = "dream";

function replaceSubstring(str, from, to) {
    const regex = new RegExp(from, 'gi');
    return str.replace(regex, to);
}

function createRepeatedString(symbol, length) {
    return symbol.repeat(length);
}

function swapLastTwoChars(str) {
    if (str.length < 2) {
        return str;
    }

    const pos_1 = str.length - 1;
    const pos_2 = str.length - 2;

    const swappedStr =
        str.slice(0, pos_2) +
        str[pos_1] +
        str[pos_2] +
        str.slice(pos_1 + 1);

    return swappedStr;
}

function swapLastAndBefore2Last(str) {
    if (str.length < 3) {
        return str;
    }

    const pos_1 = str.length - 1; 
    const pos_2 = str.length - 3; 

    
    const swappedStr =
        str.slice(0, pos_2) +
        str[pos_1] +
        str.slice(pos_2 + 1, pos_1) +
        str[pos_2];

    return swappedStr;
}

let error_count = 0;

async function fetchTranslation(originalText, textNodeName, src_lang, dst_lang, popularLangs) {
	try {
		// learn screen 1
		if (textNodeName == "phrase_2_word_translation") {
			if (popularLangs[0] == 'en') {
				return { text: phrase_2_word_translation_text, text_lang: 'en' };
			} else {
				let txt = await translate_phrase(phrase_2_word_translation_text, src_lang, popularLangs[0]);
				return { text: txt, text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "phrase_1_word_translation") {
			if (popularLangs[0] == 'en') {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, dst_lang);
				return { text: word_phrase.dst_word, text_lang: dst_lang };
			} else {
				let word_phrase_1 = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				let word_phrase_2 = await translate_word_phrase(word_phrase_1.dst_phrase, word_phrase_1.dst_word, popularLangs[0], dst_lang);
				return { text: word_phrase_2.dst_word, text_lang: dst_lang };
			}
		}

		if (textNodeName == "phrase_1_guess_space") {
			if (popularLangs[0] == 'en') {
				return { text: createRepeatedString('_', phrase_1_word_text.length), text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				return { text: createRepeatedString('_', word_phrase.dst_word.length), text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "phrase_1_guess") {
			if (popularLangs[0] == 'en') {
				let guess_phrase = replaceSubstring(phrase_1_text, phrase_1_word_text, createRepeatedString('_', phrase_1_word_text.length));
				return { text: guess_phrase, text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				let guess_phrase = replaceSubstring(word_phrase.dst_phrase, word_phrase.dst_word, createRepeatedString('_', word_phrase.dst_word.length));
				return { text: guess_phrase, text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "phrase_1_translation") {
			if (popularLangs[0] == 'en') {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, dst_lang);
				return { text: word_phrase.dst_phrase, text_lang: dst_lang };
			} else {
				let word_phrase_1 = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				let word_phrase_2 = await translate_word_phrase(word_phrase_1.dst_phrase, word_phrase_1.dst_word, popularLangs[0], dst_lang);
				return { text: word_phrase_2.dst_phrase, text_lang: dst_lang };
			}
		}

		if (textNodeName == "random_word_1") {
			if (popularLangs[0] == 'en') {
				return { text: swapLastTwoChars(phrase_1_word_text), text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				return { text: swapLastTwoChars(word_phrase.dst_word.toLowerCase()), text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "random_word_2") {
			if (popularLangs[0] == 'en') {
				return { text: phrase_1_word_text, text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				return { text: word_phrase.dst_word.toLowerCase(), text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "random_word_3") {
			if (popularLangs[0] == 'en') {
				return { text: swapLastAndBefore2Last(phrase_1_word_text), text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_1_text, phrase_1_word_text, src_lang, popularLangs[0]);
				return { text: swapLastAndBefore2Last(word_phrase.dst_word.toLowerCase()), text_lang: popularLangs[0] };
			}
		}

		// learn screen 2
		if (textNodeName == "phrase_3_word") {
			if (popularLangs[0] == 'en') {
				return { text: phrase_3_word_text, text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, popularLangs[0]);
				return { text: word_phrase.dst_word, text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "phrase_3") {
			if (popularLangs[0] == 'en') {
				return { text: phrase_3_text, text_lang: 'en' };
			} else {
				let word_phrase = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, popularLangs[0]);
				return { text: word_phrase.dst_phrase, text_lang: popularLangs[0] };
			}
		}

		if (textNodeName == "phrase_3_word_translation") {
			if (popularLangs[0] == 'en') {
				let word_phrase = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, dst_lang);
				return { text: word_phrase.dst_word, text_lang: dst_lang };
			} else {
				let word_phrase_1 = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, popularLangs[0]);
				let word_phrase_2 = await translate_word_phrase(word_phrase_1.dst_phrase, word_phrase_1.dst_word, popularLangs[0], dst_lang);
				return { text: word_phrase_2.dst_word, text_lang: dst_lang };
			}
		}

		if (textNodeName == "phrase_3_translation") {
			if (popularLangs[0] == 'en') {
				let word_phrase = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, dst_lang);
				return { text: word_phrase.dst_phrase, text_lang: dst_lang };
			} else {
				let word_phrase_1 = await translate_word_phrase(phrase_3_text, phrase_3_word_text, src_lang, popularLangs[0]);
				let word_phrase_2 = await translate_word_phrase(word_phrase_1.dst_phrase, word_phrase_1.dst_word, popularLangs[0], dst_lang);
				return { text: word_phrase_2.dst_phrase, text_lang: dst_lang };
			}
		}

		if (to_popular_lang_tags.has(textNodeName)) {
			if (src_lang != popularLangs[0]) {
				let txt = await translate_phrase(originalText, src_lang, popularLangs[0]);
				return { text: txt, text_lang: popularLangs[0] };
			} else {
				return { text: originalText, text_lang: src_lang };
			}
		}

		if (popular_langs.has(textNodeName)) {
			let txt = await translate_language(textNodeName == "lang_1" ? popularLangs[0] : popularLangs[1], dst_lang);
			return { text: txt, text_lang: dst_lang };
		}

		let txt = await translate_phrase(originalText, src_lang, dst_lang);
		return { text: txt, text_lang: dst_lang };
	} catch (error) {
		error_count += 1;
		console.log(`error during fetch translation: ${error}`);
	}
}

async function setFontForText(text_lang, textNode) {
	if (text_lang in exception_fonts) {
		try {
			try {
				console.log("set it here 1");
				const desiredFont = { family: exception_fonts[text_lang], style: textNode.fontName.style };
				await figma.loadFontAsync(desiredFont);
				textNode.fontName = desiredFont;
			} catch (error) {
				console.log("set it here 2");
				console.log(`style: ${textNode.fontName.style}`);
				const desiredFont = { family: exception_fonts[text_lang], style: textNode.fontName.style.replace(' ', '') };
				await figma.loadFontAsync(desiredFont);
				textNode.fontName = desiredFont;
			}
		} catch (error) {
			console.error("Error setting font or translating text 1:", error);
		}
	}
}

async function translateAllInstances(ui_src_lang, dst_lang, paddingY, popularLangs) {
	for (const targetComponentName of targetComponentsNames) {
		// if (targetComponentName == "4_store_topic_generation") return;

		const targetComponent = targetComponentsMap[targetComponentName];
	
		if (targetComponent) {
			const originalX = targetComponent.x;
			const originalY = targetComponent.y;
	
			let instance_tmp = targetComponent.createInstance();

			let instance = (targetComponentName === "2_store_simple_and_fast" || targetComponentName === "3_store_instant_feedback") ? instance_tmp.detachInstance() : instance_tmp;

			if (targetComponentName === "2_store_simple_and_fast" || targetComponentName === "3_store_instant_feedback") {
				let inside_instance = instance.findAllWithCriteria({ types: ['INSTANCE'] }).find(ins => ins.name === 'learn screen store 3');
				inside_instance.detachInstance();
			}

			instance.name = instance.name + `_${dst_lang}`;
			
			if (!instance) {
				console.error('The instance is null or undefined.');
				console.log('Instance type:', instance.type);
				return;
			}

			// // Ensure that instance is a ComponentInstance
			// if (instance.type !== 'INSTANCE') {
			// 	console.error('The node is not a ComponentInstance:', instance);
			// 	return;
			// }
	
			instance.x = originalX;
			instance.y = originalY + paddingY;

			async function translateInstanceTexts() {
				if (targetComponentName === "3_store_instant_feedback") {
					let group_to_detach = instance.findAllWithCriteria({ types: ['INSTANCE'] }).find(frame => frame.name === 'group_to_detach');
					group_to_detach.detachInstance();
				}

				const textNodes = instance.findAllWithCriteria({ types: ['TEXT'] });
			
				for (const textNode of textNodes) {
					if (textNode.name === "no_translation") {
						continue;
					}

					if (textNode.name !== "translate" && (targetComponentName === "2_store_simple_and_fast" || targetComponentName === "3_store_instant_feedback")) {
						continue;
					}
	
					const fontName = textNode.fontName;
					if (fontName !== figma.mixed) {
						await figma.loadFontAsync(fontName);
					} else {
						console.error(`Mixed fonts found in text node: ${textNode.name}. Cannot load.`);
						continue;
					}
	
					const translation_result = await fetchTranslation(textNode.characters, textNode.name, ui_src_lang, dst_lang, popularLangs);
					const text_lang = translation_result.text_lang;

					// font
					if (text_lang in exception_fonts) {
						console.log(`set font for text lang: ${text_lang}, text: ${translation_result.text}`);
						
						await setFontForText(text_lang, textNode);
					}
					textNode.characters = translation_result.text;
				}
			}

			async function setInstanceText(inst, text) {
				let textNode = inst.findOne(node => node.type === 'TEXT');
				await figma.loadFontAsync(textNode.fontName);
				textNode.characters = text;
			}

			async function setInstanceValidFont(inst, text_lang) {
				let textNode = inst.findOne(node => node.type === 'TEXT');
				await setFontForText(text_lang, textNode);
			}

			async function createPhrasesTranslation(targetComponentName) {
				let frame_to_fill = instance.findAllWithCriteria({ types: ['FRAME'] }).find(frame => frame.name === 'frame_to_fill');
				let guess_frame = frame_to_fill.findAllWithCriteria({ types: ['FRAME'] }).find(frame => frame.name === 'guess_frame');

				let is_first_comp = targetComponentName === '2_store_simple_and_fast';

				let phrase_1_highlight_space = (await fetchTranslation('', is_first_comp ? 'phrase_1_guess_space' : 'phrase_3_word', ui_src_lang, dst_lang, popularLangs)).text;
				let phrase_1 = (await fetchTranslation('', is_first_comp ? 'phrase_1_guess' : 'phrase_3', ui_src_lang, dst_lang, popularLangs)).text;
				let phrase_1_splited = phrase_1.split(" ");

				while (guess_frame.children.length > 0) {
					guess_frame.children[0].remove();
				}

				for (let phrase_part of phrase_1_splited) {
					if (phrase_part.toLowerCase() === phrase_1_highlight_space.toLowerCase()) {
						let inst = is_first_comp ? guess_word_frame_comp.createInstance() : guess_word_frame_comp_2.createInstance();
						setInstanceText(inst, phrase_1_highlight_space);
						guess_frame.appendChild(inst);
					} else {
						let inst = is_first_comp ? guess_text_comp.createInstance() : guess_text_comp_2.createInstance();
						setInstanceText(inst, phrase_part);
						guess_frame.appendChild(inst);
					}
				}

				let translation_frame = frame_to_fill.findAllWithCriteria({ types: ['FRAME'] }).find(frame => frame.name === 'translation_frame');

				while (translation_frame.children.length > 0) {
					translation_frame.children[0].remove();
				}
				
				let phrase_1_translation_result = (await fetchTranslation('', is_first_comp ? 'phrase_1_translation' : 'phrase_3_translation', ui_src_lang, dst_lang, popularLangs));
				let phrase_1_translation = phrase_1_translation_result.text;
				let phrase_1_translation_lang = phrase_1_translation_result.text_lang;
				let phrase_1_word_translation = (await fetchTranslation('', is_first_comp ? 'phrase_1_word_translation' : 'phrase_3_word_translation', ui_src_lang, dst_lang, popularLangs)).text;

				phrase_1_translation = phrase_1_translation.replace(phrase_1_word_translation, ' * ');
				phrase_1_translation = phrase_1_translation.replace('  ', ' ');

				let phrase_1_translation_splited = phrase_1_translation.split(" ");

				console.log(`word part: '${phrase_1_word_translation}'`);

				for (let phrase_part of phrase_1_translation_splited) {
					console.log(`phrase part: '${phrase_part}'`);
					if (phrase_part == '') {
						continue;
					} else if (phrase_part == '*') {
						let inst = translation_word_comp.createInstance();
						setInstanceText(inst, phrase_1_word_translation);
						await setInstanceValidFont(inst, phrase_1_translation_lang);
						translation_frame.appendChild(inst);
					} else if (phrase_part.toLowerCase() === phrase_1_word_translation.toLowerCase()) {
						let inst = translation_word_comp.createInstance();
						setInstanceText(inst, phrase_part);
						await setInstanceValidFont(inst, phrase_1_translation_lang);
						translation_frame.appendChild(inst);
					} else {
						let inst = translation_text_comp.createInstance();
						setInstanceText(inst, phrase_part);
						await setInstanceValidFont(inst, phrase_1_translation_lang);
						translation_frame.appendChild(inst);
					}
				}


				let random_words = frame_to_fill.findAllWithCriteria({ types: ['TEXT'] })
					.filter(text => text.name === 'random_word_1' || text.name === 'random_word_2' || text.name === 'random_word_3');

				for (let random_word of random_words) {
					random_word.characters = (await fetchTranslation('', random_word.name, ui_src_lang, dst_lang, popularLangs)).text;
				}
			}

			if (targetComponentName == "2_store_simple_and_fast" || targetComponentName == "3_store_instant_feedback") {
				await createPhrasesTranslation(targetComponentName);
			}
			await translateInstanceTexts();
		} else {
			error_count += 1;
			console.log(`Component ${targetComponentName} not found`);
		}
	}
}

let heightOfComponent = 1920;
let paddingBetween = 100;

let paddingY = heightOfComponent + paddingBetween;

const test_langs = new Set(['hy']);

for (const [dst_lang, popular_langs] of Object.entries(languages)) {
	const ui_src_lang = 'en';

	// if (!(dst_lang in exception_fonts)) continue;

	// if (!(test_langs.has(dst_lang))) continue;
	console.log(`dst_lang: ${dst_lang}`);

	if (excluded_langs.has(dst_lang)) continue;
	await translateAllInstances(ui_src_lang, dst_lang, paddingY, popular_langs);

	paddingY = paddingY + heightOfComponent + paddingBetween;
}

console.log(`Error count: ${error_count}`);