# Kioku with RWKV Instant for iPhone

The iOS build pins JSchoreels/anki at 609d60db1bf6d72a23889745457c1556a7be6dcd. It compiles the Rust bridge for iOS and builds the desktop Python packages and Deck Options web interface from the same checkout. Model files are bundled in aqt/rwkv_inference.

On a Mac with the prerequisites in ios/README.md, run ios/tools/build.sh from the repository root. Alternatively use the iOS IPA workflow on a macOS GitHub Actions runner. The unsigned IPA requires signing for your device.

In Deck Options, choose RWKV Instant for the preset and save it. For a device acceptance test, use a temporary profile with a copy of a deck. Review several cards, close and reopen Kioku, and verify the preset and review history persist. An iPhone build and this device test are pending.
