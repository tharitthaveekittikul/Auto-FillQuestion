from src.cleaning_data import clean_text
from src.extract import extract_text_from_pdf


def extract_and_clean_text(pdf_path, start_page, end_page):
    raw_text = extract_text_from_pdf(pdf_path, start_page, end_page)
    return raw_text


def merge_answers_with_questions(questions, answers):
    for question in questions:
        question_number = question['number']
        if question_number in answers:
            question['answer'] = answers[question_number]
        else:
            question['answer'] = None
    return questions


def identify_missing_elements(questions, question_range):
    all_question_numbers = set(str(i) for i in range(1, question_range + 1))
    # all_question_numbers = set(str(i) for i in range(49, question_range + 1))
    parsed_question_numbers = set(q['number'] for q in questions)
    missing_questions = all_question_numbers - parsed_question_numbers
    missing_answers = [q['number'] for q in questions if q['answer'] is None]
    return missing_questions, missing_answers
