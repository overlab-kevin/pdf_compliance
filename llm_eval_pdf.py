import argparse
import os
import fitz  # PyMuPDF
import google.generativeai as genai
import time
import pypandoc

def configure_api():
    """Configures the Gemini API with the key from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set it to your API key.")
    genai.configure(api_key=api_key)

def pdf_to_images(pdf_path, temp_dir="temp_images"):
    """
    Converts each page of a PDF to a PNG image in a temporary directory.

    Args:
        pdf_path (str): The path to the input PDF file.
        temp_dir (str): The directory to store the output images.

    Returns:
        list: A list of tuples, where each tuple contains the image path and the page size (width, height).
    """
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    image_paths = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Higher DPI for better quality
        pix = page.get_pixmap(dpi=300)
        image_path = os.path.join(temp_dir, f"{page_num + 1:03d}.png")
        pix.save(image_path)
        image_paths.append((image_path, (page.rect.width, page.rect.height))) # Append tuple of image path and page size
        print(f"Generated image: {image_path}")

    doc.close()
    return image_paths

def upload_files_to_gemini(file_paths):
    """
    Uploads a list of files to the Gemini API.

    Args:
        file_paths (list): A list of paths to the files to upload.

    Returns:
        list: A list of file objects from the Gemini API.
    """
    print("Uploading files to Gemini...")
    uploaded_files = []
    for file_path in file_paths:
        file = genai.upload_file(path=file_path)
        print(f"Uploaded '{file.display_name}' as {file.uri}")
        uploaded_files.append(file)
        # Add a small delay to respect API rate limits if uploading many files.
        time.sleep(1)
    return uploaded_files

def cleanup_images(image_paths):
    """

    Deletes the generated image files and the temporary directory.

    Args:
        image_paths (list): A list of paths to the image files to delete.
    """
    print("Cleaning up temporary image files...")
    for image_path in image_paths:
        try:
            os.remove(image_path)
        except OSError as e:
            print(f"Error removing file {image_path}: {e}")

    # Try to remove the directory if it's empty
    if image_paths: # Check if the list is not empty
        temp_dir = os.path.dirname(image_paths[0])
        try:
            os.rmdir(temp_dir)
            print(f"Removed temporary directory: {temp_dir}")
        except OSError as e:
            print(f"Could not remove directory {temp_dir}: {e}")


def process_pdf(pdf_path, checklist_path, temp_image_dir):
    """Processes a single PDF file."""
    image_paths = []  # Initialize here to ensure it exists in the finally block
    try:
        # --- 1. Configure API ---
        configure_api()

        # --- 2. Create images from PDF ---
        image_data = pdf_to_images(pdf_path, temp_dir=temp_image_dir)
        image_paths = [item[0] for item in image_data]
        page_sizes = [item[1] for item in image_data]

        # --- 3. Upload files to Gemini ---
        files_to_upload = [pdf_path] + image_paths + [checklist_path]
        uploaded_files = upload_files_to_gemini(files_to_upload)

        # --- 4. Call the Gemini API with the prompt and files ---
        print("\nSending request to Gemini for evaluation...")
        model = genai.GenerativeModel('models/gemini-2.5-pro-preview-06-05')

        prompt = f"""
        I'm providing you with a PDF of a submitted manuscript to Pattern Recognition.
        I'm also providing an image for every page in the paper.
        The page sizes are as follows: {page_sizes}
        Please evaluate whether the paper meets the criteria in the uploaded "check_list.md."
        Return only a MARKDOWN formatted report with the results. It should mirror the structure of the checklist.
        Make the last section a summary of the evaluation, including the overall compliance status.
        """

        # Combine the prompt and the uploaded files for the model
        request_content = [prompt] + uploaded_files

        response = model.generate_content(request_content)

        # --- 5. Print the response ---
        print("\n--- Gemini Evaluation Result ---")
        print(response.text)
        print("------------------------------")

        # --- New feature: Convert response to HTML using pandoc ---
        print("\nConverting response to a styled, standalone HTML file using pandoc...")

        # --- MODIFIED LINE: Use 'gfm' format and add 'standalone' extra argument ---
        html_content = pypandoc.convert_text(
            response.text,
            'html',
            format='gfm',  # Use GitHub-Flavored Markdown for better list parsing
            extra_args=['--standalone', '--metadata', 'title="Manuscript Evaluation Report"']  # Create a full document with default styles and a title
        )

        # --- New feature: Output HTML to a file ---
        # Get the directory and base name of the input PDF
        input_dir = os.path.dirname(os.path.abspath(pdf_path))
        input_basename = os.path.splitext(os.path.basename(pdf_path))[0]

        # Define the output HTML file path
        output_html_path = os.path.join(input_dir, f"{input_basename}.html")

        # Write the HTML content to the file
        with open(output_html_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

        print(f"Successfully saved HTML report to: {output_html_path}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

    finally:
        # --- 6. Clean up the generated images ---
        if image_paths:
            cleanup_images(image_paths)


def main():
    """Main function to run the manuscript evaluation process."""
    parser = argparse.ArgumentParser(description="Evaluate a manuscript PDF using the Gemini API.")
    parser.add_argument("pdf_path", help="The path to the target PDF manuscript or a directory containing PDFs.")
    args = parser.parse_args()

    # --- File Paths ---
    pdf_path = args.pdf_path
    checklist_path = "check_list.md"
    temp_image_dir = "temp_manuscript_images"

    if not os.path.exists(checklist_path):
        print(f"Error: The required 'check_list.md' file was not found in the script's directory.")
        return

    if os.path.isfile(pdf_path):
        # Process a single PDF file
        process_pdf(pdf_path, checklist_path, temp_image_dir)
    elif os.path.isdir(pdf_path):
        # Process all PDF files in the directory
        for filename in os.listdir(pdf_path):
            if filename.lower().endswith(".pdf"):
                pdf_file_path = os.path.join(pdf_path, filename)
                print(f"Processing PDF file: {pdf_file_path}")
                process_pdf(pdf_file_path, checklist_path, temp_image_dir)
    else:
        print(f"Error: The path '{pdf_path}' is neither a valid file nor a directory.")
        return


if __name__ == "__main__":
    main()
