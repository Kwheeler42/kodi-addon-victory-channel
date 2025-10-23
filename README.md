# Victory Channel (Kodi)

Browse and play Victory Channel programs.

Install
- Kodi → Settings → Add-ons → Unknown sources: enable.
- Download the release ZIP from GitHub Releases.
- Install from zip file → select the downloaded ZIP.

Development install (macOS)
- Symlink:
  ln -sfn "$PWD" "$HOME/Library/Application Support/Kodi/addons/plugin.video.victorychannel"
- Restart Kodi.

Settings
- API URL: backend endpoint.
- Request timeout: network timeout in seconds.
- Enable debug logging: logs to kodi.log.

Build ZIP
- ./scripts/build-zip.sh

License
- MIT
