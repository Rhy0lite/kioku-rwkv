# Compile Kioku RWKV with Theos on WSL

Use WSL 2 Ubuntu with Theos for Linux installed, THEOS exported, and an arm64 iPhoneOS SDK (iOS 17 or newer; prefer the version used by the kit producer). Work in your Linux home directory. The build targets an iPhone, not the simulator.

## Get the matching dependency kit

Place this source tree in your own GitHub repository. Run the **iOS IPA** workflow manually on that revision with **Also export the WSL/Theos link kit** selected and download its **kioku-theos-kit** artifact. GitHub wraps the tarball in a zip. The macOS job compiles the native dependencies, Qt plugins, resources and Python modules, then exports link inputs. You can reuse the same kit for launcher edits. Regenerate it after changing native dependencies, Python packages, resources or the pinned Anki revision.

## Build in WSL

From the source root, with the downloaded artifact in your home directory:

```bash
cd ios/theos
unzip ~/kioku-theos-kit.zip
tar -xzf kioku-theos-kit.tar.gz
make clean package FINALPACKAGE=1
```

Theos compiles the Objective-C++ launcher, links the arm64 executable and stages the app and its Python frameworks. The IPA appears in packages/. Use your usual IPA signing and sideloading method. In Deck Options select RWKV Instant. The matching dependency kit is required before the WSL compile can run.
