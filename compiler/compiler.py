import os
import json
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class JsonFile:
    name: str
    content: str
    example: Optional[str] = None
    error: Optional[str] = None
@dataclass
class Subcategory:
    name: str
    json_files: List[JsonFile]

@dataclass
class DirectoryContent:
    path: str
    subcategories: List[Subcategory]

def read_json_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}
    except FileNotFoundError:
        return {"error": "File not found"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def get_example_content(example_path: str) -> str:
    content = read_json_file(example_path)
    if "error" in content:
        return "{}"
    return json.dumps(content)

def process_json_file(file_path: str, example_path: str) -> JsonFile:
    content = read_json_file(file_path)
    example = get_example_content(example_path)

    if "error" in content:
        return JsonFile(
            name=os.path.basename(file_path),
            content="{}",
            example=example,
            error=content["error"]
        )

    return JsonFile(
        name=os.path.basename(file_path),
        content=json.dumps(content),
        example=example
    )

def get_json_files(directory: str) -> List[JsonFile]:
    json_files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.json'):
            file_path = os.path.join(directory, filename)
            example_path = os.path.join(directory, 'examples', filename)
            json_file = process_json_file(file_path, example_path)
            json_files.append(json_file)
    return json_files

def is_valid_directory(name: str) -> bool:
    return name not in ('examples', 'schema-compiler')

def get_subcategory(dirpath: str, subcategory: str) -> Optional[Subcategory]:
    subcat_path = os.path.join(dirpath, subcategory)
    if os.path.isdir(subcat_path):
        json_files = get_json_files(subcat_path)
        if json_files:
            return Subcategory(subcategory, json_files)
    return None

def get_directory_contents(root_dir: str) -> List[DirectoryContent]:
    contents = []
    for dirpath, dirnames, _ in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if is_valid_directory(d)]
        if dirpath != root_dir:
            rel_path = os.path.relpath(dirpath, root_dir)
            subcategories = []

            for subcategory in ['In Topic', 'Out Topic']:
                subcat = get_subcategory(dirpath, subcategory)
                if subcat:
                    subcategories.append(subcat)

            if subcategories:
                contents.append(DirectoryContent(rel_path, subcategories))
    return contents

def generate_html_content(contents: List[DirectoryContent]) -> str:
    def generate_file_html(file: JsonFile) -> str:
        file_name = file.name.replace(".json", "").replace("-", " ")
        example_attr = f'data-example=\'{file.example}\'' if file.example else ''
        return f'<li><div class="json-file" data-content=\'{file.content}\' {example_attr}>{file_name}</div></li>'

    html_parts = []
    for content in contents:
        html_parts.extend([
            f'<li><h2>{content.path.replace("-", " ")}</h2>',
            '<ul>'
        ])
        for subcategory in content.subcategories:
            html_parts.extend([
                f'<li><h3>{subcategory.name}</h3>',
                '<ul>',
                *[generate_file_html(file) for file in subcategory.json_files],
                '</ul></li>'
            ])
        html_parts.append('</ul></li>')
    return '\n'.join(html_parts)

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
    ROOT_DIRECTORY = '../'
    OUTPUT_FILE = 'schema.html'
    TEMPLATE_FILE = 'template.html'
    main(ROOT_DIRECTORY, OUTPUT_FILE, TEMPLATE_FILE)
