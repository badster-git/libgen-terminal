import os

# General Settings
DOWNLOAD_PATH = (
    os.path.curdir
)  # Where do you want the books to be downloaded. Default is the script directory.
N_AUTHORS = 1  # Maximum of authors displayed.
MAX_CHARS_AUTHORS = (
    25  # Maximum characters displayed for the author. Change according to N_AUTHORS.
)
MAX_CHARS_TITLE = 50  # Maximum characters displayed for the book title
MAX_CHARS_PUBLISHER = 20  # Maximum characters displayed for the publisher.
SHOW_MIRRORS = True  # Set to True or False depending if you want the program to show the download mirrors.

# Tabulate Headers
TABULATE_HEADERS = ["#", "Author", "Title", "Publisher", "Year", "Lang", "Ext", "Size"]

# Column names
LIBGEN_COLUMN_NAMES = {
    "ID": 0,
    "Author": 1,
    "Title": 2,
    "Publisher": 3,
    "Year": 4,
    "Pages": 5,
    "Language": 6,
    "Size": 7,
    "Extension": 8,
    "Mirrors": 9,
    "Edit": 10,
}

# Mirrors
LIBGEN_MIRROR_LIST = [
    "https://libgen.is",
    "https://libgen.li",
    "https://libgen.rs",
    "https://libgen.st",
]

# Requests Settings
USER_AGENT_HEADER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
ACCEPT_HEADER = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
ACCEPT_CHARSET_HEADER = "ISO-8859-1,utf-8;q=0.7,*,q=0.3"
ACCEPT_LANG_HEADER = "en-US,en;q=0.8"
CONNECTION_HEADER = "keep-alive"
HEADERS = {
    "User-Agent": USER_AGENT_HEADER,
    "Accept": ACCEPT_HEADER,
    "Accept-Charset": ACCEPT_CHARSET_HEADER,
    "Accept-Language": ACCEPT_LANG_HEADER,
    "Connection": CONNECTION_HEADER,
}
