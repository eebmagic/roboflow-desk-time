# Roboflow Desk Time

This project processes and presents insights from a large set of of images taken from a camera setup in my apartment.

It uses [this Roboflow workflow](https://app.roboflow.com/workflows/embed/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ3b3JrZmxvd0lkIjoibmZnVW90cE9NbWhzMk83RE5QWlYiLCJ3b3Jrc3BhY2VJZCI6ImxXTWdTSHU0SjZXYUUyUllBRnlnb3prRzMwNTMiLCJ1c2VySWQiOiJsV01nU0h1NEo2V2FFMlJZQUZ5Z296a0czMDUzIiwiaWF0IjoxNzcwMDAxOTQyfQ.ugb4FzJVKtBbr8c44VmIn_4N-cnkGzVsizZ4K6VcFxY) that I made to process all of the images. 

The Roboflow workflow:
1. Takes an image as input
2. Uses the roboflow object detection model to check if a person(s) is in frame
3. If a single person is present, then ask Gemini-3-flash if I'm at my desk and if I'm facing a monitor
4. Return the bool flags and cropped image of myself

I ran this workflow on 14,661 images over ~5 days. 
Then made an `aggregate.py` script to simplify and merge the responses into 15-minute blocks.

The `index.html` uses [Chart.js](https://www.chartjs.org/) to present a few charts and animation.

You can view the dashboard at [this GitHub page](https://eebmagic.github.io/roboflow-desk-time/)


## Exploration Notebooks
### Find Night Images Std Value.ipynb
My camera was taking pictures every 20s for a few random 48hr stretches. 
As a result a lot of the images are at nighttime and are pitch-black and not even worth passing to the Roboflow workflow for processing.

In this jupyter notebook I load the images and plot and histogram the stddev of pixel values.
Then based off those two charts I picked a cutoff of $\delta = 15$ for the best threshold for what is likely a nighttime image that can be disregarded.

This $\delta$ was then used in the `process.py` script which checked all the images in a thread worker pool before uploading them to the workflow endpoint.

### Generate Average Room Image.ipynb
The Roboflow workflow returns cropped images of a person in frame of the inputs.
I wanted to use these in some sort of visual for my position over time in my apartment.

Instead of using a randomly sampled image I wanted to instead use an "average" image of my room under good lighting conditions.

This may have been a bad choice because the data is from two different weeks that are ~6 months apart and there have been some small changes to my room, resulting in some ghosting on the image. 
Also there is some oversampling resulting from two days where I recorded images at a doubled rate.
But I think the resulting image is still a little better than a single random image, so I used it as the background on the `Position Tracker` chart on the dashboard. 
