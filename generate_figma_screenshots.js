// figma.currentPage.selection[0].clone()

await figma.loadAllPagesAsync();

const languages = {
	'en': ['es', 'fr'], 'es': ['en', 'fr'], 'fr': ['en', 'es'], 'de': ['en', 'fr'], 'zh': ['en', 'ja'], 'ja': ['en', 'ko'],
	'it': ['en', 'es'], 'pt': ['en', 'es'], 'ru': ['en', 'de'], 'ko': ['en', 'ja'], 'ar': ['en', 'fr'], 'nl': ['en', 'de'],
	'sv': ['en', 'de'], 'tr': ['en', 'de'], 'hi': ['en', 'ur'], 'no': ['en', 'de'], 'el': ['en', 'de'], 'pl': ['en', 'de'],
	'vi': ['en', 'zh'], 'id': ['en', 'zh'], 'da': ['en', 'de'], 'th': ['en', 'zh'], 'uk': ['ru', 'pl'], 'fa': ['en', 'ar'],
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
		return phrase;
	}

	const data = await response.json();
	return data.translatedText || phrase;
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
		return "Error";
	}

	return (await response.json()).translatedLanguage || "Error";
}

const learn_screen_1 = new Set(["phrase_1_guess_space", "phrase_1_word_translation", "phrase_1_guess",
	"phrase_1", "phrase_1_guess_word", "phrase_1_random_word_1", "phrase_1_random_word_2", "phrase_2_word"
]);

const learn_screen_2 = new Set(["phrase_2_word", "phrase_2_word_translation", "phrase_2", "phrase_2_translation"]);

const popular_langs = new Set(["lang_1", "lang_2"]);

const to_popular_lang_tags = new Set(["one_word", "text_source_content", "website_source_content"]);

async function translateAllInstances(ui_src_lang, dst_lang, paddingY, popularLangs) {
	for (const targetComponentName of targetComponentsNames) {
		const targetComponent = targetComponentsMap[targetComponentName];
	
		if (targetComponent) {
			const originalX = targetComponent.x;
			const originalY = targetComponent.y;
	
			let instance = targetComponent.createInstance();
			instance.name = instance.name + `_${dst_lang}`;

			if (!instance) {
				console.error('The instance is null or undefined.');
				console.log('Instance type:', instance.type);
				return;
			}
			
			// Ensure that instance is a ComponentInstance
			if (instance.type !== 'INSTANCE') {
				console.error('The node is not a ComponentInstance:', instance);
				return;
			}
	
			instance.x = originalX;
			instance.y = originalY + paddingY;
	
			async function fetchTranslation(originalText, textNodeName) {
				try {
					if (learn_screen_1.has(textNodeName) || learn_screen_2.has(textNodeName) 
					) {
						return "TODO";
					} else if (to_popular_lang_tags.has(textNodeName)) {
						if (ui_src_lang != popularLangs[0]) {
							return (await translate_phrase(originalText, ui_src_lang, popularLangs[0]));
						} else {
							return originalText;
						}
					} else if (popular_langs.has(textNodeName)) {
						return (await translate_language(textNodeName == "lang_1" ? popularLangs[0] : popularLangs[1], dst_lang));
					} else {
						return (await translate_phrase(originalText, ui_src_lang, dst_lang));
					}
				} catch (error) {
					console.error("Error during fetch:", error);
					return originalText;
				}
			}
	
			async function translateInstanceTexts() {
				const textNodes = instance.findAllWithCriteria({ types: ['TEXT'] });
			
				for (const textNode of textNodes) {
					if (textNode.name === "no_translation") {
						continue;
					}
	
					const fontName = textNode.fontName;
					if (fontName !== figma.mixed) {
						await figma.loadFontAsync(fontName);
					} else {
						console.error(`Mixed fonts found in text node: ${textNode.name}. Cannot load.`);
						continue;
					}
	
					const translatedText = await fetchTranslation(textNode.characters, textNode.name);

					if (dst_lang in exception_fonts) {
						async function setFont(desiredFontName) {
							console.log(`desired font: ${desiredFontName}`);
							try {
								console.log(`current font name family: ${textNode.fontName.family}`);

								const desiredFont = { family: desiredFontName, style: textNode.fontName.style };
								await figma.loadFontAsync(desiredFont);
								
								textNode.fontName = desiredFont;
							} catch (error) {
								console.error("Error setting font or translating text:", error);
							}
						}

						if (learn_screen_1.has(textNode.name) || learn_screen_2.has(textNode.name) 
						) {
							//
						} else if (to_popular_lang_tags.has(textNode.name) && ui_src_lang != popularLangs[0]) {
							await setFont(exception_fonts[dst_lang]);
						} else if (popular_langs.has(textNode.name)) {
							await setFont(exception_fonts[dst_lang]);
						} else {
							await setFont(exception_fonts[dst_lang]);
						}
					}
					console.log(`got translation: ${translatedText}`);
					textNode.characters = translatedText;
				}
			}
	
			await translateInstanceTexts();
		} else {
			console.log(`Component ${targetComponentName} not found.`);
		}
	}
}

let heightOfComponent = 1920;
let paddingBetween = 100;

let paddingY = heightOfComponent + paddingBetween;

let counterBreak = 0;

for (const [dst_lang, popular_langs] of Object.entries(languages)) {
	const ui_src_lang = 'en';

	if (excluded_langs.has(dst_lang)) continue;
	await translateAllInstances(ui_src_lang, dst_lang, paddingY, popular_langs);

	paddingY = paddingY + heightOfComponent + paddingBetween;

	counterBreak += 1;
	if (counterBreak > 1) {
		// break;
	}
}