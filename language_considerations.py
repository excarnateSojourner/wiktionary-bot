import argparse
import collections.abc
import difflib
import re

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

import pywikibot_helpers

MOVE_SUMMARY = 'Moved to match the title of [[Wiktionary:English entry guidelines]] per [[Wiktionary talk:English entry guidelines#RFM discussion: November 2015–August 2018|old RFM]] and [[Wiktionary:Requests for moves, mergers and splits#Wiktionary:English entry guidelines vs "About (language)" in every other language|new RFM]]'
REDIRECT_SUMMARY = 'Moved target to match the title of [[Wiktionary:English entry guidelines]] per [[Wiktionary talk:English entry guidelines#RFM discussion: November 2015–August 2018|old RFM]] and [[Wiktionary:Requests for moves, mergers and splits#Wiktionary:English entry guidelines vs "About (language)" in every other language|new RFM]]'
SORT_KEY_SUMMARY = 'Removed redundant sort key'
VERBOSE_FACTOR = 10
BANNED_TITLE_PARTS = ['/', 'language', 'script', 'transliteration']
# Reconstruction backlinks are acceptable because because [[Template:reconstructed]] links to the language consideration page for the term's language, causing every term in a reconstructed language to be a backlink
ACCEPTABLE_BACKLINK_PREFIXES = ['Talk:', 'User:', 'Reconstruction:', 'Wiktionary:Beer parlour', 'Wiktionary:Etymology scriptorium', 'Wiktionary:Information desk', 'Wiktionary:Grease pit', 'Wiktionary:Tea room', 'Wiktionary:Requests for ', 'Wiktionary:Translation requests/archive', 'Wiktionary:News for editors/Archive', 'Wiktionary:Votes/', 'Wiktionary:Language treatment requests']
LANG_CONS_CAT_TITLE = 'Category:Wiktionary language considerations'
BACKLINK_DISPLAY_MAX = 200

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
			print(f'Note: Skipping [[{title}]] because its title does not fit the expected pattern.')
			continue
		lang = title.removeprefix('Wiktionary:About ')
		if lang in args.skip:
			continue
		if any(word[0].islower() for word in lang.split()):
			print(f'Note: Skipping [[{title}]] because its language would not be titlecased.')
			continue

		new_title = f'Wiktionary:{lang} entry guidelines'
		backlinks = get_and_print_backlinks(page, lang)
		print('What now? (m = move it and and update backlinks; s = skip; q = quit)')
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
			try:
				# Move the page and its subpages (but leave backlinks for later)
				pywikibot_helpers.advanced_move(page, new_title, MOVE_SUMMARY, backlinks='none', dry_run=args.dry_run)
				new_page = pywikibot.Page(site, new_title)
			except pywikibot.exceptions.LockedPageError:
				print(f'Warning: Skipping [[{title}]] because the page is protected (so I can\'t move it).')
				continue
		move_count += 1

		# Update backlinks
		for link_target_title, links in backlinks.items():
			subpage_part = link_target_title.partition('/')[2]
			new_link_target_title = f'{new_title}/{subpage_part}' if subpage_part else new_title
			for bl in links:
				bl_title = bl.title()
				if (bl_title.startswith('Template:') or bl_title.startswith('Module:')) and not bl_title.endswith('/documentation'):
					print(f'Warning: [[{bl_title}]] links to [[{link_target_title}]], but I am NOT going to touch it since it\'s a template or module.')
					continue
				is_lang_code_redirect = bool(re.fullmatch(r'Wiktionary:A[A-Z]{2,3}(-[A-Z]{3})?', bl_title))
				update_links(bl, link_target_title, new_link_target_title, skip_confirmation=is_lang_code_redirect, dry_run=args.dry_run)

		# Remove redundant sort key
		wikitext = wikitextparser.parse(new_page.text)
		original_text = wikitext.string
		try:
			cat_link = next(link for link in wikitext.wikilinks if link.title == LANG_CONS_CAT_TITLE)
		except StopIteration:
			print(f'Warning: Unable to find category link in [[{new_title}]] to [[{LANG_CONS_CAT_TITLE}]].')
			continue
		old_sort_key = cat_link.text
		# Modifies wikitext
		cat_link.string = f'[[{LANG_CONS_CAT_TITLE}]]'
		lang_lower = lang.casefold()
		# Middle Dutch had "Dutch, Middle" as its sort key, which should have been preserved
		if old_sort_key.rstrip() == lang:
			pywikibot_helpers.edit(new_page, wikitext.string, SORT_KEY_SUMMARY, skip_confirmation=True, dry_run=args.dry_run, indent='\t')
		else:
			print(f'Note: The sort key used at [[{new_title}]] is "{old_sort_key}", which does not match the language ({lang}), so I am NOT going to attempt to remove the sort key.')

		# Confirm that all backlinks have been addressed
		get_and_print_backlinks(page, lang)
		print()

def get_and_print_backlinks(parent_page: pywikibot.Page, lang: str) -> dict[str, list[pywikibot.Page]]:
	'''Looks up, prints, and returns backlinks of the specified page and all its subpages.'''
	page_with_subpages = [parent_page]
	page_with_subpages.extend(pywikibot.pagegenerators.PrefixingPageGenerator(f'{parent_page.title()}/', site=parent_page.site))
	backlinks: dict[str, list[pywikibot.Page]] = {}
	for page in page_with_subpages:
		page_title = page.title()
		backlinks[page_title] = [bl for bl in page.backlinks(follow_redirects=False) if should_backlink_be_updated(bl.title(), lang)]
		if backlinks[page_title]:
			print(f'[[{page.title()}]] has the following relevant backlinks:')
			for bl in backlinks[page_title][:BACKLINK_DISPLAY_MAX]:
				print(f'\t{bl.title()}')
			if len(backlinks[page_title]) > BACKLINK_DISPLAY_MAX:
				print(f'Warning: {len(backlinks[page_title]) - BACKLINK_DISPLAY_MAX} more backlinks not shown.')
		else:
			print(f'[[{page.title()}]] has no relevant backlinks.')
	return backlinks

def update_links(page: pywikibot.Page, old_target: str, new_target: str, skip_confirmation: bool = False, dry_run: bool = False) -> None:
	wikitext = wikitextparser.parse(page.text)
	original_text = wikitext.string
	for link in wikitext.wikilinks:
		if link.title.removeprefix(':').replace('WT:', 'Wiktionary:') == old_target:
			# Modifies wikitext
			link.title = new_target
			if link.text == old_target.partition(':')[2]:
				link.text = new_target.partition(':')[2]
	summary = REDIRECT_SUMMARY if original_text[:9].casefold() == '#redirect' else f'Updated links to [[{new_target}]]'
	if not pywikibot_helpers.edit(page, wikitext.string, summary, skip_confirmation, dry_run, indent='\t'):
		print(f'\tWarning: Did NOT update the link to [[{old_target}]] at [[{page.title()}]].')
	print()

def should_backlink_be_updated(backlink: str, lang: str) -> bool:
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
