import re
import math
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

scraper = cloudscraper.create_scraper(
    browser={'custom': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/114.0.0.0 Safari/537.36'}
)
base_url   = 'https://www.bayt.com/en/international/jobs/data-scientist-jobs/'

first_html = scraper.get(base_url).text
first_soup = BeautifulSoup(first_html, 'html.parser')

count_el = (
    first_soup.select_one('span.jobs-filter__count') or
    first_soup.select_one('div.results-header__count') or
    first_soup.select_one('h1 span.count')
)

if count_el and count_el.get_text(strip=True).isdigit():
    total_jobs = int(count_el.get_text(strip=True))
else:
    text = first_soup.get_text(separator=' ')
    m = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*)\s+jobs\s+found', text, re.IGNORECASE)
    if not m:
        raise RuntimeError("Failed to find total jobs (selector or regex needs update)")
    total_jobs = int(m.group(1).replace(',', ''))

print(f"Official total jobs: {total_jobs}")

first_cards = first_soup.select('li[data-js-job]')
per_page    = len(first_cards) or 20
max_pages   = math.ceil(total_jobs / per_page)
print(f"Detected {per_page} jobs/page, need ~{max_pages} pages.")

jobs_by_id = {}
for page in range(1, max_pages+1):
    url   = f"{base_url}?page={page}"
    soup  = BeautifulSoup(scraper.get(url).text, 'html.parser')
    cards = soup.select('li[data-js-job]')
    if not cards:
        break

    for card in cards:
        jid = card.get('data-job-id')
        if jid in jobs_by_id:
            continue

        jobs_by_id[jid] = {
            'Title':    card.select_one('h2 a').get_text(strip=True),
            'Company':  (card.select_one('.jb-logo') or {}).get('alt'),
            'Location': card.select_one('.t-mute.t-small').get_text(strip=True),
            'Summary':  card.select_one('.jb-descr').get_text(strip=True),
            'Date':     card.select_one('.jb-date span').get_text(strip=True),
        }

    if len(jobs_by_id) >= total_jobs:
        break

df = pd.DataFrame(jobs_by_id.values())
df.to_csv('jobs.csv', index=False, encoding='utf-8-sig')
print("Saved to jobs.csv")
print(f"Total unique jobs scraped: {len(df)} / {total_jobs}")
print(df.head())
