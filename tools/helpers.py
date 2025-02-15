from settings import settings
from tabulate import tabulate
from urllib import request
from urllib import error as urrlib_error
from urllib.parse import urlencode
from bs4 import BeautifulSoup


class Helper(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def getSoup(url):
        """
        getSoup takes in url & returns a BeautifulSoup object

        :param url: url to get soup from
        :return: a BeautifulSoup object
        """
        req = request.Request(url)
        req.add_header('User-Agent', settings.USER_AGENT_HEADER)
        soup = BeautifulSoup(request.urlopen(req).read(), features="lxml")

        return soup

    @staticmethod
    def encodeLink(url, params) -> str:
        # params = urlencode({'req': term, 'column': column, 'page': page})
        return f"{url}/search.php?&%s" % urlencode(params)

    @staticmethod
    def isValid(url):
        """
        checkWorkingLink sends request to link to check for valid response

        :param url: URL to send request to check
        :return: Boolean indicating whether link is valid
        """
        try:
            print(url)
            req = request.Request(url)
            req.add_header('User-Agent', settings.USER_AGENT_HEADER)
            _ = request.urlopen(req)
        except urrlib_error.HTTPError as e:
            print(f"HTTPError: {e}")
            return False
        except urrlib_error.URLError as e:
            print(f"URLError: {e}")
            return False
        else:
            return True

    @staticmethod
    def formatOutput(headers=settings.TABULATE_HEADERS, data=None, page=0) -> None:
        """
        formatOutput Prepares the input data for tabulate & prints using tabulate

        :param headers: A list of strings needed for tabulate to correctly format output
        :param data: A dictionary that contains scraped data from given url
        :parm page: The current page number
        """

        def prepareData(input_data) -> dict:
            #
            """
            prepareData Seperates values from dictionary into key,value pairs according to the tabulate headers. The values are lists with all the books key value.

            :param input_data: A dictionary that contains scraped data from given url
            :return: Returns a dictionary with keys value pairs needed for tabulate to output data properly
            """
            tabulate_data_dict = {}

            for key in headers:
                tabulate_data_array = []
                for book_dict in input_data["parsedBooks"][
                    (input_data["currentPage"] - 1) * 25 : input_data["currentPage"]
                    * 25
                ]:
                    if key == "#":
                        tabulate_data_array.append(str(book_dict["Count"]))
                    elif key == "Lang":
                        tabulate_data_array.append(str(book_dict["Language"]))
                    elif key == "Ext":
                        tabulate_data_array.append(str(book_dict["Extension"]))
                    else:
                        tabulate_data_array.append(str(book_dict[key]))
                tabulate_data_dict[key] = tabulate_data_array
            return tabulate_data_dict

        tabulate_data = prepareData(data)
        print(tabulate(tabulate_data, headers="keys"))

    @staticmethod
    def selectBook(books=[], total_pages=0, curr_page=0, total_books=0):
        no_more_books = total_books == len(books)

        if curr_page == 0 and len(books) == 0:
            print("\nNO BOOKS RETURNED")
            exit()

        if no_more_books:
            print("\nEND OF LIST. NO MORE BOOKS FOUND.")

        while curr_page <= total_pages:
            choice = (
                input("Type # of book to download or q to quit: ")
                if no_more_books
                else input(
                    "Type # of book to download, q to quit or Enter to load next page: "
                )
            )
            if choice.isnumeric():
                book_num = int(choice) - 1
                if book_num < len(books) and book_num >= 0:
                    print(
                        f"Downloading {books[book_num]['Title']} by {books[book_num]['Author']}..."
                    )
                    return books[book_num]
                else:
                    print("Not a valid range. Try again.")
                    continue
            elif choice.lower() == "q":
                exit()
            elif not choice:
                if not no_more_books:
                    return True
            print("Not a valid option. Try again.")

    @staticmethod
    def downloadFile(url, filepath):
        def reportHook(count, block_size, total_size):
            """
            This function was grabbed from: https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html
            """
            import time, sys

            global start_time
            if count == 0:
                start_time = time.time()
                return
            duration = time.time() - start_time
            progress_size = int(count * block_size)
            speed = int(progress_size / (1024 * (int(duration) + 1)))
            percent = min(int(count * block_size * 100 / total_size), 100)
            sys.stdout.write(
                "\r%d%%, %d MB, %d KB/s, %d seconds passed"
                % (percent, progress_size / (1024 * 1024), speed, duration)
            )
            sys.stdout.flush()

        print(f"\nDownloading from {url}...\n")
        custom_urlretrieve = CustomURLopener()
        try:
            custom_urlretrieve.retrieve(url, filepath, reportHook)
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
        else:
            return True

class CustomURLopener(request.FancyURLopener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addheaders = [
            ("User-Agent", settings.USER_AGENT_HEADER)  
        ]