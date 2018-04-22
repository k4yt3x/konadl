#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 _   __                       ______  _
| | / /                       |  _  \| |
| |/ /   ___   _ __    __ _   | | | || |
|    \  / _ \ | '_ \  / _` |  | | | || |
| |\  \| (_) || | | || (_| |  | |/ / | |____
\_| \_/ \___/ |_| |_| \__,_|  |___/  \_____/


Name: Konachan Downloader Library
Dev: K4YT3X
Date Created: 11 Apr. 2018
Last Modified: 22 Apr. 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X

Description: Konachan downloader is a simple python
script / library that will help you download
konachan.com / konachan.net images.
"""
from bs4 import BeautifulSoup
import configparser
import datetime
import os
import queue
import re
import threading
import time
import traceback
import requests


def print_locker(function):
    """ Prevents printing formating error

    Prevents other threads from printing when
    current thread is printing.
    """

    def wrapper(*args):
        args[0].print_lock.acquire()
        function(*args)
        args[0].print_lock.release()
    return wrapper


class konadl:
    """
    Konachan Downloader

    This class will help you bulk retrieve
    images off of konachan.com/.net. Refer
    to github page for tutorials.
    """

    def __init__(self):
        """ Initialize crawler

        This method initializes the crawler, defines site root
        URL and defines image storage folder.
        """
        self.begin_time = time.time()
        self.VERSION = '1.7 beta3'
        self.storage = '/tmp/konachan/'
        self.pages = False
        self.crawl_all = False
        self.yandere = False  # Use Yande.re website
        self.safe = True
        self.explicit = False
        self.questionable = False
        self.post_crawler_threads_amount = 10
        self.downloader_threads_amount = 20
        self.load_progress = False
        self.error_logs_file = False
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 \
                        Safari/537.36'}

    def icon(self):
        print('     _   __                       ______  _')
        print('    | | / /                       |  _  \| |')
        print('    | |/ /   ___   _ __    __ _   | | | || |')
        print('    |    \  / _ \ | \'_ \  / _` |  | | | || |')
        print('    | |\  \| (_) || | | || (_| |  | |/ / | |____')
        print('    \_| \_/ \___/ |_| |_| \__,_|  |___/  \_____/\n')
        print('            Konachan Downloader Library')
        spaces = ((44 - len('Kernel Version ' + self.VERSION)) // 2) * ' '
        print(spaces + '   Kernel Version ' + self.VERSION + '\n')

    def write_traceback(self, uri=False, page=False):
        """ Records traceback information

        This method prints the error message to screen and
        writes the full traceback information to error log
        if self.error_logs_file is defined.
        """
        # print error to screen
        traceback.print_exc()
        # writes error to log
        if self.error_logs_file:
            self.error_log_lock.acquire()
            with open(self.error_logs_file, 'a+') as error_file:
                error_file.write('TIME={}\n'.format(
                    str(datetime.datetime.now())))
                if page:
                    error_file.write('PAGE={}\n'.format(page))
                if uri:
                    error_file.write('URI={}\n'.format(uri))
                traceback.print_exc(file=error_file)
                error_file.write('\n')
                error_file.close()
            self.error_log_lock.release()

    def process_crawling_options(self):
        """ Processes crawling options

        Processes crawling information. Core function is to
        determine the value for self.site_root.
        """
        if self.explicit:
            self.site_root = 'https://konachan.com'
        else:
            self.site_root = 'https://konachan.net'
        if self.yandere:
            self.site_root = 'https://yande.re'

    def crawl(self):
        """ Generic crawling

        Regular crawling controller. Craws a certain amount
        of pages according to the specified value from argument
        "total_pages"
        """
        self.process_crawling_options()
        self.error_logs_file = '{}errors.log'.format(self.storage)

        # Initialize page queue and downloader queue
        self.post_queue = queue.Queue()
        self.download_queue = queue.Queue()
        # Prepare containers for threads
        self.page_threads = []
        self.downloader_threads = []

        self.print_lock = threading.Lock()
        self.error_log_lock = threading.Lock()

        # load progress from progress file if needed
        if self.load_progress:
            self.read_progress()

        try:
            # Create post crawler threads
            for identifier in range(self.post_crawler_threads_amount):
                thread = threading.Thread(target=self.crawl_post_page_worker, args=(
                    self.post_queue, self.download_queue))
                thread.name = 'Post Crawler {}'.format(identifier)
                thread.start()
                self.page_threads.append(thread)

            # Create image downloader threads
            for identifier in range(self.downloader_threads_amount):
                thread = threading.Thread(
                    target=self.retrieve_post_image_worker, args=(self.download_queue,))
                thread.name = 'Downloader {}'.format(identifier)
                thread.start()
                self.downloader_threads.append(thread)

            # Every page is a job in the queue
            if not self.load_progress:
                for page_num in range(1, self.pages + 1):
                    self.post_queue.put(page_num)

            # Wait for all jobs to be done
            self.post_queue.join()
            self.download_queue.join()
            # Send exit signal to all threads
            for _ in range(self.post_crawler_threads_amount):
                self.post_queue.put(None)
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None))

            while True:
                for thread in self.page_threads:
                    if thread.is_alive():
                        continue
                for thread in self.downloader_threads:
                    if thread.is_alive():
                        continue
                time.sleep(1)
                break

            return True  # Job entirely done
        except (KeyboardInterrupt, SystemExit):
            # Main thread catches KeyboardInterrupt
            # Clear queues and put None as exit signal
            self.warn_keyboard_interrupt()
            if not self.download_queue.empty():
                self.save_progress()
            self.post_queue.queue.clear()
            for _ in range(self.post_crawler_threads_amount):
                self.post_queue.put(None)
            self.download_queue.queue.clear()
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None))
            return False  # Job paused

    def crawl_page(self, page_num):
        """ [OUTDATED] Crawl a specific page

        This is very similar to the "crawl" method.
        Instead of crawling a number of pages, this
        method crawls images on a specific page.
        """
        self.process_crawling_options()
        page_posts = self.crawl_post_page(page_num)
        for post in page_posts:
            self.retrieve_post_image(post)

    def crawl_all_pages(self):
        """ Crawl the entire site

        WARNING: this will crawl thousands of pages
        use with caution!
        """
        self.crawl_all = True
        self.process_crawling_options()
        # Crawl the first post page and read the number of total pages
        index_page = requests.get(
            '{}/post?page=1&tags='.format(self.site_root), headers=self.headers).text
        index_soup = BeautifulSoup(index_page, "html.parser")
        # Find the page number of the last page
        self.pages = int(index_soup.findAll('a', href=True)[-10].text)
        return self.crawl()

    def get_page_rating(self, content):
        """ Get page rating

        Determines page rating by searching key
        words in the page.
        """
        if 'Rating: Explicit' in content:
            return 'explicit'
        elif 'Rating: Questionable' in content:
            return 'questionable'
        elif 'Rating: Safe'in content:
            return 'safe'
        else:
            return False

    def retrieve_post_image_worker(self, download_queue):
        """ Get the large image url and download

        Crawls the post page, find the large image url(s)
        and calls the downloader to download all of them.
        """
        while True:
            file_path = False
            try:
                uri, page = download_queue.get()
                if uri is None:
                    self.print_thread_exit(
                        str(threading.current_thread().name))
                    break
                image_page_source = requests.get(
                    self.site_root + uri, headers=self.headers).text
                rating = self.get_page_rating(
                    image_page_source)

                # Determine if the current page is desired to be downloaded
                if self.safe and rating == 'safe':
                    pass
                elif self.questionable and rating == 'questionable':
                    pass
                elif self.explicit and rating == 'explicit':
                    pass
                else:
                    download_queue.task_done()
                    continue

                image_soup = BeautifulSoup(image_page_source, "html.parser")
                for link in image_soup.findAll('a', {'id': 'highres'}):
                    file_name = link['href'].split("/")[-1].replace('%20', '_').replace('_-_', '_')
                    self.print_retrieval(link['href'], page)
                    suffix = link['href'].split(".")[-1]
                    file_path = '{}{}.{}'.format(self.storage, file_name, suffix)
                    image_request = requests.get(link['href'], headers=self.headers)
                    with open(file_path, 'wb') as file:
                        file_length = file.write(image_request.content)
                        file.close()
                if int(image_request.headers['content-length']) != file_length:
                    raise Exception('Faulty download')
                elif image_request.status_code != requests.codes.ok:
                    if image_request.status_code == 429:
                        self.print_429()
                    download_queue.task_done()
                    download_queue.put((uri, page))
                    os.remove(file_path)
                    image_request.raise_for_status()
                download_queue.task_done()
            except requests.exceptions.HTTPError:
                self.write_traceback(page=page)
            except Exception:
                self.write_traceback(uri=uri, page=page)
                self.print_exception()
                download_queue.task_done()
                download_queue.put((uri, page))
                if file_path:
                    os.remove(file_path)

    def crawl_post_page_worker(self, post_queue, download_queue):
        """ Crawl the post list page and find posts

        Craws the posts index pages and record every post's
        URL before handing them to the image downloader.
        """
        while True:
            try:
                page = post_queue.get()
                if page is None:
                    self.print_thread_exit(
                        str(threading.current_thread().name))
                    break
                self.print_crawling_page(page)
                page_source = requests.get(
                    '{}/post?page={}&tags='.format(self.site_root, page), headers=self.headers)
                if page_source.status_code != requests.codes.ok:
                    if page_source.status_code == 429:
                        self.print_429()
                    post_queue.task_done()
                    post_queue.put(page)
                    page_source.raise_for_status()
                soup = BeautifulSoup(page_source.text, "html.parser")
                for link in soup.findAll('a', href=True):
                    if re.match('/post/show/[0-9]*', link['href']):
                        download_queue.put((link['href'], page))
                post_queue.task_done()
            except requests.exceptions.HTTPError:
                self.write_traceback(page=page)
            except Exception:
                self.write_traceback(page=page)
                self.print_exception()
                post_queue.task_done()
                post_queue.put(page)

    def progress_files_present(self):
        # Determines if the progress files are present
        self.progress_files = ['{}download_queue.progress'.format(self.storage),
                               '{}post_queue.progress'.format(self.storage),
                               '{}settings.progress'.format(self.storage)]
        for file in self.progress_files:
            if not os.path.isfile(file):
                return False
        return True

    def remove_progress_files(self):
        for file in self.progress_files:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

    def save_progress(self):
        """ Saves the download progress

        TODO: find a more accurate method of recording
        the download progress. The current method is not
        accurate if an error has occurred during the
        download or if the page order in download queue
        is complete.

        The better way might be writing everything in
        memory (download_queue, post_queue, etc.) to
        the progress file, which everything can be recovered
        accurately.
        """
        with open('{}download_queue.progress'.format(self.storage), 'w') as download_progress:
            while not self.download_queue.empty():
                link, page = self.download_queue.get()
                download_progress.write('{}|{}\n'.format(link, str(page)))
                self.download_queue.task_done()
            download_progress.close()

        with open('{}post_queue.progress'.format(self.storage), 'w') as post_progress:
            while not self.post_queue.empty():
                post_progress.write('{}\n'.format(self.post_queue.get()))
                self.post_queue.task_done()
            post_progress.close()

        self.print_saving_progress()
        progress = configparser.ConfigParser()
        progress['RATINGS'] = {}
        progress['RATINGS']['safe'] = str(int(self.safe))
        progress['RATINGS']['questionable'] = str(int(self.questionable))
        progress['RATINGS']['explicit'] = str(int(self.explicit))

        with open('{}settings.progress'.format(self.storage), 'w') as progressf:
            progress.write(progressf)

    def read_progress(self):
        """ Reads the download progress

        Parses the download progress and returns
        the configuration file contents.
        """
        self.print_loading_progress()

        try:
            with open('{}download_queue.progress'.format(self.storage), 'r') as download_progress:
                for line in download_progress:
                    self.download_queue.put(
                        (line.split('|')[0], int(line.split('|')[1].strip('\n'))))

            with open('{}post_queue.progress'.format(self.storage), 'r') as post_progress:
                for line in post_progress:
                    self.post_queue.put(int(line.strip('\n')))
                post_progress.close()

            progress = configparser.ConfigParser()
            progress.read('{}settings.progress'.format(self.storage))
            self.safe = bool(int(progress['RATINGS']['safe']))
            self.questionable = bool(int(progress['RATINGS']['questionable']))
            self.explicit = bool(int(progress['RATINGS']['explicit']))
        except (KeyError, ValueError):
            self.print_faulty_progress_file()
            exit(1)

    @print_locker
    def warn_keyboard_interrupt(self):
        # Tells the user that Ctrl^C is caught
        print('[Main Thread] KeyboardInterrupt Caught!')
        print('[Main Thread] Flushing queues and exiting')

    @print_locker
    def print_saving_progress(self):
        # Tells the user that the progress is being saved
        print('[Main Thread] Saving progress to {}'.format(self.storage))

    def print_loading_progress(self):
        # Tells the user that the progress is being loaded
        print('[Main Thread] Loading progress from {}'.format(self.storage))

    @print_locker
    def print_retrieval(self, url, page):
        # Print retrieval information
        hour = datetime.datetime.now().time().hour
        minute = datetime.datetime.now().time().minute
        second = datetime.datetime.now().time().second
        print("[{}:{}:{}] [Page={}] Retrieving: {}".format(
            hour, minute, second, page, url))

    @print_locker
    def print_crawling_page(self, page):
        # Print which page is being crawled
        print('Crawling page {}'.format(page))

    @print_locker
    def print_thread_exit(self, name):
        # Thread exiting message
        print('[libkonadl] {} thread exiting'.format(name))

    @print_locker
    def print_429(self):
        # HTTP returns 429
        print('HTTP Error 429: You are sending too many requests')
        print('Trying to recover from error')
        print('Putting job back to queue')

    @print_locker
    def print_exception(self):
        # Any exception
        print('An error has occurred in this thread')
        print('Trying to recover from error')
        print('Putting job back to queue')

    @print_locker
    def print_faulty_progress_file(self):
        # Tell the use the progress file is faulty
        print('Error: Faulty progress file!')
        print('Aborting\n')


if __name__ == '__main__':
    """ Sample crawling

    Crawls safe images off of konachan.com
    when called directly as a standalone program
    for demonstration.
    """
    kona = konadl()  # Create crawler object

    # Set storage directory
    # Note that there's a "/" and the end
    kona.storage = '/tmp/konachan/'
    if not os.path.isdir(kona.storage):  # Quit if storage directory not found
        print('Error: storage directory not found')
        exit(1)

    # Set this to True If you want to crawl yande.re
    kona.yandere = False

    # Download images by ratings
    kona.safe = False            # Include safe rated images
    kona.questionable = False   # Include questionable rated images
    kona.explicit = True       # Include explicit rated images

    # Set crawler and downloader threads
    kona.post_crawler_threads_amount = 10
    kona.downloader_threads_amount = 20
    kona.pages = 3  # Crawl 3 pages

    kona.load_progress = False
    if kona.progress_files_present():
        kona.load_progress = True

    # Execute
    kona.crawl()
    print('\nMain thread exited without errors')
    print('Time taken: {} seconds'.format(
        round((time.time() - kona.begin_time), 5)))
