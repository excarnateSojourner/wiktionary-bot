import argparse
import difflib
import itertools

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

REDIRECT_PREFIX = '#redirect'

def advanced_move(old_page: pywikibot.Page, new_title: str, move_reason: str, backlinks: str | None = None, redirect_reason: str | None = None, link_reason: str | None = None, ignore_subpages: bool = False, dry_run: bool = False):
	'''
	old_page: The page to move.
	new_title: The new title to move the page to.
	move_reason: The edit summary to use when moving pages.
	backlinks: Indicates how, if at all, backlinks should be updated.
		'skip_pages': Update redirects to the old title, but do not update pages that link to the old title.
		'skip': Do not update redirects to the old title or pages that link to the old title.
	redirect_reason: The edit summary to use when updating a redirect to a page that has been moved.
	link_reason: The edit summary to use when updating a link to a page that has been moved.
	ignore_subpages: Indicates that any subpages of the page to move should not be moved (and should therefore not have backlinks updated).
	dry_run: Indicates that no moves or edits should actually be made, but these actions should just be previewed.
	'''

	old_title = old_page.title()

	if dry_run:
		print(f'Would move {old_title} to {new_title}.')
	else:
		try:
			print(f'Moving {old_title} to {new_title}.')
			old_page.move(new_title, move_reason, movesubpages=False)
		# If the parent page has already been moved, proceed normally
		except pywikibot.exceptions.ArticleExistsConflictError:
			print(f'Skipping {old_title} because {new_title} already exists.')
			pass
	if backlinks != 'none':
		update_backlinks(old_page, new_title, backlinks, redirect_reason, link_reason, dry_run=dry_run)
	subpage_prefix = f'{old_title}/'
	# Despite pywikibot.BasePage.move() having a movesubpages parameter that defaults to True, this method does not actually move subpages in my experience as of pywikibot v9.6.1.
	if not ignore_subpages:
		for subpage in pywikibot.pagegenerators.PrefixingPageGenerator(subpage_prefix):
			new_subpage_title = f'{new_title}/{subpage.title()[len(subpage_prefix):]}'
			if dry_run:
				print(f'Would move {subpage.title()} to {new_subpage_title}.')
			else:
				print(f'Moving {subpage.title()} to {new_subpage_title}.')
				subpage.move(new_subpage_title, move_reason, movesubpages=False)
			if backlinks != 'none':
				update_backlinks(subpage, new_subpage_title, backlinks, redirect_reason, link_reason, dry_run=dry_run)

def update_backlinks(old_page: pywikibot.Page, new_title: str, type_: str = 'all', redirect_reason: str | None = None, link_reason: str | None = None, skip_confirmation: bool = False, dry_run: bool = False) -> None:
	'''
	type_: Indicates which kinds of backlinks should be updated.
		'all': Both redirects and links from other pages.
		'redirects': Just redirects.
		'links': Just links from other pages.
	skip_confirmation: See edit().
	'''
	old_title = old_page.title()
	for source_page in old_page.backlinks(follow_redirects=False):
		source_title = source.title()
		if source_title.startswith('Template:') and not source_title.endswith('/documentation'):
			print(f'\tWarning: {source_title} links to {old_title}, but I am not going to try to edit it since it\'s a template.')
			continue

		# If source_page is a redirect to old_page
		if startswith_casefold(source_page.text, REDIRECT_PREFIX):
			if type_ == 'links':
				continue
			specific_reason = redirect_reason or f'Moved {old_title} to {new_title}'
		# If source_page links to old_page
		else:
			if type_ == 'redirects':
				continue
			specific_reason = link_reason or f'Updated links to [[{new_title}]]'

		wikitext = wikitextparser.parse(source_page.text)
		for link in wikitext.wikilinks:
			if link.title == old_title:
				# Modifies wikitext
				link.title = new_title
				# If the link text is just the page title with the namespace removed, update it to use the new page title
				if ':' in old_title and link.text == old_title.partition(':')[2]:
					link.text = new_title.partition(':')[2]
		if not edit(page, wikitext.string, specific_reason, skip_confirmation, dry_run, indent='\t\t'):
			print(f'\tWarning: Unable to update the link to {old_target} at {page.title()}.')

def edit(page: pywikibot.Page, new_text: str, reason: str, skip_confirmation: bool = False, dry_run: bool = False, indent: str = '') -> None:
	'''
	page: The page to edit. In order for the edit diff to be accurate page.text must not have been altered.
	new_text: The updated text of the entire page.
	reason: The edit summary to pass to page.save().
	skip_confirmation (default False): Do not ask for confirmation before saving the edit. This value is ignored and no confirmation is asked for if dry_run is True.
	dry_run (default False): Do not save the edit; just preview it.
	indent (defaults to the empty string): A string to print before each of this function's messages. Intended to be used when this function is called many times within a larger program.
	'''

	def print_with_indent(message):
		print(f'{indent}{message}')

	title = page.title()
	diff = difflib.unified_diff(page.text.splitlines(keepends=True), new_text.splitlines(keepends=True), n=1)
	if not diff:
		print_with_indent(f'Warning: Refusing to edit because the new text is identical to the existing text.')
		return False
	if dry_run:
		print_with_indent(f'Would make the following edit at {title}:')
	else:
		print_with_indent(f'Making the following edit at {title}:')
	for line in diff:
		print_with_indent(f'\t{line}')
	print()
	print_with_indent(f'Summary: {reason}')
	if not dry_run:
		if not skip_confirmation:
			print_with_indent(f'Save edit? (y/n)')
			confirmation = input(f'{indent}==> ').casefold()
			if not confirmation.startswith('y'):
				return False
		page.text = new_text
		try:
			page.save(summary=reason)
		except pywikibot.exceptions.LockedPageError:
			print_with_indent(f'Error: Unable to save edit at {title} because the page is protected.')
			return False
	return True

def startswith_casefold(st: str, prefix: str) -> bool:
	return st[:len(prefix)].casefold() == prefix.casefold()

if __name__ == '__main__':
	main()
