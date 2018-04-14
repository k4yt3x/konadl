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
import datetime
import queue
import re
import threading
import traceback
import time
import urllib.request


def self_recovery(function):
    """ Fail-safe when program fails

    This function should be used with the decorator
    @self_recovery only. Using this decoratorwill enable
    the ability for the decorated function to keep retrying
    until error is resolved.

    This funciton is made since konachan may ban requests. This is
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
        self.VERSION = '1.3.1'
        self.storage = '/tmp/konachan/'
        self.yandere = False  # Use Yande.re website
        self.safe = True
        self.explicit = False
        self.questionable = False
        self.post_crawler_threads_amount = 10
        self.downloader_threads_amount = 20

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

    def crawl(self, total_pages):
        """ Generic crawling

        Regular crawling controller. Craws a certain amount
        of pages according to the specified value from argument
        "total_pages"
        """
        self.process_crawling_options()

        # Initialize page queue and downloader queue
        post_queue = queue.Queue()
        download_queue = queue.Queue()
        # Prepare containers for threads
        page_threads = []
        downloader_threads = []

        # Create post crawler threads
        for identifier in range(self.post_crawler_threads_amount):
            thread = threading.Thread(target=self.crawl_post_page_worker, args=(post_queue, download_queue))
            thread.name = 'Post Crawler {}'.format(identifier)
            thread.start()
            page_threads.append(thread)

        # Create image downloader threads
        for identifier in range(self.downloader_threads_amount):
            thread = threading.Thread(target=self.retrieve_post_image_worker, args=(download_queue,))
            thread.name = 'Downloader {}'.format(identifier)
            thread.start()
            downloader_threads.append(thread)

        # Every page is a job in the queue
        for page_num in range(1, total_pages + 1):
            post_queue.put(page_num)

        post_queue.join()
        download_queue.join()
        for _ in range(self.post_crawler_threads_amount):
            post_queue.put(None)
        for _ in range(self.downloader_threads_amount):
            download_queue.put(None)

        while True:
            for thread in page_threads:
                if thread.is_alive():
                    continue
            for thread in downloader_threads:
                if thread.is_alive():
                    continue
            time.sleep(1)
            break

    def crawl_page(self, page_num):
        """ Crawl a specific page

        This is very similar to the "crawl" method.
        Instead of crawling a number of pages, this
        method crawls images on a specific page.
        """
        self.process_crawling_options()
        page_posts = self.crawl_post_page(page_num)
        for post in page_posts:
            self.retrieve_post_image(post)

    def crawl_all(self):
        """ Crawl the entire site

        WARNING: this will crawl thousands of pages
        use with caution!
        """
        self.process_crawling_options()
        index_page = self.get_page('{}/post?page=1&tags='.format(self.site_root))
        index_soup = BeautifulSoup(index_page, "html.parser")
        total_pages = int(index_soup.findAll('a', href=True)[-10].text)
        self.crawl(total_pages)

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
    def download_file(self, url, file_name):
        """ Download file

        Downloads one file and saves it to the
        specified folder with its original name.
        """
        self.print_retrieval(url)
        suffix = url.split(".")[-1]
        file_path = self.storage + file_name + '.' + suffix
        urllib.request.urlretrieve(url, file_path)

    def print_retrieval(self, url):
        """ Print retrieval information
        This method can be overwritten in CLI for
        better appearance
        """
        hour = datetime.datetime.now().time().hour
        minute = datetime.datetime.now().time().minute
        second = datetime.datetime.now().time().second
        print("[{}:{}:{}] Retrieving: {}".format(hour, minute, second, url))

    @self_recovery
    def retrieve_post_image_worker(self, download_queue):
        """ Get the large image url and download

        Crawls the post page, find the large image url(s)
        and calls the downloader to download all of them.
        """
        while True:
            uri = download_queue.get()
            if uri is None:
                self.print_thread_exit(str(threading.current_thread().name))
                break
            image_page_source = self.get_page(self.site_root + uri)
            rating = self.get_page_rating(image_page_source.decode('utf-8'))

            if kona.safe and rating == 'safe':
                pass
            elif kona.questionable and rating == 'questionable':
                pass
            elif kona.explicit and rating == 'explicit':
                pass
            else:
                continue

            image_soup = BeautifulSoup(image_page_source, "html.parser")
            for link in image_soup.findAll('img', {'class': 'image'}):
                if 'https:' not in link['src']:
                    self.download_file('https:' + link['src'], uri.split("/")[-1])
                else:
                    self.download_file(link['src'], uri.split("/")[-1])
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
                    download_queue.put(link['href'])
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


if __name__ == '__main__':
    """ Sample crawling

    Crawls safe images off of konachan.com
    when called directly as a standalone program
    for demonstration.
    """
    kona = konadl()  # Create crawler object
    kona.storage = '/tmp/konachan/'  # note there's a '/' at the end

    kona.yandere = False  # If you want to crawl yande.re

    # Set rating settings
    kona.safe = True
    kona.explicit = False
    kona.questionable = False
    kona.post_crawler_threads_amount = 10
    kona.downloader_threads_amount = 20
    kona.crawl(10)  # Execute. Crawl 10 pages
    print('\nKonachan Downloader finished successfully')
    print('Time taken: {} seconds'.format(round((time.time() - kona.begin_time), 5)))
