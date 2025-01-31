import argparse
import difflib
import re

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

MOVE_SUMMARY = 'Moved to match the title of [[Wiktionary:English entry guidelines]] per [[Wiktionary talk:English entry guidelines#RFM discussion: November 2015–August 2018|old RFM]] and [[Wiktionary:Requests for moves, mergers and splits#Wiktionary:English entry guidelines vs "About (language)" in every other language|new RFM]]'
REDIRECT_SUMMARY = 'Moved target to match the title of [[Wiktionary:English entry guidelines]] per [[Wiktionary talk:English entry guidelines#RFM discussion: November 2015–August 2018|old RFM]] and [[Wiktionary:Requests for moves, mergers and splits#Wiktionary:English entry guidelines vs "About (language)" in every other language|new RFM]]'
SORT_KEY_SUMMARY = 'Removed redundant sort key'
VERBOSE_FACTOR = 10
BANNED_TITLE_PARTS = ['/', 'language', 'script', 'transliteration']
# Reconstruction backlinks are acceptable because because [[Template:reconstructed]] links to the language consideration page for the term's language, causing every term in a reconstructed language to be a backlink
ACCEPTABLE_BACKLINK_PREFIXES = ['Talk:', 'User:', 'Reconstruction:', 'Wiktionary:Beer parlour', 'Wiktionary:Etymology scriptorium', 'Wiktionary:Information desk', 'Wiktionary:Grease pit', 'Wiktionary:Tea room', 'Wiktionary:Requests for ', 'Wiktionary:Translation requests/archive', 'Wiktionary:News for editors/Archive', 'Wiktionary:Votes/']
LANG_CONS_CAT_TITLE = 'Category:Wiktionary language considerations'

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--skip', nargs='*', default=[], help='A list of languages which should not have their language consideration pages moved.')
	parser.add_argument('-d', '--dry_run', action='store_true')
	parser.add_argument('-l', '--limit', type=int, default=-1)
	args = parser.parse_args()

	site = pywikibot.Site()
	lang_cons_cat = pywikibot.Category(site, LANG_CONS_CAT_TITLE)
	lang_cons = pywikibot.pagegenerators.CategorizedPageGenerator(lang_cons_cat)
	move_count = 0
	for page in lang_cons:
		if 0 <= args.limit <= move_count:
			break
		title = page.title()
		# If already done
		if title.endswith(' entry guidelines'):
			continue
		title_lower = title.casefold()
		if not title.startswith('Wiktionary:About ') or any(banned in title_lower for banned in BANNED_TITLE_PARTS):
			print(f'Warning: Skipping {title} because its title does not fit the expected pattern.')
			continue
		lang = title.removeprefix('Wiktionary:About ')
		if lang in args.skip:
			continue
		if any(word[0].islower() for word in lang.split()):
			print(f'Warning: Skipping {title} because its language would not be titlecased.')
			continue
		new_title = 'Wiktionary:' + lang + ' entry guidelines'
		automatable_redirects = []
		manual_redirect_titles = []
		for redirect in page.redirects():
			red_title = redirect.title()
			if re.fullmatch(r'Wiktionary:A[A-Z]{2,3}(-[A-Z]{3})?', red_title):
				automatable_redirects.append(redirect)
			else:
				manual_redirect_titles.append(red_title)
		# Find only direct links from pages (not redirects or pages that link to redirects)
		backlink_titles = [bl.title() for bl in page.backlinks(follow_redirects=False, filter_redirects=False)]
		backlink_titles = [bl for bl in backlink_titles if is_backlink_problematic(bl, lang)]
		if manual_redirect_titles or backlink_titles:
			print(f'Stopping at {title} because it has the following backlinks that may need to be manually updated:')
			if manual_redirect_titles:
				print('\tRedirects:')
				for red in manual_redirect_titles:
					print(f'\t\t{red}')
			if backlink_titles:
				print('\tPages:')
				for bl in backlink_titles:
					print(f'\t\t{bl}')
			print('What now? (m = move it and wait for manual backlink updates; s = skip; q = quit)')
			action = input('==> ').casefold()
			if action.startswith('s'):
				continue
			# If quit or invalid action chosen
			if not action.startswith('m'):
				return

		if args.dry_run:
			print(f'Would move [[{title}]] to [[{new_title}]].')
			new_page = page
		else:
			print(f'Moving [[{title}]] to [[{new_title}]].')
			page.move(new_title, reason=MOVE_SUMMARY)
			new_page = pywikibot.Page(site, new_title)
		move_count += 1

		# Update language code redirects
		for red in automatable_redirects:
			wikitext = wikitextparser.parse(red.text)
			original_text = wikitext.string
			red_link = next(link for link in wikitext.wikilinks if link.title == title)
			# Modifies wikitext
			red_link.title = new_title
			edit(red, original_text, wikitext.string, REDIRECT_SUMMARY, dry_run=args.dry_run)

		# Remove redundant sort key
		wikitext = wikitextparser.parse(new_page.text)
		original_text = wikitext.string
		try:
			cat_link = next(link for link in wikitext.wikilinks if link.title == LANG_CONS_CAT_TITLE)
		except StopIteration:
			print(f'Warning: Unable to find category link in {new_title} to {LANG_CONS_CAT_TITLE}.')
			continue
		# Modifies wikitext
		cat_link.string = f'[[{LANG_CONS_CAT_TITLE}]]'
		edit(new_page, original_text, wikitext.string, SORT_KEY_SUMMARY, dry_run=args.dry_run)

		# Confirm that all backlinks have been addressed
		if manual_redirect_titles or backlink_titles:
			print('Waiting for manual backlink updates.')
			input('==>')
		remaining_backlinks = page.backlinks(follow_redirects=False)
		print(f'The following backlinks to {title} remain:')
		for bl in remaining_backlinks:
			print(f'\t{bl.title()}')

def edit(page, original_text, new_text, summary, dry_run=False):
	title = page.title()
	diff = difflib.unified_diff(original_text.splitlines(keepends=True), new_text.splitlines(keepends=True), n=1)
	if dry_run:
		print(f'Would make the following edit at {title}:')
	else:
		print(f'Making the following edit at {title}:')
	for line in diff:
		print(f'\t{line}')
	print()
	if not dry_run:
		page.text = new_text
		page.save(summary=summary)

def is_backlink_problematic(backlink, lang):
	for good_prefix in ACCEPTABLE_BACKLINK_PREFIXES:
		if backlink.startswith(good_prefix):
			return False
	if ' talk:' in backlink:
		return False
	if backlink == f'Category:{lang} language':
		return False

	return True

if __name__ == '__main__':
	main()
