## Notes

Thanks to [Orangepixel](https://orangepixel.net/) for creating **Gunslugs 2**. Run, jump and shoot through chaotic action-platforming missions against the Black Duck Army. PortMaster adaptation by **Pixelforge Ports (Ronax)**.

## Get Gunslugs2.jar from GOG

1. Open [Gunslugs 2 on GOG](https://www.gog.com/en/game/gunslugs_2) in your owned library and download the **full Windows offline backup installer** for the supported build (fingerprint listed below). Download every accompanying `.bin` part, if listed, and keep them beside the `.exe`. Use the full installer, not a patch or the Galaxy installer.
2. Run the installer on Windows and open the installed game directory. Find `Gunslugs2.jar` beside the game executable. Enable file extensions in Explorer so its name is visible.
3. Copy that file unchanged into the installed port at `<ports directory>/gunslugs2/gamedata/Gunslugs2.jar`. Keep its exact name, capitalization and spaces. The Windows EXE and bundled Windows Java runtime are not needed.

Alternatively, extract your full offline installer using [innoextract](https://constexpr.org/innoextract/).
Run `innoextract -d extracted "your-full-offline-installer.exe"`, then locate `Gunslugs2.jar`
inside the extracted files (usually `extracted/app/`) and copy it to the same destination.
Installer layouts vary; use Windows installation if your extractor cannot read that installer.
Do not unpack or rename the game archive itself.

No game-data conversion is required on a PC or handheld. The handheld verifies the supplied
archive and creates its save folders. It cannot generate the purchased game data from nothing.

Supported archive SHA-256 (`Gunslugs2.jar`):

```text
8f92f9ea2f84b055be744f98b911dbcdc6f8199bd1ec75b54338bff3ffffa913
```

Compare it with `Get-FileHash -Algorithm SHA256 "Gunslugs2.jar"` in PowerShell,
or `sha256sum "Gunslugs2.jar"` on Linux. A different build needs a compatibility check.

## Installation

1. Update PortMaster. Put **Gunslugs2.zip** in PortMaster's `autoinstall/` directory, then open PortMaster to install it. Connect to the network to download Java 17 and Westonpack if they are not installed yet.
2. Copy the owned file to **`<ports directory>/gunslugs2/gamedata/Gunslugs2.jar`**.
3. Launch **Gunslugs 2** from your firmware's ports menu.

The launcher detects display size and supports **640x480**, **720x480**, **720x720**, **1024x768**, **1280x720**, and other valid PortMaster dimensions while preserving aspect ratio. If detection is wrong, put the actual size, such as `720x480`, in `gunslugs2/resolution.txt`; use `auto` or remove the file to restore automatic detection.

Back up **`gunslugs2/saves/`** before updating. If startup fails, check **`gunslugs2/log.txt`**. When reporting a problem, include the device, firmware version, resolution, reproduction steps, and log. Keep purchased game files private.

## Controls

| Control | Keyboard input / action |
|---|---|
| D-pad up | UP / Up / navigate |
| D-pad down | DOWN / Down / navigate |
| D-pad left | LEFT / Left / navigate |
| D-pad right | RIGHT / Right / navigate |
| A | X / Action / confirm |
| B | Z |
| X | UP / Up / navigate |
| Y | DOWN / Down / navigate |
| L1 | X / Action / confirm |
| R1 | Z |
| L2 | X / Action / confirm |
| R2 | Z |
| Start | O / Options |
| Select | ESC / Back / pause |
| Left stick | Same directions as the D-pad |
| Select + Start | Exit; save through the game first |

Use the game's default keyboard bindings. Start sends **O** for options.
