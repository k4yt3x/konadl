# Archival Note

A web crawler is no longer needed for scraping images off of konachan.com or yande.re. You can use their [API](https://konachan.com/help/api) directly or via a Python wrapper such as [Pybooru](https://github.com/LuqueDaniel/pybooru/), which are both more efficient and reliable.

# Konachan Downloader

**Please read the [EULA](https://github.com/K4YT3X/konadl#eula) section carefully before starting to use this software.**

libkonadl Version: **1.9.0**
KonaDL CLI Version: **1.3.9**

## **[Video Demo](https://youtu.be/a2_tC_uugP4)**

## **[Usages | 使用教程](https://github.com/K4YT3X/konadl/wiki)**

Please refer to the [wiki page](https://github.com/K4YT3X/konadl/wiki) for usages and instructions.

## Important Features

Just preventing people from missing this.

- **You can press Ctrl+C at any time to pause the download.**
  **The progress will be saved and you will be prompted automatically to continue the next time you launch the program.**
- **The program can now recover itself from all kinds of errors and continue downloading**
  **Examples:**
  - Temporary network issues
  - Temporary server-side situations

## libkonadl 1.9.0 (October 19, 2018)

1. Changed metadata format from INI to JSON.
1. Fixed all the problems with pausing and resuming the download by serializing and storing queues instead of dumping queues into files.

## KonadDL CLI 1.3.9 (October 19, 2018)

1. Changed class names to follow python naming conventions.
1. Updated for avalon framework 1.6.1.

![konadl1 7](https://user-images.githubusercontent.com/21986859/39401587-a75ab99e-4b16-11e8-8282-7b7c10853751.png)

## What This Is

**It bulk downloads images from Konachan.com and Yande.re with high speed.**

KonaDL CLI is a standalone application that uses libkonadl to bulk download images from konachan.com / konachan.net / yande.re. It provides better user interface comparing to libkonadl, but it cannot be used as a library.

libkonadl is a library that helps you bulk downloading images according to ratings (Safe/Questionable/Explicit) from konachan.com / konachan.net / yande.re with multithreading. It can also run as a standalone program that can run directly on any platform that supports python (at least according to the current design).

## EULA

By using the "konadl" software ("this software") you agree to this EULA. If you do not agree to the EULA, stop using this software immediately.

- **By enabling crawling from [Konachan.com](Konachan.com) you agree to the [ToS of Konachan.com](https://konachan.com/static/terms_of_service).**
- **By enabling crawling from [Yande.re](Yande.re) you agree to the [ToS of Yande.re](https://yande.re/static/terms_of_service).**
- You must respect the website requests (ex. stop the software when HTTP 429 is received).
- You need to have the developer's permission before using this software for commercial purposes.
- You must obey the law of the country which you are in.

Just thought it would be fun to have an EULA.
