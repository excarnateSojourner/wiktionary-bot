'''
The effect of running
python recategorize.py move Foo Bar
is similar to that of
pwb.py category move Foo Bar
But the latter will always try to move the category page to the new name as well as recategorizing its members. Sometimes this is undesirable.
'''

import argparse

import pywikibot
import pywikibot.pagegenerators

def main():
	parser = argparse.ArgumentParser(description='Add, remove, or replace plain category links in pages.')
	parser.add_argument('action', choices=['add', 'remove', 'replace'], help='Add, remove, or replace.')
	parser.add_argument('existing_cat', help='The existing category to iterate over the members of. If removing, this is also the category to remove. If replacing, this is also the category to replace.')
	parser.add_argument('new_cat', nargs='?', help='If adding, the category to add. If removing, optional and ignored. If replacing, this is the category to replace with.')
	parser.add_argument('-s', '--summary', help='The edit summary to use when saving the pages.')
	parser.add_argument('-d', '--dry-run', '--dr', action='store_true', help='Save changed pages locally instead of remotely (so no change is made to the remote).')
	parser.add_argument('-l', '--limit', default=-1, type=int, help='Limit the number of pages to be moved.')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	site = pywikibot.Site()
	existing_cat = pywikibot.Category(site, args.existing_cat)
	gen = pywikibot.pagegenerators.CategorizedPageGenerator(existing_cat)

	count = 0
	for page in gen:
		if 0 <= args.limit <= count:
			break
		print(f'DEBUG: processing "{page.title()}"')
		if args.action == 'add':
			page.text = pywikibot.textlib.replaceCategoryLinks(page.text, [args.new_cat], site=site, add_only=True)
			if args.dry_run:
				print(f'Would add "{page.title()}" to category "{args.new_cat}".')
		elif args.action == 'remove':
			cats = pywikibot.textlib.getCategoryLinks(page.text, site=site)
			cats.remove(pywikibot.Category(site, args.existing_cat))
			page.text = pywikibot.textlib.replaceCategoryLinks(page.text, cats, site=site)
			if args.dry_run:
				print(f'Would save "{page.title()}" with categories: {cats}')
		# the only other possiblility
		elif args.action == 'replace':
			if args.new_cat:
				new_cat = pywikibot.Category(site, args.new_cat)
			else:
				raise ValueError('You tried to replace a category, but did not specify what other category to replace it with.')
			# sort key is preserved
			page.text = pywikibot.textlib.replaceCategoryInPlace(page.text, existing_cat, new_cat)
			if args.dry_run:
				print(f'Would change category "{args.existing_cat}" to "{args.new_cat}" in "{page.title()}".')
		if not args.dry_run:
			page.save(summary=args.summary, botflag=True, quiet=not args.verbose)
		count += 1

if __name__ == '__main__':
	main()
