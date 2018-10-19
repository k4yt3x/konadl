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
Date Created: April 11, 2018
Last Modified: July 7, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X

Description: Konachan downloader is a simple python
script / library that will help you download
konachan.com / konachan.net images.
"""
from bs4 import BeautifulSoup
from queue import Queue as _Queue
import copyreg
import datetime
import json
import os
import pickle
import requests
import sys
import threading
import time
import traceback


# Make Queue a new-style class, so it can be used with copy_reg
class Queue(_Queue, object):
    pass


def pickle_queue(q):
    # Shallow copy of __dict__ (the underlying deque isn't actually copied, so this is fast)
    q_dct = q.__dict__.copy()
    # Remove all non-picklable synchronization primitives
    del q_dct['mutex']
    del q_dct['not_empty']
    del q_dct['not_full']
    del q_dct['all_tasks_done']
    return Queue, (), q_dct


def unpickle_queue(state):
    # Recreate our queue.
    q = state[0]()
    q.mutex = threading.Lock()
    q.not_empty = threading.Condition(q.mutex)
    q.not_full = threading.Condition(q.mutex)
    q.all_tasks_done = threading.Condition(q.mutex)
    q.__dict__ = state[2]
    return q


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


class Konadl:
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
        self.time_elapsed = 0
        self.VERSION = '1.9.0'
        self.storage = '/tmp/konachan/'
        self.separate = False
        self.total_downloads = 0
        self.pages = False
        self.crawl_all = False
        self.yandere = False  # Use Yande.re website
        self.safe = True
        self.explicit = False
        self.questionable = False
        self.current_newest_id = False
        self.previous_newest_id = False
        self.post_crawler_threads_amount = 10
        self.downloader_threads_amount = 20
        self.job_done = False
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

    def write_traceback(self, url=False, page=False):
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
                if url:
                    error_file.write('URL={}\n'.format(url))
                traceback.print_exc(file=error_file)
                error_file.write('\n')
                error_file.close()
            self.error_log_lock.release()

    def process_crawling_options(self):
        """ Processes crawling options

        Processes crawling information. Core function is to
        determine the value for self.site_root.
        """
        self.site_root = 'https://konachan.com'
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
        copyreg.pickle(Queue, pickle_queue, unpickle_queue)
        self.post_queue = Queue()
        self.download_queue = Queue()
        # Prepare containers for threads
        self.page_threads = []
        self.downloader_threads = []

        self.print_lock = threading.Lock()
        self.error_log_lock = threading.Lock()
        self.abort = False

        # load progress from progress file if needed
        if self.load_progress:
            self.read_queues()

        try:
            self.current_newest_id = self.get_newest_image_id()

            # Create post crawler threads
            for identifier in range(self.post_crawler_threads_amount):
                thread = threading.Thread(target=self.crawl_post_page_worker)
                thread.name = 'Post Crawler {}'.format(identifier)
                thread.start()
                self.page_threads.append(thread)

            # Create image downloader threads
            for identifier in range(self.downloader_threads_amount):
                thread = threading.Thread(
                    target=self.retrieve_post_image_worker)
                thread.name = 'Downloader {}'.format(identifier)
                thread.start()
                self.downloader_threads.append(thread)

            # Every page is a job in the queue
            if not self.load_progress:
                for page_num in range(1, self.pages + 1):
                    self.post_queue.put(page_num)

            # Wait for all jobs to be done
            # We are not using Queue.join() since if the session is restored,
            # Queue will not join even when all jobs are done.
            if self.load_progress:
                while not self.post_queue.empty() or not self.download_queue.empty():
                    time.sleep(0.1)  # Make each tick longer than pass
            else:
                self.post_queue.join()
                self.download_queue.join()

            # Send exit signal to all threads
            for _ in range(self.post_crawler_threads_amount):
                self.post_queue.put(None)
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None, None))

            for thread in self.page_threads:
                thread.join()
            for thread in self.downloader_threads:
                thread.join()

            self.job_done = True
            self.save_metadata()
            return True  # Job entirely done
        except (KeyboardInterrupt, SystemExit):
            # Main thread catches KeyboardInterrupt
            # Clear queues and put None as exit signal
            self.warn_keyboard_interrupt()
            self.abort = True
            if not self.download_queue.empty():
                self.save_queues()

            self.post_queue.queue.clear()
            for _ in range(self.post_crawler_threads_amount):
                self.post_queue.put(None)
            self.download_queue.queue.clear()
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None, None))

            for thread in self.page_threads:
                thread.join()
            for thread in self.downloader_threads:
                thread.join()

            self.save_metadata()
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
        self.pages = self.get_total_pages()
        return self.crawl()

    def update(self):
        self.process_crawling_options()
        self.read_metadata()
        self.current_newest_id = self.get_newest_image_id()
        self.error_logs_file = '{}errors.log'.format(self.storage)

        # Initialize page queue and downloader queue
        self.post_queue = Queue()
        self.download_queue = Queue()
        # Prepare containers for threads
        self.downloader_threads = []

        self.print_lock = threading.Lock()
        self.error_log_lock = threading.Lock()

        if self.get_newest_image_id() == self.previous_newest_id:
            return False

        try:

            # Create image downloader threads
            for identifier in range(self.downloader_threads_amount):
                thread = threading.Thread(
                    target=self.retrieve_post_image_worker, args=(self.download_queue,))
                thread.name = 'Downloader {}'.format(identifier)
                thread.start()
                self.downloader_threads.append(thread)

            self.crawl_new_images()

            self.download_queue.join()
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None, None))
            for thread in self.downloader_threads:
                thread.join()
            self.job_done = True
            self.save_metadata()
            return True
        except (KeyboardInterrupt, SystemExit):
            self.warn_keyboard_interrupt()
            if not self.download_queue.empty():
                self.save_queues()

            self.download_queue.queue.clear()
            for _ in range(self.downloader_threads_amount):
                self.download_queue.put((None, None, None))
            for thread in self.downloader_threads:
                thread.join()

            self.save_metadata()
            return False  # Job paused

    def get_total_pages(self):
        # Crawl the first post page and read the number of total pages
        index_page = requests.get('{}/post?page=1&tags='.format(self.site_root), headers=self.headers).text
        index_soup = BeautifulSoup(index_page, 'html.parser')
        # Find the page number of the last page
        return int(index_soup.findAll('a', href=True)[-10].text)

    def get_newest_image_id(self):
        """Gets the id of the newest image

        Gets the ID of the newest image, where the rating
        of the image has to be included in the desired
        ratings.
        """
        index_page = requests.get('{}/post?page=1&tags='.format(self.site_root), headers=self.headers).text
        index_soup = BeautifulSoup(index_page, 'html.parser')
        posts_list = index_soup.find('ul', {'id': 'post-list-posts'})
        posts = posts_list.findAll('li')
        for post in posts:
            alt = post.find('img', alt=True)['alt']
            rating = False
            if 'Rating: Safe'in alt and self.safe:
                rating = 'safe'
            elif 'Rating: Questionable' in alt and self.questionable:
                rating = 'questionable'
            elif 'Rating: Explicit' in alt and self.explicit:
                rating = 'explicit'
            if rating:
                return(post['id'])

    def crawl_new_images(self):
        """ Load all new images

        Crawl the site and append all the new images
        since the last download into download_queue
        """
        update_post_queue = Queue()
        for page_num in range(1, self.get_total_pages() + 1):
            update_post_queue.put(page_num)

        while not update_post_queue.empty():
            page = update_post_queue.get()
            self.print_crawling_page(page)
            page_source = requests.get('{}/post?page={}&tags='.format(self.site_root, page), headers=self.headers)
            if page_source.status_code != requests.codes.ok:
                if page_source.status_code == 429:
                    self.print_429()
                page_source.raise_for_status()
            soup = BeautifulSoup(page_source.text, "html.parser")
            # Find large image link and ratings
            posts_list = soup.find('ul', {'id': 'post-list-posts'})
            posts = posts_list.findAll('li')

            for post in posts:
                if post['id'] == self.previous_newest_id:
                    return
                alt = post.find('img', alt=True)['alt']
                rating = False
                if 'Rating: Safe'in alt and self.safe:
                    rating = 'safe'
                elif 'Rating: Questionable' in alt and self.questionable:
                    rating = 'questionable'
                elif 'Rating: Explicit' in alt and self.explicit:
                    rating = 'explicit'
                if rating:
                    url = post.find('a', {'class': 'directlink'})['href']
                    if 'https:' not in url:
                        url = '{}{}'.format('https:', url)
                    self.download_queue.put((url, page, rating))

    def retrieve_post_image_worker(self):
        """ Get the large image url and download

        Crawls the post page, find the large image url(s)
        and calls the downloader to download all of them.
        """

        # Always check if main thread wants to abort before getting a job
        while not self.abort:
            try:

                # Get a job from queue
                url, page, rating = self.download_queue.get()

                # Check if main thread wants to exit
                if url is None:
                    break

                # Start retrieving image
                self.print_retrieval(url, page)
                file_name = url.split("/")[-1].replace('%20', '_').replace('_-_', '_')
                subfolder = ''

                # Store into subdirectories if requested
                if self.separate:
                    subfolder = '{}/'.format(rating)
                file_path = '{}{}{}'.format(self.storage, subfolder, file_name)

                # Get image
                image_request = requests.get(url, headers=self.headers)

                # Write image to file
                with open(file_path, 'wb') as file:
                    file_length = file.write(image_request.content)
                    file.close()

                # Check image integrity
                if int(image_request.headers['content-length']) != file_length:
                    raise Exception('Faulty download')

                # Put job back to queue if 429 detected and warn user
                elif image_request.status_code != requests.codes.ok:
                    if image_request.status_code == 429:
                        self.print_429()
                    self.download_queue.task_done()
                    self.download_queue.put((url, page, rating))
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    image_request.raise_for_status()
                self.total_downloads += 1
                self.download_queue.task_done()
            except requests.exceptions.HTTPError:
                self.write_traceback(page=page)
            except Exception:
                self.write_traceback(url=url, page=page)
                self.print_exception()
                self.download_queue.task_done()
                self.download_queue.put((url, page, rating))
                if os.path.isfile(file_path):
                    os.remove(file_path)

        # Print exit message when thread exits
        self.print_thread_exit(str(threading.current_thread().name))

    def crawl_post_page_worker(self):
        """ Crawl the post list page and find posts

        Craws the posts index pages and record every post's
        URL before handing them to the image downloader.
        """

        # Always check if main thread wants to abort before getting a job
        while not self.abort:
            try:
                # Get job from queue
                page = self.post_queue.get()
                if page is None:
                    break

                self.print_crawling_page(page)

                # Get the page source
                page_source = requests.get(
                    '{}/post?page={}&tags='.format(self.site_root, page), headers=self.headers)

                # Put job back to queue if 429 received, and warn the user
                if page_source.status_code != requests.codes.ok:
                    if page_source.status_code == 429:
                        self.print_429()
                    self.post_queue.task_done()
                    self.post_queue.put(page)
                    page_source.raise_for_status()

                # Start parsing page
                soup = BeautifulSoup(page_source.text, "html.parser")

                # Find large image link and ratings
                posts_list = soup.find('ul', {'id': 'post-list-posts'})
                posts = posts_list.findAll('li')

                # For every post, if its rating is what we want, add the
                # post into the download_queue
                for post in posts:
                    alt = post.find('img', alt=True)['alt']
                    rating = False
                    if 'Rating: Safe'in alt and self.safe:
                        rating = 'safe'
                    elif 'Rating: Questionable' in alt and self.questionable:
                        rating = 'questionable'
                    elif 'Rating: Explicit' in alt and self.explicit:
                        rating = 'explicit'
                    if rating:
                        url = post.find('a', {'class': 'directlink'})['href']
                        if 'https:' not in url:
                            url = '{}{}'.format('https:', url)
                        self.download_queue.put((url, page, rating))
                self.post_queue.task_done()
            except requests.exceptions.HTTPError:
                self.write_traceback(page=page)
            except Exception:
                self.write_traceback(page=page)
                self.print_exception()
                self.post_queue.task_done()
                self.post_queue.put(page)

        # Print exit message when thread exits
        self.print_thread_exit(str(threading.current_thread().name))

    def progress_files_present(self):
        # Determines if the progress files are present
        self.progress_files = ['{}download_queue.pkl'.format(self.storage),
                               '{}post_queue.pkl'.format(self.storage)]
        for file in self.progress_files:
            if not os.path.isfile(file):
                return False
        return True

    def remove_progress_files(self):
        # Remove progress files
        # Called when download is fully finished
        for file in self.progress_files:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

    def metadata_present(self):
        return os.path.isfile('{}metadata.json'.format(self.storage))

    def remove_metatada(self):
        # Remove metadata
        # Called when an old download progress is to be
        # removed
        try:
            os.remove('{}metadata.json'.format(self.storage))
        except FileNotFoundError:
            pass

    def save_metadata(self):
        """ Saves the settings and stats into file

        Saves the desired rating, total downloads
        and time information into file.
        """
        self.print_saving_progress()

        metadata = {}
        metadata['RATINGS'] = {}
        metadata['RATINGS']['safe'] = self.safe
        metadata['RATINGS']['questionable'] = self.questionable
        metadata['RATINGS']['explicit'] = self.explicit
        metadata['STATISTICS'] = {}
        metadata['STATISTICS']['total_downloads'] = self.total_downloads
        metadata['STATISTICS']['time_elapsed'] = round((time.time() - self.begin_time), 5)
        if self.job_done:
            metadata['STATISTICS']['total_downloads'] = 0
            metadata['STATISTICS']['time_elapsed'] = 0
        metadata['UPDATING'] = {}
        metadata['UPDATING']['previous_newest_id'] = self.current_newest_id
        metadata['UPDATING']['SEPARATE'] = self.separate

        with open('{}metadata.json'.format(self.storage), 'w') as progressf:
            json.dump(metadata, progressf, indent=2)

    def read_metadata(self):
        with open('{}metadata.json'.format(self.storage), 'r') as progressf:
            metadata = json.load(progressf)
            progressf.close()
        self.safe = metadata['RATINGS']['safe']
        self.questionable = metadata['RATINGS']['questionable']
        self.explicit = metadata['RATINGS']['explicit']
        self.total_downloads += metadata['STATISTICS']['total_downloads']
        self.time_elapsed = metadata['STATISTICS']['time_elapsed']
        self.previous_newest_id = metadata['UPDATING']['previous_newest_id']
        self.separate = metadata['UPDATING']['SEPARATE']

    def save_queues(self):
        """ Saves the queues to files

        This method should be called before the queue is cleared.
        It will write all the items in download_queue and page_queue
        into the progress files.
        """

        # Serialize download queue and dump to file
        with open('{}download_queue.pkl'.format(self.storage), 'wb') as download_progress:
            pickle.dump(self.download_queue, download_progress)
            download_progress.close()

        # Serialize post queue and dump to file
        with open('{}post_queue.pkl'.format(self.storage), 'wb') as post_progress:
            pickle.dump(self.post_queue, post_progress)
            post_progress.close()

    def read_queues(self):
        """ Reads the download progress

        Parses the download progress and returns
        the configuration file contents.
        """

        self.print_loading_progress()

        try:
            # Deserialize and load download queue
            with open('{}download_queue.pkl'.format(self.storage), 'rb') as download_progress:
                self.download_queue = pickle.load(download_progress)
                download_progress.close()

            # Deserialize and load post queue
            with open('{}post_queue.pkl'.format(self.storage), 'rb') as post_progress:
                self.post_queue = pickle.load(post_progress)
                post_progress.close()

            # Read metadata
            self.read_metadata()
        except (KeyError, ValueError):
            self.print_faulty_progress_file()
            exit(1)

    @print_locker
    def warn_keyboard_interrupt(self):
        # Tells the user that Ctrl^C is caught
        print('[Main Thread] KeyboardInterrupt Caught!', file=sys.stderr)
        print('[Main Thread] Flushing queues and exiting', file=sys.stderr)

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
            hour, minute, second, page, url), file=sys.stderr)

    @print_locker
    def print_crawling_page(self, page):
        # Print which page is being crawled
        print('Crawling page {}'.format(page))

    @print_locker
    def print_thread_exit(self, name):
        # Thread exiting message
        print('[libkonadl] {} thread exiting'.format(name), file=sys.stderr)

    @print_locker
    def print_429(self):
        # HTTP returns 429
        print('HTTP Error 429: You are sending too many requests', file=sys.stderr)
        print('Trying to recover from error', file=sys.stderr)
        print('Putting job back to queue', file=sys.stderr)

    @print_locker
    def print_exception(self):
        # Any exception
        print('An error has occurred in this thread', file=sys.stderr)
        print('Trying to recover from error', file=sys.stderr)
        print('Putting job back to queue', file=sys.stderr)

    @print_locker
    def print_faulty_progress_file(self):
        # Tell the use the progress file is faulty
        print('Error: Faulty progress file!', file=sys.stderr)
        print('Aborting\n', file=sys.stderr)


if __name__ == '__main__':
    """ Sample crawling

    Crawls safe images off of konachan.com
    when called directly as a standalone program
    for demonstration.
    """
    kona = Konadl()  # Create crawler object

    # Set storage directory
    # Note that there's a "/" and the end
    kona.storage = '/tmp/konachan/'
    if not os.path.isdir(kona.storage):  # Quit if storage directory not found
        print('Error: storage directory not found', file=sys.stderr)
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
    print('{} image(s) downloaded'.format(kona.total_downloads))
    print('Time taken: {} seconds'.format(
        round((time.time() - kona.begin_time), 5)))
