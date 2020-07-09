import json
import os
import re

import requests

import config

current_dir = os.path.dirname(os.path.realpath(__file__))


SPECIAL_TICKETS = "БЪДИ С ОТБОРА!"
EXCLUDE_BLOCKS = {
    " Блок 20",
    " Блок 20.",
    " Блок 23",
    # " Блок 7",
    # " Блок 25",
    # " Блок 26",
}

# Exclude all the rows less or equals to the specified.
EXCLUDE_ROWS = {
    " Блок 15": 1,
    " Блок 16": 1,
    " Блок 17": 18,
    " Блок 18": 18,
    " Блок 19": 1,



}
SECTOR_ORDER = [
    "ВИП",
    #"Скайбокс*",
    "Сектор А",
    "Сектор Б",
    "Сектор В",
    "Сектор Г"
]

SECTOR_LIMITED_SIZE = {
    # "Сектор А": 1000,
    # "Сектор Б": 1000,
    # "Сектор В": 1000,
    # "Сектор Г": 1000
}

def _get_token():
    url = config.eventim_url
    r = requests.get(url)
    tokenPattern = '''"authToken":"(.*?)"'''
    match = re.search(tokenPattern, r.text)
    return match.groups(0)[0]


def _get_setmap_from_url():
    token = config.token if config.token else _get_token()
    print(token)
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://www.eventim.bg',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': config.eventim_url,
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    r = requests.get("https://api.eventim.com/seatmap/api/public/seatmap/TDLREST-1301-{}?smcVersion=v6.1&version=v6.3.0&availabilityTimestamp=0&a_ts=1594301758906&a_systemID=17&a_TDLToken={}&a_PromotionID=0".format(config.event_id, token), headers=headers)
    return r.json()


def _get_seatmap_from_file():
    with open(os.path.join(current_dir, "sample-seatmap.json")) as json_file:
        return json.load(json_file)


def _get_availability_from_url():
    token = config.token if config.token else _get_token()
    print(token)
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://www.eventim.bg',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': config.eventim_url,
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    r = requests.get("https://api.eventim.com/seatmap/api/public/availability/TDLREST-1301-{}?smcVersion=v6.1&version=v6.3.0&key=tdlrest_1301_AUT_0_7625_28675751_{}_0&availabilityTimestamp=0&a_ts=1594309572978&a_systemID=17&a_TDLToken={}&a_PromotionID=0".format(config.event_id, config.event_id, token), headers=headers)
    return r.json()


def _get_availability_map_from_file():
    with open(os.path.join(current_dir, "sample-availability.json")) as json_file:
        return json.load(json_file)


def _get_availability_map():
    data = _get_availability_map_from_file() if config.load_data_from_file else _get_availability_from_url()
    seats = data["seats"]

    result_map = {}
    seat_id = 0
    for index, seat in enumerate(seats):
        seat_id = seat_id + seat[0]
        result_map[seat_id] = seat[1]

    return result_map


def get_sector_results():
    def populate_sector(sector_name, available, reserved):
        sector_name = "ВИП" if sector_name == "STRABAG VIP" else sector_name
        sector_name = "Сектор А" if sector_name.startswith("STRABAG") else sector_name

        if sector_name not in sectors:
            return

        sectors[sector_name][0] += reserved
        sectors[sector_name][1] += available

    seatmap = _get_seatmap_from_file() if config.load_data_from_file else _get_setmap_from_url()
    availability_map = _get_availability_map()

    sectors = {
        "Скайбокс*": [0, 0],
        "ВИП": [0, 0],
        "Сектор А": [0, 0],
        "Сектор Б": [0, 0],
        "Сектор В": [0, 0],
        "Сектор Г": [0, 0]
    }

    for block in seatmap["areas"][0]["blocks"]:
        sector_name = block["name"].split(",")[0]
        block_name = block["name"].split(",")[1] if len(block["name"].split(",")) > 1 else ""

        if block_name in EXCLUDE_BLOCKS:
            continue

        if sector_name == SPECIAL_TICKETS:
            #print(block["graphics"][0]["pcBlock"])
            #print(block["graphics"][1]["pcBlock"])
            continue

        reserved = 0
        available = 0

        # Sort the rows by seat number so the lower rows to be the first.
        rows = sorted(block["rows"], key=lambda r: r["seats"][0])

        for row_number, row in enumerate(rows):
            if EXCLUDE_ROWS.get(block_name) and EXCLUDE_ROWS.get(block_name) >= row_number + 1:
                continue

            row_id = 0
            for group in row["seats"]:
                for seat in group:
                    row_id += seat[0]

                    seat_status = availability_map.get(row_id, 0)

                    if seat_status == 1:
                        available += 1
                    else:
                        reserved += 1

        if block_name.startswith(" Box"):
            continue
            #sector_name = "Скайбокс*"
            #reserved = 0 if len(block["graphics"][0]["pcBlock"]) > 0 else 17
            #available = 17 - reserved

        populate_sector(sector_name, available, reserved)

    total_reserved = 0
    total_available = 0

    sector_results = []
    for sector_name in SECTOR_ORDER:
        counts = sectors[sector_name]
        total = SECTOR_LIMITED_SIZE.get(sector_name) if SECTOR_LIMITED_SIZE.get(sector_name) else counts[0] + counts[1]
        counts[0] = total - counts[1]

        total_reserved += counts[0]
        total_available += counts[1]
        print("{}, Продадени: {}, Свободни: {}, Общо:{}".format(sector_name, counts[0], counts[1], total))
        print("{}%".format(int(counts[0] * 100 / (counts[0] + counts[1]))))

        sector_results.append(
            {
                "name": sector_name,
                "sold": counts[0],
                "available": counts[1],
                "total": total
            }
        )

    print("Общо Продадени: {} ({}% от капацитета), Свободни: {}, Общо:{}".format(
        total_reserved,
        int(total_reserved * 100 / (total_reserved + total_available)),
        total_available,
        total_reserved + total_available))

    return total_reserved, total_available, sector_results