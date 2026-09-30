"""Validate the Gunslugs 2 PortMaster package and exported port tree."""
import configparser
import io
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from portmaster_package import settings, public_files, public_directories, installed_name, game_data_path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    root = Path(root)
    config = settings(root)
    game = config['id']
    package = root/'package'
    files = public_files(root)
    require(files[config['script']] == (package/config['script']).read_bytes(),
            'Exported launcher must be byte-identical to package source')
    require(files['port.json'] == (package/'port.json').read_bytes(),
            'Exported port.json must be byte-identical to package source')
    directories = public_directories(root)
    expected = {installed_name(name, config): data for name, data in files.items()}
    expected_directories = {installed_name(name, config) for name in directories}
    with zipfile.ZipFile(root/'dist'/config['zip']) as archive:
        require(archive.testzip() is None, 'Damaged ZIP')
        entries = archive.namelist()
        require(len(entries) == len(expected)+len(expected_directories), 'Duplicate/extra ZIP entry')
        require(set(entries) == set(expected)|expected_directories, 'Unexpected ZIP contents')
        for entry in archive.infolist():
            require(entry.filename.startswith(game+'/') or entry.filename == config['script'], 'Unsafe path')
            mode = (entry.external_attr >> 16) & 0o777
            if entry.is_dir():
                require(entry.filename in expected_directories and archive.read(entry) == b'',
                        'Unexpected directory: '+entry.filename)
                require(mode == 0o755, 'Wrong directory permissions')
            else:
                require(archive.read(entry) == expected[entry.filename], 'Stale file: '+entry.filename)
                require(mode == (0o755 if entry.filename.endswith('.sh') else 0o644), 'Wrong Unix permissions')
    require(sorted(path.name for path in (root/'dist').iterdir()) == [config['zip']],
            'dist must contain only the universal ZIP')

    metadata = json.loads(files['port.json'])
    require(set(metadata) == {'version', 'name', 'items', 'items_opt', 'attr'}, 'Wrong metadata fields')
    require(metadata['version'] == 4 and metadata['name'] == config['zip'], 'Wrong metadata version/name')
    require(metadata['items'] == [config['script'], game] and metadata['items_opt'] == [], 'Wrong items')
    attr = metadata['attr']
    required_attr = {'title', 'porter', 'desc', 'desc_md', 'inst', 'inst_md', 'genres', 'image',
                     'rtr', 'exp', 'runtime', 'store', 'availability', 'reqs', 'arch', 'min_glibc'}
    require(set(attr) == required_attr, 'Wrong PortMaster attribute fields')
    require(attr['title'] == config['title'], 'Wrong metadata title')
    require(isinstance(attr['porter'], list) and attr['porter'] and
            all(isinstance(name, str) and name.strip() for name in attr['porter']), 'Missing porter')
    require(attr['availability'] == 'paid' and attr['rtr'] is False and attr['exp'] is False, 'Wrong BYO flags')
    require(attr['arch'] == ['aarch64'], 'Wrong architecture')
    require(attr['runtime'] == ['weston_pkg_0.2.squashfs', 'zulu17.54.21-ca-jre17.0.13-linux.squashfs'],
            'Wrong runtimes')
    require(all(set(store) == {'name', 'gameurl', 'developerurl'} for store in attr['store']),
            'Invalid store objects')

    data_path = game_data_path(root, config).as_posix()
    destination = '<ports directory>/'+game+'/'+data_path
    require(destination in attr['inst'] and destination in attr['inst_md'],
            'Metadata must give the exact game-data destination')
    build_source = (root/'tools/build.py').read_text(encoding='utf-8')
    hash_line = next((line for line in build_source.splitlines() if line.startswith('SHA256 =')), '')
    fingerprint = hash_line.partition('=')[2].strip().strip(chr(39)+chr(34))
    require(re.fullmatch(r'[0-9a-f]{64}', fingerprint) is not None, 'Missing game-data fingerprint')
    require('SHA-256' in attr['inst_md'] and fingerprint in attr['inst_md'],
            'Metadata instructions must identify the supported game data')
    require(game+'/'+data_path not in files, 'Owned game data must not be packaged')
    require('testing_thread.txt' not in files, 'Testing thread must not be packaged')
    require((package/'testing_thread.txt').read_bytes() == (root/'testing_thread.txt').read_bytes(),
            'Stale testing thread')

    readme = files['README.md'].decode('utf-8')
    require(readme.startswith('## Notes\n'), 'Package README must start with Notes')
    require('SHA-256' in readme and fingerprint in readme, 'Package README must identify supported game data')
    source_readme = (root/'README.md').read_text(encoding='utf-8')
    require('\n## Build the PortMaster package\n' in source_readme,
            'Source README must include package build instructions')
    for name, data in files.items():
        if name.endswith(('.sh', '.ini', '.inc', '.md', '.json', '.xml', '.txt')):
            require(b'\r' not in data and not data.startswith(b'\xef\xbb\xbf'),
                    'Use UTF-8 without BOM and LF: '+name)

    screenshot = files['screenshot.png']
    cover = files['cover.png']
    require(screenshot.startswith(b'\x89PNG\r\n\x1a\n'), 'Missing PNG screenshot')
    require(cover.startswith(b'\x89PNG\r\n\x1a\n'), 'Missing PNG cover')
    width, height = struct.unpack('>II', screenshot[16:24])
    require(width >= 640 and height >= 480, 'Screenshot below 640x480')
    require(struct.unpack('>II', cover[16:24]) == (640, 480), 'Cover must be 640x480')
    xml = ET.fromstring(files['gameinfo.xml']).find('game')
    require(xml.findtext('path') == './'+config['script'], 'Wrong gameinfo path')
    require(xml.findtext('image') == './'+game+'/cover.png', 'Wrong gameinfo cover path')
    require(xml.findtext('developer') and xml.findtext('desc'), 'Incomplete gameinfo')

    require(config['mapping'].endswith('.ini'), 'gptokeyb2 requires an INI mapping')
    launcher = files[config['script']].decode('utf-8')
    require('$GPTOKEYB2 java -c ' in launcher, 'Launcher must use gptokeyb2')
    require('$GPTOKEYB ' not in launcher and 'TEXTINPUTINTERACTIVE' not in launcher,
            'Legacy mapper setup')
    mapping = files[game+'/'+config['mapping']].decode('utf-8')
    controls = configparser.ConfigParser(interpolation=None, strict=True)
    controls.read_string(mapping)
    require(controls['controls']['start'] == 'o', 'Start must open options')
    require(controls['controls'].get('overlay') == 'clear', 'Explicit root controls required')
    for section in controls.sections():
        for key, value in controls[section].items():
            require(not key.endswith('_hk'), 'Use a v2 hotkey state')
            if value.startswith(('hold_state ', 'push_state ', 'set_state ')):
                require('controls:'+value.split()[1] in controls, 'Unknown control state')

    license_root = game+'/licenses/'
    licenses = {name[len(license_root):] for name in files if name.startswith(license_root)}
    require(licenses == {'LICENSE-gunslugs2-host.txt', 'LICENSE-libjpeg-turbo.txt'},
            'Package must include the Gunslugs2 host and libjpeg licenses')
    host_license = files[license_root+'LICENSE-gunslugs2-host.txt']
    require(b'MIT License' in host_license and
            b'Copyright (c) 2026 Pixelforge Ports contributors' in host_license and
            b'Permission is hereby granted' in host_license, 'Missing Gunslugs2 host MIT terms')
    jpeg_license = files[license_root+'LICENSE-libjpeg-turbo.txt'].lower()
    require(b'libjpeg-turbo' in jpeg_license, 'Missing libjpeg-turbo license')
    host_jar = game+'/runtime/'+game+'-host.jar'
    with zipfile.ZipFile(io.BytesIO(files[host_jar])) as host:
        require(bool(host.namelist()), 'Empty host JAR')
        require(all(name.startswith('org/portmaster/'+game+'/') and name.endswith('.class')
                    for name in host.namelist()), 'Game or compile-only classes leaked into host')

    tree = root/'ports'/game
    for name, data in files.items():
        require((tree/name).read_bytes() == data, 'Stale public tree: '+name)
    expected_tree_files = set(files)
    actual_tree_files = {path.relative_to(tree).as_posix() for path in tree.rglob('*') if path.is_file()}
    require(actual_tree_files == expected_tree_files, 'Port source folder must contain only exported package files')
    require(not (tree/'testing_thread.txt').exists(), 'Testing thread must not be copied to the port source folder')
    expected_tree_directories = {name.rstrip('/') for name in directories}
    for name in expected_tree_files:
        parent = Path(name).parent
        while str(parent) not in ('', '.'):
            expected_tree_directories.add(parent.as_posix())
            parent = parent.parent
    actual_tree_directories = {path.relative_to(tree).as_posix() for path in tree.rglob('*') if path.is_dir()}
    require(actual_tree_directories == expected_tree_directories, 'Port source folder contains stale directories')
    print('PACKAGE_OK', config['zip'], len(expected), 'files and', len(expected_directories), 'directories')


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
