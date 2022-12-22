import argparse
import re
import sys
from typing import Optional

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

NS_NAME = 'Category'
CAT_ALIASES = {'categorize', 'cat'}
CLN_ALIASES = {'catlangname', 'cln'}
C_ALIASES = {'topics', 'top', 'C', 'c'}
TEMP_ALIASES = CAT_ALIASES | CLN_ALIASES | C_ALIASES

class WiktionaryCat():

	# WiktionaryCat('2-syllable words', 'en', 'English')
	# WiktionaryCat('Philosopy', 'en', 'English', topic=True)
	def __init__(self, base_name: str, lang_code: str, lang_name: str, topic: bool = False):
		self.base_name = base_name
		self.lang_code = lang_code
		self.lang_name = lang_name
		self.topic = topic
		self.full_name = f'{NS_NAME}:{self.lang_code}:{self.base_name}' if self.topic else f'{NS_NAME}:{self.lang_name} {self.base_name}'
		self.link_regexp = '\n' + r'\[\['+ (f'({self.full_name}|{self.full_name.replace(" ", "_")})' if ' ' in self.full_name else self.full_name) + r'(\|(?P<sort>.*?))?\]\]'

	def to_generator(self):
		site = pywikibot.Site()
		cat = pywikibot.Category(site, self.full_name)
		return pywikibot.pagegenerators.CategorizedPageGenerator(cat)

	def add_one(self, page: pywikibot.page.BasePage, sortKey: Optional[str] = None) -> None:
		parsedPage = wikitextparser.parse(page.text)
		try:
			temp = next(t for t in parsedPage.templates if t.normal_name() in (C_ALIASES if self.topic else CLN_ALIASES) and t.arguments[0].positional and t.arguments[0].value == self.lang_code)
			last_positional = next(a for a in reversed(temp.arguments) if a.positional).name
			# insert before non-positional args, just because inserting after looks weird
			temp.set_arg('', self.base_name, positional=True, after=last_positional)
			if sortKey and not temp.has_arg('sort'):
				temp.set_arg('sort', sortKey)
		# no appropriate categorization template to add to
		except StopIteration:
			try:
				section = next(s for s in parsedPage.get_sections(level=2) if s.title.strip() == self.lang_name)
				new_temp = wikitextparser.Template(f'{{{{{"c" if self.topic else "cln"}|{self.lang_code}|{self.base_name}}}}}')
				if sortKey:
					new_temp.set_arg('sort', sortKey)
				try:
					section.insert(str(section).rindex('\n----'), f'\n{new_temp}\n')
				# horizontal line not found
				except ValueError:
					section.contents += f'\n{new_temp}'
			except StopIteration:
				print(f'Error: Unable to find a "{self.lang_name}" section on "{page.title()}". Failed to add it to {self.full_name}', file=sys.stderr)
		parsedPage.string = self.remove_extra_newlines(str(parsedPage))
		page.text = str(parsedPage)

	def remove_one(self, page: pywikibot.page.BasePage, verbose: bool = False) -> Optional[str]:
		parsedPage = wikitextparser.parse(page.text)
		# setting temp.string to the empty string removes the temp from parsedPage.templates, so create copy to avoid modifying list while we are iterating over it
		pageTemps = parsedPage.templates.copy()
		for temp in pageTemps:
			temp_name = temp.normal_name()
			if temp_name in TEMP_ALIASES and temp.get_arg('1').value == self.lang_code:
				try:
					arg = next(a for a in temp.arguments if a.positional and a.value == self.base_name)
				except StopIteration:
					continue
				try:
					sortKey = temp.get_arg('sort').value
				except AttributeError:
					sortKey = None
				# if the category we are removing was the only one listed in the template, remove the entire template
				if arg.name == '2' and not temp.has_arg('3'):
					temp.string = ''
				# there are other categories listed that we want to keep
				else:
					temp.del_arg(arg.name)
				if verbose:
					print(f'Removed {{{{{temp_name}}}}} link from [[{page.title()}]].')
				break
		# else branch of for loop
		else:
			mat = re.search(self.link_regexp, str(parsedPage))
			if mat:
				parsedPage.string = str(parsedPage)[:mat.start()] + str(parsedPage)[mat.end():]
				sortKey = mat.group('sort')
				if verbose:
					print(f'Removed plain link from [[{page.title()}]].')
			# template and link removal may leave behind stray newlines
			parsedPage.string = self.remove_extra_newlines(str(parsedPage))

		if page.text == str(parsedPage):
			raise ValueError(f'Unable to find the link to "{self.full_name}" in the text of "{page.title()}".')
		page.text = str(parsedPage)
		return sortKey

	@classmethod
	def remove_extra_newlines(cls, text: str):
		return re.sub('\n{3,}', '\n\n', text)

def move_or_redirect_cat_page(src_name: str, dst_name: str, summary: Optional[str] = None, dry_run: bool = False, verbose: bool = False) -> None:
	verbose = verbose or dry_run
	site = pywikibot.Site()
	src_page = pywikibot.page.Category(site, src_name)
	if not src_page.exists():
		return
	dst_page = pywikibot.page.Category(site, dst_name)
	if dst_page.exists():
		try:
			src_target = src_page.getRedirectTarget().title()
			if src_target == dst_name:
				return
		except pywikibot.exceptions.IsNotRedirectPageError:
			pass
		if verbose:
			print(f'Turning "{src_name}" into a redirect to "{dst_name}".')
		if not dry_run:
			src_page.set_redirect_target(dst_name, force=True, summary=summary)
	else:
		if verbose:
			print(f'Moving "{src_name}" to "{dst_name}".')
		if not dry_run:
			src_page.move(dst_name, reason=summary)
