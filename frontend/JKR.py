import os
import sys

def document_current_directory():
    """
    Scans all files in the current directory recursively (excluding __pycache__
    and node_modules), reads their content, and writes structure + content into
    a single text file.
    """

    OUTPUT_FILE = "project_structure_and_content.txt"
    EXCLUDED_DIRS = {"__pycache__", "node_modules"}
    EXCLUDED_EXTENSIONS = {
        ".pyc", ".DS_Store", ".log", ".db",
        ".png", ".jpg", ".jpeg", ".gif",
        ".zip", ".lock"
    }

    SEPARATOR = "\n" + "=" * 80 + "\n"

    print(f"Documenting current directory → {OUTPUT_FILE}")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
            for root, dirs, files in os.walk("."):
                # Exclude unwanted directories in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                for filename in files:
                    filepath = os.path.join(root, filename)

                    # Skip the output file itself
                    if os.path.abspath(filepath) == os.path.abspath(OUTPUT_FILE):
                        continue

                    # Skip unwanted file extensions
                    if any(filepath.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                        continue

                    try:
                        with open(filepath, "r", encoding="utf-8") as infile:
                            content = infile.read()

                        outfile.write(SEPARATOR)
                        outfile.write(f"--- FILE PATH: {filepath} ---\n")
                        outfile.write(SEPARATOR)
                        outfile.write(content + "\n")

                    except UnicodeDecodeError:
                        outfile.write(SEPARATOR)
                        outfile.write(f"--- FILE PATH: {filepath} ---\n")
                        outfile.write(SEPARATOR)
                        outfile.write(
                            "[CONTENT SKIPPED: File is not UTF-8 decodable]\n"
                        )

                    except Exception as e:
                        outfile.write(SEPARATOR)
                        outfile.write(f"--- FILE PATH: {filepath} ---\n")
                        outfile.write(SEPARATOR)
                        outfile.write(f"[ERROR READING FILE: {e}]\n")

        print("Documentation complete.")

    except IOError as e:
        print(f"Failed to write output file: {e}", file=sys.stderr)


if __name__ == "__main__":
    document_current_directory()
