# Recategorize quotation navigation templates
# https://en.wiktionary.org/wiki/Wiktionary:Beer_parlour/2024/September#Recategorizing_quotation_navigation_templates_by_bot

import argparse
import re

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--dry-run', action='store_true')
	parser.add_argument('-l', '--limit', type=int, default=10 ** 9)
	args = parser.parse_args()

	site = pywikibot.Site()
	quote_cat = pywikibot.Category(site, 'Quotation templates by language')
	for lang_quote_cat in quote_cat.subcategories():
		lang_quote_temps = pywikibot.pagegenerators.CategorizedPageGenerator(lang_quote_cat)
		lang_quote_nav_cat_title = lang_quote_cat.title().replace('quotation', 'quotation navigation')
		lang_quote_nav_count = 0
		for lang_quote_temp in lang_quote_temps:
			if args.limit <= 0:
				break
			temp_title = lang_quote_temp.title()
			# Modify categories at e.g. [[Template:Douglas Adams quotation templates/documentation]]
			if temp_title.endswith(' quotation templates'):
				args.limit -= 1
				doc_page = pywikibot.Page(site, temp_title + '/documentation')
				doc_text = doc_page.text

				# Remove [[cat:Navigation templates]]
				nav_cat_match = re.search(r'\[\[Category:Navigation templates(?:\|(.*?))?\]\]\n', doc_text)
				if nav_cat_match:
					doc_text = doc_text[:nav_cat_match.start()] + doc_text[nav_cat_match.end():]
				# Replace [[cat:English quotation templates]] with [[cat:English quotation navigation templates]]
				quote_cat_match = re.search(r'\[\[' + lang_quote_cat.title() + r'(?:\|(.*?))?\]\]\n', doc_text)
				if quote_cat_match:
					doc_text = doc_text[:quote_cat_match.start()] + '[[' + lang_quote_nav_cat_title + ']]\n' + doc_text[quote_cat_match.end():]
				else:
					print(f'\n===\nError: Could not find language-specific quotation category link at {doc_page.title()}\n===\n')
					continue
				# Update sort key
				defaultsort_match = re.search(r'\{\{DEFAULTSORT:(.*?)\}\}', doc_text)
				if defaultsort_match:
					sort_key = defaultsort_match[1]
					if sort_key.startswith('*'):
						doc_text = doc_text[:defaultsort_match.start(1)] + sort_key.removeprefix('*') + doc_text[defaultsort_match.end(1):]
					else:
						print(f'\n===\nError: Found DEFAULTSORT for {doc_page.title()}, but the sort key did not start with an asterisk.\n===\n')
						continue
				else:
					print(f'\n===\nError: Could not find defaultsort for {doc_page.title()}.\n===\n')
					continue
				if args.dry_run:
					with open(doc_page.title(underscore=True, with_ns=False).removesuffix('_quotation_templates/documentation') + '.txt', 'w') as out_file:
						out_file.write(doc_text)
				else:
					doc_page.text = doc_text
					doc_page.save(summary='Recategorize quotation navigation templates per [[Wiktionary:Beer parlour/2024/September#Recategorizing quotation navigation templates by bot|discussion]]', bot=True)
				lang_quote_nav_count += 1

				# Null edit so the template appears in the quotation navigation category
				if not args.dry_run:
					pywikibot.Page(site, temp_title).touch(bot=True)

		# Create [[cat:English quotation navigation templates]] if necessary
		if lang_quote_nav_count:
			lang_quote_nav_cat = pywikibot.Category(site, lang_quote_nav_cat_title)
			if not lang_quote_nav_cat.exists():
				if args.dry_run:
					print(f'Would create {lang_quote_nav_cat_title}')
				else:
					lang_quote_nav_cat.text = '{{auto cat}}\n'
					lang_quote_nav_cat.save(summary='Recategorize quotation navigation templates per [[Wiktionary:Beer parlour/2024/September#Recategorizing quotation navigation templates by bot|discussion]]', bot=True)
				args.limit -= 1
		if args.limit <= 0:
			break

if __name__ == '__main__':
	main()
