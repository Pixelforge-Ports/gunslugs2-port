# Controller support

All input is supplied through PortMaster's gptokeyb2 and the shipped `.ini` mapping.
Update PortMaster before installing. Native Xbox 360 emulation is not enabled in this
host: its native controller path is disabled. The mapper's `-x` mode replaces keyboard
and mouse output and requires a working native controller backend in the game.
Do not add `-x` to this launcher; it would bypass the controls listed above.

Reviewed against the supplied PortMaster complete reference and gptokeyb2
upstream revision 7100d030fe10a7cd5f3053cd9922249498ab3a8d.

- https://github.com/PortsMaster/gptokeyb2/blob/master/ADVANCED_USAGE.md
- https://github.com/PortsMaster/gptokeyb2/blob/master/src/main.c

Native controller support would require a separate host/backend implementation
and device tests for menu navigation, gameplay, input duplication and exit.
The presence of controller support in the original Windows game alone does not
verify that its controller backend runs in this ARM64 Java port.
