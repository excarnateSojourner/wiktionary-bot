# Add language codes to transclusions of {{lookfrom}}.

import argparse
import re

import pywikibot
import wikitextparser

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d' , '--dry-run', action='store_true')
	parser.add_argument('-l', '--limit', type=int)
	args = parser.parse_args()

	site = pywikibot.Site()
	with open('lookfrom.txt') as list_file:
		for line in list_file:
			if args.limit <= 0:
				break
			page_title = line[:-1]
			if 2 <= len(page_title) <= 3:
				continue
			page = pywikibot.Page(site, page_title)
			parsed = wikitextparser.parse(page.text)
			lang_sections = parsed.get_sections(level=2)
			for section in lang_sections:
				if section.title == 'English':
					if args.dry_run:
						for line in section.contents.splitlines():
							if '{{lookfrom' in line or '{{Lookfrom' in line:
								print(f'Old line at {page_title}:\n{line}')
								line, sub_count = re.subn(r'\{\{[lL]ookfrom(?=\||\}\})', '{{lookfrom|en', line)
								print(f'New line at {page_title}:\n{line}')
								args.limit -= 1
					# For real
					else:
						section.contents, sub_count = re.subn(r'\{\{[lL]ookfrom(?=\||\}\})', '{{lookfrom|en', section.contents)
						if sub_count:
							page.text = str(parsed)
							page.save(summary='Add language code to {{[[Template:lookfrom|lookfrom]]}} ([[Wiktionary:Requests for deletion/Others#Template:lookfrom|discussion]]).', botflag=True)
							args.limit -= 1
						else:
							print(f'No instances of {{{{lookfrom}}}} found at "{page_title}".')
				# Not English
				elif '{{lookfrom' in section.contents or '{{Lookfrom' in section.contents:
					print(f'"{page_title}" has an instance of {{{{lookfrom}}}} in a non-English section.')

if __name__ == '__main__':
	main()
