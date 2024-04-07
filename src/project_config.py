SPLIT_DATA_FOLDER = 'split_data'
ORIGINAL_DATA_FILE = 'data/ResalePricesSingapore.csv'
SORTED_DATA_FILE = 'data/ResalePricesSingapore_sorted.csv'
RESULTS_FOLDER = 'results'
MAX_FILE_LINE = 50000
MAPPER = {
    'town':{
        '0': 'ANG MO KIO',
        '1': 'BEDOK',
        '2': 'BUKIT BATOK',
        '3': 'CLEMENTI',
        '4': 'CHOA CHU KANG',
        '5': 'HOUGANG',
        '6': 'JURONG WEST',
        '7': 'PUNGGOL',
        '8': 'WOODLANDS',
        '9': 'YISHUN',
    }
}

RELAVANT_COLS = (
    'month',
    'town',
    'floor_area_sqm',
    'resale_price'
)

ZONE_MAP_COLS = (
    'month',
    'floor_area_sqm',
    'resale_price'
)
