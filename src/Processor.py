from project_config import (
    SPLIT_DATA_FOLDER,
    MAX_FILE_LINE,
    RESULTS_FOLDER,
    MAPPER
)
from typing import List, Dict, Tuple
import os
import csv


class Processor:
    def __init__(
        self,
        matric_num: str,
        zone_maps: Dict[str, List[Tuple[int, int]]]
    ) -> None:
        self.zone_maps = zone_maps
        self.matric_num = matric_num
        self.commence_month, self.end_month, self.town = self.get_month_year_town()

    def get_month_year_town(self):
        """Convert matric digits to month, year and town"""
        year = int(self.matric_num[-2])
        commence_month = int(self.matric_num[-3])
        town = int(self.matric_num[-4])
        if commence_month >=10 or year >= 10 or town >= 10:
            raise ValueError('Invalid values for month, year or town')
        
        if commence_month == 0:
            commence_month_str = '10'
            end_month_str = '12'
        else:
            commence_month_str = f'0{commence_month}'
            if commence_month >= 8:
                end_month_str = str(commence_month+2)
            else:
                end_month_str = f'0{commence_month+2}'
            
        
        if year<4:
            year_str = f'202{year}'
        else:
            year_str = f'201{year}'

        town_str = MAPPER['town'][str(town)]

        return f'{year_str}-{commence_month_str}', f'{year_str}-{end_month_str}', town_str

    def find_zones(self):
        for zone, min_max in enumerate(self.zone_maps['month']):
            if self.commence_month >= min_max['min_val'] and self.commence_month <= min_max['max_val']:
                if self.end_month <= min_max['max_val']:
                    return (zone, zone)
                else:
                    return (zone, zone + 1)
    
    def get_relevant_index(self, zones):
        """Get the relavant index
        Steps:
            - Get the relevant data from the zone files
            - Filter the data by the commence and end month
            - Filter the data by the town

        Note: Because the data is sorted by month, we can use binary search to speed up the process
        """

        original_start_idx = self.zone_maps['month'][zones[0]]['min_idx']
        origina_end_idx = self.zone_maps['month'][zones[1]]['max_idx']

        # Get the data from the zone files
        month_data = []
        for zone in range(zones[0], zones[1] + 1):
            with open(f'{SPLIT_DATA_FOLDER}/month_{zone}.txt', 'r') as f:
                month_data += [line.rstrip() for line in f]

        relative_start_idx, relative_end_idx = self.filter_by_month(month_data)

        start_idx = original_start_idx + relative_start_idx
        end_idx = original_start_idx + relative_end_idx
        town_zones = (start_idx // MAX_FILE_LINE, end_idx // MAX_FILE_LINE)

        town_data = []
        # Calculate town zones based on start, end idx and MAX_FILE_LINE
        for zone in range(town_zones[0], town_zones[1] + 1):
            with open(f'{SPLIT_DATA_FOLDER}/town_{zone}.txt', 'r') as f:
                town_data += [line.rstrip() for line in f]

        list_idx = self.filter_by_town(town_data, relative_start_idx, relative_end_idx)

        return [original_start_idx + i for i in list_idx]
    
    def filter_by_month(self, data: List[str]) -> List[str]:
        """Filter the data by the commence and end month by using binary search. Assumes data is sorted by month."""
        l = 0
        r = len(data) - 1

        while l < r-1:
            mid = (l + r) // 2
            if data[mid] < self.commence_month:
                l = mid + 1
            elif data[mid] > self.commence_month:
                r = mid - 1
            else:
                r = mid
        
        if data[l] == self.commence_month:
            start_idx = l
        else:
            start_idx = r
        
        l = start_idx
        r = len(data) - 1

        while l < r-1:
            mid = (l + r) // 2
            if data[mid] < self.end_month:
                l = mid + 1
            elif data[mid] > self.end_month:
                r = mid - 1
            else:
                l = mid
        
        if data[r] == self.end_month:
            end_idx = r
        else:
            end_idx = l
        
        return start_idx, end_idx
    
    def filter_by_town(self, data: List[str], start_idx, end_idx) -> List[str]:
        """Filter the data by the town"""
        list_idx = []
        for i in range(start_idx, end_idx + 1):
            if data[i] == self.town:
                list_idx.append(i)
        return list_idx

    def process_data(self):
        """Process the data"""
        print(f"Processing data from {self.commence_month} to {self.end_month} for town {self.town}...")
        zones = self.find_zones()
        original_start_idx = self.zone_maps['month'][zones[0]]['min_idx']

        list_idx = self.get_relevant_index(zones)
        if len(list_idx) == 0:
            print("No records found")
        else:
            print(f"Found {len(list_idx)} records")

        relevant_zones = (list_idx[0] // MAX_FILE_LINE, list_idx[-1] // MAX_FILE_LINE)

        list_relative_idx = [i-original_start_idx for i in list_idx]

        resale_price_data = []
        idx = 0
        for zone in range(relevant_zones[0], relevant_zones[1] + 1):
            with open(f'{SPLIT_DATA_FOLDER}/resale_price_{zone}.txt', 'r') as f:
                for line in f:
                    if idx in list_relative_idx:
                        resale_price_data.append(float(line.rstrip()))
                    idx += 1

        min_price, avg_price, std_dev_price = self.calculate_stats(data=resale_price_data)

        area_data = []
        idx = 0
        for zone in range(relevant_zones[0], relevant_zones[1] + 1):
            with open(f'{SPLIT_DATA_FOLDER}/floor_area_sqm_{zone}.txt', 'r') as f:
                for line in f:
                    if idx in list_relative_idx:
                        area_data.append(float(line.rstrip()))
                    idx += 1

        min_area, avg_area, std_dev_area = self.calculate_stats(data=area_data)

        self.write_results(
            min_price=min_price,
            avg_price=avg_price,
            std_dev_price=std_dev_price,
            min_area=min_area,
            avg_area=avg_area,
            std_dev_area=std_dev_area
        )
    
    def calculate_stats(self, data: List[int]):
        """Calculate min, average and standard deviation"""
        min_val = min(data)
        avg_val = sum(data) / len(data)
        std_dev = (sum([(x - avg_val) ** 2 for x in data]) / (len(data)-1)) ** 0.5
        return min_val, avg_val, std_dev
    
    def write_results(self, min_price, avg_price, std_dev_price, min_area, avg_area, std_dev_area):
        """Write results to file"""
        # Check if results folder exists
        if not os.path.exists(RESULTS_FOLDER):
            os.makedirs(RESULTS_FOLDER)
        
        commence_month = self.commence_month[5:]
        year = self.commence_month[:4]

        with open(f'{RESULTS_FOLDER}/ScanResult_{self.matric_num}.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Year', 'Month', 'town', 'Category', 'Value'])
            writer.writerow([year, commence_month, self.town, 'Minimum Price', min_price])
            writer.writerow([year, commence_month, self.town, 'Average Price', round(avg_price,2)])
            writer.writerow([year, commence_month, self.town, 'Standard Deviation of Price', round(std_dev_price,2)])
            writer.writerow([year, commence_month, self.town, 'Minimum Area', min_area])
            writer.writerow([year, commence_month, self.town, 'Average Area', round(avg_area,2)])
            writer.writerow([year, commence_month, self.town, 'Standard Deviation of Area', round(std_dev_area,2)])
        
        print(f"Results written to {RESULTS_FOLDER}/ScanResult_{self.matric_num}.csv")
