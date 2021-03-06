import cv2 as cv
import numpy as np
from PIL import Image

from Exam_container import Exam_container
from task_types import Task_type
from checkboxchecker import find_checkboxes
from letterdetection import letter_slicer
from Task import Task
Image.MAX_IMAGE_PIXELS = None

def autocorrect_exams(exam_container: Exam_container) -> Exam_container:
    '''
    Function for detecting given answers in tasks and giving points.

    This function is the main interface for the ai, it needs a filled out exam_container
    with a correct_exam and a list of student_exams.

    Parameters:
    exam_container (Exam_container): Exam container filled with a correct_exam and exams that
    need correction.

    Returns:
    exam_container (Exam_container): Returns the samme exam_container as the input but with
    filled actual_answer in the student_exams and corresponding points for them.

    Raises:
    There are several errors that can be raises, see validate_exam_container below
    '''

    try:
        validate_exam_container(exam_container, True)
    except Exception as error:
        raise error

    for exam in exam_container.student_exams:
        image = cv.cvtColor(np.array(exam.image), cv.COLOR_RGB2BGR)

        for task in exam.tasks:
            roi = [task.x,task.y,task.x+task.width,task.y+task.height]

            if task.type == Task_type.SINGLE_CHOICE:
                task.actual_answer, img = find_checkboxes(image, roi, task, True)
                exam.image_modified.paste(img, (task.x, task.y))
                task = calculate_points_checkbox(task, True)

            elif task.type == Task_type.MULTIPLE_CHOICE:
                task.actual_answer, img = find_checkboxes(image, roi, task, True)
                exam.image_modified.paste(img, (task.x, task.y))
                task = calculate_points_checkbox(task, False)

            elif task.type == Task_type.NUMBER:
                task.actual_answer = letter_slicer(image, roi, task.type)
                task = calculate_points_text(task)

            elif task.type == Task_type.TEXT:
                task.actual_answer = letter_slicer(image, roi, task.type)
                task = calculate_points_text(task)

            elif task.type == Task_type.TEXT_NO_NUMBERS:
                task.actual_answer = letter_slicer(image, roi, task.type)
                task = calculate_points_text(task)

            elif task.type == Task_type.SHAPE:
                pass

            else:
                raise ValueError("Unknown Task Type")

    return exam_container

def autodetect_expected_answers(exam_container: Exam_container):
    '''
    Function for detecting an already filled out correct_exam.

    This function will try to detect and fill the expected_answer of the correct_exam.

    Parameters:
    exam_container (Exam_container): An exam_container filled with just a picture of the
    model solution and the corrdinates of the selected tasks.

    Returns:
    exam_container (Exam_container): The same exam_container but with filled expected_answer.

    Raises:
    There are several errors that can be raises, see validate_exam_container below
    '''

    try:
        validate_exam_container(exam_container, False)
    except Exception as error:
        raise error

    image = cv.cvtColor(np.array(exam_container.correct_exam.image), cv.COLOR_RGB2BGR)

    for task in exam_container.correct_exam.tasks:
        task_type = task.type
        roi = [task.x,task.y,task.x+task.width,task.y+task.height]


        if task_type == Task_type.SINGLE_CHOICE:
            task.expected_answer, img = find_checkboxes(image, roi, task, False)
            exam_container.correct_exam.image_modified.paste(img, (task.x, task.y))

        elif task_type == Task_type.MULTIPLE_CHOICE:
            task.expected_answer, img = find_checkboxes(image, roi, task, False)
            exam_container.correct_exam.image_modified.paste(img, (task.x, task.y))

        elif task_type == Task_type.NUMBER:
            task.expected_answer = letter_slicer(image, roi, task_type)

        elif task_type == Task_type.TEXT:
            task.expected_answer = letter_slicer(image, roi, task_type)

        elif task_type == Task_type.TEXT_NO_NUMBERS:
            task.expected_answer = letter_slicer(image, roi, task_type)

        elif task_type == Task_type.SHAPE:
            pass

        else:
            raise ValueError("Unknown Task Type")

    return exam_container


def calculate_points_checkbox(task: Task, is_single_choice : bool)-> Task:
    '''
    Function for calculating points for a checkbox task.
    Min 0 points are allowed

    Parameters:
    task (Task): Single task that needs its points calculated
    is_single_choice (bool): Switch if several marks have been set

    Returns:
    task (Task): Single taks that has its points calculated

    '''
    task.points = task.max_points
    if is_single_choice:
        if task.actual_answer != task.expected_answer:
            task.points = 0
    else:
        if len(task.actual_answer) <= 0:  # No answer given
            task.points = 0
        else:
            for index, answer in enumerate(task.expected_answer.split(",")):
                if index >= len(task.actual_answer):
                    task.points -= len(task.expected_answer) - len(task.actual_answer)
                    break
                if answer != task.actual_answer[index]:
                    task.points -= task.deduction_per_error

    if task.points < 0:
        task.points = 0
    return task

def calculate_points_text(task: Task)-> Task:
    '''
    Function for calculating points for a text task.
    Min 0 points are allowed

    Parameters:
    task (Task): Single task that needs its points calculated

    Returns:
    task (Task): Single taks that has its points calculated
    '''
    task.points = task.max_points
    if len(task.actual_answer) <= 0:
        task.points = 0
    else :
        for index, answer in enumerate(list(task.expected_answer)):
            if index >= len(task.actual_answer):
                task.points -= len(task.expected_answer) - len(task.actual_answer)
                break
            if answer != task.actual_answer[index]:
                task.points -= task.deduction_per_error
    if task.points < 0:
        task.points = 0
    return task


def validate_exam_container(exam_container: Exam_container, check_student_exams : bool):
    '''
    Function to validate the exam_container given as parameter.

    This function will test if the given parameters are passing for expected parameters.
    If not an error will be raised

    Parameters:
    exam_container (Exam_container):
    check_student_exams (bool):
    '''

    if exam_container.correct_exam.image.width <= 1 or \
        exam_container.correct_exam.image.height <= 1:
        raise FileNotFoundError("Image too small")

    for index, task in enumerate(exam_container.correct_exam.tasks):
        if task.x < 0 or task.y < 0:
            raise ValueError("Task ", str(index), " has negativ coordinates.")

        if task.width <= 0 or task.height <= 0:
            raise ValueError("Task ", str(index), " has negativ dimensions.")

        if task.max_points < 0:
            raise ValueError("Task ", str(index), " has a negativ of maximum points")

        if task.deduction_per_error < 0:
            raise ValueError("In task ", str(index),
                    " deduction_per_error should be positiv (or zero)")


    if check_student_exams:
        for exam_num, exam in enumerate(exam_container.student_exams):

            if exam.image.width <= 1 or exam.image.height <= 1:
                raise FileNotFoundError("Student exam #", exam_num, " image too small")

            # Check every exam task
            for task_num, task in enumerate(exam.tasks):

                if task.x < 0 or task.y < 0:
                    raise ValueError("Task ", str(task_num), " in exam #", str(exam_num),
                            " has negativ coordinates.")

                if task.width <= 0 or task.height <= 0:
                    raise ValueError("Task ", str(task_num), " in exam #", str(exam_num),
                            " has negativ dimensions.")

                if task.max_points < 0:
                    raise ValueError("Task ", str(task_num), " in exam #", str(exam_num),
                            " has a negativ of maximum points")

                if task.deduction_per_error < 0:
                    raise ValueError("In task ", str(task_num), " in exam #", str(exam_num),
                            " deduction_per_error should be positiv (including zero)")

                if len(task.expected_answer) <= 0:
                    raise ValueError("Task ", str(task_num), " in exam #", str(exam_num),
                            " has no expected answer")
