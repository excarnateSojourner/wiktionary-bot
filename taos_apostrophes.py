'''
Replace U+2019 RIGHT SINGLE QUOTATION MARK with U+02BC MODIFIER LETTER APOSTROPHE in Taos entries.
'''

import argparse
import itertools
import re

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

quote_mark = '\N{RIGHT SINGLE QUOTATION MARK}'
mod_letter = '\N{MODIFIER LETTER APOSTROPHE}'
move_summary = 'Replace curly apostrophes (U+2019) with modifier letter apostrophes (U+02BC) per [[Wiktionary:Requests for moves, mergers and splits#Entries in CAT:Taos lemmas with curly apostrophes|discussion]].'
text_summary = move_summary
category_names = ['Taos lemmas', 'Taos non-lemma forms', 'Taos noun forms']

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--limit', default=-1, type=int)
	parser.add_argument('-d', '--dry-run', action='store_true')
	args = parser.parse_args()

	site = pywikibot.Site()
	page_generators = [pywikibot.pagegenerators.CategorizedPageGenerator(pywikibot.Category(site, name)) for name in category_names]
	for i, page in enumerate(itertools.chain.from_iterable(page_generators)):
		if 0 < args.limit <= i:
			print(f'Limit reached.')
			break

		parsed_page = wikitextparser.parse(page.text)
		sections = parsed_page.get_sections(level=2)
		if len(sections) == 1 and sections[0].title.strip() == 'Taos':
			# Replace in page title
			if quote_mark in page.title():
				new_title = page.title().replace(quote_mark, mod_letter)
				if args.dry_run:
					print(f'Would move {page.title(as_link=True)} to [[{new_title}]].')
				else:
					print(f'Moving {page.title(as_link=True)} to [[{new_title}]].')
					page.move(new_title, reason=move_summary)

			# Replace in page text
			section_lines = sections[0].contents.splitlines()
			section_sub_count = 0
			print(f'Reading {page.title(as_link=True)}...')
			for j, line in enumerate(section_lines):
				section_lines[j], line_sub_count = re.subn(f'(?<=\\w){quote_mark}(?=\\w)', mod_letter, line)
				if line_sub_count:
					print(f'Before: ' + line.encode('unicode-escape').decode())
					print(f' After: ' + section_lines[j].encode('unicode-escape').decode())
					section_sub_count += line_sub_count
			if section_sub_count:
				sections[0].contents = '\n'.join(section_lines)
				page.text = str(parsed_page)
				save = input(f'Save changes?\n==> ')
				if save.casefold().startswith('y'):
					if args.dry_run:
						with open(f'{i}-{page.title()}.wiki', 'w') as saveFile:
							saveFile.write(page.text)
					else:
							page.save(summary=text_summary, botFlag=True, quiet=False)
		else:
			print(f'Error: {page.title(as_link=True)} had an unexpected format. Skipped.')

if __name__ == '__main__':
	main()
