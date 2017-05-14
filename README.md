# SinaWeiboScrapper
This is a Web Scrapper for Sina Weibo Search for Keywords

## How to Download
Open terminal, and navigate to the directory where you want to store the program, then type ```git clone address``` to download the program

## Dependences
1. Python 2.7 or above
2. Firefox browser (Other browsers may be supported in future)
3. selenium. Type ```pip install selenium```
4. time. Type ```pip install time```
5. bs4. Type ```pip install bs4```
6. urllib. Type ```pip install urllib```
7. datetime. Type ```pip install datetime```
8. unicodecsv. Type ```pip install unicodecsv```

## How to Use

### Before running the program
Sina Weibo limits the permission of search feature that only users has signed in is able to use advanced search(such as search with specific time period). So please register for a sina Weibo account and sign in through Firefox browser(So Firefox automatically signs in next time). Then find the path of the Firefox profile (Refer to [Where is Firefox profile stored](https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data)). and replace the path in line 49 in ```scraper.py```.

### Query
```query.txt``` file is for storing all the queries. Please add queries in the form of ```keyword;startDate;endDate;pageofResult```, one query per line. Sina Weibo does not support "Scroll to bottom to view more" feature in search. Instead, it separates the query results into pages. And Sina limits the page of results to 50. So for each query, only 50 pages of the results can be accessed by users. And each page contains 20 posts. Therefore, for each search there are maximum 1000 posts can be obtained. **However, it might be the case that there are less than 1000 posts from the query. So please check the maximum number of pages that contain all results of the query**. 

### Run the Program
Run the program by typing ```python scraper.py```

### What happens during execution
Firefox browser will be executed, navigated to search page with keyword autimatically.

### Output
Results will be in ```output``` folder in csv format. Each query generates one csv file. Excel has problem displaying Chinese characters. So viewing through other text editor is better(If you are using Mac, you can use Numbers to open the csv files).