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
# import time as systime

# Homepage of Weibo search
domain   = "https://s.weibo.com"


def create_session(firefox_profile_path):
    """Create a requests session with cookies from a Firefox profile."""
    
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.profile = firefox_profile_path
    driver = webdriver.Firefox(options=options)

    driver.get(domain)
    # systime.sleep(5)
    session = requests.Session()
    cookies = {
        cookie['name']: cookie['value']
        for cookie in driver.get_cookies()
    }
    session.cookies.update(cookies)
    driver.quit()

    return session



def fetch_result_pages(session, keyword, start_date, end_date):
    """For each keyword, fetch search result pages and (ideally) return a list of links to all possible result pages."""
    
    path   = "/weibo?"
    params = urlencode(
        {
            'q': keyword,
            'scope': 'ori',
            'suball': 1,
            'timescope': f'custom:{start_date}:{end_date}'
        }
    )

    url = urljoin(domain, path + params)
    response  = session.get(url)
    print(f"Accessing main result page: {response.url} ...")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        mpage_section = soup.find('div', class_='m-page')

        if mpage_section: # if there are multiple pages of search results
            pages_suffix = [
                unquote(li.a['href'].replace('×', '&times')) 
                for li in mpage_section.find_all('li')
            ]
            pages = [urljoin(domain, quote(suffix, safe='&:/=?')) for suffix in pages_suffix]
            print(f"Found {len(pages)} search result pages.")

        elif soup.find('div', class_="content"): # if there are search results but only 1 page
            pages = [url]
            print(f"Found 1 search result page.")

        else:   # if no search results found
            pages = f"No search results found for {keyword} between {start_date} and {end_date}."

        return pages
    
    else:
        raise Exception(f'Failed to fetch search results for {keyword} between {start_date} and {end_date}: {response.status_code} - {response.reason}')
    


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



def process_search_results(session, keyword, start_date, end_date):
    """Process search results for a single keyword between start_date and end_date, and write the extracted posts to a CSV file."""

    pages = fetch_result_pages(session, keyword, start_date, end_date)
    all_posts = []
    for i, page in enumerate(pages):
        # systime.sleep(5)
        response = session.get(page)
        # systime.sleep(5)
        print(f'Processing page {i+1}: {response.url} ...')
               
        soup  = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', class_='card-wrap')
        posts = [parse_post_card(card) for card in cards if card.find('div', class_='content')]
        for post in posts:
            post['page'] = i+1
            post['keyword'] = keyword

        all_posts.extend(posts)
        print(f"Extracted {len(posts)} post(s) for search result page {i+1}.")
        
    print(f'Processing finished. Successfully extracted {len(all_posts)} posts in total for keyword {keyword} between {start_date} and {end_date}')

    return all_posts



def posts_to_csv(posts, output_fpath):
    """Write the extracted posts found for one single keyword between start_date and end_date to a CSV file."""
    
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



def WeiboKeywordSearch(query_file, firefox_profile_path, output_dir):
    """Main function to scrape Weibo search results by keywords."""
    
    session = create_session(firefox_profile_path,)
    os.makedirs(output_dir, exist_ok=True)

    with open(query_file, 'r', encoding='utf-8') as queries:
        reader = csv.reader(queries)
        for query in reader:
            keyword, start_date, end_date = query
            output_csv = f"{keyword}_{start_date}_{end_date}.csv"
            output_fpath = os.path.join(output_dir, output_csv)
            all_posts = process_search_results(session, keyword, start_date, end_date)
            posts_to_csv(all_posts, output_fpath)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scrape Weibo search results by keywords'
    )
    parser.add_argument(
        'query', 
        type=str,
        help='The directory to your query file containing keywords and date range used to search for',
    )
    parser.add_argument(
        '-p','--profile_path', 
        type=str,
        required=True,
        help='The directory to the Firefox profile containing the cookies for the Weibo session', 
        # default="/Users/ko/Library/Application Support/Firefox/Profiles/pejmtqsl.default-release-1714475519242"
    )
    parser.add_argument(
        '-o','--output_dir', 
        type=str, 
        required=False,
        help='The directory to save the extracted posts', 
        default="./result"
    )
    args = parser.parse_args()
    WeiboKeywordSearch(
        args.query, 
        args.profile_path, 
        args.output_dir
    )
