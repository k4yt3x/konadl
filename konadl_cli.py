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

from libkonadl import konadl  # Import konadl library
import avalon_framework as avalon
import argparse
import os
import traceback

VERSION = '1.0'


def process_arguments():
    """This function parses all arguments

    Users can customize the behavior of konadl using
    commandline arguments
    """
    parser = argparse.ArgumentParser()
    control_group = parser.add_argument_group('Controls')
    control_group.add_argument('-n', '--pages', help='Number of pages to download', type=int, action='store', default=False)
    control_group.add_argument('-a', '--all', help='Download all images', action='store_true', default=False)
    control_group.add_argument('-p', '--page', help='Crawl a specific page', type=int, action='store', default=False)
    control_group.add_argument('-s', '--safe', help='Include Safe rated images', action='store_true', default=False)
    control_group.add_argument('-q', '--questionable', help='Include Questionable rated images', action='store_true', default=False)
    control_group.add_argument('-e', '--explicit', help='Include Explicit rated images', action='store_true', default=False)
    control_group.add_argument('-y', '--yandere', help='Crawl Yande.re site', action='store_true', default=False)
    control_group.add_argument('-o', '--storage', help='Storage directory', action='store', default=False)
    etc = parser.add_argument_group('Extra')
    etc.add_argument('-v', '--version', help='Show KonaDL version and exit', action='store_true', default=False)
    return parser.parse_args()


def check_storage_dir(args):
    """ Processes storage argument and passes it on

    Formats the storage input to the format that libkonadl
    will recognize.
    """
    if args.storage is False:
        return '/tmp/konachan/'
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


def display_options(kona):
    """ Display konadl crawling options

    Prints the options of konadl before start crawling.
    Warns user if questionable images or explicit images
    are to be downloaded.

    Also shows other supplement information if any. More to
    be added in the future.
    """
    avalon.dbgInfo('Program Started')
    avalon.info('Using storage directory: {}{}'.format(avalon.FG.W, kona.storage))
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
        avalon.warning('Crawling {}{}ALL{}{} Pages'.format(avalon.FG.W, avalon.FM.BD, avalon.FM.RST, avalon.FG.G))
    elif args.page:
        avalon.info('Crawling Page #{}'.format(args.page))


args = process_arguments()


class konadl_linux(konadl):
    def print_retrieval(self, url):
        avalon.dbgInfo("Retrieving: {}".format(url))

    def print_crawling_page(self, page):
        avalon.info('Crawling page: {}{}#{}'.format(avalon.FM.BD, avalon.FG.W, page))


try:
    if __name__ == '__main__':
        kona = konadl_linux()  # Create crawler object
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
        kona.yandere = args.yandere
        kona.safe = args.safe
        kona.questionable = args.questionable
        kona.explicit = args.explicit
        display_options(kona)

        if not kona.safe and not kona.questionable and not kona.explicit:
            avalon.error('Please supply information about what you want to download')
            print(avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -s, --safe            Include Safe rated images')
            print('  -q, --questionable    Include Questionable rated images')
            print('  -e, --explicit        Include Explicit rated images')
            print('Use --help for more information\n' + avalon.FM.RST)
            exit(1)
        elif not args.pages and not args.all and not args.page:
            avalon.error('Please supply information about what you want to download')
            print(avalon.FM.BD + 'You must include one of the following arguments:')
            print('  -n PAGES, --pages PAGES')
            print('                        Number of pages to download')
            print('  -a, --all             Download all images')
            print('  -p PAGE, --page PAGE  Crawl a specific page')
            print('Use --help for more information\n' + avalon.FM.RST)

        if args.pages:
            kona.crawl(args.pages)
        elif args.all:
            kona.crawl_all()
        elif args.page:
            kona.crawl_page(args.page)

    avalon.info('Konachan Downloader finished successfully\n')

except KeyboardInterrupt:
    avalon.warning('Ctrl+C detected')
    avalon.warning('Exiting program\n')
    exit(0)
except Exception:
    avalon.error('An error occurred during the execution of the program')
    traceback.print_exc()
    avalon.warning('This is critical information for fixing bugs and errors')
    avalon.warning('If you\'re kind enough wanting to help improving this program,')
    avalon.warning('please contact the developer.')
    exit(1)
