"""Build one universal BYO-data ZIP from an explicit redistributable file list."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import stat
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
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != config['game_file']:
        raise ValueError('Unsafe game-data destination in package/port.json')
    return Path(*relative.parts)

def public_files(root):
    root = Path(root)
    config = settings(root)
    package = root/'package'
    game = config['id']
    names = [config['script'], 'port.json', 'README.md', 'gameinfo.xml', 'screenshot.png', 'cover.png',
             game+'/display.inc', game+'/'+config['mapping'],
             game+'/gamedata/PLACE_GAMEDATA_HERE.txt',
             game+'/runtime/'+game+'-host.jar']
    names += [p.relative_to(package).as_posix()
              for p in sorted((package/game/'licenses').iterdir()) if p.is_file()]
    lock = root/'tools/runtime-lock.json'
    if config.get('runtime_libraries'):
        for entry in json.loads(lock.read_text(encoding='utf-8')):
            if entry['test_only']:
                continue
            library_dir = Path(entry.get('directory', 'runtime/lib'))
            if library_dir.is_absolute() or '..' in library_dir.parts:
                raise ValueError('Unsafe runtime library directory: '+str(library_dir))
            name = (Path(game)/library_dir/entry['name']).as_posix()
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
    game = config['id']
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
    tree.mkdir(parents=True, exist_ok=True)

    data_path = game_data_path(root, config)
    data_directory = (tree/game/data_path.parent).resolve()
    data_directory.relative_to(tree.resolve())
    manifest = root/'build/portmaster-export.json'
    previous = []
    if manifest.is_file():
        saved = json.loads(manifest.read_text(encoding='utf-8'))
        previous = saved.get('files', []) if isinstance(saved, dict) else saved
        if not isinstance(previous, list) or not all(isinstance(name, str) for name in previous):
            raise ValueError('Invalid generated port manifest: '+str(manifest))

    for name in previous:
        if name in files:
            continue
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('Unsafe path in generated port manifest: '+name)
        target = tree.joinpath(*relative.parts)
        resolved = target.resolve()
        resolved.relative_to(tree.resolve())
        if resolved == data_directory or data_directory in resolved.parents:
            continue
        if target.is_symlink():
            raise ValueError('Refusing to remove generated path through a symlink: '+str(target))
        if target.is_file():
            target.chmod(target.stat().st_mode | stat.S_IWRITE)
            target.unlink()

    for name in directories:
        target = (tree/name.rstrip('/')).resolve()
        target.relative_to(tree.resolve())
        target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = tree/name
        if target.is_symlink():
            raise ValueError('Refusing to overwrite generated path through a symlink: '+str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.chmod(target.stat().st_mode | stat.S_IWRITE)
        target.write_bytes(data)

    for directory in sorted((path for path in tree.rglob('*') if path.is_dir()),
                            key=lambda path: len(path.parts), reverse=True):
        resolved = directory.resolve()
        if resolved == data_directory or data_directory in resolved.parents or resolved in data_directory.parents:
            continue
        try:
            directory.rmdir()
        except OSError:
            pass

    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = manifest.with_suffix('.json.tmp')
    temporary_manifest.write_text(json.dumps({'files': sorted(files)}), encoding='utf-8')
    os.replace(temporary_manifest, manifest)
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
