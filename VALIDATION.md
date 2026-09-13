# Validation

Porter: Pixelforge ports (Ronax)

The host and universal BYO ZIP compile without purchased game files. Build with
`python tools/build.py --jdk "<installed JDK directory>"`, then run:

```sh
python tools/verify_package.py
bash tests/verify_display.sh
python tests/verify_launcher.py
```

Package checks verify the allowlisted files, host class boundary, licenses,
metadata, LF endings, Unix ZIP permissions and generated PortMaster tree.
Launcher tests use mock runtimes; no game files, real mounts or handheld are needed.
Optional gameplay tests require your owned archive and a desktop Java 17 runtime;
they never belong to the game-independent package build.

Physical testing of this updated package is still needed on the target firmware.
Use `testing_thread.txt` to record device, version, resolution and observed results.

## Recorded checks: 2026-09-12

- JDK 26 compilation targeting Java 8 succeeded using only public libGDX compile dependencies and handwritten declarations.
- Fresh source-only build without the purchased JAR/DAT or MewnBase data succeeded. Its final ZIP exactly matches this release.
- Before the MewnBase input change, the declaration-based host classes matched reference compilation against the owned game classes byte for byte for all 12 ports.
- Package boundary, metadata, license, LF and ZIP permission checks passed.
- Display-helper checks passed for 640x480, 720x480, 720x720, 1024x768 and 1280x720, plus overrides and invalid inputs.
- Nine launcher scenarios passed: missing data, success, game failure, invalid data, invalid resolution, wrong architecture, failed mount, firmware with mount replacement, and failed runtime download.
- The current PortMaster-New `tools/build_release.py --do-check` passed for all 12 generated port trees, with no warnings or errors. This was a local check only.

Archive: `Gunslugs2.zip`
SHA-256: `b9b83fdc06a2b56644abc5041dcd5c812c9daf9c66ba21e4d932fc5881b2e1cc`

The source tree retains backups and previous private outputs only under ignored `build/`.
Neither GitHub nor PortMaster received an upload from these checks.

## gptokeyb2 verification

All release launchers now require GPTOKEYB2 and real INI controls. Strict INI checks
validate the root mapping and referenced states and reject legacy mappings.
All 108 mocked launcher scenarios passed with only GPTOKEYB2 available.
The rebuilt ZIPs match the game-data-free fixtures byte for byte. The official
PortMaster checker passed for all twelve updated trees without warnings or errors.
Mouse, text-entry and controller behavior still require physical handheld testing.
Native Xbox 360 emulation is not enabled; see docs/CONTROLLERS.md.
