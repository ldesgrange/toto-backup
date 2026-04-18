# Toto backup

Simple tool to back up your Yoto cards.

![Github Actions](https://github.com/ldesgrange/toto-backup/workflows/Build/badge.svg)

## Usage

- Read your Yoto card and copy the associated URL (it should look like `https://yoto.io/XXXXX?ABCDEFGHIJKL=MNOPQRSTUVWXY`).
  You can download an NFC reader application on your smartphone to do that:
  - Android: [NFC Tools](https://play.google.com/store/apps/details?id=com.wakdev.wdnfc)
  - iOS: [NFC Tools](https://apps.apple.com/app/nfc-tools/id1252962749)
- Download the latest `toto-backup.pyz` version from https://github.com/ldesgrange/toto-backup/releases.
- In a terminal, run: `python toto-backup.pyz URL` where `URL` is replaced with the URL present on your Yoto card.
  That will create a folder with the tracks, icons and cover art in it.

Compatibility:

| Card type         | Supported | Comments                                                    |
|-------------------|:---------:|-------------------------------------------------------------|
| Regular story     |    ✔️     |                                                             |
| MYO               |    ✔️     |                                                             |
| Interactive story |    ✔️❌    | All tracks are backed-up, but no support for interactivity. |
| Stream            |     ❓     | Not tested but unlikey to work.                             |
| Yoto Original     |     ❌     | Returns 404, probably use undocumented API.                 |

Supported audio formats:
- MP3
- M4A
- OGG (Vorbis and Opus)

## Development environment

- [Install mise-en-place](https://mise.jdx.dev/getting-started.html#installing-mise-cli) and [activate](https://mise.jdx.dev/getting-started.html#activate-mise) it.
- Clone repository: `git clone https://github.com/ldesgrange/toto-backup`
- Go into the project directory and initialize it:
  ```
  mise trust  # Look at mise.toml first to know what’s going to happen.
  mise install
  ```
- Git hooks are installed automatically by `mise install` via `pre-commit`.
- Run all commit-time checks once on the whole repository: `pre-commit run --all-files`
- Run pre-push checks once on the whole repository: `pre-commit run --hook-stage pre-push --all-files`
- Run tests: `mise run test`
- Format code: `mise run fmt`
- Check code: `mise run lint`
- Check types: `mise run typecheck`
- Check for known vulnerabilities: `mise run audit`
- Run all checks: `mise run check`
- Run the app: `mise run run --url="URL"`
- Build the app: `mise run build`
- Generate a zipapp: `mise run pyz`

## Release

- Update version in `pyproject.toml` and commit/push it.
- Add tag `git tag -a vX.Y.Z -m "Release version X.Y.Z"`
- Push tag:
  `git push origin vX.Y.Z`

## Update

- Update tools (`python`, `pdm`): `mise update --interactive --bump`
- Update dependencies: `pdm update`
- Update pre-commit hooks (frozen/pinned to commit SHA): `pre-commit autoupdate --freeze`
- Validate updated hooks: `pre-commit run --all-files && pre-commit run --hook-stage pre-push --all-files`
