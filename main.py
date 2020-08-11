#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Set, Tuple
import requests
import bs4
import sys

tv_show_id: str = ''
if len(sys.argv) == 2:
    tv_show_id = sys.argv[1]

URL_IMDB_TOP_RATED_EPISODES = ''.join((
    'https://www.imdb.com/search/title/?',
    '&'.join((
        'series={tv_show_id}',  # only accept tv show id for now
        'count={per_page}',  # how many results on a single page, max is 250
        # 'start={start_index}',
        'view=simple',
        'sort=user_rating,desc',
    )),
))
URL_IMDB_TITLE_ENTRY = 'https://www.imdb.com/title/{title_id}/'

temp_PROXIES = {
    'http': '',
    'https': '',
}
temp_HEADERS_USER_AGENT = {
    'User-Agent': ' '.join((
        '',
    ))
}


def fetch(
    tv_show_id: str,
    per_page: int = 50,
) -> Set[Tuple[int, int, str, float, int, str]]:
# -> Set[Tuple[season, episode, title, rating, original_index, tv_episode_id]]
    # css path:
    # - the list: div.lister.list.detail.sub-list div.lister-list
    #   - each entry: div.lister-item.mode-simple div.lister-item-content div.lister-col-wrapper
    #     - original_index    : div.col-title span.lister-item-header span.lister-item-index.unbold.text-primary
    #     - tv_episode_id     : div.col-title span.lister-item-header span a
    #     - title             : div.col-title span.lister-item-header span a
    #     - rating            : div.col-imdb-rating strong
    session = requests.Session()
    session.proxies.update(temp_PROXIES)
    session.headers.update(temp_HEADERS_USER_AGENT)

    top_rated_page = session.get(
        URL_IMDB_TOP_RATED_EPISODES.format(tv_show_id=tv_show_id, per_page=per_page)
    )
    top_rated_page_soup = bs4.BeautifulSoup(top_rated_page.text, 'html.parser')

    episode_list = []
    for e in (
        top_rated_page_soup
        .find('div', {'class': 'lister-list'})
        .find_all('div', {'class': 'lister-col-wrapper'})
    ):
        original_index: int = int(
            e
            .find('span', {'class': 'lister-item-index unbold text-primary'})
            .string[:-1]
        )

        _temp = e.find('span', {'class': 'lister-item-header'}).find_all('a')[1]
        tv_episode_id: str = _temp['href'].split('/')[2]
        title: str = _temp.string

        rating: float = float(e.find('strong').string.strip())

        episode_page = session.get(URL_IMDB_TITLE_ENTRY.format(title_id=tv_episode_id))
        episode_page_soup = bs4.BeautifulSoup(episode_page.text, 'html.parser')
        _temp = (
            episode_page_soup
            .find('div', {'class': 'bp_item bp_text_only'})
            .find('div', {'class': 'bp_heading'})
            .text
            .split(' ')
        )
        season: int = int(_temp[1])
        episode: int = int(_temp[4])

        episode_list.append((season, episode, title, rating, original_index, tv_episode_id))

    return set(episode_list)


if __name__ == '__main__':
    if tv_show_id == '':
        tv_show_id = input('IMDb ID of the TV show to fetch: ')
    fetch(tv_show_id)
