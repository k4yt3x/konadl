# Konachan Downloader

Please read the [EULA](https://github.com/K4YT3X/KonaDL#eula) section carefully before starting to use this software.

libkonadl Version: **1.6.1**  
KonaDL CLI Version: **1.3.1**

</br>

## Important Features

Just preventing people from missing this.

+ **You can press Ctrl+C at any time to pause the download.**  
**The progress will be saved and you will be prompted automatically to continue the next time you launch the program.**
+ **The program can now recover itself from all kinds of errors and continue downloading**  
**Examples:**
   + Temporary network issues
   + Temporary server-side situations

</br>

### Current Version Changes

1. **Images downloaded are now uncompressed original images**


![konadl_cli](https://user-images.githubusercontent.com/21986859/38762615-bb0269a4-3f5b-11e8-895d-0eb197a3de8f.png)

### Recent Changes
1. The program can now recover itself from all kinds of errors and continue downloading  
Examples:
   + Temporary network issues
   + Temporary server-side situations
1. Progress file is now stored in the storage directory
1. Added print lock to prevent printing formating error
1. User can now continue from where they left off
   + Progress will be saved when download queue not empty
   + KonaDL CLI automatically detects if progress file is present
1. Minor changes to the libkonadl API
1. Added self-recovery when exception caught
1. libkonadl can now handle ctrl+c properly and exit gracefully
1. Added **multithreading**
1. Added KonaDL CLI for Linux and Windows
1. Improved libkonadl for better performance
1. Self-recovery is now available
1. Added support for [Yande.re](https://yande.re)
1. Other useful changes

</br>

## What this is

**It bulk downloads images from Konachan.com and Yande.re with high speed.**

KonaDL CLI is a standalone application that uses libkonadl to bulk download images from konachan.com / konachan.net / yande.re. It provides better user interface comparing to libkonadl, but it cannot be used as a library.

libkonadl is a library that helps you bulk downloading images according to ratings (Safe/Questionable/Explicit) from konachan.com / konachan.net / yande.re with multithreading. It can also run as a standalone program that can run directly on any platform that supports python (at least according to the current design).

</br>

## Quick Start

**This is applicable for Windows and Linux**

If you're an ordinary user and want to download images with it, here's how you can do it easily.

First, clone the project:
```
$ git clone https://github.com/K4YT3X/KonaDL.git
$ cd KonaDL
```

Then simply execute konadl_cli.py.

Here's an example for downloading 10 pages of images including safe, questionable and explicit rated images to directory `/tmp/konachan`.
```
$ python3 konadl_cli.py -o /tmp/konachan -e -s -q -n 10
```

You can also set crawler and downloader threads.  
`-c 10` means 10 crawler threads, 10 by default  
`-d 20` means 20 downloader threads, 20 by default  
```
$ python3 konadl_cli.py -o /tmp/konachan -e -s -q -n 10 -c 10 -d 20
```

Full usage:
```
usage: konadl_cli.py [-h] [-n PAGES] [-a] [-p PAGE] [-y] [-o STORAGE] [-s]
                     [-q] [-e] [-c CRAWLERS] [-d DOWNLOADERS] [-v]

optional arguments:
  -h, --help            show this help message and exit

Controls:
  -n PAGES, --pages PAGES
                        Number of pages to download
  -a, --all             Download all images
  -p PAGE, --page PAGE  Crawl a specific page
  -y, --yandere         Crawl Yande.re site
  -o STORAGE, --storage STORAGE
                        Storage directory
  -s, --safe            Include Safe rated images
  -q, --questionable    Include Questionable rated images
  -e, --explicit        Include Explicit rated images

Threading:
  -c CRAWLERS, --crawlers CRAWLERS
                        Number of post crawler threads
  -d DOWNLOADERS, --downloaders DOWNLOADERS
                        Number of downloader threads

Extra:
  -v, --version         Show KonaDL version and exit
```

</br>

## Getting Started with libkonadl

Here's a simple example of how to use libkonadl library.

```
from libkonadl import konadl  # Import library

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
```

If you want to crawl all images:

```
kona.crawl_all_pages()
```

Here's how you can overwrite a method:

```
class konadl_avalon(konadl):
    """ Overwrite original methods for better
    appearance and readability.
    """

    def print_retrieval(self, url):
        avalon.dbgInfo("Retrieving: {}".format(url))

    def print_crawling_page(self, page):
        avalon.info('Crawling page: {}{}#{}'.format(avalon.FM.BD, avalon.FG.W, page))

    def print_thread_exit(self, name):
        avalon.dbgInfo('[libkonadl] {} thread exiting'.format(name))

# Create an object off of the modified class
kona = konadl_avalon()
```


## EULA
By using the "konadl" software ("this software") you agree to this EULA. If you do not agree to the EULA, stop using this software immediately.

- **By enabling crawling from [Konachan.com](Konachan.com) you agree to the [ToS of Konachan.com](https://konachan.com/static/terms_of_service).**  
- **By enabling crawling from [Yande.re](Yande.re) you agree to the [ToS of Yande.re](https://yande.re/static/terms_of_service).**
- You must respect the website requests (ex. stop the software when HTTP 429 is received).
- You need to have the developer's permission before using this software for commercial purposes.
- You must obey the law of the country which you are in.

Just thought it would be fun to have an EULA.