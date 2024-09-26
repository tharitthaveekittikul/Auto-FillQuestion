import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager

from src.config import WEB_FORM_URL, USERNAME, PASSWORD


def setup_webdriver():
    service = ChromeService(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def open_url(driver, url):
    driver.get(url)


def find_element(driver, selector):
    return driver.find_element(By.CSS_SELECTOR, selector)


def find_form_elements(driver, form_selectors):
    question_field = find_element(driver, form_selectors['question'])
    choices_field = find_element(driver, form_selectors['choices'])
    answer_field = find_element(driver, form_selectors['answer'])
    submit_button = find_element(driver, form_selectors['submit'])
    return question_field, choices_field, answer_field, submit_button


def fill_field(field, value):
    field.clear()
    field.send_keys(value)


def fill_choices_field(choices_field, choices):
    choices_field.clear()
    for choice in choices:
        choices_field.send_keys(choice + Keys.RETURN)


def submit_form(submit_button):
    submit_button.click()


def wait_for_submission(second=1):
    time.sleep(second)


def close_webdriver(driver):
    driver.quit()


def login(driver, username, password):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@id="username"]'))
    )
    username_field = driver.find_element(By.XPATH, '//input[@id="username"]')
    password_field = driver.find_element(By.XPATH, '//input[@id="password"]')
    login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')

    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button.click()


def navigate_to_question_creation(driver):
    click_create_new_question(driver)
    click_multiple_choice(driver)
    click_add_button(driver)


def click_create_new_question(driver):
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Create a new question")]'))
    )
    create_question_button = driver.find_element(By.XPATH, '//button[contains(text(), "Create a new question")]')
    create_question_button.click()


def click_multiple_choice(driver):
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@id="item_qtype_multichoice"]'))
    )
    multiple_choice_radio = driver.find_element(By.XPATH, '//input[@id="item_qtype_multichoice"]')
    multiple_choice_radio.click()


def click_add_button(driver):
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@class="submitbutton btn btn-primary" and @value="Add"]'))
    )
    add_button = driver.find_element(By.XPATH, '//input[@class="submitbutton btn btn-primary" and @value="Add"]')
    add_button.click()


def fill_question(driver, question, category, reason):
    question_text = question['question']
    choices = question['choices']
    answers = question['answer']

    number = int(question['number'])
    formatted_number = f"{number:02d}"
    question_name = f"{category}MC{formatted_number}E"

    # Fill question name
    question_name_field = driver.find_element(By.ID, "id_name")
    question_name_field.clear()
    question_name_field.send_keys(question_name)

    # Fill question text
    question_text_field = driver.find_element(By.ID, "id_questiontexteditable")
    question_text_field.clear()
    question_text_field.send_keys(question_text)

    # Set answer type
    multiple_answers_dropdown = driver.find_element(By.ID, "id_single")
    select = Select(multiple_answers_dropdown)
    if len(answers) > 1:
        select.select_by_value("0")  # Multiple answers allowed
    else:
        select.select_by_value("1")  # One answer only

    # Fill choices and reasons
    for index, (key, choice) in enumerate(choices.items()):
        choice_field = None
        try:
            choice_field = driver.find_element(By.ID, f"id_answer_{index}editable")
        except NoSuchElementException:
            # If the element is not found, click to add more choices
            blank_more_choices = driver.find_element(By.ID, "id_addanswers")
            blank_more_choices.click()
            # Try to find the element again after adding more choices
            choice_field = driver.find_element(By.ID, f"id_answer_{index}editable")

        choice_field.clear()
        choice_field.send_keys(f"{choice}")
        if reason:
            reason_text = reason.get(key, "")
            feedback_field = driver.find_element(By.ID, f"id_feedback_{index}editable")
            feedback_field.clear()
            feedback_field.send_keys(reason_text)

        # Select the correct answers
        if answers:
            if len(answers) == 1:
                correct_fraction_str = "1.0"
            else:
                correct_fraction = 1.0 / len(answers)
                correct_fraction_str = format(correct_fraction, ".7f").rstrip('0').rstrip('.')

            for answer in answers:
                answer_letter = answer[0]
                correct_answer_index = None
                for idx, (key, _) in enumerate(choices.items()):
                    if key == answer_letter:
                        correct_answer_index = idx
                        break

                if correct_answer_index is not None:
                    correct_answer_dropdown = None
                    try:
                        correct_answer_dropdown = driver.find_element(By.ID, f"id_fraction_{correct_answer_index}")
                    except NoSuchElementException:
                        # If the element is not found, click to add more choices
                        blank_more_choices = driver.find_element(By.ID, "id_addanswers")
                        blank_more_choices.click()
                        # Try to find the element again after adding more choices
                        correct_answer_dropdown = driver.find_element(By.ID, f"id_fraction_{correct_answer_index}")
                    select = Select(correct_answer_dropdown)
                    # Find the closest option value
                    options = [option.get_attribute('value') for option in select.options]
                    closest_match = min(options, key=lambda x: abs(float(x) - float(correct_fraction_str)))
                    if abs(float(closest_match) - float(correct_fraction_str)) < 1e-6:  # Small tolerance
                        select.select_by_value(closest_match)
                    else:
                        print(f"Option with value {correct_fraction_str} not found in the dropdown")
                else:
                    print(f"Correct answer {answer} not found in choices")
        else:
            # If no answer is provided, set the default correct answer to choice A
            correct_answer_dropdown = driver.find_element(By.ID, f"id_fraction_0")
            select = Select(correct_answer_dropdown)
            select.select_by_value("1.0")  # Select the option with value "1.0" for 100%

    # Click save button
    save_button = driver.find_element(By.ID, "id_submitbutton")
    save_button.click()


def main():
    driver = setup_webdriver()
    category = "04"
    try:
        open_url(driver, WEB_FORM_URL)
        login(driver, USERNAME, PASSWORD)
        navigate_to_question_creation(driver)
        fill_question(driver, questions_with_answers[0], category)
        time.sleep(5)

        print("Form submission complete. Keeping the browser open for manual inspection.")
        while True:
            pass  # Infinite loop to keep the browser open
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing browser.")
        driver.quit()


questions_with_answers = [{'number': '1', 'question': 'What program does the workstation firmware start at boot time?',
                           'choices': ['A. A bootloader', 'B. The fsck program', 'C. The Windows OS',
                                       'D. The mount command', 'E. The mkinitrd program'], 'answer': 'A'},
                          {'number': '2',
                           'question': 'Where does the firmware first look for a Linux bootloader program?',
                           'choices': ['A. The /boot/grub folder', 'B. The Master Boot Record (MBR)',
                                       'C. The /var/log folder', 'D. A boot partition', 'E. The /etc folder'],
                           'answer': 'B'}, {'number': '3',
                                            'question': 'The ______ command allows us to examine the most recent boot messages.',
                                            'choices': ['A. fsck', 'B. init', 'C. mount', 'D. dmesg', 'E. mkinitrd'],
                                            'answer': 'A'},
                          {'number': '4', 'question': 'What folder do most Linux distributions use to store boot logs?',
                           'choices': ['A. /etc', 'B. /var/messages', 'C. /var/log', 'D. /boot', 'E. /proc'],
                           'answer': 'C'}, {'number': '5',
                                            'question': 'Where does the workstation BIOS attempt to find a bootloader program? (Choose all that apply. )',
                                            'choices': ['A. An internal hard drive', 'B. An external hard drive',
                                                        'C. A DVD drive', 'D. A USB memory stick',
                                                        'E. A network server Review Questions 153'], 'answer': None},
                          {'number': '6',
                           'question': 'Where is the Master Boot Record located? (Choose all that apply. )',
                           'choices': ['A. The first sector of the first hard drive on the system',
                                       'B. The boot partition of any hard drive on the system',
                                       'C. The last sector of the first hard drive on the system',
                                       'D. Any sector on any hard drive on the system',
                                       'E. The first sector of the second hard drive on the system 7 . The EFI System Partition (ESP) is stored in the _______ directory on Linux systems.',
                                       'A. /boot', 'B. /etc', 'C. /var', 'D. /boot/efi', 'E. /boot/grub'],
                           'answer': 'A'},
                          {'number': '8', 'question': 'What file extension do UEFI bootloader files use?',
                           'choices': ['A. . cfg', 'B. . uefi', 'C. . lst', 'D. . conf', 'E. . efi'], 'answer': 'E'},
                          {'number': '9', 'question': 'Which was the first bootloader program used in Linux?',
                           'choices': ['A. GRUB Legacy', 'B. LILO', 'C. GRUB2', 'D. SYSLINUX', 'E. ISOLINUX'],
                           'answer': 'B'},
                          {'number': '10', 'question': 'Where are the GRUB Legacy configuration files stored?',
                           'choices': ['A. /boot/grub', 'B. /boot/efi', 'C. /etc', 'D. /var', 'E. /proc'],
                           'answer': 'A'}, {'number': '11',
                                            'question': 'Where are GRUB2 configuration files stored? (Choose all that apply. )',
                                            'choices': ['A. /proc', 'B. /etc/grub. d', 'C. /boot/grub', 'D. /boot/efi',
                                                        'E. /var 154 Chapter 5 ■ Explaining the Boot Process'],
                                            'answer': None}, {'number': '12',
                                                              'question': 'You must run the ______ command to generate the GRUB2 grub. cfg configuration file.',
                                                              'choices': ['A. mkinitrd', 'B. mkinitramfs',
                                                                          'C. grub- mkconfig', 'D. grub- install',
                                                                          'E. fsck'], 'answer': 'C'}, {'number': '13',
                                                                                                       'question': 'What command must you run to save changes to a GRUB Legacy boot menu?',
                                                                                                       'choices': [
                                                                                                           'A. mkinitrd',
                                                                                                           'B. mkinitramfs',
                                                                                                           'C. grub- mkconfig',
                                                                                                           'D. grub- install',
                                                                                                           'E. fsck'],
                                                                                                       'answer': 'D'},
                          {'number': '14',
                           'question': 'The ____ firmware method has replaced BIOS on most modern IBM- compatible computers.',
                           'choices': ['A. FTP', 'B. UEFI', 'C. PXE', 'D. NFS', 'E. HTTPS'], 'answer': 'B'},
                          {'number': '15', 'question': 'What memory area does Linux use to store boot messages?',
                           'choices': ['A. BIOS', 'B. The GRUB bootloader', 'C. The MBR', 'D. The initrd RAM disk',
                                       'E. The kernel ring buffer'], 'answer': 'E'}, {'number': '16',
                                                                                      'question': 'What command parameter would you add to the end of the GRUB2 linux command to force a Linux system to start in single- user mode?',
                                                                                      'choices': ['A. single',
                                                                                                  'B. fsck',
                                                                                                  'C. mkinitrd',
                                                                                                  'D. mkinitramfs',
                                                                                                  'E. dmesg 17 . What is the term commonly used for when the Linux system halts due to a system error?',
                                                                                                  'A. Kernel panic',
                                                                                                  'B. Kernel ring buffer',
                                                                                                  'C. initrd RAM disk',
                                                                                                  'D. Bootloader',
                                                                                                  'E. Firmware Review Questions 155'],
                                                                                      'answer': 'A'}, {'number': '18',
                                                                                                       'question': 'The ________ command generates the GRUB2 configuration used for booting.',
                                                                                                       'choices': [
                                                                                                           'A. mkinitrd',
                                                                                                           'B. grub- mkconfig',
                                                                                                           'C. grub- install',
                                                                                                           'D. mkinitramfs',
                                                                                                           'E. dmesg'],
                                                                                                       'answer': 'B'},
                          {'number': '19',
                           'question': 'What program allows you to fix corrupted hard drive partitions?',
                           'choices': ['A. mount', 'B. umount', 'C. fsck', 'D. dmesg', 'E. mkinitrd'], 'answer': 'C'},
                          {'number': '20',
                           'question': 'Which command allows you to append a partition to the virtual directory on a running Linux system?',
                           'choices': ['A. mount', 'B. umount', 'C. fsck', 'D. dmesg', 'E. mkinitramfs'],
                           'answer': 'A'}]

if __name__ == "__main__":
    # form_selectors = {
    #
    # }
    main()
