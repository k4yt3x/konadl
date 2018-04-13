#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 _   __                       ______  _
| | / /                       |  _  \| |
| |/ /   ___   _ __    __ _   | | | || |
|    \  / _ \ | '_ \  / _` |  | | | || |
| |\  \| (_) || | | || (_| |  | |/ / | |____
\_| \_/ \___/ |_| |_| \__,_|  |___/  \_____/


Name: Konachan Downloader
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
import re
import os
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
            except Exception:
                hour = datetime.datetime.now().time().hour
                minute = datetime.datetime.now().time().minute
                second = datetime.datetime.now().time().second
                print('[{}:{}:{}] Error Detected. Retrying.....'.format(hour, minute, second), end='\r')
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
        self.VERSION = '1.1'
        self.explicit = False
        self.explicit_only = False
        self.include_questionable = False
        self.storage = '/tmp/konachan/'
        if not os.path.isdir(self.storage):
            print('ERROR: Storage path not found!')
            print('Current storage path: {}\n'.format(self.storage))
            exit(1)

    def crawl(self, total_pages):
        """ Generic crawling

        Regular crawling controller. Craws a certain amount
        of pages according to the specified value from argument
        "total_pages"
        """
        if self.explicit:
            self.site_root = 'https://konachan.com'
            print('WARNING: Explicit Enabled')
        else:
            self.site_root = 'https://konachan.net'
        if self.explicit_only:
            print('Explicit Only Enabled')
        if self.include_questionable:
            print('Including Questionable Rated Images')

        print('Crawling {} Pages\n'.format(total_pages))
        for page_num in range(1, total_pages + 1):
            page_posts = self.crawl_post_page(page_num)
            for post in page_posts:
                self.retrieve_post_image(post)

    def crawl_all(self):
        """ Crawl the entire site

        WARNING: this will crawl thousands of pages
        use with caution!
        """
        index_page = self.get_page('{}/post?page=1&tags='.format(self.site_root))
        index_soup = BeautifulSoup(index_page, "html.parser")
        total_pages = int(index_soup.findAll('a', href=True)[-10].text)
        self.crawl(total_pages)

    def get_page_rating(self, content):
        """ Judge if page is R18

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
        """
        req = urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
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
        print("Retrieving: {}".format(url))
        suffix = url.split(".")[-1]
        file_path = self.storage + file_name + '.' + suffix
        urllib.request.urlretrieve(url, file_path)

    @self_recovery
    def retrieve_post_image(self, uri):
        """ Get the large image url and download

        Crawls the post page, find the large image url(s)
        and calls the downloader to download all of them.
        """
        image_page_source = self.get_page(self.site_root + uri)
        rating = self.get_page_rating(image_page_source.decode('utf-8'))
        if self.explicit_only:
            if rating != 'explicit':
                if rating != 'questionable' or not self.include_questionable:
                    return
        image_soup = BeautifulSoup(image_page_source, "html.parser")
        for link in image_soup.findAll('img', {'class': 'image'}):
            if not self.explicit:
                self.download_file('https:' + link['src'], uri.split("/")[-1])
            else:
                self.download_file(link['src'], uri.split("/")[-1])

    @self_recovery
    def crawl_post_page(self, page):
        """ Crawl the post list page and find posts

        Craws the posts index pages and record every post's
        url before handing them to the image downloader.
        """
        posts = []
        page_source = self.get_page('{}/post?page={}&tags='.format(self.site_root, page))
        soup = BeautifulSoup(page_source, "html.parser")
        for link in soup.findAll('a', href=True):
            if re.match('/post/show/[0-9]*/', link['href']):
                posts.append(link['href'])
        return posts


if __name__ == '__main__':
    kona = konadl()  # Create crawler object
    kona.explicit = False  # Be careful with these...
    kona.explicit_only = False
    kona.include_questionable = False
    kona.crawl(10)  # Execute
