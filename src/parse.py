import json
import pprint
import re

import openai

from src.config import QUESTION_RANGE, QUESTION_START_PAGE, QUESTION_END_PAGE, ANSWER_START_PAGE, \
    ANSWER_END_PAGE, PDF_PATH
from src.utils import extract_and_clean_text, merge_answers_with_questions, identify_missing_elements

openai.api_key = "<your-api-key>"

def parse_questions(text):
    # Remove unwanted line breaks within questions and choices
    text = text.replace(" \n", " ").replace("\n", " ")
    # Define the regular expression patterns
    question_pattern = re.compile(r'(\d+\s*\.\s+.*?)(?=\d+\s*\.\s|\Z)', re.DOTALL)
    answer_choices_pattern = re.compile(r'([A-F])\.\s+(.*?)(?=\s+[A-F]\.\s|$)', re.DOTALL)
    question_number_pattern = re.compile(r'(\d+)\s*\.')

    # Find all questions
    questions = question_pattern.findall(text)

    # Extract questions and answer choices
    parsed_questions = []
    for question in questions:
        number_match = question_number_pattern.match(question)
        if number_match:
            question_number = number_match.group(1)
        else:
            question_number = None

        # Extract the question text without the number
        question_text_match = re.split(r'\s+[A-G]\.\s', question, maxsplit=1)
        question_text = question_text_match[0].strip()
        if question_number:
            question_text = question_text[len(question_number) + 1:].strip()

        # Extract answer choices
        choices_text = question[
                       len(question_text) + len(question_number) + 1:].strip() if question_number else question[
                                                                                                       len(question_text):].strip()
        choices = answer_choices_pattern.findall(choices_text)
        parsed_choices = {choice[0]: choice[1].strip() for choice in choices}

        if parsed_choices:
            parsed_questions.append({
                'number': question_number,
                'question': question_text,
                'choices': parsed_choices
            })

    return parsed_questions


def parse_answers(text):
    # Clean up the text to remove newlines between answers and questions
    cleaned_text = re.sub(r'\n\s+', ' ', text)
    cleaned_text = re.sub(r"☑", '', cleaned_text)
    cleaned_text = re.sub(r", and", ',', cleaned_text)
    cleaned_text = re.sub(r" and ", ', ', cleaned_text)
    cleaned_text = re.sub(r" is correct.", '.', cleaned_text)
    cleaned_text = re.sub(r" are correct.", '.', cleaned_text)
    cleaned_text = re.sub("\\t","", cleaned_text)
    print(cleaned_text)

    # Pattern to capture question numbers and answers within the chapter
    question_pattern = re.compile(r'(\d+)\s*\.\s*(?:\n\s*)?([A-F](?:,\s*[A-F])*)\.')

    # Find all matches
    matches = question_pattern.findall(cleaned_text)

    # Create the output dictionary
    answers = {}
    start_processing = False

    for match in matches:
        question_number = match[0]
        answer_text = match[1]

        if int(question_number) == 1:
        # if int(question_number) == 49:
            start_processing = True

        if start_processing:
            if question_number not in answers:
                # Split the answers by comma and strip any whitespace
                answers[question_number] = [ans.strip() for ans in answer_text.split(',') if ans.strip()]

    # Ensure all question numbers from 1 to 20 are included in the answers
    all_questions = {str(i): [] for i in range(1, QUESTION_RANGE + 1)}
    # all_questions = {str(i): [] for i in range(49, QUESTION_RANGE + 1)}
    all_questions.update(answers)

    return all_questions


def parse_reasons(questions, explanations):
    prompt = f"""
        Extract the reasons for each answer choice for each question from the following explanations. If an explanation is not provided or incomplete, generate a plausible reason based on common knowledge. Format the results as a list of dictionaries, where each dictionary represents a question. Each dictionary should have a key "number" with the question number and keys "A", "B", "C", "D", and "E" (if applicable) for the respective answer choices and their reasons.

        Questions:
        {json.dumps(questions, indent=4)}

        Explanations:
        {explanations}

        Ensure the output follows this format and is valid JSON:

        Example Output:
        [
            {{
                "number": 1,
                "A": "Reason for Option A",
                "B": "Reason for Option B",
                "C": "Reason for Option C",
                "D": "Reason for Option D",
                "E": "Reason for Option E"
            }},
            {{
                "number": 2,
                "A": "Reason for Option A",
                "B": "Reason for Option B",
                "C": "Reason for Option C",
                "D": "Reason for Option D",
                "E": "Reason for Option E"
            }}
        ]
        """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_output = response['choices'][0]['message']['content'].strip()
    print("Raw output from the model:\n", raw_output)

    # Clean and process the output
    try:
        # Remove code block formatting if present
        raw_output = re.sub(r'```(json)?', '', raw_output).strip()

        # Validate JSON structure
        if not (raw_output.startswith('[') and raw_output.endswith(']')):
            print("Output does not appear to be valid JSON")
            return None

        # Attempt to parse JSON
        data = json.loads(raw_output)
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def extract_choice(answer_text):
    match = re.match(r'([A-F])\.', answer_text.strip())
    return match.group(1) if match else 'No answer found'


if __name__ == "__main__":
    cleaned_questions_text = extract_and_clean_text(PDF_PATH, QUESTION_START_PAGE,
                                                    QUESTION_END_PAGE)
    cleaned_answers_text = extract_and_clean_text(PDF_PATH, ANSWER_START_PAGE, ANSWER_END_PAGE)
    print(cleaned_questions_text)
    # print(cleaned_answers_text)
    questions = parse_questions(cleaned_questions_text)
    # for question in questions:
    #     if question['question'] == 'Which subnet mask is assigned to this address?' and question['number'] == '22':
    #       question['number'] = '34'
    #     elif question['question'] == 'Which directive in the /etc/ssh/sshd_config file can do this?' and question['number'] == '22':
    #       question['number'] = '41'
    answers = parse_answers(cleaned_answers_text)
    questions_with_answers = merge_answers_with_questions(questions, answers)
    # print(cleaned_questions_text)
    missing_questions, missing_answers = identify_missing_elements(questions_with_answers, QUESTION_RANGE)
    if missing_questions:
        print(f"Questions missing from parsing: {', '.join(missing_questions)}")
    else:
        print("All questions parsed successfully.")

    if missing_answers:
        print(f"Questions missing answers: {', '.join(missing_answers)}")
    else:
        print("All questions have answers.")

    print(questions)
    print(answers)
