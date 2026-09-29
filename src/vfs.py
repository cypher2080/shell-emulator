import base64
import binascii
import json

from src.errors import VfsError

NODE_DIR = "dir"
NODE_FILE = "file"
TEXT_ENCODING = "text"
BASE64_ENCODING = "base64"
ROOT_NAME = "/"
CHARSET = "utf-8"
JSON_INDENT = 2


class VfsNode:
    def __init__(self, name, node_type, data=b""):
        self.name = name
        self.node_type = node_type
        self.data = data
        self.children = {}

    @property
    def is_dir(self):
        return self.node_type == NODE_DIR

    def add_child(self, node):
        self.children[node.name] = node
        return node

    def names(self):
        return sorted(self.children)

    def count(self):
        return 1 + sum(child.count() for child in self.children.values())

    def to_dict(self):
        if self.is_dir:
            return {
                "name": self.name,
                "type": NODE_DIR,
                "children": [c.to_dict() for c in self.children.values()],
            }
        return _file_to_dict(self)


class Vfs:
    def __init__(self, root, source=None):
        self.root = root
        self.source = source

    @classmethod
    def load(cls, path):
        return cls(node_from_dict(_read_json(path)), path)

    @classmethod
    def default(cls, source=None):
        return cls(default_root(), source)

    def save(self):
        if not self.source:
            return False
        _write_json(self.source, self.root.to_dict())
        return True


def node_from_dict(raw):
    if not isinstance(raw, dict):
        raise VfsError("узел VFS должен быть объектом")
    name = raw.get("name", "")
    node_type = raw.get("type", NODE_FILE)
    if node_type == NODE_DIR:
        return _dir_from_dict(raw, name)
    if node_type != NODE_FILE:
        raise VfsError("неизвестный тип узла: " + str(node_type))
    return VfsNode(name, NODE_FILE, _decode_content(raw))


def default_root():
    root = VfsNode(ROOT_NAME, NODE_DIR)
    home = root.add_child(VfsNode("home", NODE_DIR))
    user = home.add_child(VfsNode("user", NODE_DIR))
    user.add_child(_text_file("hello.txt", "привет\nмир\n"))
    root.add_child(VfsNode("tmp", NODE_DIR))
    return root


def _dir_from_dict(raw, name):
    node = VfsNode(name, NODE_DIR)
    children = raw.get("children", [])
    if not isinstance(children, list):
        raise VfsError(name + ": children должен быть списком")
    for child in children:
        node.add_child(node_from_dict(child))
    return node


def _decode_content(raw):
    content = raw.get("content", "")
    encoding = raw.get("encoding", TEXT_ENCODING)
    if not isinstance(content, str):
        raise VfsError("content должен быть строкой")
    if encoding == TEXT_ENCODING:
        return content.encode(CHARSET)
    if encoding == BASE64_ENCODING:
        return _decode_base64(content)
    raise VfsError("неизвестная кодировка: " + str(encoding))


def _decode_base64(content):
    try:
        return base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as error:
        raise VfsError("неверные данные base64: " + str(error))


def _text_file(name, text):
    return VfsNode(name, NODE_FILE, text.encode(CHARSET))


def _file_to_dict(node):
    try:
        content = node.data.decode(CHARSET)
        encoding = TEXT_ENCODING
    except UnicodeDecodeError:
        content = base64.b64encode(node.data).decode("ascii")
        encoding = BASE64_ENCODING
    return {
        "name": node.name,
        "type": NODE_FILE,
        "encoding": encoding,
        "content": content,
    }


def _read_json(path):
    try:
        with open(path, encoding=CHARSET) as stream:
            return json.load(stream)
    except OSError as error:
        raise VfsError("не удалось открыть VFS: " + str(error))
    except ValueError as error:
        raise VfsError("неверный формат VFS: " + str(error))


def _write_json(path, data):
    try:
        with open(path, "w", encoding=CHARSET) as stream:
            json.dump(data, stream, ensure_ascii=False, indent=JSON_INDENT)
            stream.write("\n")
    except OSError as error:
        raise VfsError("не удалось сохранить VFS: " + str(error))
