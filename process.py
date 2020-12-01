
import argparse
import glob
import os

from PIL import Image
from tqdm import tqdm
import cv2

CASCADE_FILE = 'cascade/lbpcascade_animeface.xml'

def erase_exif_single(filename):
    '''overwrite the file without exif'''
    # convert to RGBA (original is P)
    with Image.open(filename).convert('RGBA') as img:
        data = img.getdata()
        mode = img.mode
        size = img.size
    with Image.new(mode, size) as img:
        img.putdata(data)
        img.save(filename)

def erase_exif(args):
    '''erase exif from images'''
    image_files = glob.glob(os.path.join(args.input, '*[!.json]'))
    for file in tqdm(image_files):
        erase_exif_single(file)

def convert_to_jpg_single(src, dst):
    src = Image.open(src).convert('RGBA')
    white = Image.new('RGB', src.size, (255, 255, 255))
    white.paste(src, mask=src.split()[3])
    white.save(dst, 'JPEG')

def convert_to_jpg(args):
    # create folder for jpg files
    jpg_folder = os.path.join(args.input, 'jpg')
    if not os.path.exists(jpg_folder):
        os.mkdir(jpg_folder)
    
    image_files = glob.glob(os.path.join(args.input, '*.png'))
    for file in tqdm(image_files):
        file_id = os.path.splitext(os.path.basename(file))[0]
        dst = os.path.join(jpg_folder, file_id+'.jpg')
        convert_to_jpg_single(file, dst)

def detect_face_lbpcascade_single(filename, face_folder, args):
    cascade = cv2.CascadeClassifier(CASCADE_FILE)
    img_png = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
    img = img_png[:, :, :3]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(args.min_size, args.min_size))

    face_images = []
    for (x, y, w, h) in faces:
        face_images.append(img_png[y:y+h, x:x+w, :])

    file_partial = os.path.basename(filename).split('.')
    num_faces = 0
    for face_image in face_images:
        out_filename = '.'.join(['_'.join([file_partial[0], str(num_faces)]), file_partial[1]])
        cv2.imwrite(os.path.join(face_folder, out_filename), face_image)
        num_faces += 1

def detect_face_lbpcascade(args):
    face_folder = os.path.join(args.input, 'face')
    if not os.path.exists(face_folder):
        os.mkdir(face_folder)

    image_files = glob.glob(os.path.join(args.input, '*.png'))
    for file in tqdm(image_files):
        detect_face_lbpcascade_single(file, face_folder, args)

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', '-i', default='data', help='Folder containing the images')
    parser.add_argument('--min-size', '-ms', default=24, type=int, help='Minimum face size')
    
    # flags to stop ignore processes
    parser.add_argument('--keepexif', action='store_true', help='Will not erase exif. Erasing exif will reduce data size so it is recommended.')
    parser.add_argument('--no-jpg', action='store_true', help='Will not convert to jpg')
    parser.add_argument('--no-face', action='store_true', help='Will not crop face')

    return parser.parse_args()

def main():

    args = get_args()
    assert args.min_size > 24, 'minimum size should be bigger than 24'

    print('Start processing images', end='\n\n')

    if not args.keepexif:
        print('--Erase EXIF data--')
        print('This will overwrite the images. Ctr+C to stop.')
        input('Press Enter to continue...')
        erase_exif(args)
        print('done')
    if not args.no_jpg:
        print(f'--Convert images to JPEG (saved to "{args.input}/jpg")--')
        convert_to_jpg(args)
        print('done')
    if not args.no_face:
        print(f'--Detect and crop faces from images (saved to "{args.input}/face")--')
        print('Using "lbpcascade_animeface.xml" from https://github.com/nagadomi/lbpcascade_animeface to detect faces')
        detect_face_lbpcascade(args)
        print('done')
    
    print('\nFinished processing images')

if __name__ == "__main__":
    main()