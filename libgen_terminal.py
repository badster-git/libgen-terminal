import argparse
import re
import os
from bs4 import BeautifulSoup
from urllib import request
from urllib.parse import urlencode
from tabulate import tabulate
from settings import *

def getSearchResults(term, page, column):
	params = urlencode({'req': term, 'column': column, 'page': page})
	# Libgen URL
	libgenUrl = "https://libgen.is/search.php?&%s" % params

	response = request.urlopen(libgenUrl)
	soup = BeautifulSoup(response, 'lxml')

	if page == 1:
		booksFound = re.search(r'(\d+) files found', str(soup))
		print(booksFound.group().upper())
		nBooks = int(booksFound.groups()[0])

	pageBooks = soup.find_all('tr')
	pageBooks = pageBooks[3:-1] # Ignores first 3 and last <tr> label.
	books = pageBooks
	if page == 1:
		return(books, nBooks)
	else:
		return(books)

def formatBooks(books, page):
	fmtBooks = []
	booksMirrors = [] 			# List of dics with complete titles & mirrors
	contBook = (page - 1)*25 + 1
	for rawBook in books:
		bookAttrs = rawBook.find_all('td')

		if len(bookAttrs) >= 13:
			authors = [a.text for a in bookAttrs[1].find_all('a')]
			author = ', '.join(authors[:N_AUTHORS])
			author = author[:MAX_CHARS_AUTHORS]

			title = bookAttrs[2].find(title=True).text
			tinytitle = title[:MAX_CHARS_TITLE]

			publisher = bookAttrs[3].text[:MAX_CHARS_PUBLISHER]
			year = bookAttrs[4].text
			lang = bookAttrs[6].text[:2] 	# Only first 2 chars
			size = bookAttrs[7].text
			ext = bookAttrs[8].text
			mirrorList = {}			# Dictionary for all four mirrors
			for i,x in zip(range(9, 12), range(0,3)):
				if bookAttrs[i].a:
					mirrorList[x] = bookAttrs[i].a.attrs['href']
			book = (str(contBook), author, tinytitle, publisher,
					year, lang, ext, size) # starts at 1
			bookMirrors = {'title': title, 'mirrors': mirrorList}
			booksMirrors.append(bookMirrors)
			contBook += 1
			fmtBooks.append(book)
	return(fmtBooks, booksMirrors)

def selectBook(books, mirrors, page, nBooks):
	headers = ['#', 'Author', 'Title', 'Publisher',
			   'Year', 'Lang', 'Ext', 'Size']

	print(tabulate(books[(page - 1) * 25:page * 25], headers))
	# Detect when books are found
	noMoreMatches = nBooks == len(books)

	if noMoreMatches:
		print("\nEND OF LIST. NO MORE BOOKS FOUND")

	while True:
		if noMoreMatches:
			elec = input('Type # of book to download or q to quit: ')
		else:
			elec = input(
				 '\nType # of book to download, q to quit or just press Enter to see more matches: ')

		if elec.isnumeric():
			choice = int(elec) - 1
			if choice < len(books) and choice >= 0: 	# Selection
				title = '{}.{}'.format(
					mirrors[choice]['title'], books[choice][-2])

				if SHOW_MIRRORS == False:
					''' This is the default mirror.
					In case other mirrors work, change True to
					a boolean variable defined in settings.py
					that defines if user wants to have option
					to select from different mirros. '''
					DownloadBook.defaultMirror(
						mirrors[choice]['mirrors'][0], title)
				else:
					numberOfMirrors = len(mirrors[choice]['mirrors'])
					printList = (
						"#1: Mirror library.lol (default)",
						"#2: Mirror booksdl.org",
						"#3: Mirror 3lib.net [UNSTABLE AND DL LIMIT]")

					while SHOW_MIRRORS:
						print("\nMirrors Availble:")
						avaMirrors = list(mirrors[choice]['mirrors'].keys())
						for mir in avaMirrors:
							print(printList[mir])

						option = input(
							'\nType # of mirror to start download or q to quit: ')

						if option.isnumeric() and int(option) > 0 and int(option) <= numberOfMirrors:
							if int(option) == 1:
								DownloadBook.defaultMirror(
									mirrors[choice]['mirrors'][0], title)
								pass
							elif int(option) == 2:
								DownloadBook.secondMirror(mirrors[choice]['mirrors'][1], title)
							elif int(option) == 3:
								DownloadBook.thirdMirror(mirrors[choice]['mirrors'][2], title)
							return(False)

						elif option == 'q' or option == 'Q': # Quit
							return(False)
						else:
							print("Not a valid option.")
							continue

				return(False)

			else:
				print("Couldn't fetch the book #{}".format(str(choice + 1)))
				continue

		elif(elec == 'q' or elec == 'Q'):	# Quit
			return(False)

		elif not elec:
			if noMoreMatches:
				print('Not a valid option')
				continue
			else:
				return(True)

		else:
			print('Not a valid option')

class DownloadBook():
	userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
	accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
	acceptCharset = 'ISO-8859-1,utf-8;q=0.7,*,q=0.3'
	acceptLang = 'en-US,en;q=0.8'
	connection = 'keep-alive'

	headers = {
		'User-Agent': userAgent,
		'Accept': accept,
		'Accept-Charset': acceptCharset,
		'Accept-Language': acceptLang,
		'Connection': connection,
	}

	def saveBook(downloadLink, fileName):
		if os.path.exists(DOWNLOAD_PATH) and os.path.isdir(DOWNLOAD_PATH):
			badChars = '\/:*?"<>|'
			for chars in badChars:
				fileName = fileName.replace(chars, " ")
			print('Downloading...')
			path = '{}/{}'.format(DOWNLOAD_PATH, fileName)
			request.urlretrieve(downloadLink, filename=path)
			print('Book downloaded to {}'.format(os.path.abspath(path)))
		elif os.path.isfile(DOWNLOAD_PATH):
			print('The download path is not a directory. Change it in settings.py')
		else:
			print('The download path does not exist. Change it in settings.py')

	def defaultMirror(link, filename):
		'''Second mirror to download.
		Base is https://libgen.lc'''
		req = request.Request(link, headers=DownloadBook.headers)
		source = request.urlopen(req)
		soup = BeautifulSoup(source, 'lxml')
		for a in soup.find_all('a'):
			if a.text == 'GET':
				downloadUrl = a.attrs['href']
				DownloadBook.saveBook(downloadUrl, filename)

	def secondMirror(link, filename):
		'''Second mirror to download.'''
		req = request.Request(link, headers=DownloadBook.headers)
		slash = (str(link).find('/', 10))
		baseLink = (str(link)[:slash])+'/'
		source = request.urlopen(req)
		soup = BeautifulSoup(source, 'lxml')
		for next_a in soup.find_all('a'):
			if 'GET' in next_a.text:
				downloadUrl = baseLink + next_a.attrs['href']
				DownloadBook.saveBook(downloadUrl, filename)

	def thirdMirror(link, filename):
		'''This is the third mirror to download.
		The base of this mirror is https://3lib.net'''
		# Get download page
		slash = (str(link).find('/', 9))
		baseLink = (str(link)[:slash])
		req = request.Request(link, headers=DownloadBook.headers)
		source = request.urlopen(req)
		soup = BeautifulSoup(source, 'lxml')
		for a in soup.find_all('a'):
			if('href' in a.attrs):
				if ('/book/' in a.attrs['href']):
					downloadPageUrl = baseLink + a.attrs['href']

		# Download from download page
		if (downloadPageUrl):
			req = request.Request(downloadPageUrl, headers=DownloadBook.headers)
			source = request.urlopen(req)
			dlLink = baseLink + BeautifulSoup(source, 'lxml').select_one('a.dlButton.addDownloadedBook').attrs['href']
			if (dlLink):
				DownloadBook.saveBook(dlLink, filename)
		else: return False



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	column = parser.add_mutually_exclusive_group()
	parser.add_argument('search', nargs='+', help='search term')
	column.add_argument('-t', '--title', action='store_true',
						help='get books from the specified title')
	column.add_argument('-a', '--author', action='store_true',
						help='get books from the specified author')
	column.add_argument('-p', '--publisher', action='store_true',
						help='get books from the specified publisher')
	column.add_argument('-y', '--year', action='store_true',
						help='get books from the specified year')

	args = parser.parse_args()

	search_term = ' '.join(args.search)
	search_arguments = [(args.title, 'title'),
						(args.author, 'author'),
						(args.publisher, 'publisher'),
						(args.year, 'year')]

	selColumn = 'def'
	for arg in search_arguments:
		if arg[0]:
			selColumn = arg[1]

	books = []
	mirrors = []
	page = 1
	get_next_page = True

	while get_next_page:
		if page == 1:
			rawBooks, nBooks = getSearchResults(search_term, page, selColumn)
		else:
			rawBooks = getSearchResults(search_term, page, selColumn)

		if rawBooks:
			newBooks, newMirrors = formatBooks(rawBooks, page)
			books += newBooks
			mirrors += newMirrors
			get_next_page = selectBook(books, mirrors, page, nBooks)
			page += 1
		elif(rawBooks == [] and nBooks != 0): # matches 0 in last page
			get_next_page = selectBook(books, mirrors, page - 1, nBooks)
		else:	# 0 matches total
			get_next_page = False
