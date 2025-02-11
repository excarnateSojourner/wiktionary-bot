'''
Find language considerations pages by title and categorize those that are not yet in Category:Wiktionary language considerations.
'''

import pywikibot
import pywikibot.pagegenerators

import wikitextparser

import advanced_move

DRY_RUN = False
LANG_CONS_PREFIX = 'About '
REDIRECT_PREFIX = '#redirect'
WIKTIONARY_NS_ID = 4

def main():
	site = pywikibot.Site()
	lang_cons_cat = pywikibot.Category(site, 'Wiktionary language considerations')
	reason = f'Add to {lang_cons_cat.title(as_link=True, textlink=True)}'
	for page in pywikibot.pagegenerators.PrefixingPageGenerator(LANG_CONS_PREFIX, namespace=site.namespaces[WIKTIONARY_NS_ID], site=site):
		# Already categorized
		if lang_cons_cat in page.categories():
			continue
		# Skip redirects
		if startswith_casefold(page.text, REDIRECT_PREFIX):
			continue
		lang = page.title(with_ns=False).removeprefix(LANG_CONS_PREFIX)
		# Skip subpages
		if '/' in lang:
			continue
		# Skip if it's just a link to Wikipedia
		if len(page.text) < 128 and any(temp.normal_name() == 'pedia' for temp in wikitextparser.parse(page.text).templates):
			continue
		print(f'Size of {page.title()} before editing: {len(page.text)}')
		# Categorize the page
		if lang.startswith('Proto-'):
			lang = lang.removeprefix('Proto-')
			cat_link = lang_cons_cat.aslink(sort_key=f'{lang}, Proto')
		else:
			cat_link = lang_cons_cat.aslink(sort_key=lang)
		new_text = f'{page.text}\n{cat_link}'
		advanced_move.edit(page, new_text, reason, dry_run=DRY_RUN)

def startswith_casefold(st: str, prefix: str) -> bool:
	return st[:len(prefix)].casefold() == prefix.casefold()

if __name__ == '__main__':
	main()
