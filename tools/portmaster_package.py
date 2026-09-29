"""Build one universal BYO-data ZIP from an explicit redistributable file list."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import shutil
import zipfile

def settings(root):
    return json.loads((Path(root)/'tools/port-config.json').read_text(encoding='utf-8'))

def game_data_path(root, config):
    root = Path(root)
    metadata = json.loads((root/'package/port.json').read_text(encoding='utf-8'))
    marker = '<ports directory>/' + config['id'] + '/'
    found = set()
    for text in (metadata['attr'].get('inst', ''), metadata['attr'].get('inst_md', '')):
        for match in re.finditer(re.escape(marker) + r'([^\s`]+)', text):
            found.add(match.group(1).rstrip('.,;:'))
    if len(found) != 1:
        raise ValueError('port.json must specify one consistent game-data destination')
    relative = PurePosixPath(found.pop())
    if relative.is_absolute() or '..' in relative.parts or relative.name != config['game_file']:
        raise ValueError('Unsafe game-data destination in package/port.json')
    return Path(*relative.parts)

def public_files(root):
    root = Path(root)
    config = settings(root)
    package = root/'package'
    game = config['id']
    names = [config['script'], 'port.json', 'README.md', 'gameinfo.xml', 'screenshot.png', 'cover.png',
             game+'/display.inc', game+'/'+config['mapping'],
             game+'/runtime/'+game+'-host.jar']
    names += [p.relative_to(package).as_posix()
              for p in sorted((package/game/'licenses').iterdir()) if p.is_file()]
    lock = root/'tools/runtime-lock.json'
    if config.get('runtime_libraries'):
        for entry in json.loads(lock.read_text(encoding='utf-8')):
            if entry['test_only']:
                continue
            name = game+'/runtime/lib/'+entry['name']
            if hashlib.sha256((package/name).read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('Runtime checksum mismatch: '+name)
            names.append(name)
    files = {}
    for name in names:
        data = (package/name).read_bytes()
        if name == 'port.json':
            try:
                json.loads(data.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError('Invalid package/port.json; fix the source file directly') from error
        files[name] = data
    return files

def public_directories(root):
    config = settings(root)
    game = config['id']
    result = set()
    for raw in config.get('directories', []):
        name = raw.replace('\\', '/').strip('/')
        parts = name.split('/') if name else []
        if not parts or any(part in ('', '.', '..') for part in parts):
            raise ValueError('Invalid package directory: '+raw)
        result.add(game+'/'+name+'/')
    return sorted(result)

def installed_name(name, config):
    if '/' not in name and name != config['script']:
        return config['id']+'/'+(config['id']+'.md' if name == 'README.md' else name)
    return name

def export(root):
    root = Path(root)
    config = settings(root)
    files = public_files(root)
    directories = public_directories(root)
    tree = root/'ports'/config['id']
    ports_root = root/'ports'
    ports_root.mkdir(parents=True, exist_ok=True)
    ports_resolved = ports_root.resolve()
    tree_resolved = tree.resolve()
    try:
        tree_resolved.relative_to(ports_resolved)
    except ValueError as error:
        raise ValueError('Generated port path escapes ports/: '+str(tree)) from error
    if tree_resolved == ports_resolved or tree.is_symlink():
        raise ValueError('Refusing unsafe generated port path: '+str(tree))
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    for name in directories:
        target = (tree/name.rstrip('/')).resolve()
        target.relative_to(tree.resolve())
        target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = tree/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    destination_dir = root/'dist'
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir/config['zip']
    temporary = root/'build'/config['zip']
    temporary.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted([*files, *directories]):
            info = zipfile.ZipInfo(installed_name(name, config), (2026, 9, 12, 0, 0, 0))
            info.create_system = 3
            if name.endswith('/'):
                info.external_attr = (0o40755 << 16) | 0x10
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, b'')
            else:
                info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, files[name])
    temporary.replace(destination)
    print('Built', destination)

if __name__ == '__main__':
    export(Path(__file__).resolve().parents[1])
