import argparse
import re

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

T_CAT_NAMES = {'cat', 'categorize'}
T_CLN_NAMES = {'cln', 'catlangname'}

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('syllable_count', type=int)
	parser.add_argument('-l', '--limit', default=10**9, type=int, help='The maximum number of pages to edit.')
	parser.add_argument('-d', '--dry-run', action='store_true', help='Save each page locally after processing it instead of saving remotely.')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()
	CATEGORY_NAME = f'Category:English {args.syllable_count}-syllable words'
	CATEGORY_LINK = f'\n[[{CATEGORY_NAME}]]'

	site = pywikibot.Site()
	cat = pywikibot.Category(site, CATEGORY_NAME)
	gen = pywikibot.pagegenerators.CategorizedPageGenerator(cat)
	page_count = 0
	for page in gen:
		if page_count >= args.limit:
			break
		if ' ' in page.title():
			contents = wikitextparser.parse(page.text)
			changes = 0
			# if cat explicitly added
			if CATEGORY_LINK in str(contents):
				contents.string = str(contents).replace(CATEGORY_LINK, '')
				changes += 1
				if args.verbose:
					print(f'Removed plain link from [[{page.title}]].')
			if not changes:
				for template in contents.templates:
					template_name = template.normal_name()
					if (template_name in T_CAT_NAMES | T_CLN_NAMES) and template.arguments[0].value == 'en':
						# if the category we are removing was the only one listed in the template, remove the entire template
						if len(template.arguments) == 2 and template_arg_is_cat(template_name, template.arguments[1]):
							contents.string, replacements = re.subn(r'\n?' + re.escape(str(template)), '', str(contents))
							changes += replacements
							if args.verbose:
								print(f'Removed a template link from [[{page.title()}]].')
							break
						else:
							for arg in template.arguments:
								if template_arg_is_cat(template_name, arg):
									template.del_arg(arg.name)
									changes += 1
									if args.verbose:
										print(f'Removed a template link from [[{page.title()}]].')
									break
			if not changes:
				for template in contents.templates:
					if template.normal_name() == 'IPA' and template.arguments[0].value == 'en' and any((' ' not in arg.value) and arg.value.startswith('/') and arg.value.endswith('/') for arg in template.arguments[1:] if arg.positional):
						template.set_arg('nocount', '1')
						changes += 1
						if args.verbose:
							print(f'Added nocount=1 to [[{page.title()}]].')

			if changes:
				page.text = str(contents)
				if args.dry_run:
					filename = page.title().replace(' ', '_') + '.wiki'
					with open(filename, 'w') as page_file:
						page_file.write(page.text)
					if args.verbose:
						print(f'Saving {filename}.')
				else:
					page.save(summary=f'Remove term containing a space from [[:{CATEGORY_NAME}]] ([[Wiktionary:Beer parlour/2022/October#Category:English words by number of syllables|discussion]]).', botflag=True, quiet=not args.verbose)
				page_count += 1
			else:
				print(f'Error: Unable to determine why [[{page.title()}]] is in {CATEGORY_NAME}.')


		def template_arg_is_cat(te_name, te_argument):
			return te_argument.positional and ((te_name in T_CAT_NAMES and te_argument.value == CATEGORY_NAME) or (te_name in T_CLN_NAMES and te_argument.value == CATEGORY_NAME.removeprefix('Category:English ')))

if __name__ == '__main__':
	main()
