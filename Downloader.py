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


def exit_cleanly(text):
    print(text)
    sleep(2)
    exit()


def print_loading(text):
    """
        A function to print text with a loading animation
    """
    global run_anim
    animations = [text+"|", text+"/", text+"-", text+"\\"]
    while True:
        for anim in animations:
            print(anim, end="\r", flush=True)
            if not run_anim:
                return
            sleep(0.15)


def get_webpage(url):
    """
        Visits url and returns the contents, exits if user is offline
    """
    try:
        return session.get(url)
    except ConnectionError:
        global run_anim
        run_anim = False
        sleep(0.175)
        exit_cleanly("Looks like you are oflline.")


def search_for_book(search_url):
    """
        Visits the search_url and finds all the results
    """
    page = get_webpage(search_url).content
    soup = BeautifulSoup(page, 'lxml')
    # The table in which results are stored.
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


def present_results():
    """
        Presents search results
    """
    for index, book in enumerate(search_results):
        print(f"Index: {index+1}")
        print(f"Author: {book.author}")
        print(f"Name: {book.name}")
        print(f"Size: {book.size}")
        print(f"Length: {book.length}")
        print(f"Format: {book.extension}")
        print("\n")


def get_final_download_link(base_url):
    """
        Returns the final download link to the file after going through two pages
    """
    page = get_webpage("http://libgen.li/" +
                       base_url).content
    soup = BeautifulSoup(page, 'lxml')
    table = soup.find("table", {"border": 0, "width": "100%"})
    download_link = table.find("a")['href']
    page = get_webpage("http://libgen.li/"+download_link).content
    soup = BeautifulSoup(page, 'lxml')
    download_link = soup.find("a")['href']
    return download_link


def download(url, file_name):
    """
        Retrieves the data from url and saves it locally as file_name
    """
    with session.get(url, stream=True) as file:
        total_size = int(file.headers['content-length'])
        downloaded_size = 0
        with open(file_name, 'wb') as downloaded_file:
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
                print("Downloading "+downloaded_percent +
                      "%", end="\r", flush=True)


if __name__ == "__main__":
    query = input("Search(minimum 3 characters): ")  # The book to be searched

    if len(query) < 3:
        exit_cleanly(
            "The length of the search string must be greater than 3 characters.")

    search_url = "http://libgen.li/search.php?req=" + \
        query.replace(" ", "+")  # url to get search results
    search_results = []
    session = Session()

    # Starting the searching animation
    run_anim = True
    Thread(target=print_loading, args=("Searching",), daemon=True).start()

    search_for_book(search_url)

    # Stopping the searching animation
    run_anim = False
    sleep(0.175)

    # Exiting if no results were found
    if len(search_results) == 0:
        print("No results Found.")
        exit()

    print(str(len(search_results))+" books found.\n")
    present_results()

    try:
        download_index = int(input("Index of the book to download: "))-1
    except ValueError:
        exit_cleanly(
            "You should enter the number under the 'Index' section of the book and not some text.")

    # Starting a loading animation
    run_anim = True
    Thread(target=print_loading, args=("Fetching",), daemon=True).start()

    try:
        download_link = get_final_download_link(
            search_results[download_index].download_link)
    except IndexError:
        exit_cleanly(
            "Looks like you entered an index larger than the number of search results.")

    # Stopping the loading animation
    run_anim = False
    sleep(0.175)

    # Downloading the book selected
    extension = search_results[download_index].extension
    name = query.replace(" ", "")
    file_name = name+extension
    download(download_link, file_name)
    print("\n"+file_name+" Downloaded.")
