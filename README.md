# A Tool for Weibo Scrapping by Keyword Search
This is an extended version of the Weibo Scraper developed by [Xuzhou Yin](https://github.com/Yhinner/SinaWeiboScraper).


## Dependencies
- Python 3 (3.12 may be better)
- Firefox browser (up-to-date)
- Packages: cf. ``` requirements.txt ``` --> to be installed through Terminal using ```pip3 install pkg1 pkg2 pk3``` command after installing Python 3
- Weibo account: a Chinese phone number is not necessary, instead, it's become a must to use your local phone number to sign up.


## What We Need as Input
- **Query**: ``` .csv ``` file for keyword and date range settings. For each search attempt, Weibo returns at most 50 result pages, each showing no more than 10 posts. It's worth noting that for some extremely hot topics, it's predictable that you end up getting 50 pages of posts published within a few hours only, which means a day-based strategy would not do the job well enough. Hopefully, the hour-based feature will be tested later ... or if possible, feel free to fork and explore it yourself. 🙌
- **Firefox profile**: to find your Firefox default profile path, perhaps the easiest way is by typing ``` about:profiles ``` in the Firefox search bar. Press ```Enter``` and there will be at least one table where you can find the ``` Root Directory ``` for your ``` Default Profile ```. (See more at [Profiles - Where Firefox stores your bookmarks, passwords and other user data](https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data))

***IMPORTANT*** - Remember to **sign in and save your username and password on Firefox** so that the Weibo Search homepage can be automatically loaded under your account when running the program. 


## In Terminal
- Go to the folder where you store the query and the Python script:  ``` cd /path/to/the/project ```

- Run the program:  ``` python3 WeiboScraper.py './queries/query.csv' '/path/to/Firefox/profile' ```

- For help message:  ``` python3 WeiboScraper.py -h ```

## Output
The extracted data will be stored in ```result``` folder by default. Each query (i.e. each line in ```query.csv```) generates one CSV file. MacBook's Numbers and Google Sheets are good tools to view this file type.

## Shortcomings
Currently, the program only supports day-based keyword searches, and for each search, the posts are sorted by time from newest to oldest, starting from 11 p.m. by default. Thus sometimes setting a wide range will still be likely to end up with 480+ posts ... that were published on the newest day  ... and during that night! 😂 In this case, suppose you need more data, the only possible tiny improvement is to narrow the date range (e.g. 1 day per query) and add multiple queries below the initial one, with the same keyword and different consecutive single days as time range.

## License
This project is licensed under the MIT License.
