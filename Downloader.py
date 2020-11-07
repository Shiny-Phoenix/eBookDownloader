#!/usr/bin/python3
from requests import Session
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from time import sleep
from threading import Thread
import readline


class Book:
    def __init__(self, author, name, download_link, size, length, extension):
        self.author = author
        self.name = name
        self.download_link = download_link
        self.size = size
        self.length = length
        self.extension = extension  # .pdf,.epub etc


BOOK = input("Search(minimum 3 characters): ")  # The book to be searched

if len(BOOK) < 3:
    print("The length of the search string must be greater than 3 characters.")
    sleep(2)
    exit()

search_url = "http://libgen.li/search.php?req=" + \
    BOOK.replace(" ", "+")  # url to get search results
search_results = []
session = Session()


def print_loading(text):
    """
        A function to print text with a loading animation
    """
    global run_anim
    animations = [text+"|", text+"/", text+"-", text+"\\"]
    while run_anim:
        for anim in animations:
            print(anim, end="\r", flush=True)
            sleep(0.15)


def get_webpage(url):
    try:
        return session.get(url)
    except ConnectionError:
        global run_anim
        run_anim = False
        sleep(0.65)
        print("Looks like you are offline.")
        sleep(2)
        exit()


# Starting the searching animation
run_anim = True
Thread(target=print_loading, args=("Searching",), daemon=True).start()

# Visiting the search_url and grabbing the results part from the page
page = get_webpage(search_url).content
soup = BeautifulSoup(page, 'lxml')
results_part = soup.find("table", {"class": "c"})
results = results_part.find_all("tr", recursive=False)

for result in results:
    if result.attrs['bgcolor'] == "#C0C0C0":  # Ignoring the Header of the table
        continue
    # Columns in which information about the book is stored
    columns = result.find_all("td", recursive=False)
    language = columns[6].get_text()
    if language != "English":
        continue
    name_column = columns[2].find_all("a")
    name = name_column[-1].get_text()
    redundant_text = []  # A list that stores all the useless part of the name
    font_tags = name_column[-1].find_all("font")
    for tag in font_tags:
        redundant_text.append(tag.get_text())
    for text in redundant_text:
        name = name.replace(text, "")
    author = columns[1].get_text()
    download_link = name_column[-1]['href']
    size = columns[7].get_text()
    length = columns[5].get_text()
    extension = "."+columns[8].get_text()
    search_results.append(
        Book(author, name, download_link, size, length, extension))

# Stopping the searching animation
run_anim = False
sleep(0.7)

# Exiting if no results were found
if len(search_results) == 0:
    print("No results Found.")
    exit()


print(str(len(search_results))+" books found.\n")

# Presenting the search results
for index, book in enumerate(search_results):
    print(f"Index: {index+1}")
    print(f"Author: {book.author}")
    print(f"Name: {book.name}")
    print(f"Size: {book.size}")
    print(f"Length: {book.length}")
    print(f"Format: {book.extension}")
    print("\n")

download_index = int(input("Index of the book to download: "))-1

# Starting a loading animation
run_anim = True
Thread(target=print_loading, args=("Fetching",), daemon=True).start()

# Finding the final download link after going through two pages
page = get_webpage("http://libgen.li/" +
                   search_results[download_index].download_link).content
soup = BeautifulSoup(page, 'lxml')
table = soup.find("table", {"border": 0, "width": "100%"})
download_link = table.find("a")['href']
page = get_webpage("http://libgen.li/"+download_link).content
soup = BeautifulSoup(page, 'lxml')
download_link = soup.find("a")['href']

# Stopping the loading animation
run_anim = False
sleep(0.7)

# Downloading the book
with session.get(download_link, stream=True) as file:
    total_size = int(file.headers['content-length'])
    downloaded_size = 0
    BOOK = BOOK.replace(" ", "")
    extension = search_results[download_index].extension
    with open(BOOK+extension, 'wb') as downloaded_file:
        for content in file.iter_content(2048):
            downloaded_file.write(content)
            downloaded_size += 2048
            downloaded_percent = (downloaded_size/total_size)*100
            if downloaded_percent >= 100.0:
                downloaded_percent = 100.0
            downloaded_percent = str(downloaded_percent)
            # Modifying download_percent to have only one digit after the decimal
            downloaded_percent = downloaded_percent[:downloaded_percent.find(
                ".")+2]
            print("Downloading "+downloaded_percent+"%", end="\r", flush=True)

print("\n"+BOOK+extension+" Downloaded.")
