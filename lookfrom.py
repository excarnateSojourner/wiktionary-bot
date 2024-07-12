# Add language codes to transclusions of {{lookfrom}}.

import argparse
import re

import pywikibot
import wikitextparser

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d' , '--dry-run')
	parser.add_argument('-v', '--verbose')
	args = parser.parse_args()

	site = pywikibot.Site()
	with open('lookfrom.txt') as list_file:
		for page_title in list_file:
			page = pywikibot.Page(site, page_title)
			parsed = wikitextparser(page.text)
			lang_sections = parsed.get_sections(level=2)
			if len(lang_sections) == 1 and lang_sections[0].title == 'English':
				section.content, sub_count = re.subn(r'\{\{lookfrom(?=\||}})', '{{lookfrom|en', section.content)
			if args.dry_run:
				print(f'New section content:\n{section.content}'))
			else:
				page.text = str(parsed)
				page.save(summary='Add language code to {{lookfrom}} ([[Wiktionary:Requests for deletion/Others#Template:lookfrom|discussion]]).', botflag=True)
