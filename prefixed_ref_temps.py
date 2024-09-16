import pywikibot

DOC_TEXT = '''{{documentation subpage}}
{{documentation needed}}<!-- Replace this with a short description of the purpose of the template, and how to use it. -->

<includeonly>
{{refcat}}
</includeonly>
'''

def main():
	with open('prefixed_ref_temps.txt', encoding='utf-8') as temps_file:
		ref_temps = temps_file.read().splitlines()

	site = pywikibot.Site()
	for temp_title in ref_temps:
		doc_title = temp_title + '/documentation'
		doc_page = pywikibot.Page()
		if doc_page.exists():
			print(f'Warning: {doc_title} already exists')
			continue
		else:
			doc_page.text = DOC_TEXT
		if dry_run:
			with open(temp_title + '.txt', 'w', encoding='utf-8') as out_file:
				out_file.write(doc_page.text)
		else:
			doc_page.save(summary='Categorize prefixed reference templates', bot=True)

if __name__ == '__main__':
	main()
