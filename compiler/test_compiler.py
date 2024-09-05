import unittest
import json
import tempfile
import os
from compiler import (
    JsonFile,
    Subcategory,
    DirectoryContent,
    read_json_file,
    get_example_content,
    process_json_file,
    get_json_files,
    get_directory_contents,
    generate_html_content
)

class TestEventSchemaCompiler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.example_json = {'key': 'value'}
        self.example_json_str = json.dumps(self.example_json)

    def tearDown(self):
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)

    def create_test_file(self, path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(content, f)

    def test_read_json_file(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        self.create_test_file(test_file, self.example_json)
        result = read_json_file(test_file)
        self.assertEqual(result, self.example_json)

    def test_get_example_content_existing_file(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        self.create_test_file(test_file, self.example_json)
        result = get_example_content(test_file)
        self.assertEqual(result, self.example_json_str)

    def test_get_example_content_missing_file(self):
        result = get_example_content(os.path.join(self.temp_dir, 'nonexistent.json'))
        self.assertEqual(result, "{}")

    def test_process_json_file(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        example_file = os.path.join(self.temp_dir, 'examples', 'test.json')
        self.create_test_file(test_file, self.example_json)
        self.create_test_file(example_file, self.example_json)

        result = process_json_file(test_file, example_file)
        self.assertIsInstance(result, JsonFile)
        self.assertEqual(result.name, 'test.json')
        self.assertEqual(result.content, self.example_json_str)
        self.assertEqual(result.example, self.example_json_str)

    def test_get_json_files(self):
        self.create_test_file(os.path.join(self.temp_dir, 'test1.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'test2.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'examples', 'test1.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'examples', 'test2.json'), self.example_json)

        result = get_json_files(self.temp_dir)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], JsonFile)
        self.assertIsInstance(result[1], JsonFile)

    def test_get_directory_contents(self):
        # Create a mock directory structure
        self.create_test_file(os.path.join(self.temp_dir, 'folder1', 'In Topic', 'test1.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'folder1', 'Out Topic', 'test2.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'folder2', 'In Topic', 'test3.json'), self.example_json)

        result = get_directory_contents(self.temp_dir)
        self.assertEqual(len(result), 2)  # Two main folders
        self.assertIsInstance(result[0], DirectoryContent)
        self.assertEqual(len(result[0].subcategories), 2)  # 'In Topic' and 'Out Topic'
        self.assertEqual(len(result[1].subcategories), 1)  # Only 'In Topic'

    def test_generate_html_content(self):
        # Create a mock directory structure
        contents = [
            DirectoryContent('folder1', [
                Subcategory('In Topic', [JsonFile('test1.json', '{"a": 1}', '{"a": 1}')]),
                Subcategory('Out Topic', [JsonFile('test2.json', '{"b": 2}', '{"b": 2}')])
            ]),
            DirectoryContent('folder2', [
                Subcategory('In Topic', [JsonFile('test3.json', '{"c": 3}', '{"c": 3}')])
            ])
        ]

        result = generate_html_content(contents)
        self.assertIn('folder1', result)
        self.assertIn('folder2', result)
        self.assertIn('In Topic', result)
        self.assertIn('Out Topic', result)
        self.assertIn('test1.json', result)
        self.assertIn('test2.json', result)
        self.assertIn('test3.json', result)

if __name__ == '__main__':
    unittest.main()
