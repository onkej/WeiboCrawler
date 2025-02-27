# -*- coding: utf-8 -*-
#!/usr/bin/env python3

# Author: Ji An (https://github.com/an-kei/SinaWeiboScraper)
# Credit: Xuzhou Yin (For original repository, see https://github.com/Yhinner/SinaWeiboScraper) 
# Updated on 2024-07-06


import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from urllib.parse import urlencode, urljoin, quote, unquote
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import argparse



# Homepage of Weibo search
domain   = "https://s.weibo.com"


def create_session(firefox_profile_path):
    """Create a requests session with cookies from a Firefox profile."""
    
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.profile = firefox_profile_path
    driver = webdriver.Firefox(options=options)

    driver.get(domain)
    session = requests.Session()
    cookies = {
        cookie['name']: cookie['value']
        for cookie in driver.get_cookies()
    }
    session.cookies.update(cookies)
    driver.quit()

    return session



def fetch_result_pages(session, keyword):
    """For each keyword, fetch search result pages and (ideally) return a list of links to all possible result pages."""
    
    path   = "/realtime?"
    params = urlencode(
        {
            'q': keyword,
            'rd': 'realtime',
            'tw': 'realtime',
        }
    )

    url = urljoin(domain, path + params).replace(' ', '+')
    response  = session.get(url)
    print(f"Accessing REALTIME main page: {response.url} ...")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        mpage_section = soup.find('div', class_='m-page')

        if mpage_section: # if there are multiple pages of search results
            pages_suffix = [
                unquote(li.a['href']) 
                for li in mpage_section.find_all('li')
            ]
            pages = [urljoin(domain, quote(suffix, safe='&:/=?')) for suffix in pages_suffix]
            print(f"Found {len(pages)} REALTIME pages.")

        elif soup.find('div', class_="content"): # if there are search results but only 1 page
            pages = [url]
            print(f"Found 1 REALTIME page.")

        else:   # if no search results found
            pages = f"No REALTIME results found for {keyword}."

        return pages
    
    else:
        raise Exception(f'Failed to fetch REALTIME results for {keyword}: {response.status_code} - {response.reason}')
    


def parse_post_time(time_str):
    """Parse the local post time (UTC+8) string and return it in 'YYYY-MM-DD HH:MM' format."""

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    if "秒前" in time_str:
        seconds_ago = int(re.search(r'(\d+)秒前', time_str).group(1))
        post_time   = now - timedelta(seconds=seconds_ago)

    elif "分钟前" in time_str:
        minutes_ago = int(re.search(r'(\d+)分钟前', time_str).group(1))
        post_time   = now - timedelta(minutes=minutes_ago)

    elif "今天" in time_str:
        today_time  = re.search(
            r'今天(\d{2}:\d{2})', time_str
        ).group(1)
        post_time   = now.replace(
            hour    = int(today_time.split(':')[0]), 
            minute  = int(today_time.split(':')[1])
        )
        
    elif "年" in time_str:
        year, month, day, hour, minute = re.search(
            r'(\d{4})年(\d{2})月(\d{2})日 (\d{2}):(\d{2})',
            time_str
        ).groups()
        post_time = datetime(
            year    = int(year), 
            month   = int(month), 
            day     = int(day), 
            hour    = int(hour), 
            minute  = int(minute)
        )

    elif "月" in time_str:
        month, day, hour, minute = re.search(
            r'(\d{2})月(\d{2})日 (\d{2}):(\d{2})', 
            time_str
        ).groups()
        post_time = now.replace(
            month   = int(month), 
            day     = int(day), 
            hour    = int(hour), 
            minute  = int(minute)
        )

    else:   
        return time_str
    
    return post_time.strftime('%Y-%m-%d %H:%M')



def parse_post_card(card: BeautifulSoup) -> dict:
    """Parse post content and metadata from the given card and return a post-level dict."""
    data = {}

    # Extract post content
    content_full = card.find('p', class_='txt', attrs={'node-type': 'feed_list_content_full'})
    if content_full:
        data['content'] = content_full.get_text(strip=False).strip().replace('收起d', '')
    else:
        content = card.find('p', class_='txt', attrs={'node-type': 'feed_list_content'})
        if content:
            data['content'] = content.get_text(strip=False).strip()

    # Extract post metadata
    user = card.find('a', class_='name')
    if user:
        data['user'] = user.get_text(strip=True)

    post_time = card.find('div', class_='from').find('a').get_text(strip=True)
    if post_time:
        data['time'] = parse_post_time(post_time)
    
    reactions = card.find('div', class_='card-act').find_all('li')
    if reactions:
        reactions = [reaction.get_text(strip=True) for reaction in reactions]
        reactions = [int(reaction) if reaction.isdigit() else 0 for reaction in reactions]
        data['reposts'], data['comments'], data['likes'] = reactions

    post_link = card.find('ul', attrs={'node-type': 'fl_menu_right'}).find('a', attrs={'@click': True})['@click']
    if post_link:
        refer_url = re.search(r"copyurl\('(.+?)'\)", post_link).group(1)
        pure_url = refer_url.split('?')[0]
        data['url'] = pure_url

    # print(data)
    return data



def process_search_results(session, keyword):
    """Process REALTIME results for a single keyword, write the extracted posts to a CSV file."""

    pages = fetch_result_pages(session, keyword)
    all_posts = []
    for i, page in enumerate(pages):
        response = session.get(page)
        print(f'Processing page {i+1}: {response.url} ...')
               
        soup  = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', class_='card-wrap')
        posts = [parse_post_card(card) for card in cards if card.find('div', class_='content')]
        for post in posts:
            post['page'] = i+1
            post['keyword'] = keyword

        all_posts.extend(posts)
        print(f"Extracted {len(posts)} post(s) for REALTIME page {i+1}.")
        
    print(f'Processing finished. Successfully extracted {len(all_posts)} REALTIME posts for keyword {keyword}')

    return all_posts



def posts_to_csv(posts, output_fpath):
    """Write the extracted posts found for one single keyword to a CSV file."""
    
    with open(output_fpath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'page', 'keyword', 
            'content', 'user', 'time', 
            'reposts', 'comments', 'likes', 'url'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for post in posts:
            writer.writerow(post)



def WeiboRealtime(query_file, firefox_profile_path, output_dir):
    """Main function to scrape Weibo REALTIME posts by keywords."""
    
    session = create_session(firefox_profile_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(query_file, 'r', encoding='utf-8') as queries:
        reader = csv.reader(queries)
        for query in reader:
            if query:
                keyword = query[0]
                output_csv = f"rt_{keyword}.csv"
                output_fpath = os.path.join(output_dir, output_csv)
                all_posts = process_search_results(session, keyword)
                posts_to_csv(all_posts, output_fpath)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='WeiboScrapingByRealtime',
        formatter_class=argparse.RawTextHelpFormatter,
        description='''
--------------------------------------------------------------------
This program helps obtain REALTIME Weibo posts based on keyword. It 
uses a Firefox profile to access Weibo search results and scrape the
corresponding posts that will then be saved in csv files.
--------------------------------------------------------------------
''',
        epilog="e.g. python3 WeiboScrapingByRealtime.py './by_realtime_query/YourQuery.csv' '/path/to/my/Firefox/profile'"
    )
    parser.add_argument(
        'query',
        type=str,
        help='path to your query file',
    )
    parser.add_argument(
        'profile', 
        type=str,
        help='path to your Firefox profile',
    )
    parser.add_argument(
        '-o',
        dest='output',
        type=str, 
        required=False,
        default='by_realtime_result',
        help="output folder name (default: %(default)s)",
    )
    args = parser.parse_args()
    WeiboRealtime(
        args.query, 
        args.profile, 
        args.output
    )

