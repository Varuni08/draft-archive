# Third-party tool licenses (check before adding anything new)

| Tool               | License                  | How we use it              |
|---------------------|--------------------------|-----------------------------|
| Piper TTS           | MIT                      | subprocess CLI call         |
| Remotion (core)      | MIT                      | subprocess CLI call against our own composition project |
| FFmpeg (stock build) | LGPL                     | subprocess CLI call         |
| static-ffmpeg (fallback binaries) | LGPL (same FFmpeg binaries, just auto-fetched) | subprocess CLI call |
| Wikimedia Commons API| public domain / CC       | HTTP API call                |
| Internet Archive     | public domain (varies by item — check per-item license) | HTTP API call |
| NASA image/video lib | public domain            | HTTP API call                |

Rule before adding a new tool: confirm its license here first. Avoid
AGPL/GPL libraries you'd need to *import* (subprocess calls to a GPL CLI are
fine; importing GPL Python code into this project is not, since that would
make this project's code subject to that license too).