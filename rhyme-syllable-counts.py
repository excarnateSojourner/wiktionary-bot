import argparse
import pywikibot
import pywikibot.pagegenerators
import re

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('syllable_count', type=int)
	parser.add_argument('page_count', type=int)
	parser.add_argument('-e', '--exclusion-distance', default=2, type=int)
	parser.add_argument('-d', '--dry-run', action='store_true')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	site = pywikibot.Site()
	cat = pywikibot.Category(site, f'Category:English {args.syllable_count}-syllable words')

	# We want to exclude any terms that fall in multiple "English N-syllable words" categories.
	exclude_terms = set()
	for count in list(range(max(args.syllable_count - args.exclusion_distance, 1), args.syllable_count)) + list(range(args.syllable_count + 1, min(args.syllable_count + args.exclusion_distance + 1, 19))):
		exclude_cat = pywikibot.Category(site, f'Category:English {count}-syllable words')
		for page in pywikibot.pagegenerators.CategorizedPageGenerator(exclude_cat):
			exclude_terms.add(page.title())

	gen = pywikibot.pagegenerators.CategorizedPageGenerator(cat)
	hits = 0
	for i, page in enumerate(gen):
		if hits >= args.page_count:
			break
		if page.title() in exclude_terms:
			# DEBUG
			print(f'Skipping "{page.title()}".')
			continue
		if re.fullmatch(r'[a-z]+', page.title(), flags=re.IGNORECASE):
			page.text, page_hits = re.subn(r'(^\*+ {{rhymes?\|en(\|(q\d*=)?[^=|}' + '\n' + ']*)+)(?=}}$)', r'\1|s=' + str(args.syllable_count), page.text, flags=re.MULTILINE)
			if page_hits:
				hits += 1
				if args.dry_run:
					with open(page.title() + '.wiki', 'w') as page_file:
						page_file.write(page.text)
					if args.verbose:
						print(f'Added syllable count(s) to "{page.title()}".')
				else:
					page.save(summary='Add syllable counts to English rhymes.', botflag=True)
		if i % 100 == 0:
			print(f'Progress: {i}')

if __name__ == '__main__':
	main()
