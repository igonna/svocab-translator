// figma.currentPage.selection[0].clone()


const frame_with_all_components = figma.currentPage.findOne(node => node.type === 'FRAME' && node.name === 'frame_with_all_components')
const guess_word_frame_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_word_frame_comp')
const guess_text_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_text_comp')

const guess_word_frame_comp_2 = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_word_frame_comp_2')
const guess_text_comp_2 = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'guess_text_comp_2')

const translation_word_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'translation_word_comp')
const translation_text_comp = frame_with_all_components.findOne(node => node.type === 'COMPONENT' && node.name === 'translation_text_comp')

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
	})

	if (!response.ok) {
		throw new Error("not valid response")
	}

	const data = await response.json()
	return data.translatedText || phrase
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
	})

	if (!response.ok) {
		throw new Error("not valid response")
	}

	const data = await response.json()
	return { dst_phrase: data.dst_phrase, dst_word: data.dst_word }
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
	})

	if (!response.ok) {
		throw new Error("not valid response")
	}

	return (await response.json()).translatedLanguage || "Error"
}


const popular_langs = new Set(["lang_1", "lang_2"])

const to_popular_lang_tags = new Set(["one_word", "text_source_content", "website_source_content"])

const phrase_2_word_translation_text = "universe"

const phrase_1_text = "The book was published"
const phrase_1_word_text = "book"

const phrase_3_text = "Every dream is a step toward wonder"
const phrase_3_word_text = "dream"

function replaceSubstring(str, from, to) {
    const regex = new RegExp(from, 'gi')
    return str.replace(regex, to)
}

function createRepeatedString(symbol, length) {
    return symbol.repeat(length)
}

function swapLastTwoChars(str) {
    if (str.length < 2) {
        return str
    }

    const pos_1 = str.length - 1
    const pos_2 = str.length - 2

    const swappedStr =
        str.slice(0, pos_2) +
        str[pos_1] +
        str[pos_2] +
        str.slice(pos_1 + 1)

    return swappedStr
}

function swapLastAndBefore2Last(str) {
    if (str.length < 3) {
        return str
    }

    const pos_1 = str.length - 1 
    const pos_2 = str.length - 3 

    
    const swappedStr =
        str.slice(0, pos_2) +
        str[pos_1] +
        str.slice(pos_2 + 1, pos_1) +
        str[pos_2]

    return swappedStr
}

let error_count = 0

async function fetchTranslation(originalText, textNodeName, src_lang, dst_lang, popularLangs) {
	try {
		let txt = await translate_phrase(originalText, src_lang, dst_lang)
		return { text: txt, text_lang: dst_lang }
	} catch (error) {
		error_count += 1
		console.log(`error during fetch translation: ${error}`)
	}
}

async function setFontForText(text_lang, textNode) {
	if (text_lang in exception_fonts) {
		try {
			try {
				console.log("set it here 1")
				const desiredFont = { family: exception_fonts[text_lang], style: textNode.fontName.style }
				await figma.loadFontAsync(desiredFont)
				textNode.fontName = desiredFont
			} catch (error) {
				console.log("set it here 2")
				console.log(`style: ${textNode.fontName.style}`)
				const desiredFont = { family: exception_fonts[text_lang], style: textNode.fontName.style.replace(' ', '') }
				await figma.loadFontAsync(desiredFont)
				textNode.fontName = desiredFont
			}
		} catch (error) {
			console.error("Error setting font or translating text 1:", error)
		}
	}
}

// text_native, text_topic_input_field, text_topic_content_colored
// text_native_lang_1, text_native_lang_2

// word_item, word_item_hidden, word_item_translation
// src_phrase_frame_1, native_phrase_frame_1, src_phrase_1_guess_letters
// src_phrase_frame_2, native_phrase_frame_2, src_phrase_2_guess_words

async function setInstanceText(inst, text) {
	let textNode = inst.findOne(node => node.type === 'TEXT')
	await figma.loadFontAsync(textNode.fontName)
	textNode.characters = text
}

async function setInstanceValidFont(inst, text_lang) {
	let textNode = inst.findOne(node => node.type === 'TEXT')
	await setFontForText(text_lang, textNode)
}

function getAllInstanceTexts(instance) {
	return instance.findAllWithCriteria({ types: ['TEXT'] })
}

async function cloneAndAppendItemWithNewText(itemToClone, appendTo, newText) {
	let newClone = itemToClone.clone();

	let textNode = newClone.findOne(node => node.type === 'TEXT')
	await figma.loadFontAsync(textNode.fontName)
	textNode.characters = newText
	textNode.name = 'done'
	newClone.name = 'done'

	appendTo.appendChild(newClone);
}

async function createClonedItemsWithPhrase(phrase, word, phraseFrame, highlightItem, defaultItem, shouldHideHighlight) {
	const lowerWord = word.toLowerCase();

	// Try normal space-based split
	let parts = phrase.split(' ');
	const found = parts.some(part => part.toLowerCase() === lowerWord);

	// If no exact part matches, fall back to substring split
	if (!found) {
		parts = [];
		let remaining = phrase;
		while (remaining.length > 0) {
			const index = remaining.toLowerCase().indexOf(lowerWord);
			if (index === -1) {
				parts.push(remaining);
				break;
			}
			if (index > 0) {
				parts.push(remaining.slice(0, index)); // non-match
			}
			parts.push(remaining.slice(index, index + word.length)); // match
			remaining = remaining.slice(index + word.length);
		}
	}

for (const part of parts) {
	if (part.toLowerCase() === lowerWord) {
		let highlightPart = part;
		if (shouldHideHighlight) {
			highlightPart = highlightPart.replace(/./g, '_');
		}
		await cloneAndAppendItemWithNewText(highlightItem, phraseFrame, highlightPart);
	} else {
		await cloneAndAppendItemWithNewText(defaultItem, phraseFrame, part);
	}
}

// Clean up children
phraseFrame.children.forEach(child => {
	if (child.name !== 'done') child.remove();
});
}


async function createClonedItemsForParent(textItems, parentFrame, toClone) {
	for (const part of textItems) {
		await cloneAndAppendItemWithNewText(toClone, parentFrame, part);
	}

	parentFrame.children.forEach(child => {
		if (child.name !== 'done') child.remove();
	});
}

// function getRandomLettersFromPhraseAndWord(phrase, word) {
// 	phrase.split(' ').forEach(part => {
// 		if (part !== word) {

// 		} 
// 	})
// }

function shuffleArray(array) {
	const arr = [...array];
	for (let i = arr.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[arr[i], arr[j]] = [arr[j], arr[i]];
	}
	return arr;
}

// function getRandomLettersFromPhraseAndWord(phrase, word) {
// 	const maxTotal = 11;
// 	const wordLetters = word.split('')
// 	const maxFromPhrase = maxTotal - wordLetters.length

// 	let phraseLetters = [];
// 	phrase.split(' ').forEach(part => {
// 		if (part !== word) {
// 			phraseLetters.push(...part.split(''));
// 		}
// 	});

// 	phraseLetters = shuffleArray(phraseLetters);
// 	const selectedPhraseLetters = phraseLetters.slice(0, maxFromPhrase);
// 	const combined = [...selectedPhraseLetters, ...wordLetters];

// 	return shuffleArray(combined);
// }

function getRandomLettersFromPhraseAndWord(phrase, word) {
	const maxTotal = 11;
	const wordLetters = word.toLowerCase().split('');
	const maxFromPhrase = maxTotal - wordLetters.length;

	let phraseLetters = [];
	phrase.split(' ').forEach(part => {
		if (part !== word) {
			phraseLetters.push(...part.toLowerCase().split(''));
		}
	});

	phraseLetters = shuffleArray(phraseLetters);
	const selectedPhraseLetters = phraseLetters.slice(0, maxFromPhrase);
	const combined = [...selectedPhraseLetters, ...wordLetters];

	return shuffleArray(combined);
}

// function generateShuffledWordOptions(word) {
// 	const options = new Set();

// 	options.add(word);

// 	while (options.size < 3) {
// 		const shuffled = shuffleWord(word);
// 		if (shuffled !== word) {
// 			options.add(shuffled);
// 		}
// 	}

// 	return shuffleArray([...options]);
// }

// function shuffleWord(word) {
// 	const arr = word.split('');
// 	for (let i = arr.length - 1; i > 0; i--) {
// 		const j = Math.floor(Math.random() * (i + 1));
// 		[arr[i], arr[j]] = [arr[j], arr[i]];
// 	}
// 	return arr.join('');
// }

function generateShuffledWordOptions(word) {
	const options = new Set();
	const isCapitalized = isWordCapitalized(word);

	options.add(word);

	while (options.size < 3) {
		let shuffled = shuffleWord(word);
		if (shuffled !== word) {
			if (isCapitalized) {
				shuffled = capitalize(shuffled);
			} else {
				shuffled = shuffled.toLowerCase();
			}
			options.add(shuffled);
		}
	}

	return shuffleArray([...options]);
}

function shuffleWord(word) {
	const arr = Array.from(word); // Supports Unicode characters correctly
	for (let i = arr.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[arr[i], arr[j]] = [arr[j], arr[i]];
	}
	return arr.join('');
}

function isWordCapitalized(word) {
	const arr = Array.from(word);
	return arr.length > 0 &&
		arr[0] === arr[0].toUpperCase() &&
		arr.slice(1).join('') === arr.slice(1).join('').toLowerCase();
}

function capitalize(word) {
	const arr = Array.from(word);
	if (arr.length === 0) return '';
	return arr[0].toUpperCase() + arr.slice(1).join('').toLowerCase();
}

function shuffleArray(array) {
	for (let i = array.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[array[i], array[j]] = [array[j], array[i]];
	}
	return array;
}


async function create_translated_instances_for_lang(targetComponentsEntries, ui_src_lang, dst_lang, paddingY, popularLangs, targetWidth, targetHeight) {
	// console.log(targetComponentsEntries)

	for (const [targetComponentName, targetComponent] of targetComponentsEntries) {
		const originalX = targetComponent.x
		const originalY = targetComponent.y

		let instance = targetComponent.createInstance().detachInstance()

		if (!instance) {
			console.error('The instance is null or undefined.')
			console.log('Instance type:', instance.type)
			return
		}

		instance.x = originalX
		instance.y = originalY + paddingY
		instance.name = instance.name + `_${dst_lang}`
		instance.resize(targetWidth, targetHeight)

		let matchedName = null
		const phraseFrame1 = 'phrase_frame_1'
		const phraseFrame2 = 'phrase_frame_2'
		const possibleNames = [phraseFrame1, phraseFrame2]

		let phrases_frame = instance.findOne(node => {
			if (node.type === 'FRAME' && possibleNames.includes(node.name)) {
				matchedName = node.name
				return true
			}
			return false
		})

		if (matchedName !== null) {
			let src_phrase = matchedName === phraseFrame1 ? 'Princess is happy today' : 'The book was published'
			let src_word = matchedName === phraseFrame1 ? 'princess' : 'book'

			let dst_phrase_pair = null

			let phrase_src_lang = ui_src_lang
			const phrase_dst_lang_to_translate = popularLangs[0]

			if (ui_src_lang !== phrase_dst_lang_to_translate) {
				phrase_src_lang = phrase_dst_lang_to_translate
				const translated_phrase_pair = await translate_word_phrase(src_phrase, src_word, ui_src_lang, phrase_dst_lang_to_translate)
				src_phrase = translated_phrase_pair.dst_phrase
				src_word = translated_phrase_pair.dst_word
			}

			dst_phrase_pair = await translate_word_phrase(src_phrase, src_word, phrase_src_lang, dst_lang)

			const dst_phrase = dst_phrase_pair.dst_phrase
			const dst_word = dst_phrase_pair.dst_word

			console.log(`popularLangs[0]: ${popularLangs[0]}`)
			console.log(`phrase_src_lang: ${phrase_src_lang}`)
			console.log(`dst_lang: ${dst_lang}`)
			console.log(`src_phrase: ${src_phrase}`)
			console.log(`src_word: ${src_word}`)
			console.log(`dst_phrase: ${dst_phrase}`)
			console.log(`dst_word: ${dst_word.toLowerCase()}`)

			let src_phrase_frame = phrases_frame.findOne(node => node.type === 'FRAME' && node.name === 'src_phrase_frame')
			let word_item_hidden = src_phrase_frame.findOne(node => node.name === 'word_item_hidden')
			let src_word_item = src_phrase_frame.findOne(node => node.name === 'word_item')
			await createClonedItemsWithPhrase(src_phrase, src_word, src_phrase_frame, word_item_hidden, src_word_item, true)

			let native_phrase_frame = phrases_frame.findOne(node => node.type === 'FRAME' && node.name === 'native_phrase_frame')
			let word_item_translation = native_phrase_frame.findOne(node => node.name === 'word_item_translation')
			let native_word_item = native_phrase_frame.findOne(node => node.name === 'word_item')
			await createClonedItemsWithPhrase(dst_phrase, dst_word, native_phrase_frame, word_item_translation, native_word_item, false)

			if (matchedName === phraseFrame1) {
				let src_phrase_guess_letters = phrases_frame.findOne(node => node.type === 'FRAME' && node.name === 'src_phrase_guess_letters')
				let guess_letter_frame = src_phrase_guess_letters.findOne(node => node.type === 'FRAME')

				let guess_letters = getRandomLettersFromPhraseAndWord(src_phrase, src_word)
				await createClonedItemsForParent(guess_letters, src_phrase_guess_letters, guess_letter_frame)
			} else if (matchedName === phraseFrame2) {
				let src_phrase_guess_words = phrases_frame.findOne(node => node.type === 'FRAME' && node.name === 'src_phrase_guess_words')
				let guess_button = src_phrase_guess_words.findOne(node => node.name === 'input_field/guess_button')

				let guess_words = generateShuffledWordOptions(src_word)
				await createClonedItemsForParent(guess_words, src_phrase_guess_words, guess_button)
			}

			const guess_frame_to_find = matchedName === phraseFrame1 ? 'src_phrase_guess_letters' : 'src_phrase_guess_words'
			let guess_frame = phrases_frame.findOne(node => node.type === 'FRAME' && node.name === guess_frame_to_find)
			let guess_texts = getAllInstanceTexts(guess_frame)

			console.log(`Guess texst count: ${guess_texts.length}`)

			let texts = getAllInstanceTexts(phrases_frame)
			for (const textNode of texts) {
				if (dst_lang in exception_fonts)
					await setFontForText(dst_lang, textNode)
			}

			console.log("Found matched name: " + matchedName)
		}

		// get text instances
		let instance_texts = getAllInstanceTexts(instance)

		// let is_src_and_dst_lang_the_same = ui_src_lang === dst_lang
		let prevTextNode = null

		for (const textNode of instance_texts) {
			if (textNode.name === 'done') continue
			if (prevTextNode !== null) prevTextNode.name = 'done'

			prevTextNode = textNode
			let translated_text = ""

			if (textNode.name === "text_native") {
				const translation_result = await fetchTranslation(textNode.characters, textNode.name, ui_src_lang, dst_lang, popularLangs)
				translated_text = translation_result.text
			} else if (textNode.name === "text_src") {
				let cur_dst_lang = popularLangs[0]
				if (cur_dst_lang === ui_src_lang) continue
				const translation_result = await fetchTranslation(textNode.characters, textNode.name, ui_src_lang, cur_dst_lang, popularLangs)
				translated_text = translation_result.text
			} else if (textNode.name === "text_native_lang_1") {
				translated_text = await translate_language(popularLangs[0], dst_lang)
			} else if (textNode.name === "text_native_lang_2") {
				translated_text = await translate_language(popularLangs[1], dst_lang)
			} else {
				continue
			}

			const fontName = textNode.fontName
			if (fontName !== figma.mixed) {
				await figma.loadFontAsync(fontName)
			} else {
				console.error(`Mixed fonts found in text node: ${textNode.name}. Cannot load.`)
				continue
			}

			if (dst_lang in exception_fonts)
				await setFontForText(dst_lang, textNode)

			textNode.characters = translated_text
		}
	}
}

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
}

// const languages = {
// 	'ru': ['en', 'de'], 'en': ['es', 'fr'], 'zh': ['en', 'ja'], 'kk': ['ru', 'en'], 'pa': ['en', 'hi']
// }

// const languages = {
// 	'kk': ['ru', 'en']
// }

const exception_fonts = {'hy': 'Noto Sans Armenian', 'my': 'Noto Sans Myanmar', 'am': 'Noto Sans Ethiopic', 'pa': 'Noto Sans Gurmukhi'}

const excluded_langs = new Set(['my', 'ta'])

const targetComponentsNames = ["1_store_main", "2_store_simple_and_fast", "3_store_instant_feedback",
	"4_store_topic_generation", "5_store_statistics", "6_learn_multiple_languages", "7_store_dark_theme"
]

// const targetComponentsNames = ["2_store_simple_and_fast"]

await figma.loadAllPagesAsync()

const allComponents = figma.root.findAll(node => node.type === 'COMPONENT')

const targetComponentsEntries = []
for (const component of allComponents) {
    if (targetComponentsNames.includes(component.name)) {
		if (!component) console.error(`Component ${component.name} undefined`)
		targetComponentsEntries.push([component.name, component])
    }
}

targetComponentsEntries.sort((a, b) => {
	return targetComponentsNames.indexOf(a[0]) - targetComponentsNames.indexOf(b[0])
})

for (const componentName of targetComponentsNames) {
	const found = targetComponentsEntries.some(([name]) => name === componentName)
	if (!found) {
		console.error(`Component ${componentName} not found`)
	}
}

// let widthOfComponent = 1080
// let heightOfComponent = 1920
// let paddingBetween = 100

let widthOfComponent = 1242
let heightOfComponent = 2688
let paddingBetween = 100

let paddingY = heightOfComponent + paddingBetween

const test_langs = new Set(['hy'])

for (const [dst_lang, popular_langs] of Object.entries(languages)) {
	const ui_src_lang = 'en'

	if (excluded_langs.has(dst_lang)) continue
	if (dst_lang in exception_fonts) continue

	await create_translated_instances_for_lang(targetComponentsEntries, ui_src_lang, dst_lang, paddingY, popular_langs, widthOfComponent, heightOfComponent)

	paddingY = paddingY + heightOfComponent + paddingBetween
}

console.log(`Error count: ${error_count}`)