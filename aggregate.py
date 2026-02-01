'''
This script is for aggregating the 14k outputs files that were generated as results
from the Roboflow workflow runs.

The data will be aggregated into 15-minute chunks.
If I was at my desk or facing my monitor for any time in that chunk then that flag will be marked True.
Positions is prediction data for each sample in that 15-minute window (might be useful to show position in room over time).
'''
from tqdm import tqdm

import json
import os

OUTPUT_DIR = 'outputs'

outputFiles = sorted(list(map(
    lambda x: f'{OUTPUT_DIR}/{x}',
    filter(
        lambda x: x.endswith('.json'),
        os.listdir(OUTPUT_DIR),
    )
)))


def cleanup(data, timestamp):
    result = data.copy()
    if type(result) == list:
        result = result[0]

    if 'skipped' in result:
        return result

    try:
        if int(result['person_count']) == 1:
            for key in [
                'is_facing_monitor',
                'is_at_desk',
            ]:
                if key in result:
                    result[key] = 'true' in result[key][0]
    except Exception as e:
        print(f'Ran into issue while trying to parse this data: ')
        print(json.dumps(result, indent=2))
        raise e

    
    result['timestamp'] = timestamp
    
    return result


# Get all data for 15-minute windows
combined = {}
for path in outputFiles:
    timestring = path.split('/')[-1].split('.')[0]

    day = timestring.split('T')[0]
    hour = '-'.join(timestring.split('-')[:3])
    minute = timestring.split('-')[3]

    roundedMinute = int(minute) // 15
    qbin = f'{hour}-{roundedMinute*15}'

    with open(path) as file:
        data = cleanup(json.load(file), timestring)
    
    found = combined.get(qbin, []) or []
    combined[qbin] = found + [data]


# Aggregate and smooth data for the time blocks
simplified = {}
for qbin, combined in tqdm(combined.items()):
    if not combined or len(combined) < 10:
        continue
    
    maxPersonCount = 0
    wasAtDesk = False
    wasAtMonitor = False
    positions = []
    for item in combined:
        # max people seen in the window
        maxPersonCount = max(
            item.get('person_count', 0),
            maxPersonCount
        )

        # at desk/monitor
        deskVal = item.get('is_at_desk', False)
        if type(deskVal) == bool:
            wasAtDesk = wasAtDesk or deskVal

        monitorVal = item.get('is_facing_monitor', False)
        if type(monitorVal) == bool:
            wasAtMonitor = wasAtMonitor or monitorVal

        # positions
        if 'predictions' in item and 'predictions' in item['predictions']:
            if len(item['predictions']['predictions']) > 0:
                pred = item['predictions']['predictions'][0]
                image = item['output_image']
                if type(image) == list and len(image) > 0:
                    image = image[0]
                positions.append({
                    'timestamp': item['timestamp'],
                    'width': pred['width'],
                    'height': pred['height'],
                    'x': pred['x'],
                    'y': pred['y'],
                    'confidence': pred['confidence'],
                    'image': image,
                })

    simplified[qbin] = {
        'timebin': qbin,
        'total_samples': len(combined),
        'max_person_count': maxPersonCount,
        'was_at_desk': wasAtDesk,
        'was_at_monitor': wasAtMonitor,
        'positions': positions,
    }

# Dump the data
with open('simplified.json', 'w') as file:
    json.dump(simplified, file)

print('WROTE TO FILE!')
