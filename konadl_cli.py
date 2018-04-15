#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Konachan Downloader CLI for Linux
Date Created: 13 Apr. 2018
Last Modified: 13 Apr. 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X
"""

from libkonadl import konadl  # Import libkonadl
from libkonadl import print_locker
import avalon_framework as avalon
import argparse
import os
import traceback

VERSION = '1.2.1'


def process_arguments():
    """This function parses all arguments

    Users can customize the behavior of libkonadl using
    commandline arguments
    """
    parser = argparse.ArgumentParser()
    control_group = parser.add_argument_group('Controls')
    control_group.add_argument('-n', '--pages', help='Number of pages to download', type=int, action='store', default=False)
    control_group.add_argument('-a', '--all', help='Download all images', action='store_true', default=False)
    control_group.add_argument('-p', '--page', help='Crawl a specific page', type=int, action='store', default=False)
    control_group.add_argument('-y', '--yandere', help='Crawl Yande.re site', action='store_true', default=False)
    control_group.add_argument('-o', '--storage', help='Storage directory', action='store', default=False)
    control_group.add_argument('--progress', help='Specify progress file to load', action='store', default='konadl.progress')
    threading_group = parser.add_argument_group('Ratings')
    control_group.add_argument('-s', '--safe', help='Include Safe rated images', action='store_true', default=False)
    control_group.add_argument('-q', '--questionable', help='Include Questionable rated images', action='store_true', default=False)
    control_group.add_argument('-e', '--explicit', help='Include Explicit rated images', action='store_true', default=False)
    threading_group = parser.add_argument_group('Threading')
    threading_group.add_argument('-c', '--crawlers', help='Number of post crawler threads', type=int, action='store', default=10)
    threading_group.add_argument('-d', '--downloaders', help='Number of downloader threads', type=int, action='store', default=20)
    etc_group = parser.add_argument_group('Extra')
    etc_group.add_argument('-v', '--version', help='Show KonaDL version and exit', action='store_true', default=False)
    return parser.parse_args()


def check_storage_dir(args):
    """ Processes storage argument and passes it on

    Formats the storage input to the format that libkonadl
    will recognize.
    """
    if args.storage is False:
        return False
    storage = args.storage
    if storage[-1] != '/':
        storage += '/'
    if not os.path.isdir(storage):
        if os.path.isfile(storage) or os.path.islink(storage):
            avalon.error('Storage path specified is a file/link')
        else:
            avalon.warning('Storage directory not found')
            if avalon.ask('Create storage directory?', True):
                try:
                    if not os.mkdir(storage):
                        avalon.info('Successfully created storage directory')
                        return storage
                except PermissionError:
                    avalon.error('Insufficient permission to create the specified directory\n')
                    exit(1)
                except Exception:
                    avalon.error('An error occurred while trying to create storage directory\n')
                    traceback.print_exc()
                    exit(0)
            else:
                avalon.error('Storage directory not found')
                avalon.error('Unable to proceed\n')
                exit(1)
    return storage


def display_options(kona, load_progress):
    """ Display konadl crawling options

    Prints the options of konadl before start crawling.
    Warns user if questionable images or explicit images
    are to be downloaded.

    Also shows other supplement information if any. More to
    be added in the future.
    """
    avalon.dbgInfo('Program Started')
    avalon.info('Using storage directory: {}{}'.format(avalon.FG.W, kona.storage))
    if load_progress:
        avalon.info('Sourcing configuration defined in the progress file')
    else:
        if kona.safe:
            avalon.info('Including {}{}SAFE{}{} rated images'.format(avalon.FG.W, avalon.FM.BD, avalon.FM.RST, avalon.FG.G))
        if kona.questionable:
            avalon.warning('Including {}QUESTIONABLE{} rated images'.format(avalon.FG.W, avalon.FG.Y))
        if kona.explicit:
            avalon.warning('Including {}EXPLICIT{} rated images'.format(avalon.FG.R, avalon.FG.Y))
        if kona.yandere:
            avalon.info('Crawling yande.re')

        if args.pages:
            if args.pages == 1:
                avalon.info('Crawling {}{}{}{}{} Page\n'.format(avalon.FG.W, avalon.FM.BD, args.pages, avalon.FM.RST, avalon.FG.G))
            else:
                avalon.info('Crawling {}{}{}{}{} Pages\n'.format(avalon.FG.W, avalon.FM.BD, args.pages, avalon.FM.RST, avalon.FG.G))
        elif args.all:
            avalon.warning('Crawling {}{}ALL{}{} Pages\n'.format(avalon.FG.W, avalon.FM.BD, avalon.FM.RST, avalon.FG.G))
        elif args.page:
            avalon.info('Crawling Page #{}'.format(args.page))

    avalon.info('Opening {}{}{}{}{} crawler threads'.format(avalon.FG.W, avalon.FM.BD, args.crawlers, avalon.FM.RST, avalon.FG.G))
    avalon.info('Opening {}{}{}{}{} downloader threads\n'.format(avalon.FG.W, avalon.FM.BD, args.downloaders, avalon.FM.RST, avalon.FG.G))


class konadl_avalon(konadl):
    """ Overwrite original methods for better
    appearance and readability.
    """

    @print_locker
    def warn_keyboard_interrupt(self):
        avalon.warning('[Main Thread] KeyboardInterrupt Caught!')
        avalon.warning('[Main Thread] Flushing queues and exiting')

    @print_locker
    def print_saving_progress(self):
        avalon.info('[Main Thread] Saving progress')

    @print_locker
    def print_retrieval(self, page, url):
        avalon.dbgInfo("[Page={}] Retrieving: {}".format(page, url))

    @print_locker
    def print_crawling_page(self, page):
        avalon.info('Crawling page: {}{}#{}'.format(avalon.FM.BD, avalon.FG.W, page))

    @print_locker
    def print_thread_exit(self, name):
        avalon.dbgInfo('[libkonadl] {} thread exiting'.format(name))

    @print_locker
    def print_faulty_progress_file(self):
        avalon.error('Faulty progress file!')
        avalon.error('Aborting\n')


args = process_arguments()

try:
    if __name__ == '__main__':
        kona = konadl_avalon()  # Create crawler object
        kona.icon()

        if args.version:  # prints program legal / dev / version info
            print('CLI Program Version: ' + VERSION)
            print('libkonadl Version: ' + kona.VERSION)
            print('Author: K4YT3X')
            print('License: GNU GPL v3')
            print('Github Page: https://github.com/K4YT3X/KonaDL')
            print('Contact: k4yt3x@protonmail.com\n')
            exit(0)

        # If progress file exists
        # Ask user if he or she wants to load it
        load_progress = False
        if os.path.isfile(args.progress):
            avalon.info('Progress file found')
            if avalon.ask('Continue from where you left off?', True):
                kona.load_progress = True
                kona.progress_file = args.progress
                load_progress = True
            else:
                avalon.info('Creating new download profile')

        kona.storage = check_storage_dir(args)
        if kona.storage is False:
            avalon.error('Please specify storage directory\n')
            exit(1)
        kona.yandere = args.yandere
        kona.safe = args.safe
        kona.questionable = args.questionable
        kona.explicit = args.explicit
        kona.post_crawler_threads_amount = args.crawlers
        kona.downloader_threads_amount = args.downloaders
        display_options(kona, load_progress)

        if not kona.safe and not kona.questionable and not kona.explicit and not load_progress:
            avalon.error('Please supply information about what you want to download')
            print(avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -s, --safe            Include Safe rated images')
            print('  -q, --questionable    Include Questionable rated images')
            print('  -e, --explicit        Include Explicit rated images')
            print('Use --help for more information\n' + avalon.FM.RST)
            exit(1)
        elif not args.pages and not args.all and not args.page and not load_progress:
            avalon.error('Please supply information about what you want to download')
            print(avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -n PAGES, --pages PAGES')
            print('                        Number of pages to download')
            print('  -a, --all             Download all images')
            print('  -p PAGE, --page PAGE  Crawl a specific page')
            print('Use --help for more information\n' + avalon.FM.RST)

        if load_progress:
            kona.crawl()
        elif args.pages:
            kona.pages = args.pages
            kona.crawl()
        elif args.all:
            kona.crawl_all_pages()
        elif args.page:
            kona.crawl_page(args.page)

    avalon.info('Main thread exited without errors\n')

except KeyboardInterrupt:
    avalon.warning('Ctrl+C detected in CLI Module')
    avalon.warning('Exiting program\n')
    exit(0)
except Exception:
    avalon.error('An error occurred during the execution of the program')
    traceback.print_exc()
    avalon.warning('This is critical information for fixing bugs and errors')
    avalon.warning('If you\'re kind enough wanting to help improving this program,')
    avalon.warning('please contact the developer.')
    exit(1)
