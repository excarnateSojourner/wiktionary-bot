import argparse
import itertools

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

VERBOSE_FACTOR = 100

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('old_name')
	parser.add_argument('new_name')
	entry_iterators = parser.add_mutually_exclusive_group(required=True)
	entry_iterators.add_argument('-l', '--language', help='Indicates that only entries in the given language should be scanned. Required if --category is not given. Overrides --category.')
	entry_iterators.add_argument('-c', '--category', help='Indicates that only entries in the given category should be scanned. Required if --language is not given. Ignored if --language is given.')
	parser.add_argument('summary', help='The edit summary to use when replacing uses of the old template with the new one.')
	parser.add_argument('-d', '--dry-run', action='store_true')
	parser.add_argument('-i', '--limit', type=int, default=-1)
	args = parser.parse_args()

	site = pywikibot.Site()
	if args.language:
		target_cat_titles = [f'{args.language} lemmas', f'{args.language} non-lemma forms']
	# args.category must have been given
	else:
		target_cat_titles = [args.category]
	target_cats = [pywikibot.Category(site, cat_title) for cat_title in target_cat_titles]
	for cat in target_cats:
		if not cat.exists():
			print(f'Warning: {cat.title()} does not exist, so it is unlikely to contain entries.')

	edit_count = 0
	page_iters = [pywikibot.pagegenerators.CategorizedPageGenerator(cat) for cat in target_cats]
	for page_count, page in enumerate(itertools.chain.from_iterable(page_iters)):
		if 0 < args.limit <= edit_count:
			break
		if page_count % VERBOSE_FACTOR == 0:
			print(page_count, flush=True)

		wikitext = wikitextparser.parse(page.text)
		target_temps = [temp for temp in wikitext.templates if temp.normal_name() == args.old_name]
		if not target_temps:
			continue
		for temp in target_temps:
			temp.name = args.new_name
		if args.dry_run:
			with open(f'{page.title()}.txt', 'w') as out_file:
				out_file.write(str(wikitext))
			print(f'Saved {page.title()}')
		else:
			page.text = str(wikitext)
			page.save(summary=args.summary, bot=True, quiet=False)
		edit_count += 1

if __name__ == '__main__':
	main()
