#!/usr/bin/python3

from time import sleep
from threading import Thread
import readline


def install(package):
    import subprocess
    import sys
    try:
        subprocess.call([sys.executable, "-m", "pip",
                         "install", package])
    except:
        print("Looks like you don't have pip installed.")
        sleep(2)
        exit()


try:
    from requests import Session
    from requests.exceptions import ConnectionError
except ModuleNotFoundError:
    install("requests")
    from requests import Session
    from requests.exceptions import ConnectionError
try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    install("beautifulsoup4")
    from bs4 import BeautifulSoup


class Book:
    def __init__(self, author, name, download_link, size, length, extension):
        self.author = author
        self.name = name
        self.download_link = download_link
        self.size = size
        self.length = length
        self.extension = extension  # .pdf,.epub etc


def exit_cleanly(text, time_out=3):
    global run_anim
    run_anim = False
    sleep(0.175)
    print(text)
    sleep(time_out)
    exit()


def print_loading(text):
    """
        A function to print text with a loading animation
    """
    global run_anim
    animations = [text+"|", text+"/", text+"-", text+"\\"]
    while True:
        for anim in animations:
            print(anim, end=+10*" "+"\r", flush=True)
            if not run_anim:
                return
            sleep(0.15)


def get_soup(url):
    """
        Visits url and returns the contents, exits if user is offline
    """
    try:
        page = session.get(url).content
        soup = BeautifulSoup(page, 'lxml')
        return soup
    except ConnectionError:
        exit_cleanly("Looks like you are oflline.")
    except NameError:
        exit_cleanly(
            "Unkown Error had occured while installing beautifulsoup4.", 5)


def search_for_book(query):
    """
        searches for the query and stores the results in a list
    """

    search_url = "http://libgen.li/search.php?req=" + \
        query.replace(" ", "+")  # url to get search results

    soup = get_soup(search_url)

    # The table in which results are stored.
    results_part = soup.find("table", {"class": "c"})
    try:
        results = results_part.find_all("tr", recursive=False)
    except AttributeError:
        exit_cleanly(soup.get_text(), 10)
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
    soup = get_soup("http://libgen.li/" +
                    base_url)
    table = soup.find("table", {"border": 0, "width": "100%"})
    download_link = table.find("a")['href']
    soup = get_soup("http://libgen.li/"+download_link)
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
                      "%", end=10*" "+"\r", flush=True)


if __name__ == "__main__":
    # The book to be searched
    query = input("Search(minimum 3 characters): ")

    if len(query) < 3:
        exit_cleanly(
            "The length of the search string must be greater than 3 characters.")

    search_results = []
    try:
        session = Session()
    except NameError:
        exit_cleanly("Unkown error occured while installing requests module.")
    # Starting the searching animation
    run_anim = True
    search_thread = Thread(target=print_loading,
                           args=("Searching",), daemon=True)
    search_thread.start()

    search_for_book(query)

    # Stopping the searching animation
    run_anim = False
    search_thread.join()

    # Exiting if no results were found
    if len(search_results) == 0:
        exit_cleanly("No results found.")

    print(str(len(search_results))+" books found.\n")

    present_results()

    try:
        download_index = int(input("Index of the book to download: "))-1
    except ValueError:
        exit_cleanly(
            "You should enter the number under the 'Index' section of the book and not some text.")

    # Starting a loading animation
    run_anim = True
    fetch_thread = Thread(target=print_loading,
                          args=("Fetching",), daemon=True)
    fetch_thread.start()

    try:
        download_link = get_final_download_link(
            search_results[download_index].download_link)
    except IndexError:
        exit_cleanly(
            "Looks like you entered an index larger than the number of search results.")

    # Stopping the loading animation
    run_anim = False
    fetch_thread.join()

    # Downloading the book selected
    extension = search_results[download_index].extension
    name = query.replace(" ", "")
    file_name = name+extension
    download(download_link, file_name)
    print("\n"+file_name+" Downloaded.\n")
