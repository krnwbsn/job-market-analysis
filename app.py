import re
import math
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

scraper = cloudscraper.create_scraper(
    browser={'custom': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/114.0.0.0 Safari/537.36'}
)
base_url = 'https://www.bayt.com/en/international/jobs/data-scientist-jobs/'

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

first_cards = first_soup.select('li[data-js-job]')
per_page = len(first_cards) or 20
max_pages = math.ceil(total_jobs / per_page)

jobs_by_id = {}
for page in range(1, max_pages+1):
    url = f"{base_url}?page={page}"
    soup = BeautifulSoup(scraper.get(url).text, 'html.parser')
    cards = soup.select('li[data-js-job]')
    if not cards:
        break

    for card in cards:
        jid = card.get('data-job-id')
        if jid in jobs_by_id:
            continue

        jobs_by_id[jid] = {
            'Title':    card.select_one('h2 a').get_text(strip=True),
            'Company':  (card.select_one('.jb-logo') or {}).get('alt', '').replace(' logo', '').strip(),
            'Location': card.select_one('.t-mute.t-small').get_text(strip=True),
            'Summary':  card.select_one('.jb-descr').get_text(strip=True),
            'Date':     card.select_one('.jb-date span').get_text(strip=True),
        }

    if len(jobs_by_id) >= total_jobs:
        break

df = pd.DataFrame(jobs_by_id.values())

me_countries = [
    'Saudi Arabia', 'United Arab Emirates', 'UAE', 'Qatar', 'Kuwait',
    'Oman', 'Bahrain', 'Jordan', 'Dubai'
]
pattern = '|'.join(me_countries)
mask = (
    df['Location'].str.contains(pattern, case=False, na=False) &
    ~df['Location'].str.contains('India', case=False, na=False)
)
df_filtered = df[mask].reset_index(drop=True)

loc_array = df_filtered['Location'].to_numpy()
loc_uniques, loc_counts = np.unique(loc_array, return_counts=True)
loc_idx = np.argsort(-loc_counts)[:5]
top5_locs    = loc_uniques[loc_idx]
top5_lcounts = loc_counts[loc_idx]

title_array = df_filtered['Title'].to_numpy()
title_uniques, title_counts = np.unique(title_array, return_counts=True)
title_idx = np.argsort(-title_counts)[:5]
top5_titles   = title_uniques[title_idx]
top5_tcounts  = title_counts[title_idx]

print("Top 5 Locations (Filtered):")
for loc, cnt in zip(top5_locs, top5_lcounts):
    print(f"  • {loc}: {cnt}")

print("\nTop 5 Job Titles (Filtered):")
for title, cnt in zip(top5_titles, top5_tcounts):
    print(f"  • {title}: {cnt}")

plt.figure(figsize=(8, 4))
plt.bar(top5_locs, top5_lcounts)
plt.title('Top 5 Locations for Data Scientist Jobs (Filtered)')
plt.xlabel('Location')
plt.ylabel('Total Postings')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('top5_locations_filtered.png', dpi=300)
plt.show()

plt.figure(figsize=(8, 4))
plt.bar(top5_titles, top5_tcounts, color='orange')
plt.title('Top 5 Job Titles for Data Scientist Jobs (Filtered)')
plt.xlabel('Job Title')
plt.ylabel('Total Postings')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('top5_titles_filtered.png', dpi=300)
plt.show()

df_filtered.to_csv('jobs_mid_east_filtered.csv', index=False, encoding='utf-8-sig')
pd.DataFrame({
    'Location': top5_locs, 'Count': top5_lcounts
}).to_csv('top5_locations_filtered.csv', index=False)
pd.DataFrame({
    'Title': top5_titles, 'Count': top5_tcounts
}).to_csv('top5_titles_filtered.csv', index=False)
