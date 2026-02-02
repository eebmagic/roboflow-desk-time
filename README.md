# Roboflow Desk Time

This project processes and presents insights from a large set of of images taken from a camera setup in my apartment.

It uses [this Roboflow workflow](https://app.roboflow.com/workflows/embed/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ3b3JrZmxvd0lkIjoibmZnVW90cE9NbWhzMk83RE5QWlYiLCJ3b3Jrc3BhY2VJZCI6ImxXTWdTSHU0SjZXYUUyUllBRnlnb3prRzMwNTMiLCJ1c2VySWQiOiJsV01nU0h1NEo2V2FFMlJZQUZ5Z296a0czMDUzIiwiaWF0IjoxNzcwMDAxOTQyfQ.ugb4FzJVKtBbr8c44VmIn_4N-cnkGzVsizZ4K6VcFxY) to process all of the images. 

The Roboflow workflow:
1. Takes an image as input
2. Uses the roboflow object detection model to check if a person(s) is in frame
3. If a single person is present, then ask Gemini-3-flash if I'm at my desk and if I'm facing a monitor
4. Return the bool flags and cropped image of myself

I ran this workflow on 14,661 images over ~5 days. 
Then made an `aggregate.py` script to simplify and merge the responses into 15-minute blocks.

The `index.html` uses [Chart.js](https://www.chartjs.org/) to present a few charts and animation.

You can view the dashboard at [this GitHub page](https://eebmagic.github.io/roboflow-desk-time/)
