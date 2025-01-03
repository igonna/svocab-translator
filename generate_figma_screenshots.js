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
	'tl': ['en', 'tl'], 'am': ['en', 'ar'], 'kn': ['en', 'hi'], 'so': ['en', 'ar'], 'bg': ['en', 'ru'], 'pa': ['en', 'hi']
};

// const languages = ['en']

targetComponentsNames = ["1_store_main", "2_store_simple_and_fast", "3_store_instant_feedback",
	"4_store_topic_generation", "5_store_statistics", "6_store_topics_mix", "7_store_multiple_languages",
	"8_store_dark_theme"
]

// targetComponentsNames = ["5_store_statistics"]

async function translateAllInstances(lang, paddingY) {
	let allComponents = figma.root.findAll(node => node.type === 'COMPONENT');
	for (const targetComponentName of targetComponentsNames) {
		let targetComponent = allComponents.find(node => node.name === targetComponentName);
	
		// let addedTotalPadding = false;
	
		if (targetComponent) {
			const originalX = targetComponent.x;
			const originalY = targetComponent.y;
	
			let instance = targetComponent.createInstance();

			if (!instance) {
				console.error('The instance is null or undefined.');
				return;
			}
		
			// Log the type of instance for debugging purposes
			console.log('Instance type:', instance.type);
			
			// Ensure that instance is a ComponentInstance
			if (instance.type !== 'INSTANCE') {
				console.error('The node is not a ComponentInstance:', instance);
				return;
			}
	
			instance.x = originalX;
			instance.y = originalY + paddingY;
	
			async function fetchTranslation(originalText) {
				try {
					const response = await fetch('http://localhost:30032/translate', {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({ text: originalText })
					});
	
					if (!response.ok) {
						console.error("Error fetching translation:", response.statusText);
						return originalText;
					}
	
					const data = await response.json();
					return data.translatedText || originalText;
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
	
					const translatedText = await fetchTranslation("Hello");
					textNode.characters = translatedText;
				}
			}
	
			await translateInstanceTexts("", instance);
		} else {
			console.log(`Component ${targetComponentName} not found.`);
		}
	}
}

let heightOfComponent = 1920;
let paddingBetween = 100;

let paddingY = heightOfComponent + paddingBetween;

for (const [lang, value] of Object.entries(languages)) {
	await translateAllInstances(lang, paddingY)

	paddingY = paddingY + heightOfComponent + paddingBetween;
}