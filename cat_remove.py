import argparse
import wiktionary_cats

def main():
	parser = argparse.ArgumentParser(description='Remove all mainspace pages from a given category.')
	parser.add_argument('base_name', help='The base name (removing the language name prefix for langname categories, and the language code prefix for topic categories) of the category to remove pages from.')
	parser.add_argument('lang_code', help='The ISO 639 code of the language of the secondary category for langname and topic categories.')
	parser.add_argument('lang_name', help='The full name of the language for langname and topic categories')
	parser.add_argument('-t', '--topic', action='store_true', help='Indicates that the category to remove pages from is a topic category (like Category:en:Philosophy), not a langname category (like Category:English nouns). This determines what templates will be searched for on pages in the category.')
	parser.add_argument('-s', '--summary', help='The edit summary to use when saving the pages.')
	parser.add_argument('-d', '--dry-run', action='store_true', help='Save changed pages locally instead of remotely (so no change is made to the remote).')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	save_kwargs = {'summary': args.summary if 'summary' in args else None, 'botflag': True, 'quiet': not args.verbose}

	cat = wiktionary_cats.WiktionaryCat(args.base_name, args.lang_code, args.lang_name, args.topic)
	for page in cat.to_generator():
		cat.remove_one(page)
		if args.dry_run:
			with open(page.title().casefold().replace('/', '_').replace(' ', '_') + '.wiki', 'w', encoding='utf-8') as outFile:
				outFile.write(page.text)
		else:
			page.save(**save_kwargs)

if __name__ == '__main__':
	main()
