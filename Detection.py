import cv2 as cv
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import torch
import datetime
import pandas as pd

CLASSES_NAMES = ['boots', 'dust mask', 'glass', 'gloves', 'helmet', 'person', 'safety vest']


def detect_image(model, image_path, image_area, result_text):
    # Load image
    origin_image = cv.imread(image_path, cv.IMREAD_COLOR)
    display_image = cv.cvtColor(origin_image, cv.COLOR_BGR2RGB)

    # Detect with YOLO model
    results = model(origin_image)[0]

    # Extract the result
    results = results.cpu().numpy()
    boxes = results.boxes
    position = boxes.xyxy.astype(int)
    classes = boxes.cls.astype(int)
    scores = boxes.conf

    # Filter detections based on the confidence threshold
    valid_indices = np.where(scores > 0.5)[0]
    classes = classes[valid_indices]
    scores = scores[valid_indices]

    # Text output
    unique_cls, counts = np.unique(classes, return_counts=True)
    result_text.append('Detect: ')
    for cls, count in zip(unique_cls, counts):
        result_text.append(f'    {model.names[cls].title()}: {count}')

    # Draw bounding box
    for i, cls in enumerate(classes):
        if scores[i] > 0.5:
            x1, y1, x2, y2 = position[i]
            cv.rectangle(display_image, (x1, y1), (x2, y2), (0, 255, 0))
            cv.putText(display_image, f'{model.names[cls].title()}', (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                       (0, 255, 0), 1)

    # Convert the image back to QImage for display
    height, width, channel = display_image.shape
    bytes_per_line = channel * width
    q_image = QImage(display_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
    image_area.setPixmap(QPixmap.fromImage(q_image))

    # Convert to QPixmap and scale
    pixmap = QPixmap.fromImage(q_image)
    scaled_pixmap = pixmap.scaled(image_area.width(), image_area.height(), Qt.KeepAspectRatio)

    # Display scaled image
    image_area.setPixmap(scaled_pixmap)


def detect_video(model, video_path, mode, timer, result_text, video_output_label, stacked_widget):
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video stream or file")
        return
    print('What mode: ', mode)
    if mode == 'Normal':
        timer.timeout.connect(lambda: normal_mode(model, cap, result_text, video_output_label, stacked_widget, timer))
    elif mode == 'Inspection':
        person_index = 1
        output_text = None
        last_person_detected = False

        def inspection_callback():
            nonlocal person_index, output_text, last_person_detected
            person_detected, output_text = inspection_mode(model, cap, result_text, video_output_label, stacked_widget,
                                                           timer, output_text, person_index)
            if not person_detected and last_person_detected:
                person_index += 1
            last_person_detected = person_detected

        timer.timeout.connect(inspection_callback)
    elif mode == 'Detect':
        timer.timeout.connect(
            lambda: worker_detection_mode(model, cap, result_text, video_output_label, stacked_widget, timer))
    elif mode == 'Tracking':
        delay_time = 0
        number_detection = 0
        dataframe = pd.DataFrame()

        def tracking_callback():
            nonlocal delay_time, number_detection, dataframe
            delay_time, number_detection, dataframe = tracking_construction_mode(model, cap, result_text,
                                                                                 video_output_label,
                                                                                 stacked_widget, timer, delay_time,
                                                                                 number_detection, dataframe)

        timer.timeout.connect(tracking_callback)
    timer.start(1000 // int(cap.get(cv.CAP_PROP_FPS)))  # Update at the rate of FPS


# Normal mode
def normal_mode(model, cap, result_text, video_output_label, stacked_widget, timer):
    ret, frame = cap.read()
    if not ret:
        timer.stop()
        cap.release()
        result_text.append("Stopped video playback")
        return

    results = model(frame)[0]
    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = map(int, result)
        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv.putText(frame, results.names[int(class_id)].upper(), (x1, y1 - 10), cv.FONT_HERSHEY_COMPLEX, 0.6,
                   (0, 255, 0), 1)

    # Convert to QImage and set on label
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    q_image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)
    video_output_label.setPixmap(pixmap.scaled(video_output_label.size(), Qt.KeepAspectRatio))
    stacked_widget.setCurrentWidget(video_output_label)


# Mode 1: Inspection
def check_overlap(r1, r2):
    return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])


def create_ppe_status_string(ppe_status):
    status_list = []
    for item, status in ppe_status.items():
        if status:
            status_list.append(f"{item} <span style='color:green;'>&#10004;</span>")
        else:
            status_list.append(f"{item} <span style='color:red;'>&#10008;</span>")
    return '<br>'.join(status_list)


def ppe_inspection(results):
    """
    This function inspects PPE for workers.
    Parameters:
        - results (YOLO object): the results of YOLO model prediction for a frame.
    Returns:
        - dict: A dictionary where each key is a tuple of the position of the person and the value is a list of their overlapping classes.
    """
    results = results.cpu().numpy()
    boxes = results.boxes
    positions = boxes.xyxy.astype(int)
    classes = boxes.cls.astype(int)
    scores = boxes.conf

    # Filter detections based on the confidence threshold
    valid_indices = np.where(scores > 0.5)[0]
    positions = positions[valid_indices]
    classes = classes[valid_indices]
    scores = scores[valid_indices]

    # Check if there are any persons
    person_indices = np.where(classes == 5)[0]
    person_boxes = positions[person_indices]

    # Initialize dictionary to store PPE status
    ppe_status = {}
    ppe_classes = [1, 2, 3, 4, 6]  # Assuming these are the indices for PPE classes

    # Check overlap for each detected person
    for idx, person_box in enumerate(person_boxes):
        classes_overlap = []
        for i, other_box in enumerate(positions):
            if i not in person_indices and check_overlap(person_box, other_box):
                classes_overlap.append(classes[i])

        # Convert person_box to a tuple, so it can be used as a dictionary key
        person_box_tuple = tuple(person_box.astype(int))

        # Convert classes_overlap for easily visualizing
        classes_overlap = np.unique(classes_overlap)
        dict_classes = {CLASSES_NAMES[cls].title(): (cls in classes_overlap) for cls in ppe_classes}

        # Append person position and overlapping classes to the ppe_status dictionary
        ppe_status[person_box_tuple] = dict_classes

    return ppe_status


y_offset_start = 800
line_height = 50
person_index = 1


def inspection_mode(model, cap, result_text, video_output_label, stacked_widget, timer, output_text=None,
                    person_index=0):
    ret, frame = cap.read()
    if not ret:
        timer.stop()
        cap.release()
        result_text.append("Stopped video playback")
        return False, output_text

    # Define the region of interest
    roi = frame[17:1080, 610:1235]

    # Detect with YOLO model
    detects = model(roi)[0]
    detects = detects.cpu().numpy()
    classes = detects.boxes.cls.astype(int)

    person_detected = False
    if np.any(classes == 5):  # Check if 'person' class is detected
        ppe_status = ppe_inspection(detects)
        y_offset = y_offset_start
        for person, status in ppe_status.items():
            if person[1] < 50 and person[3] > 1050:  # Detect for only person in the region of interest
                person_detected = True
                # Output in result
                output_text = create_ppe_status_string(status)
                result_text.clear()
                result_text.append(f'Person #{person_index}')
                result_text.append(output_text)
                # Output in frame
                for cls, retval in status.items():
                    color = (0, 255, 0) if retval else (0, 0, 255)
                    cv.putText(frame, f'{cls}'.upper(), (30, y_offset), cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    y_offset += line_height

    if not person_detected and output_text is not None:
        result_text.clear()
        output_text = None

    # Convert to QImage and set on label
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    q_image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)
    video_output_label.setPixmap(pixmap.scaled(video_output_label.size(), Qt.KeepAspectRatio))
    stacked_widget.setCurrentWidget(video_output_label)

    return person_detected, output_text


# Mode 2: Worker detection
def Show_Status_and_Alert(img, person_tracking_ppe, number_worker, number_normal_person, show_worker=True,
                          show_normal_person=True):
    '''
    This function will show the status of PPE for each person, alert when appearing normal person,also count the
    number of workers
    Parameters:
        - img (np.array): which is a frame or image
        - person_tracking_ppe (dict): which is a dictionary containing the coordinates of the bounding box for each person
    with the status of the PPE Return:
        - number_worker (int): this function also return the number of workers appearing in the frame
        - number_normal_person (int): this function also return the number of normal person appearing in the frame
    '''

    # Detect Worker based on the PPE status
    for person, ppe_status in person_tracking_ppe.items():

        # Print the status of PPE for each person
        # Check the normal personMode3_test_1.mov
        if (ppe_status['Safety Vest'] == False) and (ppe_status['Helmet'] == False):
            # Track the normal person
            normal_person = img[person[1]:person[3], person[0]:person[2]]
            number_normal_person += 1
            if show_normal_person:
                cv.rectangle(img, (person[0], person[1]), (person[2], person[3]), (0, 0, 255), 2)
                cv.putText(img, "ALERT !!!", (person[0] + 10, person[1] + 100),
                           cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Track the worker with PPE
            worker = img[person[1]:person[3], person[0]:person[2]]
            number_worker += 1
            if show_worker:
                cv.rectangle(img, (person[0], person[1]), (person[2], person[3]), (0, 255, 0), 2)
                cv.putText(img, "Worker", (person[0] - 20, person[1] - 10),
                           cv.FONT_HERSHEY_COMPLEX, 0.6 ,(0, 255, 0), 2)

    return number_worker, number_normal_person


def worker_detection_mode(model, cap, result_text, video_output_label, stacked_widget, timer):
    ret, frame = cap.read()
    if not ret:
        timer.stop()
        cap.release()
        result_text.append("Stopped video playback")
        return

    # Initialize
    number_worker = 0
    number_normal_person = 0

    # Detect with YOLO model
    detects = model(frame)[0]

    # Check PPE
    person_tracking_ppe = ppe_inspection(detects)

    # Show the status and alert when appearing normal person
    number_worker, number_normal_person = Show_Status_and_Alert(frame, person_tracking_ppe, number_worker,
                                                                number_normal_person)

    # Show the number of workers and number of normal persons
    cv.putText(frame, "Number of workers: " + str(number_worker), (30, 30),
               cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
    cv.putText(frame, "Number of normal persons: " + str(number_normal_person), (30, 60),
               cv.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

    # Convert to QImage and set on label
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    q_image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)
    video_output_label.setPixmap(pixmap.scaled(video_output_label.size(), Qt.KeepAspectRatio))
    stacked_widget.setCurrentWidget(video_output_label)


# Mode 3: Tracking Worker in construction
def result_table(number_worker, require_number):
    current_datetime = datetime.datetime.now()

    formated_datetime = current_datetime.strftime("%B %d, %Y %H:%M:%S")

    data = {
        "Date time": [],
        "Number of workers": [],
        "State": []
    }

    if number_worker == require_number:

        data["Date time"].append(formated_datetime)
        data["Number of workers"].append(number_worker)
        data["State"].append("Normal")

    elif number_worker < require_number:

        data["Date time"].append(formated_datetime)
        data["Number of workers"].append(number_worker)
        data["State"].append("Missing")

    else:
        data["Date time"].append(formated_datetime)
        data["Number of workers"].append(number_worker)
        data["State"].append("Redundant")

    return data


def tracking_construction_mode(model, cap, result_text, video_output_label, stacked_widget, timer, delay_time,
                               number_detection, dataframe):
    ret, frame = cap.read()
    if not ret:
        timer.stop()
        cap.release()
        result_text.append("Stopped video playback")
        result_text.append(f"Tracking file have been saved at 'Tracking_State.csv'")
        return delay_time, number_detection, dataframe

    number_normal_person = 0
    delay_time += 1
    number_worker = 0

    # Detect with YOLO model
    detects = model(frame)[0]

    # Check PPE
    person_tracking_ppe = ppe_inspection(detects)

    # Show the status and alert when appearing normal person
    number_worker, number_normal_person = Show_Status_and_Alert(frame, person_tracking_ppe, number_worker,
                                                                number_normal_person)
    if delay_time > 33:
        number_detection += 1

        # Take the information to the dataframe and save it to csv file, The required number of workers in the area is 5
        data = result_table(number_worker, require_number=5)
        df1 = pd.DataFrame(data)
        dataframe = pd.concat([dataframe, df1])
        dataframe.to_csv('Tracking_State.csv', index=False)

        delay_time = 0

    cv.putText(frame, "Number of workers: " + str(number_worker), (30, 30),
               cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    cv.putText(frame, "Number of detection " + str(number_detection), (30, 90),
               cv.FONT_HERSHEY_COMPLEX, 1, (200, 0, 0), 2)

    # Convert to QImage and set on label
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    q_image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(q_image)
    video_output_label.setPixmap(pixmap.scaled(video_output_label.size(), Qt.KeepAspectRatio))
    stacked_widget.setCurrentWidget(video_output_label)

    return delay_time, number_detection, dataframe
