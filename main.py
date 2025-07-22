from IPython.display import Image as IPImage, display
import fitz
import re
import os
import json
from collections import defaultdict
import pdfplumber


def clean_question_text(text):
    """Helper function to clean question text"""
    return " ".join(text.split()).strip()


def clean_question_text2(text):
    """Remove answer portion (everything after 'Ans') but keep options"""
    # Remove everything from 'Ans.' or 'Ans' to end of string
    cleaned_text = re.sub(r"Ans\.?.*$", "", text, flags=re.IGNORECASE)
    return cleaned_text.strip()


def image_extractor(path="pdf.pdf"):
    all_questions = []
    doc = fitz.open(path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split("\n")

        current_question = ""

        for line in lines:
            line = line.strip()
            match = re.match(r"^(\d+)\.\s*(.*)", line)
            if match:
                question_num = match.group(1)
                text_to_find = f"{question_num}."
                text_instances = page.search_for(text_to_find)

                if text_instances:
                    if current_question:
                        all_questions.append(
                            {
                                "number": prev_question_num,
                                "page": page_num + 1,
                                "position": prev_question_pos,
                                "text": clean_question_text(current_question),
                            }
                        )

                    current_question = f"{match.group(1)}. {match.group(2)}"
                    prev_question_num = question_num
                    prev_question_pos = text_instances[0]
            elif current_question:
                current_question += " " + line

        # Save the last question of the page
        if current_question:
            all_questions.append(
                {
                    "number": prev_question_num,
                    "page": page_num + 1,
                    "position": prev_question_pos,
                    "text": clean_question_text(current_question),
                }
            )

    for i in range(len(all_questions) - 1):
        q1 = all_questions[i]
        q2 = all_questions[i + 1]

        # Case 1: Both questions on same page
        if q1["page"] == q2["page"]:
            page = doc[q1["page"] - 1]
            between_rect = fitz.Rect(
                72,
                q1["position"].y1,
                max(q1["position"].x1, q2["position"].x1) + 400,
                q2["position"].y0,
            )

            image_list = page.get_images(full=True)
            extracted_images = []

            for img_index, img in enumerate(image_list):
                if img[8] == "DCTDecode":
                    continue
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_rect = page.get_image_bbox(img)

                if between_rect.contains(image_rect):
                    image_filename = f"extracted_content/q{q1['number']}-q{q2['number']}_img_{img_index}_option.{base_image['ext']}"
                    with open(image_filename, "wb") as f:
                        f.write(base_image["image"])
                    extracted_images.append(image_filename)
                    display(
                        IPImage(
                            data=base_image["image"],
                            format=base_image["ext"],
                            width=200,
                        )
                    )

        # Case 2: Questions span page break (Q1 on page N, Q2 on page N+1)
        elif q2["page"] == q1["page"] + 1:
            page1 = doc[q1["page"] - 1]
            rect1 = fitz.Rect(
                72, q1["position"].y1, page1.rect.width - 72, page1.rect.height
            )
            text_part1 = page1.get_text("text", clip=rect1).strip()

            page2 = doc[q2["page"] - 1]
            rect2 = fitz.Rect(
                72, 0, q2["position"].x1 + 400, q2["position"].y0  # Top of page
            )

            # Extract images from both sections
            extracted_images = []

            # Images from end of Q1's page
            image_list1 = page1.get_images(full=True)
            for img_index, img in enumerate(image_list1):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_rect = page1.get_image_bbox(img)

                if rect1.contains(image_rect):
                    image_filename = f"extracted_content/q{q1['number']}-q{q2['number']}_img1_{img_index}_option.{base_image['ext']}"
                    with open(image_filename, "wb") as f:
                        f.write(base_image["image"])
                    extracted_images.append(image_filename)
                    display(
                        IPImage(
                            data=base_image["image"],
                            format=base_image["ext"],
                            width=200,
                        )
                    )

            # Images from start of Q2's page
            image_list2 = page2.get_images(full=True)
            for img_index, img in enumerate(image_list2):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_rect = page2.get_image_bbox(img)

                if rect2.contains(image_rect):
                    image_filename = f"extracted_content/q{q1['number']}-q{q2['number']}_img2_{img_index}_option.{base_image['ext']}"
                    with open(image_filename, "wb") as f:
                        f.write(base_image["image"])
                    extracted_images.append(image_filename)
                    display(
                        IPImage(
                            data=base_image["image"],
                            format=base_image["ext"],
                            width=200,
                        )
                    )

        else:
            print(
                f"Skipping Q{q1['number']} to Q{q2['number']} - not consecutive pages"
            )
            continue
    return True


def filter_and_delete_image_groups(directory="extracted_content", min_images=4):
    question_groups = defaultdict(list)

    # Group images by question pairs
    for img_file in os.listdir(directory):
        if img_file.lower().endswith(".png") and "_" in img_file:
            question_pair = img_file.split("_")[0].upper()
            question_groups[question_pair].append(img_file)

    # Delete small groups
    for question_pair, images in list(question_groups.items()):
        if len(images) < min_images:
            print(f"\nDeleting group {question_pair} ({len(images)} images):")
            for img_file in images:
                img_path = os.path.join(directory, img_file)
                os.remove(img_path)
                print(f"Deleted: {img_file}")
            del question_groups[question_pair]

    return question_groups


def extract_numbered_questions(pdf_path):
    """
    Extract only numbered questions (1., 2., 3., etc.) from PDF
    and clean them by removing answers but keeping options
    """
    questions = []
    current_question = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                line = line.strip()

                # Check for numbered questions (digits followed by a dot)
                match = re.match(r"^(\d+)\.\s*(.*)", line)
                if match:
                    # Save previous question if exists
                    if current_question:
                        cleaned = clean_question_text(current_question)
                        questions.append({"question": cleaned})
                    # Start new question
                    current_question = f"{match.group(1)}. {match.group(2)}"
                elif current_question:  # Continue current question
                    current_question += " " + line

    # Add the last question if exists
    if current_question:
        cleaned = clean_question_text(current_question)
        questions.append({"question": cleaned})

    return questions


def save_to_json(data, output_path):
    """Save data to JSON file"""
    print(data)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def map_images_to_questions(questions, image_dir="extracted_content"):
    """Map images to their corresponding questions based on filenames"""
    q_index_map = {}
    for i, q in enumerate(questions):
        # Extract question number from text (e.g., "1. What is...")
        match = re.match(r"^(\d+)\.", q["question"])
        if match:
            q_num = match.group(1)
            q_index_map[q_num] = i

    # Initialize images list for each question
    for q in questions:
        q["images"] = []

    # Scan image directory and map to questions
    for img_file in os.listdir(image_dir):
        if img_file.lower().endswith(".png") and "_" in img_file:
            # Extract question pair from filename (e.g., "q1-q2_img_0.png")
            q_pair = img_file.split("_")[0].lower()  # Gets "q1-q2"
            q_nums = q_pair.split("-")  # Gets ["q1", "q2"]

            # The image belongs to the first question in the pair
            if len(q_nums) == 2 and q_nums[0][1:] in q_index_map:
                q_num = q_nums[0][1:]  # Extract just the number ("1")
                img_path = os.path.join(image_dir, img_file)
                questions[q_index_map[q_num]]["images"].append(img_path)

    return questions


# Modified save_to_json function to include image mapping
def save_questions_with_images(questions, output_path):
    """Save questions with mapped images to JSON file"""
    questions_with_images = map_images_to_questions(questions)
    with open(output_path, "w") as f:
        json.dump(questions_with_images, f, indent=2, ensure_ascii=False)
    print(f"Saved questions with mapped images to {output_path}")


# Update the main block
if __name__ == "__main__":
    os.makedirs("extracted_content", exist_ok=True)

    image_extractor("pdf.pdf")
    filter_and_delete_image_groups("extracted_content", 4)
    questions = extract_numbered_questions("pdf.pdf")
    save_questions_with_images(questions, "questions_with_images.json")

    print("Processing complete. Check 'extracted_content' for images and 'questions_with_images.json' for questions.")
