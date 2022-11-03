import argparse
import re

import pywikibot
import pywikibot.pagegenerators

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('syllable_count')
	parser.add_argument('-l', '--limit', default=10**9, type=int, help='The maximum number of pages to edit.')
	parser.add_argument('-d', '--dry-run', action='store_true', help='Save each page locally after processing it instead of saving remotely.')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	site = pywikibot.Site()
	cat = pywikibot.Category(site, f'Category:English {args.syllable_count}-syllable words')
	gen = pywikibot.pagegenerators.CategorizedPageGenerator(cat)
	page_count = 0
	for page in gen:
		if page_count >= args.limit:
			break
		if ' ' in page.title():
			page.text, replace_count = re.subn(r'(^\*+ {{IPA\|en(\|[^ |' + '\n' + r']*)+)}}', r'\1|nocount=1}}', page.text, flags=re.IGNORECASE | re.MULTILINE)
			if replace_count:
				if args.dry_run:
					with open(page.title().replace(' ', '_') + '.wiki', 'w') as page_file:
						page_file.write(page.text)
					if args.verbose:
						print(f'Saving {page.title()}.wiki.')
				else:
					page.save(summary=f'Remove from [[Category:English {args.syllable_count}-syllable words]].', botflag=True, quiet=not args.verbose)
				page_count += 1

if __name__ == '__main__':
	main()
