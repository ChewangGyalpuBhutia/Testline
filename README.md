# Testline PDF Question Extractor

This repository extracts questions and associated images from a PDF file and saves them in a structured JSON format. It is designed for educational content digitization, especially for question papers with visual options.

## Environment Creation Steps

1. **Create a virtual environment** (recommended):

   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. Run the main script:

   ```powershell
   python main.py
   ```

3. Extracted images will be saved in [`extracted_content`](extracted_content).
4. Questions and their mapped images will be saved in [`questions_with_images.json`](questions_with_images.json).

## File Structure

- [`main.py`](main.py): Main extraction and mapping script
- [`pdf.pdf`](pdf.pdf): Source PDF file
- [`questions_with_images.json`](questions_with_images.json): Output JSON with questions and image paths
- [`extracted_content`](extracted_content): Directory containing extracted images
- [`.gitignore`](.gitignore): Ignores virtual environment and notebook checkpoints

## Example Output

Each entry in [`questions_with_images.json`](questions_with_images.json) looks like:

```json
{
  "question": "1. Find the next figures in the figure pattern given below. [A] [B] [C] [D]",
  "images": [
    "extracted_content/q1-q2_img_1_option.png",
    "extracted_content/q1-q2_img_2_option.png"
  ]
}
```

## Notes

- Only images between consecutive questions are extracted.
- Images are mapped to the first question in each pair.
- Questions without images will have an empty `images` list.
