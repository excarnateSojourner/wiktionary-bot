import argparse
import csv
import re
import sys
from typing import Self

import pywikibot
import pywikibot.pagegenerators
import wikitextparser

NS_PREFIX = 'Category'
CAT_ALIASES = {'categorize', 'cat'}
CLN_ALIASES = {'catlangname', 'cln'}
C_ALIASES = {'topics', 'top', 'C', 'c'}
TEMP_ALIASES = CAT_ALIASES | CLN_ALIASES | C_ALIASES

class ParentCat():
	def __init__(self, base_name: str, topic: bool, lang_file_path: str):
		self.site = pywikibot.Site()
		self.base_name = base_name
		self.topic = topic
		self.full_name = self.base_to_full_name(self.base_name, self.topic)
		self.pwb_cat = pywikibot.Category(self.site, self.full_name)
		self.code_to_name = {}
		self.name_to_code = {}
		with open(lang_file_path, newline='', encoding='utf-8') as lang_file:
			for row in csv.reader(lang_file, delimiter=';'):
				code = row[1]
				name = row[2]
				self.code_to_name[code] = name
				self.name_to_code[name] = code

	def move(self, dst_base_name: str, summary: str, dst_topic: bool = None, page: bool = False, dry_run: bool = False, limit: int | None = None, verbose: bool = False) -> int:
		if dst_topic == None:
			dst_topic = self.topic
		actions = 0
		if page:
			move_or_redirect_cat_page(self.pwb_cat, self.base_to_full_name(dst_base_name, dst_topic), summary, dry_run, verbose)
			actions += 1

		for src_pwb_subcat in self.pwb_cat.subcategories():
			if limit != None and limit <= actions:
				break
			# Pywikibot can misinterpret the language code in a topic category ('zh:Philosophy') as a link to a different wiki (the Chinese Wiktionary).
			# One of the consequences of this is it will insert the NS prefix *after* the language code (zh:Category:Philosophy).
			src_title = src_pwb_subcat.title(as_link=True).removeprefix('[[').removesuffix(']]').replace(f'{NS_PREFIX}:', '', 1)
			if self.topic:
				lang_code, _, _ = src_title.partition(':')
				lang_name = self.code_to_name[lang_code]
			else:
				lang_name = src_title.removesuffix(self.base_name)
				lang_code = self.name_to_code[lang_name]
			src_subcat = LangCat(self.base_name, lang_code, lang_name, self.topic, self.site)
			dst_full_name = LangCat(dst_base_name, lang_code, lang_name, dst_topic, self.site).full_name
			move_or_redirect_cat_page(src_subcat.pwb_cat, dst_full_name, summary, dry_run, verbose)
			actions += 1
			actions += src_subcat.move(dst_base_name, dst_topic, summary, dry_run, limit = None if limit == None else limit - actions, verbose=verbose)
		return actions

	@classmethod
	def base_to_full_name(cls, base_name: str, topic: bool) -> str:
		return base_name if topic else f'{base_name.capitalize()} by language'

class LangCat:

	# LangCat('2-syllable words', 'en', 'English')
	# LangCat('Philosopy', 'en', 'English', topic=True)
	def __init__(self, base_name: str, lang_code: str, lang_name: str, topic: bool = False, site: pywikibot.site._basesite.BaseSite | None = None):
		self.site = site or pywikibot.Site()
		self.base_name = base_name
		self.lang_code = lang_code
		self.lang_name = lang_name
		self.topic = topic
		self.full_name = f'{self.lang_code}:{self.base_name}' if topic else f'{self.lang_name} {self.base_name}'
		self.pwb_cat = pywikibot.Category(self.site, with_prefix(self.full_name))
		self.link_regexp = '\n' + r'\[\[[cC]at(egory)?:'+ f'({self.full_name}|{self.full_name.replace(" ", "_")})' + r'(\|(?P<sort>.*?))?\]\]'

	def move(self, dst_base_name: str, dst_topic: bool = None, summary: str | None = None, dry_run: bool = False, limit: int | None = None, verbose: bool = False):
		if dst_topic == None:
			dst_topic = self.topic

		actions = 0
		for page in self.pages():
			if limit != None and limit <= actions:
				break
			dst_cat = LangCat(dst_base_name, self.lang_code, self.lang_name, dst_topic, self.site)
			try:
				sort_key = self.remove_one(page, verbose=verbose)
				dst_cat.add_one(page, sort_key=sort_key, verbose=verbose)
			except ValueError as er:
				print(er)
				continue
			if dry_run:
				with open(page.title().replace(' ', '_').replace('/', '_'), 'w') as outFile:
					outFile.write(page.text)
			else:
				page.save(summary=summary, bot=True, quiet=not verbose)
			actions += 1
		return actions

	def pages(self):
		return pywikibot.pagegenerators.CategorizedPageGenerator(self.pwb_cat)

	def add_one(self, page: pywikibot.page.BasePage, sort_key: str | None = None, verbose: bool = False) -> None:
		parsedPage = wikitextparser.parse(page.text)
		try:
			temp = next(t for t in parsedPage.templates if t.normal_name() in (C_ALIASES if self.topic else CLN_ALIASES) and t.arguments[0].positional and t.arguments[0].value == self.lang_code)
			last_positional = next(a for a in reversed(temp.arguments) if a.positional).name
			# insert before keyword args, just because inserting after looks weird
			temp.set_arg('', self.base_name, positional=True, after=last_positional)
			if sort_key and not temp.has_arg('sort'):
				temp.set_arg('sort', sort_key)
			if verbose:
				print(f'Added to existing {{{{{temp.normal_name()}}}}} on [[{page.title()}]].')
		# no appropriate categorization template to add to
		except StopIteration:
			try:
				section = next(s for s in parsedPage.get_sections(level=2) if s.title.strip() == self.lang_name)
				new_temp = wikitextparser.Template(f'{{{{{"c" if self.topic else "cln"}|{self.lang_code}|{self.base_name}}}}}')
				if sort_key:
					new_temp.set_arg('sort', sort_key)
				section.contents += f'\n{new_temp}'
				if verbose:
					print(f'Added new {{{{{new_temp.normal_name()}}}}} on [[{page.title()}]].')
			except StopIteration:
				print(f'Error: Unable to find a "{self.lang_name}" section on "{page.title()}". Failed to add it to {self.full_name}', file=sys.stderr)
		parsedPage.string = self.remove_extra_newlines(str(parsedPage))
		page.text = str(parsedPage)

	def remove_one(self, page: pywikibot.page.BasePage, verbose: bool = False) -> str | None:
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
					sort_key = temp.get_arg('sort').value
				except AttributeError:
					sort_key = None
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
				sort_key = mat.group('sort')
				if verbose:
					print(f'Removed plain link from [[{page.title()}]].')
			# template and link removal may leave behind stray newlines
			parsedPage.string = self.remove_extra_newlines(str(parsedPage))

		if page.text == str(parsedPage):
			raise ValueError(f'Unable to find the link to "{self.full_name}" in the text of "{page.title()}".')
		page.text = str(parsedPage)
		return sort_key

	@classmethod
	def remove_extra_newlines(cls, text: str) -> str:
		return re.sub('\n{3,}', '\n\n', text)

def move_or_redirect_cat_page(src_page: pywikibot.Category, dst_name: str, summary: str, dry_run: bool = False, verbose: bool = False) -> None:
	verbose = verbose or dry_run
	site = src_page.site
	if not src_page.exists():
		return
	dst_page = pywikibot.page.Category(site, with_prefix(dst_name))
	if dst_page.exists():
		try:
			src_target = src_page.getRedirectTarget().title()
			if src_target == dst_name:
				return
		except pywikibot.exceptions.IsNotRedirectPageError:
			pass
		if dry_run:
			if verbose:
				print(f'Would turn "{src_page.title()}" into a redirect to "{dst_page.title()}".')
		else:
			src_page.set_redirect_target(dst_name, force=True, summary=summary)
			if verbose:
				print(f'Turned "{src_page.title()}" into a redirect to "{dst_page.title()}".')
	else:
		if dry_run:
			if verbose:
				print(f'Would move "{src_page.title()}" to "{dst_page.title()}".')
		else:
			src_page.move(dst_name, reason=summary)
			if verbose:
				print(f'Moved "{src_page.title()}" to "{dst_page.title()}".')

def with_prefix(cat_name: str) -> str:
	'''
	Pywikibot can misinterpret the language code in a topic category ('zh:Philosophy') as a link to a different wiki (the Chinese Wiktionary).
	Ensure category prefix is included to prevent this.
	'''
	if cat_name.startswith(f'{NS_PREFIX}:'):
		return cat_name
	else:
		return f'{NS_PREFIX}:{cat_name}'
