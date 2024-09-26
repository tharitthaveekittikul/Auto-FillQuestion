import fitz


def extract_text_from_pdf(pdf_path, start_page=0, end_page=None):
    document = fitz.open(pdf_path)
    text = ""
    total_pages = len(document)

    if end_page is None or end_page > total_pages:
        end_page = total_pages

    for page_num in range(start_page, end_page):
        page = document.load_page(page_num)
        text += page.get_text("text")
    return text
