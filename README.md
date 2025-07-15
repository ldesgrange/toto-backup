# Toto backup

Simple tool to back up your Yoto cards.

## Usage

- Read your Yoto card and copy the associated URL (it should look like `https://yoto.io/XXXXX?ABCDEFGHIJKL=MNOPQRSTUVWXY`).
  You can download an NFC reader application on your smartphone to do that:
  - Android: [NFC Tools](https://play.google.com/store/apps/details?id=com.wakdev.wdnfc)
  - iOS: [NFC Tools](https://apps.apple.com/app/nfc-tools/id1252962749)
- In a terminal, run: `toto-backup URL` where `URL` is replaced with the URL present on your Yoto card.
  That will create a folder with the tracks, icons and cover art in it.

## Development environment

- [Install mise-en-place](https://mise.jdx.dev/getting-started.html#installing-mise-cli) and [activate](https://mise.jdx.dev/getting-started.html#activate-mise) it.
- Clone repository: `git clone https://github.com/ldesgrange/toto-backup`
- Go into the project directory and initialize it:
  ```
  mise trust  # Look at mise.toml first to know what’s going to happen.
  mise install
  ```
- Run tests: `pytest`
- Format code: `ruff format`
- Check code: `ruff check --fix`
- Check types: `mypy src`
- Check for known vulnerabilities: `pip-audit`
- Run the app: `pdm run toto_backup URL`
- Build the app: `pdm build`
