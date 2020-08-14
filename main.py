#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tty7tyil_python import crawler_requests_session as crs
from tty7tyil_python import print_banner as pb
from typing import Any, Callable, List, Set, Tuple
import bs4
import requests
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

CRS_SESSION = crs.Crawler_Requests_Session(
    proxies_list=[
        {
            'http': 'socks5h://127.0.0.1:1080/',
            'https': 'socks5h://127.0.0.1:1080/',
        },
    ],
)


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

    top_rated_page = CRS_SESSION.get(
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

        episode_page = CRS_SESSION.get(URL_IMDB_TITLE_ENTRY.format(title_id=tv_episode_id))
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


def print_episode_set(
    episode_set: Set[Tuple[int, int, str, float, int, str]],
    sort_method: Callable[
        [
            Tuple[
                int,    # 0> season
                int,    # 1> episode
                str,    # 2> title
                float,  # 3> rating
                int,    # 4> original_index
                str     # 5> tv_episode_id
            ]
        ],
        Any
    ] = lambda e: e[4],
) -> None:
    episode_list = list(episode_set)
    episode_list.sort(key=sort_method)
    for e in episode_list:
        print(
            '{4:_>{index_width}} ({3: >4})> S{0:0>2} E{1:0>2} - {2}'.format(
                *e, index_width=max(len(str(e[4])) for e in episode_list)
            )
        )


def print_episode_set_by_season(episode_set: Set[Tuple[int, int, str, float, int, str]]) -> None:
    episode_list = list(episode_set)
    episode_list.sort(key=lambda e: e[0])

    episode_set_by_season_list: List[Tuple[int, Set[Tuple[int, int, str, float, int, str]]]] = []
    _season: int = episode_list[0][0]
    _per_season_list: List[Tuple[int, int, str, float, int, str]] = []
    for e in episode_list:
        if e[0] == _season:
            _per_season_list.append(e)
        else:
            episode_set_by_season_list.append((_season, set(_per_season_list)))
            _season = e[0]
            _per_season_list = []
            _per_season_list.append(e)
    episode_set_by_season_list.append((_season, set(_per_season_list)))

    for s in episode_set_by_season_list:
        pb.print_banner('season {}'.format(s[0]))
        print_episode_set(s[1], lambda e: (e[0], e[1]))
        print()


if __name__ == '__main__':
    if tv_show_id == '':
        tv_show_id = input('IMDb ID of the TV show to fetch: ')
    episode_set = fetch(tv_show_id)
    print_episode_set(episode_set)
