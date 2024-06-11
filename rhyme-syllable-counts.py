import argparse
import itertools
import re

import pywikibot
import pywikibot.pagegenerators

DRY_RUN_LIMIT = 10 ** 3
TEMP_PARAMS_PATTERN = r'(\|(q\d*=)?[^=|}' + '\n' + r']*)+'

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--limit', default=-1, type=int)
	parser.add_argument('-d', '--dry-run', action='store_true')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	site = pywikibot.Site()
	cats = {}
	for syllable_count in range(1, (2 if args.dry_run else 20)):
		cat = pywikibot.Category(site, f'Category:English {syllable_count}-syllable words')
		gen = pywikibot.pagegenerators.CategorizedPageGenerator(cat)
		cats[syllable_count] = {page for page in (itertools.islice(gen, DRY_RUN_LIMIT) if args.dry_run else gen)}

# We want to exclude any terms that fall in multiple "English N-syllable words" categories.
	if args.verbose:
		print('Excluding entries that are in multiple categories:')
	for cat in cats.values():
		for other in cats.values():
			if other != cat:
				if args.verbose:
					for page in cat & other:
						cat.discard(page)
						print(page.title())
				else:
					cat -= other

	if args.verbose:
		print('Adding syllable counts. Periods represent pages for which no action was taken.')
	hits = 0
	for syllable_count, cat in cats.items():
		if args.verbose:
			print(f'{syllable_count}-syllable words:')
		for page in cat:
			if 0 < args.limit <= hits:
				break
			if re.fullmatch(r'[a-z]+', page.title(), flags=re.IGNORECASE):
				page.text, page_hits = re.subn(r'^(\*+ {{rhymes?\|en' + TEMP_PARAMS_PATTERN + r')}}$', r'\1|s=' + str(syllable_count) + r'}}', page.text, flags=re.MULTILINE)
				if page_hits:
					hits += 1
					if args.dry_run:
						with open(page.title() + '.wiki', 'w') as page_file:
								page_file.write(page.text)
					else:
						page.save(summary='Add syllable counts to English rhymes ([[Wiktionary:Beer parlour/2024/April#Copying rhyme syllable counts from existing categories|discussion]]).', botflag=True)
					if args.verbose:
							print(f'Added syllable count of {syllable_count} to "{page.title()}".')
				elif args.verbose:
					print('.', end='')
	if args.verbose:
		print()

if __name__ == '__main__':
	main()
