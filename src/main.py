import os
import shutil
from project_config import (
    SPLIT_DATA_FOLDER,
    ORIGINAL_DATA_FILE,
    SORTED_DATA_FILE,
    MAX_FILE_LINE,
    MAPPER,
    ZONE_MAP_COLS
)
from typing import List, Dict, Tuple
from Processor import Processor
import time


def get_columns(data_file: str) -> List:
    """Gets header columns in file"""
    return open(data_file, 'r').readline().rstrip().split(',')


def split_columns(data_file: str, zone_maps: Dict) -> Dict: 
    """Splits the large csv into individual columns in their own files"""
    columns = get_columns(data_file=data_file)
    recreate_folders(folders=[SPLIT_DATA_FOLDER])
    opened_files = []
    with open(data_file, 'r') as f:
        next(f)
        min_max_dict = initialize_min_max_dict(zone_maps=zone_maps)
        curr_zone = 0
        i = 0
        for line in f:
            if i % MAX_FILE_LINE == MAX_FILE_LINE - 1:
                for col in min_max_dict:
                    min_max_dict[col]['max_idx'] = i
            if i % MAX_FILE_LINE == 0:
                if opened_files:
                    # store in map and reset min_max_dict
                    zone_maps, min_max_dict = store_in_zone_map(
                        min_max_dict=min_max_dict,
                        zone_maps=zone_maps
                    )
                    close_files(opened_files=opened_files)
                for col in min_max_dict:
                    min_max_dict[col]['min_idx'] = i
                opened_files = [
                    open(f'{SPLIT_DATA_FOLDER}/{col}_{curr_zone}.txt', 'w')
                    for col in columns
                ]
                curr_zone += 1
            content = line.rstrip().split(',')
            for file, c, col in zip(opened_files, content, columns):
                # if col in MAPPER:
                #     c = MAPPER[col][c]
                if col in ZONE_MAP_COLS:
                    min_val = min_max_dict[col]['min_val']
                    max_val = min_max_dict[col]['max_val']
                    if col == 'month':
                        min_max_dict[col]['min_val'] = min(min_val, c)
                        min_max_dict[col]['max_val'] = max(max_val, c)
                    else:
                        min_max_dict[col]['min_val'] = min(min_val, float(c))
                        min_max_dict[col]['max_val'] = max(max_val, float(c))
                file.write(f'{c}\n')
            i += 1
    for col in min_max_dict:
        min_max_dict[col]['max_idx'] = i - 1
    zone_maps, min_max_dict = store_in_zone_map(
        min_max_dict=min_max_dict,
        zone_maps=zone_maps
    )
    close_files(opened_files=opened_files)
    return zone_maps


def recreate_folders(folders: List[str]) -> None:
    for folder in folders:
        if os.path.exists(folder) and os.path.isdir(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)
    return


def initialize_min_max_dict(zone_maps: Dict) -> Dict:
    """Initialize the dictionary that stores the min and max for each col zone"""
    min_month_str = '9999-01'
    max_month_str = '0001-01'
    min_max_dict = {}
    for col in zone_maps:
        min_max_dict[col] = {
            'min_idx': int(1e9),
            'max_idx': -1,
            'min_val': col == 'month' and min_month_str or 1e9,
            'max_val': col == 'month' and max_month_str or -1,
        }
    return min_max_dict


def store_in_zone_map(
    min_max_dict: Dict,
    zone_maps: Dict
) -> Tuple[Dict, Dict]:
    """Store the current min and max in the zone map and reinitialize the min and max"""
    for col in zone_maps:
        zone_maps[col].append(min_max_dict[col])
    min_max_dict = initialize_min_max_dict(zone_maps=zone_maps)
    return zone_maps, min_max_dict


def close_files(opened_files: List) -> None:
    for file in opened_files:
        file.close()
    return
    

def main() -> None:
    """Main interface with user"""
    print(f'Data file used: {ORIGINAL_DATA_FILE}')
    print(f'File Size is {os.stat(ORIGINAL_DATA_FILE).st_size / (1024 * 1024)} MB')

    line_count = sum(1 for _ in open(ORIGINAL_DATA_FILE, 'r'))
    print(f'Number of Lines in the file is {line_count}')

    zone_maps = {
        col: []
        for col in ZONE_MAP_COLS
    }

    # sort the data file by month column, excluding the header
    print('Sorting data by month...')
    os.system(f'(head -n 1 {ORIGINAL_DATA_FILE} && tail -n +2 {ORIGINAL_DATA_FILE} | sort -t, -k1,1) > {SORTED_DATA_FILE}')

    zone_maps = split_columns(data_file=SORTED_DATA_FILE, zone_maps=zone_maps)

    while True:
        print()
        text = 'Enter your matriculation number for processing, c to cancel: '
        matric_num = input(text).strip()
        if matric_num == 'c':
            print('Have a good day, bye bye...')
            break
        try:
            if len(matric_num) != 9:
                print('Invalid input, matriculation number is of length 9...')
                continue
        except ValueError:
            print('Invalid input, please try again...')
            continue
        
        processer = Processor(matric_num=matric_num, zone_maps=zone_maps)
        start = time.time()
        processer.process_data()
        print(f'Time taken: {time.time() - start:.2f} seconds')


if __name__ == '__main__':
    main()
