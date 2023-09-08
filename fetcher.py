from subprocess import run
from typing import Any, Dict, List
import os
import re

from readability import Document
from html2text import html2text
import requests

class Fetcher:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.timeout_seconds: int = config['timeout_seconds']
        self.cache_dir: int = config['cache_dir']
        self.cached_files: List[str] = []

    def fetch_and_convert(self, url: str, title: str = None, save_to_file: bool = True) -> str:
        html = self.fetch(url)
        output_file_path = self.convert_html(html, title=title, save_to_file=save_to_file)

        return output_file_path

    def fetch(self, url: str) -> str:
        response = requests.get(url, timeout=self.timeout_seconds)
        return response.text

    def convert_html(self, html: str, title: str = None, save_to_file: bool = True) -> str:
        doc = Document(html)
        content = html2text(doc.summary())

        if not save_to_file:
            return content

        if title is None:
            title = re.sub(r'[\?\.\/\\\'\#\:•\s]', '_', doc.title())

        input_file_path = self.convert_text(title, content)

        output_file_path = os.path.join(self.cache_dir, f'{title}.epub')
        run(['pandoc', '-o', output_file_path, '--metadata', f'title="{title}"', input_file_path], check=True)

        self.cached_files.extend([input_file_path, output_file_path])

        return output_file_path

    def convert_text(self, title: str, content: str) -> str:
        input_file_path = os.path.join(self.cache_dir, f'{title}.md')
        self.write_to_file(input_file_path, content)

        return input_file_path

    def delete_cached_files(self) -> None:
        for cached_file in self.cached_files:
            os.remove(cached_file)

    def write_to_file(self, input_file_path: str, content: str) -> None:
        if not os.path.exists(self.cache_dir) or not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        with open(input_file_path, 'w') as cache_file:
            cache_file.write(content)

        self.cached_files.append(input_file_path)
