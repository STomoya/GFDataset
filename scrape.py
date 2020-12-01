
import argparse
import os
import shutil
import json
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup
import lxml
from PIL import Image
from tqdm import tqdm

GET_INTERVAL = 1 # sec
TABLE_PAGE = 'https://gbf-wiki.com/index.php?%C1%B4%A5%AD%A5%E3%A5%E9%A5%AF%A5%BF%A1%BC%B0%EC%CD%F7'

def get_and_save(url, args):
    '''get and save web page by a given url to temp/temp.html'''
    page = requests.get(url)
    with open(os.path.join(args.temp, 'temp.html'), 'w', encoding='utf-8') as fout:
        fout.write(page.text)

def scrape_detail_url(args):
    '''scrape urls of detail pages in TABLE_PAGE
    must be called after calling "get_and_save(TABLE_PAGE)"
    '''
    with open(os.path.join(args.temp, 'temp.html'), 'r', encoding='utf-8') as fin:
        page_text = fin.read()
    soup = BeautifulSoup(page_text, 'lxml')
    table = soup.find('table', id='sortabletable1')
    entries = table.find_all('tr')[1:] # erase thead row
    urls = {}
    for entry in tqdm(entries):
        # first column contains the url to the detailed page
        a = entry.find('a')
        # title is the name of the character
        urls[a['title']] = a['href']
    
    with open(os.path.join(args.temp, 'detail_urls.json'), 'w', encoding='utf-8') as fout:
        json.dump(urls, fout, ensure_ascii=False, indent=2)

def scrape_image_urls_single(args):
    '''scrape urls of images from temp/temp.html
    called by "scrape_image_urls()"
    '''
    with open(os.path.join(args.temp, 'temp.html'), 'r', encoding='utf-8') as fin:
        page_text = fin.read()
    soup = BeautifulSoup(page_text, 'lxml')
    divs = soup.select('div.ie5, div.img_margin, h3') # div.ie5 : fullbody, sd | div.img_margin : expose | h3 : section
    full_div, sd_div = None, None
    urls = []

    def only_images(div):
        '''scrape only image urls'''
        image_url_base = 'https://gbf-wiki.com/index.php?plugin=attach&refer=img&openfile='
        a_list = div.find_all('a', title=True)
        for a in a_list:
            if '.png' in a['title']:
                urls.append(image_url_base+a['title'])

    for index, div in enumerate(divs):
        # divs containing the image urls are right after 
        # h3 tags containing the bellow keywords
        if '基本情報' in div.text:
            only_images(divs[index+1])
        if 'SDキャラ画像' in div.text:
            only_images(divs[index+1])
        if 'EX POSE画像' in div.text:
            only_images(divs[index+1])
    return urls

def scrape_image_urls(args):
    '''scrape image urls from all pages scraped from TABLE_PAGE'''
    with open('temp/detail_urls.json', 'r', encoding='utf-8') as fin:
        urls = json.load(fin)
    
    last_get = time.time()

    title2imageurls = {}
    for title, url in tqdm(urls.items()):
        get_and_save(url, args)
        imageurls = scrape_image_urls_single(args)
        title2imageurls[title] = imageurls
        # waiting
        time.sleep(max(0, GET_INTERVAL - (time.time() - last_get)))
        last_get = time.time()

    with open(os.path.join(args.temp, 'image_urls.json'), 'w', encoding='utf-8') as fout:
        json.dump(title2imageurls, fout, ensure_ascii=False, indent=2)

def save_image_single(url, file_id, args):
    '''save a image by the given url'''
    response = requests.get(url)
    if 'image' in response.headers['content-type']:
        img = Image.open(BytesIO(response.content))
        img.save(os.path.join(args.output, file_id+f'.{img.format.lower()}'))

def save_image(args):
    '''save images from pages scraped from TABLE_PAGE'''
    with open(os.path.join(args.temp, 'image_urls.json'), 'r', encoding='utf-8') as fin:
        image_urls = json.load(fin)

    # calc the digit of the total number of images for generating file ids
    total_images = sum([len(urls) for urls in image_urls.values()])
    digit = len(str(total_images)) + 1

    last_get = time.time()
    bar = tqdm(total=total_images)

    num_images = 0
    key2file_ids = {}
    for key, urls in image_urls.items():
        file_ids = []
        for url in urls:
            file_id = str(num_images).zfill(digit)
            save_image_single(url, file_id, args)
            file_ids.append(file_id)
            num_images += 1
            bar.update(1)
            # waiting
            time.sleep(max(0, GET_INTERVAL - (time.time() - last_get)))
            last_get = time.time()
        key2file_ids[key] = file_ids

    with open(os.path.join(args.output, 'image_ids.json'), 'w', encoding='utf-8') as fout:
        json.dump(key2file_ids, fout, ensure_ascii=False, indent=2)



'''main flow'''

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--output', '-o', default='data', help='the name of the output folder')
    parser.add_argument('--temp', '-t', default='temp', help='name of the temporal folder')
    parser.add_argument('--keeptemp', '-k', action='store_true', help='keep the temporal folder')

    return parser.parse_args()

def main():
    
    args = get_args()

    if not os.path.exists(args.output):
        os.mkdir(args.output)
    if not os.path.exists(args.temp):
        os.mkdir(args.temp)

    print('Start collecting images', end='\n\n')

    print('--GET page with list of characters--')
    get_and_save(TABLE_PAGE, args)
    print('done')
    print('--scrape urls of detailed character information page--')
    scrape_detail_url(args)
    print('done')
    print('--GET the detail pages and scrape urls of images--')
    scrape_image_urls(args)
    print('done')
    print('--GET and save images from the scraped urls--')
    save_image(args)
    print('done')
    if not args.keeptemp:
        print('--cleanup--')
        shutil.rmtree(args.temp)
        print('done')

    print('\nfinished collecting images.')
    print(f'The scraped images are saved at {args.output}')

if __name__ == "__main__":
    # main()
    args = get_args()
    save_image(args)