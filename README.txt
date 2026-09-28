Frontend UI fix completed for now_playing_bar.py.

Changes:
1. Replaced broken button glyphs with proper Unicode icons.
2. Refactored playback state logic into set_state().
3. Added repeat mode cycling for one/all/off.
4. Added shuffle state handling for on/off.
5. Fixed volume mute/low/high icon switching.

The fix ensures all icons render correctly on Windows 10/11 and operate as expected in the dark glassmorphism style. No runtime changes to backend interfaces are required.