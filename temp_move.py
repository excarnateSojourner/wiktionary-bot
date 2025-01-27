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
	parser.add_argument('summary', help='The edit summary to use when replacing uses of the old template with the new one.')
	entry_iterators = parser.add_mutually_exclusive_group(required=True)
	entry_iterators.add_argument('-l', '--language', help='Indicates that only entries in the given language should be scanned. Exactly one of -l, -c, and -p must be given.')
	entry_iterators.add_argument('-c', '--category', help='Indicates that only entries in the given category should be scanned. Exactly one of -l, -c, and -p must be given.')
	entry_iterators.add_argument('-p', '--pages', help='A text file in which is listed the titles of the pages to scan (one per line). Exactly one of -l, -c, and -p must be given.')
	parser.add_argument('-d', '--dry-run', action='store_true')
	parser.add_argument('-i', '--limit', type=int, default=-1)
	args = parser.parse_args()

	site = pywikibot.Site()
	if args.language:
		target_cat_titles = [f'{args.language} lemmas', f'{args.language} non-lemma forms']
		target_cats = [pywikibot.Category(site, cat_title) for cat_title in target_cat_titles]
		for cat in target_cats:
			if not cat.exists():
				print(f'Warning: {cat.title()} does not exist, so it is unlikely to contain entries.')
		page_iters = [pywikibot.pagegenerators.CategorizedPageGenerator(cat) for cat in target_cats]
		pages = itertools.chain.from_iterable(page_iters)
	elif args.category:
		target_cat = pywikibot.Category(site, args.category)
		if not target_cat.exists():
			print(f'Warning: {cat.title()} does not exist, so it is unlikely to contain entries.')
		pages = pywikibot.pagegenerators.CategorizedPageGenerator(target_cats)
	# args.pages must have been given
	else:
		with open(args.pages) as pages_file:
			page_titles = [line[:-1] for line in pages_file]
			pages = (pywikibot.Page(site, title) for title in page_titles)

	edit_count = 0
	for page_count, page in enumerate(pages):
		if 0 < args.limit <= edit_count:
			break
		if page_count % VERBOSE_FACTOR == 0:
			print(page_count, flush=True)

		wikitext = wikitextparser.parse(page.text)
		target_temps = [temp for temp in wikitext.templates if temp.normal_name() == args.old_name]
		# Skip pages that do not use the target template
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
