import time

from src.config import PDF_PATH, QUESTION_START_PAGE, QUESTION_END_PAGE, ANSWER_START_PAGE, ANSWER_END_PAGE, \
    QUESTION_RANGE, WEB_FORM_URL, USERNAME, PASSWORD, CATEGORY
from src.fill_form import setup_webdriver, open_url, login, navigate_to_question_creation, fill_question
from src.parse import parse_questions, parse_answers, parse_reasons
from src.utils import extract_and_clean_text, merge_answers_with_questions, identify_missing_elements


def main():
    cleaned_questions_text = extract_and_clean_text(PDF_PATH, QUESTION_START_PAGE, QUESTION_END_PAGE)
    cleaned_answers_text = extract_and_clean_text(PDF_PATH, ANSWER_START_PAGE, ANSWER_END_PAGE)

    questions = parse_questions(cleaned_questions_text)
    # for question in questions:
    #     if question['question'] == 'Which subnet mask is assigned to this address?' and question['number'] == '22':
    #       question['number'] = '34'
    #     elif question['question'] == 'Which directive in the /etc/ssh/sshd_config file can do this?' and question['number'] == '22':
    #       question['number'] = '41'
    # questions = [q for q in questions if q['number'] != "1"]
    print(questions)
    answers = parse_answers(cleaned_answers_text)
    questions_with_answers = merge_answers_with_questions(questions, answers)
    missing_questions, missing_answers = identify_missing_elements(questions_with_answers, QUESTION_RANGE)
    reasons = parse_reasons(questions_with_answers, cleaned_answers_text)
    if reasons is None:
        return
    if missing_questions:
        print(f"Questions missing from parsing: {', '.join(missing_questions)}")
        # return
    else:
        print("All questions parsed successfully.")

    if missing_answers:
        print(f"Questions missing answers: {', '.join(missing_answers)}")
        # return
    else:
        print("All questions have answers.")

    # Print parsed questions for debugging
    # print(questions_with_answers)
    driver = setup_webdriver()
    category = CATEGORY
    try:
        open_url(driver, WEB_FORM_URL)
        login(driver, USERNAME, PASSWORD)
        print(questions_with_answers)
        print(reasons)
        for question in questions_with_answers:
            question_number = question['number']
            reason = next((r for r in reasons if str(r['number']) == question_number), None)
            navigate_to_question_creation(driver)
            fill_question(driver, question, category, reason)
            time.sleep(1)

        print("Form submission complete. Keeping the browser open for manual inspection.")
        while True:
            pass  # Infinite loop to keep the browser open
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing browser.")
        driver.quit()


if __name__ == "__main__":
    main()
