"""Build the Gunslugs 2 PortMaster host and BYO-data ZIP without modifying package/."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import zipfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SHA256 = '8f92f9ea2f84b055be744f98b911dbcdc6f8199bd1ec75b54338bff3ffffa913'


def add(out, source, target):
    entry = zipfile.ZipInfo(target, (2026, 9, 9, 0, 0, 0))
    entry.create_system = 3
    entry.external_attr = (0o100755 if target.endswith('.sh') else 0o100644) << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    out.writestr(entry, source.read_bytes())


def package_snapshot():
    package = ROOT/'package'
    return {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package.rglob('*') if path.is_file()
    }


def ensure_package_unchanged(before):
    after = package_snapshot()
    if before != after:
        changed = sorted(set(before)^set(after) | {name for name in before.keys() & after.keys() if before[name] != after[name]})
        raise SystemExit('Build changed package/ file(s): '+', '.join(changed))
    print('PACKAGE_UNCHANGED', len(after), 'files')


def package(generated_host=None):
    from portmaster_package import export
    export(ROOT, generated_host)
    from verify_package import verify
    verify(ROOT, generated_host)


DEPENDENCIES = {
    'gdx': 'd5860eaf5787a4083e14183ae47da99d3e6908029ca99691947bbd0852b49264',
    'gdx-backend-lwjgl3': '963d49a2846d294d13a5beb2d9a8e51bd7d32fac78a35bfeca23ebf8f1ec2d64',
}


def dependencies(offline=False):
    folder = ROOT/'build/dependencies'
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for artifact, digest in DEPENDENCIES.items():
        name = artifact+'-1.13.1.jar'
        path = folder/name
        if not path.is_file():
            if offline:
                raise SystemExit('Missing cached dependency: '+str(path))
            url = 'https://repo.maven.apache.org/maven2/com/badlogicgames/gdx/'+artifact+'/1.13.1/'+name
            print('Downloading', name, flush=True)
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise SystemExit('Dependency checksum mismatch: '+name)
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise SystemExit('Cached dependency checksum mismatch: '+name)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-jar', type=Path, help='Optional compatibility fingerprint check; never used for compilation')
    parser.add_argument('--jdk', type=Path)
    parser.add_argument('--offline', action='store_true', help='Use only cached compile dependencies')
    parser.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    package_before = package_snapshot()

    if args.package_only:
        package()
        ensure_package_unchanged(package_before)
        return
    if not args.jdk:
        parser.error('--jdk is required')
    if args.game_jar and hashlib.sha256(args.game_jar.read_bytes()).hexdigest() != SHA256:
        parser.error('Unsupported game JAR fingerprint')
    suffix = '.exe' if os.name == 'nt' else ''
    javac = args.jdk.resolve()/'bin'/('javac'+suffix)
    if not javac.is_file():
        parser.error('JDK compiler not found: '+str(javac)+'. Use the installed JDK directory, quoted with double quotes on Windows.')

    classes = ROOT/'build/classes'
    classes.mkdir(parents=True, exist_ok=True)
    for old in classes.rglob('*.class'):
        old.resolve().relative_to(classes.resolve())
        old.unlink()
    cp = os.pathsep.join(str(path) for path in dependencies(args.offline))
    sources = sorted((ROOT/'compile-api').rglob('*.java'))+sorted((ROOT/'src').rglob('*.java'))
    subprocess.run([str(javac), '--release', '8', '-Xlint:-options', '-encoding', 'UTF-8',
                    '-cp', cp, '-d', str(classes), *map(str, sources)], check=True)

    host_classes = sorted((classes/'org/portmaster/gunslugs2').rglob('*.class'))
    if not host_classes:
        raise SystemExit('No Gunslugs 2 host classes were produced')
    artifact_dir = ROOT/'build/artifacts'
    artifact_dir.mkdir(parents=True, exist_ok=True)
    generated_host = artifact_dir/'gunslugs2-host.jar'
    temporary = artifact_dir/'gunslugs2-host.jar.tmp'
    with zipfile.ZipFile(temporary, 'w') as out:
        for path in host_classes:
            add(out, path, path.relative_to(classes).as_posix())
    with zipfile.ZipFile(temporary) as host:
        if host.testzip() is not None:
            raise SystemExit('Generated host JAR failed its archive check')
    temporary.replace(generated_host)
    package(generated_host)
    ensure_package_unchanged(package_before)


if __name__ == '__main__':
    main()
