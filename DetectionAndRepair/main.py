import os
from reporter import print_analysis_report
from detector import analyze_template
from fixer import fix_template

def read_jinja2_template(file_path):

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        return template_content
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except UnicodeDecodeError:
        print(f"Error: {file_path} encoding is not UTF-8.")
        return None
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return None

def process_directory(directory_path):

    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    files = [f for f in os.listdir(directory_path) if f.endswith('.j2')]

    if not files:
        print(f"No .j2 files found in '{directory_path}'.")
        return

    print(f"Found {len(files)} template files. Starting analysis...\n")

    for filename in files:
        file_path = os.path.join(directory_path, filename)
        
        print(f" Processing File: {filename}")

        template_content = read_jinja2_template(file_path)
        
        if template_content is not None:
            
            errors = analyze_template(template_content)

            fixed_template = fix_template(template_content, errors)
            
            print_analysis_report(errors, template_content, fixed_template)

J2_DIRECTORY_PATH = r""

if __name__ == "__main__":
    process_directory(J2_DIRECTORY_PATH)