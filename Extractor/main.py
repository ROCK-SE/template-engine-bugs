import os
import json as json_module
from analyzer import analyze_template

def read_jinja2_template(file_path):
    """
    Read the content of a Jinja2 template file.

    Args:
        file_path: Path to the Jinja2 template file.

    Returns:
        str: Content of the template file, or None if reading fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        return template_content
    except FileNotFoundError:
        print(f"Error: Jinja2 template file '{file_path}' not found")
        return None
    except UnicodeDecodeError:
        print(f"Error: {file_path} encoding is not UTF-8. Please check the file encoding.")
        return None
    except Exception as e:
        print(f"Failed to read J2 file: {e}")
        return None

def process_directory(input_directory, output_directory):
    """
    Iterate through all .j2 files in the input directory, perform analysis, 
    and save the results as individual JSON files in the output directory.

    Args:
        input_directory: Path containing the source .j2 files.
        output_directory: Path where the resulting .json files will be saved.
    """
    # Check if the input directory exists
    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' does not exist.")
        return

    # Create the output directory if it does not exist
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
            print(f"Created output directory: {output_directory}")
        except OSError as e:
            print(f"Error creating output directory: {e}")
            return

    # Get all .j2 files in the directory
    files = [f for f in os.listdir(input_directory) if f.endswith('.j2')]
    
    if not files:
        print(f"No .j2 files found in '{input_directory}'")
        return

    print(f"Found {len(files)} template files. Starting processing...\n")

    # Process each file
    for filename in files:
        input_file_path = os.path.join(input_directory, filename)
        
        # Read file content
        template_content = read_jinja2_template(input_file_path)
        
        if template_content is not None:
            try:
                # Perform analysis
                result = analyze_template(template_content)

                # Construct output filename: replace .j2 extension with .json
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_file_path = os.path.join(output_directory, output_filename)

                # Write analysis result to the JSON file
                with open(output_file_path, 'w', encoding='utf-8') as json_file:
                    json_module.dump(result, json_file, indent=4, ensure_ascii=False)
                
                print(f"[Success] Processed: {filename} -> Saved to: {output_filename}")

            except Exception as e:
                print(f"[Error] Failed to analyze or save {filename}: {e}")

J2_TEMPLATE_DIR = r""
OUTPUT_DIR = os.path.join(J2_TEMPLATE_DIR, "json_output")

# Execute processing
if __name__ == "__main__":
    process_directory(J2_TEMPLATE_DIR, OUTPUT_DIR)