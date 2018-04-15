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
Last Modified: 13 Apr. 2018

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
import urllib.request


def self_recovery(function):
    """ Fail-safe when program fails

    This function should be used with the decorator
    @self_recovery only. Using this decorator will enable
    the ability for the decorated function to keep retrying
    until error is resolved.

    This function is made since konachan may ban requests. This is
    especially useful when using crawl_all
    """

    def wrapper(*args):
        while True:
            try:
                return function(*args)
            except FileNotFoundError:
                print('Error: Storage directory not found!')
                exit(1)
            except OSError as e:
                traceback.print_exc()
                hour = datetime.datetime.now().time().hour
                minute = datetime.datetime.now().time().minute
                second = datetime.datetime.now().time().second
                print('[{}:{}:{}] Socket error detected. Retrying.....'.format(hour, minute, second), end='\r')
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
        url and defines image storage folder.
        """
        self.begin_time = time.time()
        self.VERSION = '1.4'
        self.storage = '/tmp/konachan/'
        self.pages = False
        self.crawl_all = False
        self.yandere = False  # Use Yande.re website
        self.safe = True
        self.explicit = False
        self.questionable = False
        self.post_crawler_threads_amount = 10
        self.downloader_threads_amount = 20
        self.logging = True
        self.load_progress = False
        self.progress_file = 'konadl.progress'

    def icon(self):
        print('     _   __                       ______  _')
        print('    | | / /                       |  _  \| |')
        print('    | |/ /   ___   _ __    __ _   | | | || |')
        print('    |    \  / _ \ | \'_ \  / _` |  | | | || |')
        print('    | |\  \| (_) || | | || (_| |  | |/ / | |____')
        print('    \_| \_/ \___/ |_| |_| \__,_|  |___/  \_____/\n')
        print('            Konachan Downloader Library')
        spaces = ((44 - len('Kernel Version ' + self.VERSION)) // 2) * ' '
        print(spaces + '    Kernel Version ' + self.VERSION + '\n')

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

        # load progress from progress file if needed
        if self.load_progress:
            pages, page, download = self.read_progress()
            if pages.isdigit():
                self.pages = int(pages)
            else:
                index_page = self.get_page('{}/post?page=1&tags='.format(self.site_root))
                index_soup = BeautifulSoup(index_page, "html.parser")
                self.pages = int(index_soup.findAll('a', href=True)[-10].text)

        # Initialize page queue and downloader queue
        self.post_queue = queue.Queue()
        self.download_queue = queue.Queue()
        # Prepare containers for threads
        self.page_threads = []
        self.downloader_threads = []

        try:
            # Create post crawler threads
            for identifier in range(self.post_crawler_threads_amount):
                thread = threading.Thread(target=self.crawl_post_page_worker, args=(self.post_queue, self.download_queue))
                thread.name = 'Post Crawler {}'.format(identifier)
                thread.start()
                self.page_threads.append(thread)

            # Create image downloader threads
            for identifier in range(self.downloader_threads_amount):
                thread = threading.Thread(target=self.retrieve_post_image_worker, args=(self.download_queue,))
                thread.name = 'Downloader {}'.format(identifier)
                thread.start()
                self.downloader_threads.append(thread)

            # Every page is a job in the queue
            if self.load_progress:
                for page_num in range(page, self.pages + 1):
                    self.post_queue.put(page_num)
            else:
                for page_num in range(1, self.pages + 1):
                    self.post_queue.put(page_num)

            self.post_queue.join()
            self.download_queue.join()
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
        except (KeyboardInterrupt, SystemExit):
            # Main thread catches KeyboardInterrupt
            # Clear queues and put None as exit signal
            self.warn_keyboard_interrupt()
            if not self.download_queue.empty():
                self.print_saving_progress()
                self.save_progress()
            self.post_queue.queue.clear()
            for _ in range(self.post_crawler_threads_amount):
                self.post_queue.put(None)
            self.download_queue.queue.clear()
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None))

    def warn_keyboard_interrupt(self):
        """ Tells the user that Ctrl^C is caught
        This method can be overwritten in CLI for
        better appearance
        """
        print('[Main Thread] KeyboardInterrupt Caught!')
        print('[Main Thread] Flushing queues and exiting')

    def print_saving_progress(self):
        """ Tells the user progress is being saved
        This method can be overwritten in CLI for
        better appearance
        """
        print('[Main Thread] Saving progress')

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
        index_page = self.get_page('{}/post?page=1&tags='.format(self.site_root))
        index_soup = BeautifulSoup(index_page, "html.parser")
        self.pages = int(index_soup.findAll('a', href=True)[-10].text)
        self.crawl()

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

    @self_recovery
    def get_page(self, url):
        """ Get page using urllib.request
        Custom UA is provided to prevent unwanted bans
        """
        req = urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 \
                Safari/537.36'
            }
        )
        with urllib.request.urlopen(req) as response:
            return response.read()

    @self_recovery
    def download_file(self, url, page, file_name):
        """ Download file

        Downloads one file and saves it to the
        specified folder with its original name.
        """
        self.print_retrieval(url, page)
        suffix = url.split(".")[-1]
        file_path = self.storage + file_name + '.' + suffix
        urllib.request.urlretrieve(url, file_path)

    def print_retrieval(self, url, page):
        """ Print retrieval information
        This method can be overwritten in CLI for
        better appearance
        """
        hour = datetime.datetime.now().time().hour
        minute = datetime.datetime.now().time().minute
        second = datetime.datetime.now().time().second
        print("[{}:{}:{}] [Page={}]Retrieving: {}".format(hour, minute, second, page, url))

    @self_recovery
    def retrieve_post_image_worker(self, download_queue):
        """ Get the large image url and download

        Crawls the post page, find the large image url(s)
        and calls the downloader to download all of them.
        """
        while True:
            uri, page = download_queue.get()
            if uri is None:
                self.print_thread_exit(str(threading.current_thread().name))
                break
            image_page_source = self.get_page(self.site_root + uri)
            rating = self.get_page_rating(image_page_source.decode('utf-8'))

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
            for link in image_soup.findAll('img', {'class': 'image'}):
                if 'https:' not in link['src']:
                    self.download_file('https:' + link['src'], page, uri.split("/")[-1])
                else:
                    self.download_file(link['src'], page, uri.split("/")[-1])
            download_queue.task_done()

    @self_recovery
    def crawl_post_page_worker(self, post_queue, download_queue):
        """ Crawl the post list page and find posts

        Craws the posts index pages and record every post's
        url before handing them to the image downloader.
        """
        while True:
            page = post_queue.get()
            if page is None:
                self.print_thread_exit(str(threading.current_thread().name))
                break
            self.print_crawling_page(page)

            page_source = self.get_page('{}/post?page={}&tags='.format(self.site_root, page))
            soup = BeautifulSoup(page_source, "html.parser")
            for link in soup.findAll('a', href=True):
                if re.match('/post/show/[0-9]*', link['href']):
                    download_queue.put((link['href'], page))
            post_queue.task_done()

    def print_crawling_page(self, page):
        """ Print which page is being crawled
        This method can be overwritten in CLI for
        better appearance
        """
        print('Crawling page {}'.format(page))

    def print_thread_exit(self, name):
        """Thread exiting message
        """
        print('[libkonadl] {} thread exiting'.format(name))

    def save_progress(self):
        progress = configparser.ConfigParser()
        progress['PAGES'] = {}
        progress['CURRENTDOWNLOAD'] = {}
        progress['CURRENTPAGE'] = {}
        progress['RATINGS'] = {}

        if self.crawl_all:
            progress['PAGES']['pages'] = 'all'
        else:
            progress['PAGES']['pages'] = str(self.pages)
        download, page = self.download_queue.get(False)
        progress['CURRENTPAGE']['page'] = str(page)
        progress['CURRENTDOWNLOAD']['download'] = download
        self.download_queue.task_done()
        progress['RATINGS']['safe'] = str(self.safe)
        progress['RATINGS']['questionable'] = str(self.questionable)
        progress['RATINGS']['explicit'] = str(self.explicit)

        with open(self.progress_file, 'w') as progressf:
            progress.write(progressf)

    def read_progress(self):
        try:
            progress = configparser.ConfigParser()
            progress.read(self.progress_file)
            pages = progress['PAGES']['pages']
            page = int(progress['CURRENTPAGE']['page'])
            download = progress['CURRENTDOWNLOAD']['download']
            self.safe = bool(progress['RATINGS']['safe'])
            self.questionable = bool(progress['RATINGS']['questionable'])
            self.explicit = bool(progress['RATINGS']['explicit'])
            return pages, page, download
        except KeyError:
            self.print_faulty_progress_file()
            exit(1)

    def print_faulty_progress_file(self):
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
    kona.safe = True            # Include safe rated images
    kona.questionable = False   # Include questionable rated images
    kona.explicit = False       # Include explicit rated images

    # Set crawler and downloader threads
    kona.post_crawler_threads_amount = 10
    kona.downloader_threads_amount = 20
    kona.pages = 3  # Crawl 3 pages
    if os.path.isfile(kona.progress_file):
        print('Loading downloading progress')
        kona.load_progress = True

    # Execute
    kona.crawl()
    print('\nMain thread exited without errors')
    print('Time taken: {} seconds'.format(round((time.time() - kona.begin_time), 5)))
