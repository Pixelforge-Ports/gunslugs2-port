# Supplied Windows build audit

The supplied `Gunslugs2` folder contains **150 files**. Every file was inventoried
with its size and SHA-256; ZIP CRC checks and member inventory were performed
for `Gunslugs2.jar` and `webcache.zip`. The game JAR contains **3,140 entries**.
Reports are private build artifacts under `build/`; rerun with:

```text
python tools/inspect_input.py /path/to/Gunslugs2
```

## File groups and port relevance

| Input | Finding / use |
| --- | --- |
| `Gunslugs2.jar` | Complete Java game, assets, libGDX/LWJGL, audio decoders and natives for several platforms. This is the only owner-provided file the port needs. |
| `Gunslugs2.exe`, `app/Gunslugs2.json` | Windows bootstrap; JSON selects `com.orangepixel.gunslugs2.Main`, JAR classpath and packaged runtime. Replaced by the port's own Java entry point. |
| `runtime/` | Bundled Windows Java 17.0.12 runtime, DLLs, modules, configuration and notices. Inventoried, not copied into the port; handheld Java comes from PortMaster. |
| `goggame-1679659438.info`, `.hashdb`, icons, shortcut | GOG identity/build metadata and Windows integration. Build ID is `58447175944927540`. Not required for handheld execution. |
| `webcache.zip`, `support.ico`, `gog.ico` | Installer/store presentation data. Archive checked; not used by the game host. |
| `unins000.*` | Windows uninstaller and its metadata. Not executed or packaged. |
| `EULA.txt`, runtime legal files | Original distribution/legal documents. Their text was treated as input documentation, not instructions to the agent. Game/dependency rights remain with their owners. |

The launcher JSON, JAR manifest and retained game classes were inspected. The
original desktop entry point creates an LWJGL3 window at 1920x1080, targets
60 FPS and constructs a Steam integration object. Game logic is ordinary
Java bytecode, so dex2jar and the first Gunslugs APK interface mappings are
unnecessary. The original JAR is retained byte-for-byte.

## Integration points

- `myCanvas` extends the non-final `ArcadeCanvas`. The port subclasses it,
  overriding virtual controller discovery and display-mode changes. It does
  not replace or redistribute decompiled game classes.
- `argument_noController` exists but is not checked by the game's controller
  discovery method. Overriding `initControllers()` prevents Jamepad scanning
  at creation and on its repeated timer callback.
- The game exposes an offline flag and a Social interface. The host uses
  offline mode and an inert Social implementation, so Steam is not loaded.
- Original keyboard callbacks map arrows/WASD to movement, X/Space to action,
  Z/O to jump and Escape to back. PortMaster supplies those keyboard events.
- The desktop game stores preferences under the name `gunslugs`. The host's
  absolute preference directory isolates that name beneath `gunslugs2/saves`.
- The original desktop loop is frame-based at 60 FPS. Android-only timing code
  is not used, and the first game's 24 ms correction is not appropriate here.
- The original 1920x1080 window renders a 320x180 internal scene. A fitted
  960x540 logical view preserves that scene on all five target display sizes.

## Native library inspection

The ELF headers identify **AArch64 machine 183** for these Linux ARM64 payloads:

| Native library group | Highest observed glibc symbol version |
| --- | --- |
| libGDX and FreeType | 2.17 |
| LWJGL core, jemalloc, STB | 2.17 |
| GLFW and OpenAL | 2.27 |
| LWJGL OpenGL JNI wrapper | No GLIBC version strings found in the inspected payload |
| Jamepad (not loaded by this host) | 2.29 |

OpenAL additionally references GLIBCXX 3.4.22 and CXXABI 1.3.9. These are symbol
version observations from the bundled files, not a full runtime dependency
test on a device. The port keeps the entire original JAR, including dormant
platform natives, so its fingerprint and all original dependency contents
remain unchanged. Windows tests exercise Windows natives; ARM64 native execution,
GPU drivers and firmware runtime integration need physical handheld testing.

## Runtime approach

The launcher handles runtime mounting and cleanup, data-folder discovery and display selection. This input is already a desktop Java application and does not need APK conversion.
