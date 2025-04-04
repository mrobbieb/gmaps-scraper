# gmaps-scraper
Scraping Google Maps

## This is tested with python 3.13. Results may very.
## You'll want to install crawlee and playright. These are the commands I ran and eventually got the proper installation to work.
```
pip3 install crawlee
pip3 install playwright
python -m pip install 'crawlee[playwright]'
python -m pip install 'crawlee[playwright_crawler]'
python -m pip install 'crawlee[all]'
```

## Might make a Dockerfile with installed to make things a bit easier.

## To run...
### pull this repo, edit `scraper.py` to have the `SEARCH_QUERY` you want to use. I use zip code but you can use city or whatever is viable on google maps.
### Once ready, run `python3 scraper.py` and results will cycle thru, eventually creating a .csv file in the same directory named `SEARCH_QUERY`. CSV has Business Name, Phone Number, Website.

### Note this is a WIP and will probably miss some businesses.
