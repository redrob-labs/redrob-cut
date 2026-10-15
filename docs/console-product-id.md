# Console product id: `film`

Redrob Film signs in to a Redrob workspace with the console's device flow (Help ▸ Connect to Redrob…,
`apps/redrob-film-app/src/device.rs`). The flow identifies the app by a **product id**, and Redrob Film's is
**`film`** (the former `cut` is gone with the rename; nothing in this repository sends it any more).

## What the console needs

The console lists the products its device flow accepts in
`mckinley-and-rice/redrob-console` → `apps/api/src/device/device-products.ts`. It needs a `film` entry
(name "Redrob Film", the same scopes as the other desktop apps) before a copy of Redrob Film can
connect on its own. **Janghoon adds that entry**; it is a console change, not one this repository can
make.

## Until then

A device-flow start the console refuses (unknown product) is reported in plain words in the Connect
dialog and the app falls back to the computer's shared sign-in: the workspace Redrob Launcher is
signed in to (`<shared config dir>/account.json`, read fresh on every use; redrob-launcher
`docs/shared-account.md`). So the instruction to a person is "sign in via Redrob Launcher"; editing
never needs an account, only the AI dock does.

## Where `film` appears

- `apps/redrob-film-app/src/device.rs`: the device-flow start body (`product: "film"`) and the tests that
  pin it.
- Redrob Launcher's catalog slug for this app is `redrob-film` (`crates/native/src/catalog.rs` in
  redrob-launcher); the in-app updater reads the launcher's `installed.json` under that key
  (`apps/redrob-film-app/src/update.rs`, `LAUNCHER_APP_ID`).
- The release assets and `redrob-launcher.json` carry the `redrob-film-<version>-…` names
  ([releasing.md](releasing.md)).
