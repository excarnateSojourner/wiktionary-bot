import argparse

import pywikibot

import wiktionary_cats

def main():
	parser = argparse.ArgumentParser(description='Move (rename) all mainspace pages in a given category to another category.')
	parser.add_argument('src_base_name', help='The base name (removing the language name prefix for langname categories, and the language code prefix for topic categories) of the category to move pages *from*.')
	parser.add_argument('src_lang_code', help='The ISO 639 code of the language of the category to move pages *from*.')
	parser.add_argument('src_lang_name', help='The full name of the language of the category to move pages *from*.')
	parser.add_argument('-t', '--src-topic', '--st', action='store_true', help='Indicates that the category to move pages *from* is a topic category (like Category:en:Philosophy), not a langname category (like Category:English nouns). The opposite is assumed if this argument is not given. This determines what templates will be searched for on pages in the category.')
	parser.add_argument('dst_base_name', help='The base name (removing the language name prefix for langname categories, and the language code prefix for topic categories) of the category to move pages *to*.')
	parser.add_argument('-c', '--dst-lang-code', '--dlc', help='The ISO 639 code of the language of the category to move pages *to*. The source language code is used by default.')
	parser.add_argument('-l', '--dst-lang-name', '--dln', help='The full name of the language of the category to move pages *to*. The source language name is used by default.')
	parser.add_argument('-o', '--dst-topic', '--dt', action='store_true', help='Indicates that the category to move pages *to* is a topic category (like Category:en:Philosophy), not a langname category (like Category:English nouns). The opposite is assumed if this argument is not given. This determines what templates will be searched for on pages in the category.')
	parser.add_argument('-p', '--page', action='store_true', help='Indicates that the category page should be moved as well as its contents. If the destination already exists, then turn the source into a redirect to the destination.')
	parser.add_argument('-s', '--summary', help='The edit summary to use when saving the pages.')
	parser.add_argument('-d', '--dry-run', '--dr', action='store_true', help='Save changed pages locally instead of remotely (so no change is made to the remote).')
	parser.add_argument('-i', '--limit', default=-1, type=int, help='Limit the number of pages to be moved.')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	if args.page:
		wiktionary_cats.move_or_redirect_cat_page(src_cat.full_name, dst_cat.full_name, summary=summary, dry_run=dry_run)
	src_cat = wiktionary_cats.LangCat(args.src_base_name, args.src_lang_code, args.src_lang_name, args.src_topic)
	src_cat.move(args.dst_base_name, args.dst_topic, summary=args.summary, dry_run=args.dry_run, limit=args.limit, verbose=args.verbose)

if __name__ == '__main__':
	main()
