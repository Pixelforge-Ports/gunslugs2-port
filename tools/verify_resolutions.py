"""Run Java 17 desktop integration checks; does not emulate handheld hardware."""
import argparse
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SIZES = ((640,480),(720,480),(720,720),(1024,768),(1280,720))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jdk',required=True,type=Path)
    parser.add_argument('--java',required=True,type=Path)
    parser.add_argument('--game-jar',required=True,type=Path)
    args = parser.parse_args()
    jdk, java, game = args.jdk.resolve(), args.java.resolve(), args.game_jar.resolve()
    host = ROOT/'package/gunslugs2/runtime/gunslugs2-host.jar'
    tests = ROOT/'build/test-classes'; tests.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(jdk/'bin'/('javac.exe' if os.name=='nt' else 'javac')),'--release','8','-Xlint:-options',
                    '-cp',os.pathsep.join((str(host),str(game))),'-d',str(tests),
                    str(ROOT/'tests/GameplaySmoke.java')],check=True)
    cp = os.pathsep.join((str(tests),str(host),str(game)))
    for width,height in SIZES:
        out = ROOT/'build/resolutions'/f'{width}x{height}'; out.mkdir(parents=True,exist_ok=True)
        command = [str(java),'-Xms32m','-Xmx256m','-XX:+UseSerialGC',f'-Dgunslugs2.width={width}',f'-Dgunslugs2.height={height}',
                   '-Dgunslugs2.hidden=true',f'-Dgunslugs2.saves={out/"saves"}',
                   f'-Dgunslugs2.output={out}','-Xlog:class+load=info:file=classes.log',
                   '-cp',cp,'org.portmaster.gunslugs2.GameplaySmoke']
        print(f'Checking {width}x{height}',flush=True)
        with (out/'run.log').open('w',encoding='utf-8') as log:
            subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        text = (out/'run.log').read_text(encoding='utf-8')
        assert 'GAMEPLAY_OK' in text, text
        assert f'GAME_RESIZE_OK {width}x{height}' in text, text
        classes = (out/'classes.log').read_text(encoding='utf-8')
        assert 'com.codedisaster.steamworks.SteamAPI source:' not in classes
        assert 'com.studiohartman.jamepad.ControllerManager source:' not in classes
        for frame in (180,900,1200,1400,1600,1800):
            png = (out/f'frame-{frame}.png').read_bytes()
            assert struct.unpack('>II',png[16:24])==(width,height)
        assert (out/'saves/gunslugs').is_file(), 'Settings not saved in isolated root'
        print(f'RESOLUTION_OK {width}x{height}: 1800 frames; saves and native-backend isolation checked',flush=True)
    print('RESOLUTION_MATRIX_OK: inspect captures; physical hardware remains untested')

if __name__ == '__main__': main()
