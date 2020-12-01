
# GFDataset

Codes for collecting and processing character images from the game [Granblue Fantasy](https://granbluefantasy.jp/en/).

## Udates

- 2020/12/01 - opened

## What

The codes will collect and process images of characters in [Granblue Fantasy](https://granbluefantasy.jp/en/) from the [wiki](https://gbf-wiki.com/).  
The `process.py` can be used to other images (but face detection only works with anime faces).

### Collected images

- Full body images

- Deformed images

- EX pose images

### Processing

- Erase EXIF

- Convert to JPEG with white background

- Detect and crop faces from images using [@nagadomi/lbpcascade_animeface](https://github.com/nagadomi/lbpcascade_animeface)

## Usage

- Clone repository and setup.

    ```console
    git clone https://github.com/STomoya/GFDataset.git
    cd GFDataset
    ./setup.sh
    ```

- Build Docker image

    ```console
    docker-compose build
    ```

- Scrape images from the [wiki](https://gbf-wiki.com/)

    Takes about an hour because it waits at least 1sec between each GET.
    Run with `--help` option to see options.  
    Default will save the images to `data` directory and erase the temporal files that are created during the process.

    ```console
    docker-compose run --rm python python scrape.py
    ```

- Process collected images

    Run with `--help` option to see options.
    Default will use the images in `data` directory.

    ```console
    docker-compose run --rm python python process.py
    ```

## License

[MIT](https://github.com/STomoya/GFDataset/blob/master/LICENSE)

## Author

[STomoya](https://github.com/STomoya)
