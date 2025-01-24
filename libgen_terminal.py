import argparse, re, os
from urllib.parse import urlparse

from settings import settings
from tools.helpers import Helper


class LibGenParser(object):

    @staticmethod
    def __parsePagePagesFound(page_soup=None) -> int:
        if page_soup is None:
            return None

        paginator_elem = page_soup.select_one("div.paginator")

        if paginator_elem is None:
            return 1

        # Check if full size paginator
        if "fullsize" in paginator_elem["class"]:
            pages_elems = paginator_elem.select("td")
            return len(pages_elems)

        print("25 more pages found. Go to last page to get remaining pages.")
        return 25

    @staticmethod
    def __parsePageBooksFound(page_soup=None) -> int:
        if page_soup is None:
            return None

        re_files_found = page_soup.find_all(
            "font", string=re.compile(r"(.*files found)")
        )

        if re_files_found is None:
            return None

        re_num_files = re.match(r"(\d*).*files found", re_files_found[0].text.strip())

        if re_num_files is None:
            return None

        return int(re_num_files.group(1))

    @staticmethod
    def __parsePageBooks(curr_page, page_soup=None):
        if page_soup is None:
            return None

        tables_elems = page_soup.find_all("table")
        if tables_elems is None:
            raise SystemExit("No data tables found. Exiting")

        results_table = tables_elems[-2]

        books_elems = results_table.find_all("tr")

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
            book["Count"] = cnt_book
            cnt_book += 1
            fmt_books.append(book)

        return fmt_books

    @staticmethod
    def __getBookAttributes(attrs_elems_soup):
        authors = [
            a.text
            for a in attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Author"]].find_all(
                "a"
            )
        ]
        author = ", ".join(authors[: settings.N_AUTHORS])
        author = author[: settings.MAX_CHARS_AUTHORS]
        title = (
            attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Title"]]
            .find(title=True)
            .text
        )
        tinytitle = title[: settings.MAX_CHARS_TITLE]
        publisher = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Publisher"]].text[
            : settings.MAX_CHARS_PUBLISHER
        ]
        year = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Year"]].text
        lang = attrs_elems_soup[settings.LIBGEN_COLUMN_NAMES["Language"]].text[
            :2
        ]  # Only first 2 chars
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
            "Mirrors": mirror_list,
        }

    @staticmethod
    def __getInitialData(page_soup) -> dict:
        parsed_pages = LibGenParser.__parsePagePagesFound(page_soup)
        parsed_total_books = LibGenParser.__parsePageBooksFound(page_soup)

        return {"parsedPages": parsed_pages, "totalBooks": parsed_total_books}

    @staticmethod
    def __parsePageDownloadLinks(page_soup):
        re_dl_link = page_soup.find_all(
            "a", {"href": re.compile("(.*download\.library.*)|(.*get\.php.*)")}
        )

        if re_dl_link is None or len(re_dl_link) == 0:
            return None

        dl_link = re_dl_link[0]["href"]

        return dl_link

    @staticmethod
    def parsePageBookList(page_soup=None, curr_page=0, data=None):
        if page_soup is None:
            raise SystemExit("No book list page soup found. Exiting.")
        parsed_books = LibGenParser.__parsePageBooks(curr_page, page_soup)

        if curr_page == 1 or data is None:
            initial_data = LibGenParser.__getInitialData(page_soup)
            return {
                "parsedBooks": parsed_books,
                "parsedPages": initial_data["parsedPages"],
                "currentPage": curr_page,
                "totalBooks": initial_data["totalBooks"],
            }

        return {
            "parsedBooks": data["parsedBooks"] + parsed_books,
            "parsedPages": data["parsedPages"],
            "currentPage": curr_page,
            "totalBooks": data["totalBooks"],
        }

    @staticmethod
    def parsePageDownload(page_soup=None):
        if page_soup is None:
            raise SystemExit("No download page soup found. Exiting.")

        download_link = LibGenParser.__parsePageDownloadLinks(page_soup)
        return download_link


class LibGenScraper(object):
    @staticmethod
    def getLibgenLink(self, params=None, index=0):
        for link in settings.LIBGEN_MIRROR_LIST[index:]:
            if Helper.isValid(link):
                return Helper.encodeLink(link, params) if params else link

        raise SystemExit("Couldn't find valid libgen link. Exiting.")

    @staticmethod
    def getSearchResults(params, data=None) -> dict:
        """
        getSearchResults gets results from page based on search parameters
        :param params: dictionary containing search results
        :return: dictionary containing search results
        """
        libgen_link = LibGenScraper.getLibgenLink(params=params)
        page_soup = Helper.getSoup(libgen_link)
        parsed_data = LibGenParser.parsePageBookList(page_soup, params["page"], data)

        return parsed_data

    @staticmethod
    def downloadBook(book_mirrors={}, file_extension=None, book_title=None):
        if book_mirrors is None:
            return None

        for book_mirror in book_mirrors.values():
            if Helper.isValid(book_mirror):
                parsed_url = urlparse(book_mirror)
                page_soup = Helper.getSoup(book_mirror)
                download_link = LibGenParser.parsePageDownload(page_soup)

                if download_link is None:
                    continue

                if "http://" not in download_link or "https://" not in download_link:
                    download_link = f"{parsed_url.scheme}://{parsed_url.netloc}/{download_link}"

                did_save = DownloadBook.saveBook(
                    download_link, file_extension, book_title
                )
                if did_save:
                    return True
        print("Could not find a working mirror.")
        return False


class DownloadBook:
    @staticmethod
    def saveBook(download_link, file_extension, filename=None):
        if os.path.exists(settings.DOWNLOAD_PATH) and os.path.isdir(
            settings.DOWNLOAD_PATH
        ):
            if filename is None:
                """Generate random filename"""
                import string, random

                filename = "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=12)
                )

            """Cleanup filename"""
            bad_chars = '\/:*?"<>|'
            for chars in bad_chars:
                filename = filename.replace(chars, " ")
            if settings.RESTRICT_FILENAMES:
                filename = filename.replace(" ", "_")

            path = f"{settings.DOWNLOAD_PATH}/{filename}.{file_extension}"
            did_download = Helper.downloadFile(download_link, path)

            if did_download:
                print(f"Book downloaded to {os.path.abspath(path)}")
                return True
            else:
                print("Trying a different mirror...")
                return False
        elif os.path.isfile(settings.DOWNLOAD_PATH):
            print(
                "The download path is not a directory. Aborting download. Change it in settings.py"
            )
            exit()
        else:
            print(
                "The download path does not exist. Aborting download. Change it in settings.py"
            )
            exit()


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

    # lg_scraper = LibGenScraper()

    while get_next_page:
        params = {"req": search_term, "page": page, "col": selColumn}
        # Get results from params
        results = LibGenScraper.getSearchResults(params, data)
        Helper.formatOutput(data=results)

        selected_book = Helper.selectBook(
            results["parsedBooks"],
            results["parsedPages"],
            results["currentPage"],
            results["totalBooks"],
        )

        if isinstance(selected_book, dict):
            # Valid book dict
            did_download = LibGenScraper.downloadBook(
                selected_book["Mirrors"],
                selected_book["Extension"],
                selected_book["Title"],
            )
            if did_download:
                print(f"\nSuccessfully Downloaded {selected_book['Title']}.")
                choice = input("q to quit or anything else to download more books: ")
                if choice.lower() == "q":
                    exit()
            else:
                print(
                    f"Could not download {selected_book['Title']}. Try a different book."
                )
            continue
        elif isinstance(selected_book, bool):
            # get next page
            page += 1
            data = results
            continue
        else:
            get_next_page = False
