import os
import json
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class JsonFile:
    name: str
    content: str
    example: Optional[str] = None

@dataclass
class Subcategory:
    name: str
    json_files: List[JsonFile]

@dataclass
class DirectoryContent:
    path: str
    subcategories: List[Subcategory]

def get_directory_contents(root_dir: str) -> List[DirectoryContent]:
    contents = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ('examples', 'schema-compiler')]
        if dirpath != root_dir:
            rel_path = os.path.relpath(dirpath, root_dir)
            subcategories = []

            for subcategory in ['in topic', 'out topic']:
                subcat_path = os.path.join(dirpath, subcategory)
                if os.path.isdir(subcat_path):
                    json_files = []
                    for filename in os.listdir(subcat_path):
                        if filename.lower().endswith('.json'):
                            file_path = os.path.join(subcat_path, filename)
                            example_path = os.path.join(subcat_path, 'examples', filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    json_content = json.load(f)
                                try:
                                    with open(example_path, 'r', encoding='utf-8') as f:
                                        example_content = json.load(f)
                                    example = json.dumps(example_content)
                                except FileNotFoundError:
                                    example = "{}"
                                json_files.append(JsonFile(
                                    name=filename,
                                    content=json.dumps(json_content),
                                    example=example
                                ))
                            except json.JSONDecodeError:
                                print(f"Error: Invalid JSON in {filename}")
                    if json_files:
                        subcategories.append(Subcategory(subcategory, json_files))gi 

            if subcategories:
                contents.append(DirectoryContent(rel_path, subcategories))
    return contents

def generate_html_content(contents: List[DirectoryContent]) -> str:
    html_parts = []
    for content in contents:
        html_parts.extend([
            f'<li><h2>{content.path.replace("-", " ")}</h2>',
            '<ul>'
        ])
        for subcategory in content.subcategories:
            html_parts.extend([
                f'<li><h3>{subcategory.name}</h3>',
                '<ul>'
            ])
            for file in subcategory.json_files:
                file_name = file.name.replace(".json", "").replace("-", " ")
                example_attr = f'data-example=\'{file.example}\'' if file.example else ''
                html_parts.append(f'<li><div class="json-file" data-content=\'{file.content}\' {example_attr}>{file_name}</div></li>')
            html_parts.append('</ul></li>')
        html_parts.append('</ul></li>')
    return '\n'.join(html_parts)

# The main function remains the same
def main(root_directory: str, output_file: str, template_file: str) -> None:
    contents = get_directory_contents(root_directory)
    html_content = generate_html_content(contents)
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()
    full_html = template.replace('{content}', html_content)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"HTML file '{output_file}' has been generated.")

if __name__ == "__main__":
    ROOT_DIRECTORY = '../'  # Current directory, change this to the desired root directory
    OUTPUT_FILE = 'schema.html'
    TEMPLATE_FILE = 'template.html'  # Name of the template file
    main(ROOT_DIRECTORY, OUTPUT_FILE, TEMPLATE_FILE)
