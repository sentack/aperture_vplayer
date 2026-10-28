#!/usr/bin/env bash
# Sign dist/Aperture.app, wrap it in a .dmg, and notarize it when credentials are present.
#
#   packaging/macos/build-dmg.sh 0.2.0
#
# Signing and notarization are opt-in through the environment:
#   MACOS_SIGN_IDENTITY   "Developer ID Application: Name (TEAMID)", already in a keychain.
#                         Unset: the app is ad-hoc signed and Gatekeeper warns on first open.
#   APPLE_ID, APPLE_TEAM_ID, APPLE_APP_PASSWORD
#                         All three set: notarize with notarytool and staple the ticket.
set -euo pipefail

version="${1:?usage: build-dmg.sh VERSION}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dist="$root/dist"
app="$dist/Aperture.app"
dmg="$dist/Aperture-$version-macos-$(uname -m).dmg"
entitlements="$root/packaging/macos/entitlements.plist"
identity="${MACOS_SIGN_IDENTITY:--}"

[[ -d "$app" ]] || { echo "run pyinstaller packaging/aperture.spec first" >&2; exit 1; }

if [[ "$identity" == "-" ]]; then
    echo "MACOS_SIGN_IDENTITY not set: ad-hoc signing, the .dmg will not pass Gatekeeper" >&2
    codesign --force --deep --sign - "$app"
else
    codesign --force --deep --options runtime --timestamp \
             --entitlements "$entitlements" --sign "$identity" "$app"
fi
codesign --verify --deep --strict "$app"

staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT
ditto "$app" "$staging/Aperture.app"
ln -s /Applications "$staging/Applications"
rm -f "$dmg"
hdiutil create -volname "Aperture $version" -srcfolder "$staging" -ov -format UDZO "$dmg"

if [[ "$identity" != "-" ]]; then
    codesign --force --timestamp --sign "$identity" "$dmg"
fi

if [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "${APPLE_APP_PASSWORD:-}" ]]; then
    [[ "$identity" != "-" ]] || { echo "notarization needs MACOS_SIGN_IDENTITY" >&2; exit 1; }
    xcrun notarytool submit "$dmg" --apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" \
                                   --password "$APPLE_APP_PASSWORD" --wait
    xcrun stapler staple "$dmg"
fi

echo "built $dmg"
