# Manuscript Evaluation Script

This script uses the Gemini API to evaluate a PDF manuscript against a checklist (`check_list.md`) and generates an HTML report of the findings.

## Setup

There are two types of dependencies: system-level and Python-level.

### 1. System Dependencies
This script requires the `pandoc` utility to be installed on your system to correctly convert the markdown report to a high-quality HTML file.

* **On macOS (using Homebrew):**
    ```bash
    brew install pandoc
    ```

* **On Debian/Ubuntu Linux:**
    ```bash
    sudo apt-get update && sudo apt-get install pandoc
    ```

* **On Windows (using Chocolatey or Winget):**
    ```bash
    # Using Chocolatey
    choco install pandoc
    
    # Or using Winget
    winget install JohnMacFarlane.Pandoc
    ```
    You can also find installers on the [official pandoc website](https://pandoc.org/installing.html).

### 2. Python Environment (Conda)
It is highly recommended to run this script in a dedicated Conda environment to avoid conflicts. The steps below use the environment name `gemini_eval` as a reference.

**Create and activate the environment:**
```bash
# Create the environment with all necessary packages from the reliable conda-forge channel
conda create -n gemini_eval -c conda-forge python=3.11 google-generativeai pymupdf pypandoc

# Activate the environment before running the script
conda activate gemini_eval
```
Alternatively, if you prefer using `pip`, create a `requirements.txt` file and install from it inside your activated environment.

**File: `requirements.txt`**
```
google-generativeai
PyMuPDF
pypandoc
```

**Install with pip:**
```bash
pip install -r requirements.txt
```

### 3. API Key
The script requires a Gemini API key. It should be set as an environment variable named `GEMINI_API_KEY`.

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

## Usage

1.  Make sure you are inside your activated conda environment (`conda activate gemini_eval`).
2.  Ensure a `check_list.md` file exists in the same directory as the script.
3.  Run the script, passing the path to the manuscript PDF as an argument.

```bash
python llm_eval_pdf.py /path/to/your/manuscript.pdf
```

The script will generate an HTML report (e.g., `manuscript.html`) in the same directory as the input PDF.
