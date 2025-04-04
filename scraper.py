import asyncio
from datetime import timedelta
from typing import Dict, Optional, Set
from crawlee.crawlers import PlaywrightCrawler
from playwright.async_api import Page, ElementHandle
import re

# use this as if you were typing it into google maps
SEARCH_QUERY = 'rv parks in 85706'

class GoogleMapsScraper:
    """
    Scraper for extracting business listing data from Google Maps.
    Handles infinite scrolling and exports results to a JSON file.
    """

    def _validNumber(self, phone_number):
        if not phone_number:
            return None
        
        pattern = re.compile("(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})")

        phone_number.replace('+', '')

        phone = pattern.search(phone_number)

        if phone:
            return phone.group(0)
        
        return None
        # # import pdb; pdb.set_trace()
        # if not phone_number:
        #     return None

        # return pattern.match(phone_number) is not None]
        # try:
        #     phone = phone_number.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        #     if isinstance(int(phone), int):
        #         return phone
        # except ValueError as e:
        #     return None
    
    def __init__(self, headless: bool = True, timeout_minutes: int = 5):
        self.crawler = PlaywrightCrawler(
            headless=headless,
            request_handler_timeout=timedelta(minutes=timeout_minutes),
        )
        self.processed_names: Set[str] = set()

    async def setup_crawler(self) -> None:
        """Configure the crawler and set up request handling."""
        self.crawler.router.default_handler(self._scrape_listings)

    async def _extract_listing_data(self, listing: ElementHandle) -> Optional[Dict]:
        """Extract structured data from a single listing element."""
        try:
            listing.query_selector_all
            name_el = await listing.query_selector(".qBF1Pd")
            if not name_el:
                return None
            name = await name_el.inner_text()
            if name in self.processed_names:
                return None

            elements = {
                "rating": await listing.query_selector(".MW4etd"),
                "reviews": await listing.query_selector(".UY7F9"),
                "price": await listing.query_selector(".wcldff"),
                "link": await listing.query_selector("a.hfpxzc"),
                "phone": await listing.query_selector(".W4Efsd:nth-child(2)"),
                "phone2": await listing.query_selector(".W4Efsd:nth-child(2)"),
                "phone3": await listing.query_selector(".W4Efsd:nth-child(3)"),
                "phone4": await listing.query_selector(".W4Efsd:nth-child(4)"),
                "category": await listing.query_selector(".W4Efsd:nth-child(1)"),
                #"website": await listing.query_selector("span.DkEaL")
                "website": await listing.query_selector(".lcr4fd"),
                #lcr4fd for link
                #"phone": await listing.query_selector('.rogA2c-child(1)')
            }
            # if not elements['website']:
            #     print(elements)
            #     exit()

            amenities = []
            amenities_els = await listing.query_selector_all(".dc6iWb")
            for amenity in amenities_els:
                amenity_text = await amenity.get_attribute("aria-label")
                if amenity_text:
                    amenities.append(amenity_text)

            phone_data = []
            #"description": await listing.query_selector(".W4Efsd"),
            phone_els = await listing.query_selector_all(".W4Efsd")
            for phone in phone_els:
                phone_text = await phone.get_attribute("span")
                if phone_text:
                    phone_data.append(phone_text)

            place_data = {
                "name": name,
                "rating": (
                    await elements["rating"].inner_text()
                    if elements["rating"]
                    else None
                ),
                "reviews": (
                    (await elements["reviews"].inner_text()).strip("()")
                    if elements["reviews"]
                    else None
                ),
                "price": (
                    await elements["price"].inner_text() if elements["price"] else None
                ),
                "phone": (
                    await elements["phone"].inner_text()
                    if elements["phone"]
                    else None
                ),
                "phone2": (
                    await elements["phone2"].inner_text()
                    if elements["phone2"]
                    else None
                ),
                "phone3": (
                    await elements["phone3"].inner_text()
                    if elements["phone3"]
                    else None
                ),
                "phone4": (
                    await elements["phone4"].inner_text()
                    if elements["phone4"]
                    else None
                ),
                "description": phone_data if phone_data else None,
                "category": (
                    await elements["category"].inner_text()
                    if elements["category"]
                    else None
                ),
                "amenities": amenities if amenities else None,
                "link": (
                    await elements["link"].get_attribute("href")
                    if elements["link"]
                    else None
                ),
                "website": (
                    await elements["website"].get_attribute("href")
                    if elements["website"]
                    else None
                )
                # "phone": (
                #     await elements["phone"].inner_text()
                #     if elements["phone"]
                #     else None
                # )
            }

            self.processed_names.add(name)
            return place_data
        except Exception as e:
            #context.log.exception(f"Error extracting listing data")
            print(f"error: {e}")
            return None

    async def _load_more_items(self, page: Page) -> bool:
        """Scroll down to load more items."""
        try:
            feed = await page.query_selector('div[role="feed"]')
            if not feed:
                return False
            prev_scroll = await feed.evaluate("(element) => element.scrollTop")
            await feed.evaluate("(element) => element.scrollTop += 800")
            await page.wait_for_timeout(2000)

            new_scroll = await feed.evaluate("(element) => element.scrollTop")
            if new_scroll <= prev_scroll:
                return False
            await page.wait_for_timeout(1000)
            return True
        except Exception as e:
            context.log.exception(f"Error during scroll")
            return False

    async def _scrape_listings(self, context) -> None:
        """Scrape business listings from the current page."""
        try:
            page = context.page
            context.log.info(f"\nProcessing URL: {context.request.url}\n")

            await page.wait_for_selector(".Nv2PK", timeout=30000)
            await page.wait_for_timeout(2000)
            
            contact_info = []

            while True:
                listings = await page.query_selector_all(".Nv2PK")
                new_items = 0
                if new_items > 2:
                    break
            
                for listing in listings:
                    place_data = await self._extract_listing_data(listing)
                    if place_data:
                        await context.push_data(place_data)
                        new_items += 1

                        # phone = None

                        # if not self._validNumber(place_data['phone']):
                        #     import pdb; pdb.set_trace()
                        # if self._validNumber(place_data['phone']):
                        #     phone = place_data['phone']
                        # elif self._validNumber(place_data['phone2']):
                        #     phone = place_data['phone2']

                        phone = None

                        phone = self._validNumber(place_data['phone'])
                        
                        if not phone:
                            phone = self._validNumber(place_data['phone2'])

                        if not phone:
                            phone = self._validNumber(place_data['phone3'])

                        if not phone:
                            phone = self._validNumber(place_data['phone4'])

                        #import pdb; pdb.set_trace()
                        context.log.info(f"Processed: {place_data['name']} | Phone: {phone} | {place_data['website']}")

                        contact_info.append({'Name': place_data['name'], 'Phone' : phone, 'Website': place_data['website']})

                if new_items == 0 and not await self._load_more_items(page):
                    break
                if new_items > 0:
                    await self._load_more_items(page)
            context.log.info(f"\nFinished processing! Total items: {len(self.processed_names)}")

            import csv
            keys = contact_info[0].keys()

            with open(f'{SEARCH_QUERY}.csv', 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(contact_info)

        except Exception as e:
            context.log.exception(f"Error in scraping")

    async def run(self, search_query: str) -> None:
        """Run the scraper for a given search query."""
        try:
            await self.setup_crawler()
            start_url = (
                f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            )
            await self.crawler.run([start_url])
            await self.crawler.export_data_json("gmap_data.json")
        except Exception as e:
            context.log.exception(f"Error running scraper")


async def main():
    """Main function to execute the scraper."""
    scraper = GoogleMapsScraper(headless=True)
    #search_query = "hotels in bengaluru"
    #search_query = "rv park in tuscon"
    #search_query = "Tucson Snowbird Nest"
    await scraper.run(SEARCH_QUERY)


if __name__ == "__main__":
    asyncio.run(main())
