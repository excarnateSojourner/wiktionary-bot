import argparse

import cat_move
import wiktionary_cats

def main():
	parser = argparse.ArgumentParser('Move (rename) a category and all of its subcategories, and move all members of the subcategories accordingly.')
	parser.add_argument('src_base_name', help='The base name of the parent category to move.')
	parser.add_argument('dst_base_name', help='The new base name the parent category should have.')
	parser.add_argument('langs_path', help='Path of a CSV file containing the CSV available at [[Wiktionary:List of languages, csv format]]. The first row (which is column headings) should be included.')
	parser.add_argument('-t', '--src-topic', action='store_true', help='Indicates the source category and its subcategories are all topic categories. Otherwise they are all assumed to be catlangname categories.')
	parser.add_argument('-o', '--dst-topic', action='store_true', help='Indicates the destination category and its subcategories are all topic categories. Otherwise they are assumed to be catlangname categories.')
	parser.add_argument('-p', '--page', action='store_true', help='Indicates that the source category page should be moved, in addition to its contents.')
	parser.add_argument('-s', '--summary', help='The edit summary to use when saving the pages.')
	parser.add_argument('-d', '--dry-run', '--dr', action='store_true', help='Save changed pages locally instead of remotely (so no change is made to the remote).')
	parser.add_argument('-l', '--limit', default=-1, type=int, help='Limit the number of pages to be moved.')
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()
	if args.limit < 0:
		args.limit = None

	parent = wiktionary_cats.ParentCat(args.src_base_name, args.src_topic, args.langs_path)
	parent.move(args.dst_base_name, args.summary, args.dst_topic, args.page, args.dry_run, args.limit, args.verbose)

if __name__ == '__main__':
	main()
