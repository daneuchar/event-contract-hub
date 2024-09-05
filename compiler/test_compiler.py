import unittest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from event_schema_compiler import (
    JsonFile,
    Subcategory,
    DirectoryContent,
    read_json_file,
    get_example_content,
    process_json_file,
    get_json_files,
    get_directory_contents,
    generate_html_content,
    is_valid_directory,
    get_subcategory
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

    def test_read_json_file_success(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        self.create_test_file(test_file, self.example_json)
        result = read_json_file(test_file)
        self.assertEqual(result, self.example_json)

    def test_read_json_file_not_found(self):
        result = read_json_file(os.path.join(self.temp_dir, 'nonexistent.json'))
        self.assertIn('error', result)
        self.assertIn('File not found', result['error'])

    def test_read_json_file_invalid_json(self):
        test_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(test_file, 'w') as f:
            f.write('{"invalid": json}')
        result = read_json_file(test_file)
        self.assertIn('error', result)
        self.assertIn('Invalid JSON', result['error'])

    def test_get_example_content_existing_file(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        self.create_test_file(test_file, self.example_json)
        result = get_example_content(test_file)
        self.assertEqual(result, self.example_json_str)

    def test_get_example_content_missing_file(self):
        result = get_example_content(os.path.join(self.temp_dir, 'nonexistent.json'))
        self.assertEqual(result, "{}")

    def test_process_json_file_success(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        example_file = os.path.join(self.temp_dir, 'examples', 'test.json')
        self.create_test_file(test_file, self.example_json)
        self.create_test_file(example_file, self.example_json)

        result = process_json_file(test_file, example_file)
        self.assertIsInstance(result, JsonFile)
        self.assertEqual(result.name, 'test.json')
        self.assertEqual(result.content, self.example_json_str)
        self.assertEqual(result.example, self.example_json_str)
        self.assertIsNone(result.error)

    def test_process_json_file_with_error(self):
        test_file = os.path.join(self.temp_dir, 'test.json')
        example_file = os.path.join(self.temp_dir, 'examples', 'test.json')
        with open(test_file, 'w') as f:
            f.write('{"invalid": json}')
        self.create_test_file(example_file, self.example_json)

        result = process_json_file(test_file, example_file)
        self.assertIsInstance(result, JsonFile)
        self.assertEqual(result.name, 'test.json')
        self.assertEqual(result.content, '{}')
        self.assertEqual(result.example, self.example_json_str)
        self.assertIsNotNone(result.error)
        self.assertIn('Invalid JSON', result.error)

    def test_get_json_files(self):
        self.create_test_file(os.path.join(self.temp_dir, 'test1.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'test2.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'examples', 'test1.json'), self.example_json)
        self.create_test_file(os.path.join(self.temp_dir, 'examples', 'test2.json'), self.example_json)

        result = get_json_files(self.temp_dir)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], JsonFile)
        self.assertIsInstance(result[1], JsonFile)

    def test_is_valid_directory(self):
        self.assertTrue(is_valid_directory('valid_dir'))
        self.assertFalse(is_valid_directory('examples'))
        self.assertFalse(is_valid_directory('schema-compiler'))

    @patch('os.path.isdir')
    @patch('event_schema_compiler.get_json_files')
    def test_get_subcategory(self, mock_get_json_files, mock_isdir):
        mock_isdir.return_value = True
        mock_get_json_files.return_value = [JsonFile('test.json', '{}', '{}')]

        result = get_subcategory('/path', 'in topic')
        self.assertIsInstance(result, Subcategory)
        self.assertEqual(result.name, 'in topic')
        self.assertEqual(len(result.json_files), 1)

        mock_get_json_files.return_value = []
        result = get_subcategory('/path', 'empty topic')
        self.assertIsNone(result)

    @patch('os.walk')
    @patch('event_schema_compiler.get_subcategory')
    def test_get_directory_contents(self, mock_get_subcategory, mock_walk):
        mock_walk.return_value = [
            ('/root', ['dir1', 'dir2'], []),
            ('/root/dir1', ['in topic', 'out topic'], []),
            ('/root/dir2', ['in topic'], [])
        ]
        mock_get_subcategory.side_effect = [
            Subcategory('in topic', [JsonFile('test1.json', '{}', '{}')]),
            Subcategory('out topic', [JsonFile('test2.json', '{}', '{}')]),
            Subcategory('in topic', [JsonFile('test3.json', '{}', '{}')])
        ]

        result = get_directory_contents('/root')
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], DirectoryContent)
        self.assertEqual(len(result[0].subcategories), 2)
        self.assertEqual(len(result[1].subcategories), 1)

    def test_generate_html_content(self):
        contents = [
            DirectoryContent('folder1', [
                Subcategory('in topic', [JsonFile('test1.json', '{"a": 1}', '{"a": 1}')]),
                Subcategory('out topic', [JsonFile('test2.json', '{"b": 2}', '{"b": 2}')])
            ]),
            DirectoryContent('folder2', [
                Subcategory('in topic', [JsonFile('test3.json', '{"c": 3}', '{"c": 3}')])
            ])
        ]

        result = generate_html_content(contents)
        self.assertIn('folder1', result)
        self.assertIn('folder2', result)
        self.assertIn('in topic', result)
        self.assertIn('out topic', result)
        self.assertIn('test1.json', result)
        self.assertIn('test2.json', result)
        self.assertIn('test3.json', result)

    def test_generate_html_content_with_error(self):
        contents = [
            DirectoryContent('folder1', [
                Subcategory('in topic', [JsonFile('test1.json', '{}', '{}', error='Invalid JSON')])
            ])
        ]

        result = generate_html_content(contents)
        self.assertIn('folder1', result)
        self.assertIn('in topic', result)
        self.assertIn('test1.json', result)
        self.assertIn('Invalid JSON', result)  # Ensure error message is included in HTML

if __name__ == '__main__':
    unittest.main()
