"""Validate the PortMaster ZIP, metadata, licenses and source layout."""
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
    files = public_files(root)
    require(files[config['script']] == (root/'package'/config['script']).read_bytes(),
            'Exported launcher must be byte-identical to package source')
    require(files['port.json'] == (root/'package/port.json').read_bytes(),
            'Exported port.json must be byte-identical to package source')
    directories = public_directories(root)
    expected = {installed_name(n, config): data for n, data in files.items()}
    expected_directories = {installed_name(n, config) for n in directories}
    with zipfile.ZipFile(root/'dist'/config['zip']) as archive:
        require(archive.testzip() is None, 'Damaged ZIP')
        names = archive.namelist()
        require(len(names) == len(expected)+len(expected_directories), 'Duplicate/extra ZIP entry')
        require(set(names) == set(expected)|expected_directories, 'Unexpected ZIP contents')
        for entry in archive.infolist():
            require(entry.filename.startswith(game+'/') or entry.filename == config['script'], 'Unsafe path')
            mode = (entry.external_attr >> 16) & 0o777
            if entry.is_dir():
                require(entry.filename in expected_directories and archive.read(entry) == b'', 'Unexpected directory: '+entry.filename)
                require(mode == 0o755, 'Wrong directory permissions')
            else:
                require(archive.read(entry) == expected[entry.filename], 'Stale file: '+entry.filename)
                require(mode == (0o755 if entry.filename.endswith('.sh') else 0o644), 'Wrong Unix permissions')
    require(sorted(p.name for p in (root/'dist').iterdir()) == [config['zip']], 'dist must contain only the universal ZIP')
    metadata = json.loads(files['port.json'])
    require(set(metadata) == {'version','name','items','items_opt','attr'}, 'Wrong PortMaster metadata fields')
    require(metadata['version'] == 4, 'Wrong metadata version')
    require(metadata['items'] == [config['script'], game] and metadata['items_opt'] == [], 'Wrong PortMaster items')
    attr = metadata['attr']
    expected_attr = {'title','porter','desc','desc_md','inst','inst_md','genres','image','rtr','exp','runtime','store','availability','reqs','arch','min_glibc'}
    require(set(attr) == expected_attr, 'Wrong PortMaster attribute fields')
    require(attr['title'] == config['title'], 'Wrong PortMaster title')
    require(isinstance(attr['porter'], list) and attr['porter'] and
            all(isinstance(name, str) and name.strip() for name in attr['porter']), 'Missing porter')
    require(attr['availability'] == 'paid' and attr['rtr'] is False and attr['exp'] is False, 'Wrong BYO flags')
    require(attr['arch'] == ['aarch64'], 'Wrong architecture')
    require(attr['runtime'] == ['weston_pkg_0.2.squashfs', 'zulu17.54.21-ca-jre17.0.13-linux.squashfs'], 'Wrong runtimes')
    require(all(set(s) == {'name','gameurl','developerurl'} for s in attr['store']), 'Invalid store objects')
    instructions = attr['inst_md']
    require(isinstance(instructions, str) and instructions.strip(), 'Missing detailed PortMaster installation instructions')
    game_destination = '<ports directory>/'+game+'/'+game_data_path(root, config).as_posix()
    require(game_destination in instructions, 'Missing exact game-data destination in metadata')
    build_source = (root/'tools/build.py').read_text(encoding='utf-8')
    hash_line = next((line for line in build_source.splitlines() if line.startswith('SHA256 =')), '')
    fingerprint = hash_line.partition('=')[2].strip().strip(chr(39)+chr(34))
    require(re.fullmatch(r'[0-9a-f]{64}', fingerprint) is not None, 'Missing supported game-data fingerprint in build configuration')
    require('SHA-256' in instructions and fingerprint in instructions, 'Missing game-data fingerprint in metadata instructions')
    require('testing_thread.txt' not in files, 'Testing thread must not be packaged')
    source_readme = (root/'README.md').read_text(encoding='utf-8')
    compile_section = '\n## Build the PortMaster package\n'
    require(compile_section in source_readme, 'Source README must separate package instructions from build instructions')
    package_readme = files['README.md'].decode('utf-8')
    require('SHA-256' in package_readme and fingerprint in package_readme, 'Package README must identify the supported game data')
    require(files['README.md'].startswith(b'## Notes\n'), 'README must start with Notes')
    require((root/'package/testing_thread.txt').read_bytes() == (root/'testing_thread.txt').read_bytes(), 'Stale testing thread')
    for name, data in files.items():
        if name.endswith(('.sh','.ini','.inc','.md','.json','.xml','.txt')):
            require(b'\r' not in data and not data.startswith(b'\xef\xbb\xbf'), 'Use UTF-8 without BOM and LF: '+name)
    require(game+'/'+config['game_file'] not in files, 'Owned game data must not be packaged')
    png = files['screenshot.png']
    require(png.startswith(b'\x89PNG\r\n\x1a\n'), 'Missing PNG screenshot')
    width, height = struct.unpack('>II', png[16:24])
    require(width >= 640 and height >= 480, 'Screenshot below 640x480')
    cover = files['cover.png']
    require(cover.startswith(b'\x89PNG\r\n\x1a\n'), 'Missing PNG cover')
    require(struct.unpack('>II', cover[16:24]) == (640, 480), 'Cover must be 640x480')
    xml = ET.fromstring(files['gameinfo.xml']).find('game')
    require(xml.findtext('path') == './'+config['script'], 'Wrong gameinfo path')
    require(xml.findtext('image') == './'+game+'/cover.png', 'Wrong gameinfo image path')
    require(xml.findtext('developer') and xml.findtext('desc'), 'Incomplete gameinfo')
    require(config['mapping'].endswith('.ini'), 'gptokeyb2 requires an INI mapping')
    launcher = files[config['script']].decode('utf-8')
    require(launcher.encode('utf-8') == (root/'package'/config['script']).read_bytes(),
            'Launcher content must remain unchanged from package source')
    require('$GPTOKEYB2 java -c ' in launcher, 'Launcher must use the port-specific gptokeyb2 INI mapping')
    require('$GPTOKEYB ' not in launcher and 'TEXTINPUTINTERACTIVE' not in launcher, 'Legacy mapper setup')
    require(not any(n.endswith('.gptk') for n in files), 'Legacy mapping in package')
    mapping = files[game+'/'+config['mapping']].decode('utf-8')
    cp = configparser.ConfigParser(interpolation=None, strict=True)
    cp.read_string(mapping)
    require(cp['controls']['start'] == ('esc' if game == 'mewnbase' else 'o'), 'Start must open options')
    if game == 'mewnbase':
        require(cp['controls']['a'] == 'mouse_left' and cp['controls']['b'] == 'mouse_right', 'MewnBase needs real mouse buttons')
    require(cp['controls'].get('overlay') == 'clear', 'Explicit root controls required')
    for section in cp.sections():
        for key, value in cp[section].items():
            require(not key.endswith('_hk'), 'Use a v2 hotkey state')
            if value.startswith(('hold_state ', 'push_state ', 'set_state ')):
                require('controls:'+value.split()[1] in cp, 'Unknown control state')
    if game == 'mewnbase':
        require(cp['controls']['back'] == 'hold_state hotkey', 'Missing hotkey state')
        require(cp['controls:hotkey']['l1'] == 'push_state text_input', 'Missing text entry')
        require(cp['controls:text_input']['start'] == 'finish_text', 'Text confirmation missing')
        require(cp['controls:text_input']['back'] == 'cancel_text', 'Text cancellation missing')
        require('<ports directory>/mewnbase/data/' in instructions, 'Missing complete MewnBase data-folder destination')
        require('1.0.2' in instructions and 'unverified' in instructions.lower(), 'Missing MewnBase 1.0.2 status')
    if game == 'gunslugs3':
        require('1.0.10b' in instructions, 'Missing Gunslugs 3 supported Windows build')
    license_root = game+'/licenses/'
    license_names = {name[len(license_root):] for name in files if name.startswith(license_root)}
    require(license_names == {'LICENSE-'+game+'-host.txt'}, 'Unexpected host license set for the current package layout')
    host_license = files[license_root+'LICENSE-'+game+'-host.txt']
    require(b'MIT License' in host_license and b'Copyright (c) 2026 Pixelforge Ports contributors' in host_license
            and b'Permission is hereby granted' in host_license, 'Missing host MIT license terms')
    with zipfile.ZipFile(io.BytesIO(files[game+'/runtime/'+game+'-host.jar'])) as host:
        require(bool(host.namelist()), 'Empty host')
        require(all(n.startswith('org/portmaster/'+game+'/') and n.endswith('.class') for n in host.namelist()), 'Game or compile-only classes leaked into host')
    tree = root/'ports'/game
    for name, data in files.items():
        require((tree/name).read_bytes() == data, 'Stale public tree: '+name)
    expected_tree_files = set(files)
    actual_tree_files = {path.relative_to(tree).as_posix() for path in tree.rglob('*') if path.is_file()}
    require(actual_tree_files == expected_tree_files, 'Port source folder must contain only freshly exported package files')
    require(not (tree/'testing_thread.txt').exists(), 'Testing thread must not be copied to the PortMaster source folder')
    expected_tree_directories = {name[len(game)+1:].rstrip('/') for name in directories}
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
