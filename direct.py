from PIL import Image
import cv2
import requests
import shutil
import pytesseract
import face_recognition as fr
import os
import numpy as np


def get_img(url):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print("Unable to retrieve image")
        return
    ext = url[url.rfind('.'):]
    filename = 'raw'+ext
    with open(filename, 'wb+') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
    print('received image')
    return ext


def read_ocr(ext):
    image = cv2.imread('raw'+ext, 1)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    gray = cv2.medianBlur(gray, 3)
    cv2.imwrite('gray'+ext, gray)
    text = pytesseract.image_to_string(Image.open('gray'+ext))
    text = text.replace('|', 'I')
    text = text.replace('\n', ' ')
    text = text.replace('[', '')
    return text


def get_encoded_faces():
    """
    looks through the faces folder and encodes all
    the faces

    :return: dict of (name, image encoded)
    """
    encoded = {}

    for dirpath, dnames, fnames in os.walk("./faces"):
        for f in fnames:
            if f.endswith(".jpg") or f.endswith(".png"):
                face = fr.load_image_file("faces/" + f)
                encoding = fr.face_encodings(face)[0]
                encoded[f.split(".")[0]] = encoding

    return encoded


FACES = get_encoded_faces()


def classify_faces(ext):
    """
    will find all of the faces in a given image and label
    them if it knows what they are

    :param im: str of file path
    :return: list of face names
    """
    global FACES
    faces = FACES
    img = cv2.imread('raw'+ext, 1)
    print('ok')
    if img is None:
        print("Invalid image array")
        return

    faces_encoded = list(faces.values())
    known_face_names = list(faces.keys())

    face_locations = fr.face_locations(img)
    unknown_face_encodings = fr.face_encodings(img, face_locations)

    face_names = []
    for face_encoding in unknown_face_encodings:
        # See if the face is a match for the known face(s)
        matches = fr.compare_faces(faces_encoded, face_encoding)
        name = "Unknown"

        # use the known face with the smallest distance to the new face
        face_distances = fr.face_distance(faces_encoded, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        face_names.append(name)

    return face_locations, face_names
