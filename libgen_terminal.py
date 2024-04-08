import argparse, re, os

from tabulate import tabulate
from settings import settings
from tools.helpers import Helper

class LibGenParser(object):
	@staticmethod
	def __parsePagePagesFound(page_soup = None) -> int:
		if page_soup is None:
			return None

		paginator_elem = page_soup.select_one('div.paginator')
		
		if paginator_elem is None:
			return 1


		# Check if full size paginator
		if "fullsize" in paginator_elem['class']:
			pages_elems = paginator_elem.select('td')
			return len(pages_elems)

		print("25 more pages found. Go to last page to get remaining pages.")
		return 25

	@staticmethod
	def __parsePageBooksFound(page_soup = None) -> int:
		if page_soup is None:
			return None

		re_files_found = page_soup.find_all('font', string=re.compile(r"(.*files found)"))

		if re_files_found is None:
			return None

		re_num_files = re.match(r'(\d*).*files found',re_files_found[0].text.strip())

		if re_num_files is None:
			return None

		return int(re_num_files.group(1))

	@staticmethod
	def __parsePageBooks(curr_page, page_soup = None):
		if page_soup is None:
			return None

		tables_elems = page_soup.find_all('table')
		if tables_elems is None:
			print("No tables found")
			return None

		results_table = tables_elems[-2]

		books_elems = results_table.find_all('tr')

		if books_elems is None:
			print("No books found")
			return None

		books_elems = books_elems[1:]

		fmt_books = []
		cnt_book = (curr_page - 1) * 25 + 1
		for book_soup in books_elems:
			book_attr_elems = book_soup.find_all("td")

			if book_attr_elems is None:
				return None

			book = LibGenParser.__getBookAttributes(book_attr_elems)
			book['Count'] = cnt_book
			cnt_book += 1
			fmt_books.append(book)

		return fmt_books

	@staticmethod
	def __getBookAttributes(attrs_elems_soup):
		authors = [a.text for a in attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Author"]].find_all("a")]
		author = ", ".join(authors[:settings.N_AUTHORS])
		author = author[:settings.MAX_CHARS_AUTHORS]
		title = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Title"]].find(title=True).text
		tinytitle = title[:settings.MAX_CHARS_TITLE]
		publisher = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Publisher"]].text[:settings.MAX_CHARS_PUBLISHER]
		year = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Year"]].text
		lang = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Language"]].text[:2]  # Only first 2 chars
		size = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Size"]].text
		ext = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Extension"]].text

		mirror_list = {}
		for i, x in zip(range(9, 12), range(0, 3)):
			if attrs_elems_soup[i].a:
				mirror_list[x] = attrs_elems_soup[i].a.attrs["href"]

		return {
			"Author": author,
			"Title": tinytitle,
			"Publisher": publisher,
			"Year": year,
			"Language": lang,
			"Extension": ext,
			"Size": size,
			"MirrorList": mirror_list
		}

	@staticmethod
	def __getInitialData(page_soup) -> dict:
		parsed_pages = LibGenParser.__parsePagePagesFound(page_soup)
		parsed_total_books = LibGenParser.__parsePageBooksFound(page_soup)

		return {"parsedPages": parsed_pages, "totalBooks": parsed_total_books}


	@staticmethod
	def parsePageSoup(page_soup = None, curr_page = 0, data = None):
		if page_soup is None:
			return None

		parsed_books = LibGenParser.__parsePageBooks(curr_page, page_soup)

		if curr_page == 1 or data is None:
			initial_data = LibGenParser.__getInitialData(page_soup)
			return {"parsedBooks": parsed_books, "parsedPages": initial_data["parsedPages"], "currentPage": curr_page, "totalBooks": initial_data["totalBooks"]}

		return {"parsedBooks": data["parsedBooks"] + parsed_books, "parsedPages": data["parsedPages"], "currentPage": curr_page, "totalBooks": data["totalBooks"]}

class LibGenScraper(object):
	def __init__(self) -> None:
		pass

	def getLibgenLink(self, params=None, index=0):
		for link in settings.LIBGEN_MIRROR_LIST[index:]:
			if Helper.isValid(link):
				return Helper.encodeLink(link, params) if params else link

		raise SystemExit("Couldn't find valid libgen link. Exiting.")

	def getSearchResults(self, params, data = None) -> dict:
		"""
		getSearchResults gets results from page based on search parameters
		:param params: dictionary containing search results
		:return: dictionary containing search results
		"""
		libgen_link = self.getLibgenLink(params)
		page_soup = Helper.getSoup(libgen_link)
		parsed_data = LibGenParser.parsePageSoup(page_soup, params['page'], data)

		# LibGenScraper.__formatResults(parsed_data)
		return parsed_data

	def getBookDownload(self):
		pass

def formatBooks(books, page):
	fmtBooks = []
	booksMirrors = []  # List of dics with complete titles & mirrors
	contBook = (page - 1) * 25 + 1
	for rawBook in books:
		bookAttrs = rawBook.find_all("td")

		if len(bookAttrs) >= 13:
			authors = [a.text for a in bookAttrs[1].find_all("a")]
			author = ", ".join(authors[:N_AUTHORS])
			author = author[:MAX_CHARS_AUTHORS]

			title = bookAttrs[2].find(title=True).text
			tinytitle = title[:MAX_CHARS_TITLE]

			publisher = bookAttrs[3].text[:MAX_CHARS_PUBLISHER]
			year = bookAttrs[4].text
			lang = bookAttrs[6].text[:2]  # Only first 2 chars
			size = bookAttrs[7].text
			ext = bookAttrs[8].text
			mirrorList = {}  # Dictionary for all four mirrors
			for i, x in zip(range(9, 12), range(0, 3)):
				if bookAttrs[i].a:
					mirrorList[x] = bookAttrs[i].a.attrs["href"]
			book = (
				str(contBook),
				author,
				tinytitle,
				publisher,
				year,
				lang,
				ext,
				size,
			)  # starts at 1
			bookMirrors = {"title": title, "mirrors": mirrorList}
			booksMirrors.append(bookMirrors)
			contBook += 1
			fmtBooks.append(book)
	return (fmtBooks, booksMirrors)


def selectBook(books, mirrors, page, nBooks):
	headers = ["#", "Author", "Title", "Publisher", "Year", "Lang", "Ext", "Size"]

	print(tabulate(books[(page - 1) * 25 : page * 25], headers))
	# Detect when books are found
	noMoreMatches = nBooks == len(books)

	if noMoreMatches:
		print("\nEND OF LIST. NO MORE BOOKS FOUND")

	while True:
		if noMoreMatches:
			elec = input("Type # of book to download or q to quit: ")
		else:
			elec = input(
				"\nType # of book to download, q to quit or just press Enter to see more matches: "
			)

		if elec.isnumeric():
			choice = int(elec) - 1
			if choice < len(books) and choice >= 0:  # Selection
				title = "{}.{}".format(mirrors[choice]["title"], books[choice][-2])

				if SHOW_MIRRORS == False:
					"""This is the default mirror.
					In case other mirrors work, change True to
					a boolean variable defined in settings.py
					that defines if user wants to have option
					to select from different mirros."""
					DownloadBook.defaultMirror(mirrors[choice]["mirrors"][0], title)
				else:
					numberOfMirrors = len(mirrors[choice]["mirrors"])
					printList = (
						"#1: Mirror library.lol (default)",
						"#2: Mirror booksdl.org",
						"#3: Mirror 3lib.net [UNSTABLE AND DL LIMIT]",
					)

					while SHOW_MIRRORS:
						print("\nMirrors Availble:")
						avaMirrors = list(mirrors[choice]["mirrors"].keys())
						for mir in avaMirrors:
							print(printList[mir])

						option = input(
							"\nType # of mirror to start download or q to quit: "
						)

						if (
							option.isnumeric()
							and int(option) > 0
							and int(option) <= numberOfMirrors
						):
							if int(option) == 1:
								DownloadBook.defaultMirror(
									mirrors[choice]["mirrors"][0], title
								)
								pass
							elif int(option) == 2:
								DownloadBook.secondMirror(
									mirrors[choice]["mirrors"][1], title
								)
							elif int(option) == 3:
								DownloadBook.thirdMirror(
									mirrors[choice]["mirrors"][2], title
								)
							return False

						elif option == "q" or option == "Q":  # Quit
							return False
						else:
							print("Not a valid option.")
							continue

				return False

			else:
				print("Couldn't fetch the book #{}".format(str(choice + 1)))
				continue

		elif elec == "q" or elec == "Q":  # Quit
			return False

		elif not elec:
			if noMoreMatches:
				print("Not a valid option")
				continue
			else:
				return True

		else:
			print("Not a valid option")


class DownloadBook:
	@staticmethod
	def saveBook(downloadLink, fileName):
		if os.path.exists(DOWNLOAD_PATH) and os.path.isdir(DOWNLOAD_PATH):
			badChars = '\/:*?"<>|'
			for chars in badChars:
				fileName = fileName.replace(chars, " ")
			print("Downloading...")
			path = "{}/{}".format(DOWNLOAD_PATH, fileName)
			request.urlretrieve(downloadLink, filename=path)
			print("Book downloaded to {}".format(os.path.abspath(path)))
		elif os.path.isfile(DOWNLOAD_PATH):
			print("The download path is not a directory. Change it in settings.py")
		else:
			print("The download path does not exist. Change it in settings.py")


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	column = parser.add_mutually_exclusive_group()
	parser.add_argument("search", nargs="+", help="search term")
	column.add_argument(
		"-t", "--title", action="store_true", help="get books from the specified title"
	)
	column.add_argument(
		"-a",
		"--author",
		action="store_true",
		help="get books from the specified author",
	)
	column.add_argument(
		"-p",
		"--publisher",
		action="store_true",
		help="get books from the specified publisher",
	)
	column.add_argument(
		"-y", "--year", action="store_true", help="get books from the specified year"
	)

	args = parser.parse_args()

	search_term = " ".join(args.search)
	search_arguments = [
		(args.title, "title"),
		(args.author, "author"),
		(args.publisher, "publisher"),
		(args.year, "year"),
	]

	selColumn = "def"
	for arg in search_arguments:
		if arg[0]:
			selColumn = arg[1]

	page = 1
	get_next_page = True
	data = {}

	lg_scraper = LibGenScraper()

	while get_next_page:
		params = {"req": search_term, "page": page, "col": selColumn}
		# Get results from params
		results = lg_scraper.getSearchResults(params, data)
		Helper.formatOutput(data=results)

		selected_book = Helper.selectBook(results["parsedBooks"], results["parsedPages"], results["currentPage"], results["totalBooks"])
		if isinstance(selected_book, dict):
			# Valid book dict
			pass
		elif isinstance(selected_book, bool):
			# get next page
			page += 1
			data = results
			continue
		else:
			get_next_page = False