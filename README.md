# Konachan Downloader

#### Current Version: 1.0


## What is this

Konachan downloader is a library that helps you bulk downloading images according to ratings (Safe/Questionable/Explicit) from konachan.com / konachan.net while also being a standalone program that can run directly on any platform that supports python (at least according to the current design).

</br>

## Screenshot(s)
![screenshot_20180411_234826](https://user-images.githubusercontent.com/21986859/38655491-f412e338-3de2-11e8-97fd-22adfe4137b1.png)


</br>

## Getting Started

To download the first 10 pages of images to folder `/tmp/konachan/`

You can change the behavior of the standalone application by editing these lines at the bottom of `konadl.py`
````
if __name__ == '__main__':
    kona = konadl()  # Create crawler object
    kona.explicit = False  # Be careful with these...
    kona.explicit_only = False
    kona.include_questionable = False
    kona.crawl(10)  # Execute
````

+ The `explicit` variable determines whether images with "Explicit" rating will be downloaded
+ The `explicit_only` is pretty self-explanatory: download explicit images only
+ The `include_questionable` variable allows you to download questionable images while set to True. However, this applies only when `explicit` is also true. (at least for now)