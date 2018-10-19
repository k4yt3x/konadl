#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Konachan Downloader CLI for Linux
Date Created: April 13, 2018
Last Modified: October 19, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X
"""
from avalon_framework import Avalon
from libkonadl import konadl  # Import libkonadl
from libkonadl import print_locker
import argparse
import os
import time
import traceback

VERSION = '1.3.8'


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
    control_group.add_argument('--separate', help='Separate images into folders by ratings', action='store_true', default=False)
    control_group.add_argument('-u', '--update', help='Update new images', action='store_true', default=False)
    ratings_group = parser.add_argument_group('Ratings')
    ratings_group.add_argument('-s', '--safe', help='Include Safe rated images', action='store_true', default=False)
    ratings_group.add_argument('-q', '--questionable', help='Include Questionable rated images', action='store_true', default=False)
    ratings_group.add_argument('-e', '--explicit', help='Include Explicit rated images', action='store_true', default=False)
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
            Avalon.error('Storage path specified is a file/link')
        else:
            Avalon.warning('Storage directory not found')
            if Avalon.ask('Create storage directory?', True):
                try:
                    if not os.mkdir(storage):
                        if args.separate:
                            os.mkdir('{}/safe'.format(storage))
                            os.mkdir('{}/questionable'.format(storage))
                            os.mkdir('{}/explicit'.format(storage))
                        Avalon.info('Successfully created storage directory')
                        return storage
                except PermissionError:
                    Avalon.error('Insufficient permission to create the specified directory\n')
                    exit(1)
                except Exception:
                    Avalon.error('An error occurred while trying to create storage directory\n')
                    traceback.print_exc()
                    exit(0)
            else:
                Avalon.error('Storage directory not found')
                Avalon.error('Unable to proceed\n')
                exit(1)
    return storage


def display_options(kona, load_progress, args):
    """ Display konadl crawling options

    Prints the options of konadl before start crawling.
    Warns user if questionable images or explicit images
    are to be downloaded.

    Also shows other supplement information if any. More to
    be added in the future.
    """
    Avalon.debug_info('Program Started')
    Avalon.info('Using storage directory: {}{}'.format(Avalon.FG.W, kona.storage))
    if load_progress or args.update:
        Avalon.info('Sourcing configuration defined in the metadata file')
    else:
        if kona.safe:
            Avalon.info('Including {}{}SAFE{}{} rated images'.format(Avalon.FG.W, Avalon.FM.BD, Avalon.FM.RST, Avalon.FG.G))
        if kona.questionable:
            Avalon.warning('Including {}QUESTIONABLE{} rated images'.format(Avalon.FG.W, Avalon.FG.Y))
        if kona.explicit:
            Avalon.warning('Including {}EXPLICIT{} rated images'.format(Avalon.FG.R, Avalon.FG.Y))
        if kona.yandere:
            Avalon.info('Crawling yande.re')

        if args.pages:
            if args.pages == 1:
                Avalon.info('Crawling {}{}{}{}{} Page\n'.format(Avalon.FG.W, Avalon.FM.BD, args.pages, Avalon.FM.RST, Avalon.FG.G))
            else:
                Avalon.info('Crawling {}{}{}{}{} Pages\n'.format(Avalon.FG.W, Avalon.FM.BD, args.pages, Avalon.FM.RST, Avalon.FG.G))
        elif args.all:
            Avalon.warning('Crawling {}ALL{} Pages\n'.format(Avalon.FG.W, Avalon.FG.Y))
        elif args.page:
            Avalon.info('Crawling Page #{}'.format(args.page))

    Avalon.info('Opening {}{}{}{}{} crawler threads'.format(Avalon.FG.W, Avalon.FM.BD, args.crawlers, Avalon.FM.RST, Avalon.FG.G))
    Avalon.info('Opening {}{}{}{}{} downloader threads\n'.format(Avalon.FG.W, Avalon.FM.BD, args.downloaders, Avalon.FM.RST, Avalon.FG.G))


class konadl_avalon(konadl):
    """ Overwrite original methods for better
    appearance and readability using avalon
    framework.
    """

    @print_locker
    def warn_keyboard_interrupt(self):
        Avalon.warning('[Main Thread] KeyboardInterrupt Caught!')
        Avalon.warning('[Main Thread] Flushing queues and exiting')

    @print_locker
    def print_saving_progress(self):
        Avalon.info('[Main Thread] Saving progress to {}{}{}'.format(Avalon.FG.W, Avalon.FM.BD, self.storage))

    def print_loading_progress(self):
        Avalon.info('[Main Thread] Loading progress from {}{}{}'.format(Avalon.FG.W, Avalon.FM.BD, self.storage))

    @print_locker
    def print_retrieval(self, url, page):
        Avalon.debug_info("[Page={}] Retrieving: {}".format(page, url))

    @print_locker
    def print_crawling_page(self, page):
        Avalon.info('Crawling page: {}{}#{}'.format(Avalon.FM.BD, Avalon.FG.W, page))

    @print_locker
    def print_thread_exit(self, name):
        Avalon.debug_info('[libkonadl] {} thread exiting'.format(name))

    @print_locker
    def print_429(self):
        Avalon.error('HTTP Error 429: You are sending too many requests')
        Avalon.warning('Trying to recover from error')
        Avalon.warning('Putting job back to queue')

    @print_locker
    def print_exception(self):
        Avalon.error('An error has occurred in this thread')
        Avalon.warning('Trying to recover from error')
        Avalon.warning('Putting job back to queue')

    @print_locker
    def print_faulty_progress_file(self):
        Avalon.error('Faulty progress file!')
        Avalon.error('Aborting\n')


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

        kona.storage = check_storage_dir(args)
        if kona.storage is False:
            Avalon.error('Please specify storage directory\n')
            exit(1)

        # If progress file exists
        # Ask user if he or she wants to load it
        load_progress = False
        if kona.progress_files_present():
            Avalon.info('Progress file found')
            if Avalon.ask('Continue from where you left off?', True):
                kona.load_progress = True
                load_progress = True
            else:
                Avalon.info('Starting new download progress')
                kona.remove_progress_files()

        # Pass terminal arguments to libkonadl object
        kona.separate = args.separate
        kona.yandere = args.yandere
        kona.safe = args.safe
        kona.questionable = args.questionable
        kona.explicit = args.explicit
        kona.post_crawler_threads_amount = args.crawlers
        kona.downloader_threads_amount = args.downloaders
        display_options(kona, load_progress, args)

        if not kona.safe and not kona.questionable and not kona.explicit and not load_progress and not args.update:
            Avalon.error('Please supply information about what you want to download')
            print(Avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -s, --safe            Include Safe rated images')
            print('  -q, --questionable    Include Questionable rated images')
            print('  -e, --explicit        Include Explicit rated images')
            print('Use --help for more information\n' + Avalon.FM.RST)
            exit(1)
        elif not args.pages and not args.all and not args.page and not load_progress and not args.update:
            Avalon.error('Please supply information about what you want to download')
            print(Avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -n PAGES, --pages PAGES')
            print('                        Number of pages to download')
            print('  -a, --all             Download all images')
            print('  -p PAGE, --page PAGE  Crawl a specific page')
            print('Use --help for more information\n' + Avalon.FM.RST)

        if load_progress:
            kona.crawl()
        elif args.update:
            Avalon.info('Updating new images')
            if kona.update() is False:
                Avalon.info('{}{}No new images found\n'.format(Avalon.FM.BD, Avalon.FG.W))
        elif args.pages:
            kona.pages = args.pages
            kona.crawl()
        elif args.all:
            kona.crawl_all_pages()
        elif args.page:
            kona.crawl_page(args.page)

        Avalon.info('Main thread exited without errors')
        Avalon.info('{}{}{}{}{} image(s) downloaded'.format(Avalon.FG.W, Avalon.FM.BD, kona.total_downloads, Avalon.FM.RST, Avalon.FG.G))
        Avalon.info('Time taken: {}{}{}{}{} seconds'.format(Avalon.FG.W, Avalon.FM.BD, round(
            (time.time() - kona.begin_time + kona.time_elapsed), 5), Avalon.FM.RST, Avalon.FG.G))
        if kona.job_done:
            Avalon.info('All downloads complete')
            if kona.progress_files_present():
                Avalon.info('Removing progress file')
                kona.remove_progress_files()
    else:
        Avalon.error('This file cannot be imported as a module!')
        raise SystemError('Cannot be imported')
except KeyboardInterrupt:
    Avalon.warning('Ctrl+C detected in CLI Module')
    Avalon.warning('Exiting program\n')
    exit(0)
except Exception:
    Avalon.error('An error occurred during the execution of the program')
    traceback.print_exc()
    Avalon.warning('This is critical information for fixing bugs and errors')
    Avalon.warning('If you\'re kind enough wanting to help improving this program,')
    Avalon.warning('please contact the developer.')
    exit(1)
