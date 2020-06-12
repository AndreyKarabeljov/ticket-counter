import os
import subprocess
from time import sleep

import config
from eventim_client import get_sector_results
from html_generator import process_html_template

current_dir = os.path.dirname(os.path.realpath(__file__))
site_dir = os.path.join(current_dir, "..", "levski")


def _commit():
    working_directory = site_dir
    os.chdir(working_directory)
    proc = subprocess.Popen(["git", "add", "index.html"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

    proc = subprocess.Popen(["git", "commit", "-m", "stats"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

    proc = subprocess.Popen(["git", "push"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

def process():
    total_reserved, total_available, sector_results = get_sector_results()
    process_html_template(total_reserved, total_available, sector_results)

    if config.publish:
        _commit()

process()
for i in range(1, config.times):
    sleep(60 * config.sleep_time)
    process()
