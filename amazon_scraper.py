import os
import time
import json
import locale
import lxml
import bs4
from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.action_chains import ActionChains

PAGES = 5
AMAZON_URL = 'https://www.amazon.de'
LOCALE = 'de_DE.UTF-8'
ONLY_OFFERS = True


# ------ FOR USERS: ONLY TOUCH WHEN YOU KNOW WHAT YOU ARE DOING -----


HEADLESS = True
DEBUG = False
PARSER = 'lxml'

# ------ FOR USERS: DONT TOUCH ANYTHING BELOW THIS LINE -----


def makedir(dirname):
    dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), dirname)
    try:
        os.mkdir(dir)
    except FileExistsError as e:
        pass
    return dir


def scroll_shim(passed_in_driver, object):
    x = object.location['x']
    y = object.location['y']
    scroll_by_coord = 'window.scrollTo(%s,%s);' % (
        x,
        y
    )
    scroll_nav_out_of_way = 'window.scrollBy(0, -120);'
    passed_in_driver.execute_script(scroll_by_coord)
    passed_in_driver.execute_script(scroll_nav_out_of_way)


print("What product do you want?")
inp = None
if DEBUG:
    inp = input(":") or 'gaming'
while not inp:
    inp = input(':')

PRODUCTS_DIR = makedir('products')

START_TIME = time.time()

query = "+".join(inp.split(" "))

options = FirefoxOptions()
options.headless = HEADLESS
if DEBUG:
    driver = Firefox(options=options)
else:
    driver = Firefox(options=options, service_log_path=os.path.devnull)
locale.setlocale(locale.LC_ALL, LOCALE)
query_url = f"{AMAZON_URL}/s?k={query}"


products = []
if ONLY_OFFERS:
    offers_tag = ''
for i in range(1, PAGES+1):
    if not DEBUG:
        print('.', end='', flush=True)
    url = f'{query_url}&page={i}'
    if ONLY_OFFERS:
        if i == 1:
            driver.get(url)
            offers_box = driver.find_element_by_css_selector(
                '#p_n_specials_match\/21618183031 > span:nth-child(1) > a:nth-child(1) > span:nth-child(2)')
            scroll_shim(driver, offers_box)
            actions = ActionChains(driver)
            actions.move_to_element(offers_box)
            actions.click()
            actions.perform()
            offers_tag = driver.current_url.split('&')[1]
        url += '&'+offers_tag
    driver.get(url)
    soup = bs4.BeautifulSoup(driver.page_source, PARSER)
    links = [x['href'] for x in soup.findAll(
        'a', {'class': 'a-link-normal a-text-normal'})]
    for product in links:
        product_url = AMAZON_URL+product
        driver.get(product_url)
        soup = bs4.BeautifulSoup(driver.page_source, PARSER)
        dealprice = soup.find('span', {'id': 'priceblock_dealprice'})
        if dealprice:
            price = soup.find('span', {'class': 'priceblock_ourprice'})
            if not price:
                price = soup.find('span', {
                    'class': 'a-size-base a-color-secondary priceBlockBuyingPriceString a-text-strike'})
                if not price:
                    price = soup.find(
                        'span', {'class': 'priceBlockStrikePriceString a-text-strike'})
                    if not price:
                        price = soup.find(
                            'span', {'class': 'priceblock_saleprice'})
            if price:
                price = locale.atof(price.text.replace('€', '').strip())
                dealprice = locale.atof(
                    dealprice.text.replace('€', '').strip())
                save = (price-dealprice)/price
                products.append({
                    'link': product_url,
                    'price': price,
                    'deal_price': dealprice,
                    'save': save,
                    'p2s': save/dealprice
                })
            else:
                if DEBUG:
                    print('No base price found: ', product_url)
                price = None

driver.close()

open(f'{os.path.join(PRODUCTS_DIR, "_".join(inp.split(" ")).strip())}.json',
     'w+').write(json.dumps(products))

if not DEBUG:
    print(flush=True)

products_save = sorted(products, key=lambda k: k['save'])
print(products_save[-1]['link'])
products_price = sorted(products, key=lambda k: k['deal_price'])
print(products_price[0]['link'])
products_p2s = sorted(products, key=lambda k: k['p2s'])
print(products_p2s[-1]['link'])


# if DEBUG:
#     print(f"num of products: {len(products)}")
# print(f"best offer: {products_save[-1]}")
# price(f"cheapest: {products_price[-1]}")
# price(f"p2s: {products_p2s[-1]}")

print(f"time elapsed: {time.time()-START_TIME}s")
