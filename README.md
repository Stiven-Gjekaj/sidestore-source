# SideStore source

The iOS apps of Stiven Gjekaj, for SideStore and AltStore.

## Add the source

In SideStore or AltStore, open Sources, tap the plus button, and enter:

```
https://stiven-gjekaj.github.io/sidestore-source/apps.json
```

## Apps

| App | Repository |
| --- | --- |
| ZettaStream | [Stiven-Gjekaj/ZettaStreamIOS](https://github.com/Stiven-Gjekaj/ZettaStreamIOS) |

## How it works

- `source.json` holds the name and the look of the source.
- Each file in `apps/` names one app, the GitHub repository of its releases,
  the IPA asset, and the changelog.
- `scripts/build.py` reads the releases of each app and writes `apps.json`.
  Each release with the IPA becomes one version. Its text comes from the
  changelog at the tag of the release.
- The Publish workflow runs the tests, builds `apps.json`, and publishes it
  with GitHub Pages. It runs on each push, every six hours, and by hand.

## Add an app

1. Copy `apps/zettastream.json` to a new file in `apps/`.
2. Change the repository, the asset, and the app fields.
3. Push. The workflow publishes the new source.

## Test

```
python3 -m unittest discover scripts
```

## License

MIT. See [LICENSE](LICENSE).
