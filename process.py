# NOTE: MUST use python3.12
from inference_sdk import InferenceHTTPClient
from tqdm import tqdm
import cv2
import numpy as np
from dotenv import load_dotenv

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import math
import json
import os

load_dotenv()

API_KEY = os.getenv("ROBOFLOW_API_KEY")
IMAGE_DIR = 'images'
OUTPUT_DIR = 'outputs'

CLIENT = InferenceHTTPClient(
    # api_url="https://serverless.roboflow.com",
    api_url="http://localhost:9001",
    api_key=API_KEY
)

def should_discard_image(image_path, std_thresh=15):
    '''
    Some of the images are taken in the dark at night, these should not be processed.

    This func will check for the stddev of pixel values and if there is a concentration
    on dark pixels then the image can be discarded.

    std_thresh: number: The stddev value under which an image should be considered a dark night image.
                NOTE: This value is determined in the "Find Night Images Std Value.ipynb" notebook.
    '''

    image = cv2.imread(image_path)
    stddev = np.std(image)

    return stddev < std_thresh

# Build list of images that need to be processed
## Load sets of images and already completed outputs
images = sorted(list(map(
    lambda x: '.'.join(x.split('.')[:-1]),
    filter(
        lambda x: x.endswith('.jpg'),
        os.listdir(IMAGE_DIR),
    )
)))
outputs = sorted(list(map(
    lambda x: '.'.join(x.split('.')[:-1]),
    filter(
        lambda x: x.endswith('.json'),
        os.listdir(OUTPUT_DIR),
    )
)))

print('Images found:\t\t', len(images), images[:5])
print('Output files found:\t', len(outputs), outputs[:5])

## Determine which images have yet to be processed
imageSet = set(images)
assert len(imageSet) == len(images)
outputSet = set(outputs)
assert len(outputSet) == len(outputs)

TRUNCATE = 50
imagesToProcess = sorted(list(imageSet - outputSet))
# imagesToProcess = sorted(list(imageSet - outputSet))
imagesToProcess = sorted(list(imageSet - outputSet))[:TRUNCATE]
print('\nImages to process:\t', len(imagesToProcess), imagesToProcess[:5])


# reallyProcess = []
# black = []
# for im in tqdm(imagesToProcess):
#     path = f'{IMAGE_DIR}/{im}.jpg'
#     if not should_discard_image(path):
#         reallyProcess.append(im)
#     else:
#         black.append(im)
    
# print(len(reallyProcess), reallyProcess[:5])
# print(len(black), black[:5])

# Set aside dark images
## Use a worker pool to evaluate all the image so we can ignore (almost) completely black images from at night
def process_image(image):
    '''
    Worker function for the intial evalutation pool.
    Checks if an image is mostly black (nighttime) and should be discarded.
    '''
    try:
        path = f'{IMAGE_DIR}/{image}.jpg'
        result = should_discard_image(path)

        return image, 'success', result
    except Exception as e:
        return image, 'error', str(e)

'''
FOR 14,661 IMAGES (on my macbook):
 1 worker  | 1:22
 5 workers | 0:31
10 workers | 0:24
20 workers | 0:19
'''
max_workers = 10
thread_results = {
    'success': {},
    'skipped': {},
    'errors': {},
}

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {
        executor.submit(process_image, img): img
        for img in imagesToProcess
    }

    print(f'\nEvaluating images to remove night images ({max_workers} workers):')
    for future in tqdm(as_completed(futures), total=len(futures)):
        img, status, result = future.result()
        thread_results[status if status in thread_results else 'errors'][img] = result
        if status == 'error':
            print(f'Error processing image: {img}: {result}')

print(f"\nProcessing complete!")
print(f"Success: {len(thread_results['success'])}")
print(f"Skipped: {len(thread_results['skipped'])}")
print(f"Errors: {len(thread_results['errors'])}")

# Any black images will get an output json file like this
BLACK_IMAGE_PAYLOAD = {
    'skipped': True,
    'message': 'The process.py script determined that this image is mostly black and should be ignored',
    'eval_time_utc': datetime.now(timezone.utc).isoformat(),
}

shouldDiscardCount = sum(thread_results['success'].values())
print('\nTotal number of images to discard: ', shouldDiscardCount)

discardWrites = 0
requestImages = []
for img, shouldDiscard in thread_results['success'].items():
    path = f'{OUTPUT_DIR}/{img}.json'
    if shouldDiscard:
        payload = BLACK_IMAGE_PAYLOAD.copy()
        payload['image'] = img

        with open(path, 'w') as file:
            json.dump(payload, file)
        discardWrites += 1
    else:
        requestImages.append(img)
    
print(f'Wrote output files for {discardWrites} / {shouldDiscardCount} of the dark images')

# Connect to workflow

def process_roboflow(image, client):
    '''
    Worker function for the Roboflow API call pool.
    Makes a request to the server (running in local docker container) for each image.
    '''
    try:
        imagePath = f'{IMAGE_DIR}/{image}.jpg'
        result = client.run_workflow(
            workspace_name="experiments-zmzdu",
            workflow_id="desk-time",
            images={
                "image": imagePath,
            },
            use_cache=True
        )

        resultPath = f'{OUTPUT_DIR}/{image}.json'
        with open(resultPath, 'w') as file:
            json.dump(result, file)

        return imagePath, 'success', f'Wrote to file: {resultPath}'
    except Exception as e:
        return imagePath, 'error', str(e)


'''
FOR 50 IMAGES (through docker container):
 1 worker  | 1:55
 5 workers | 0:42
10 workers | 0:52
20 workers | 0:54
'''
robo_max_workers = 10
robo_thread_results = {
    'success': {},
    'skipped': {},
    'errors': {},
}

with ThreadPoolExecutor(max_workers=robo_max_workers) as executor:
    futures = {
        executor.submit(process_roboflow, img, CLIENT): img
        for img in requestImages
    }

    print(f'\nSending inference requests to Roboflow server ({robo_max_workers} workers):')
    for future in tqdm(as_completed(futures), total=len(futures)):
        img, status, result = future.result()
        robo_thread_results[status if status in thread_results else 'errors'][img] = result
        if status == 'error':
            print(f'Error processing image: {img}: {result}')

print(f"\nRoboflow call pool complete!")
print(f"Success: {len(robo_thread_results['success'])}")
print(f"Skipped: {len(robo_thread_results['skipped'])}")
print(f"Errors: {len(robo_thread_results['errors'])}")

print('\nDONE!')
