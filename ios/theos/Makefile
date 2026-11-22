ARCHS := arm64
TARGET := iphone:clang:latest:17.0
THEOS_PACKAGE_FORMAT := ipa
include kit/config.mk
include $(THEOS)/makefiles/common.mk

APPLICATION_NAME := Kioku
Kioku_FILES := launcher.mm
Kioku_OBJCCFLAGS := -fno-objc-arc -I$(CURDIR)/kit/include -DKIOKU_PYTHON_VERSION=\"$(PY_VERSION)\"
ifneq ($(ENTRY),main)
Kioku_OBJCCFLAGS += -DKIOKU_ENTRY=$(ENTRY) $(ENTRY_LINKAGE)
endif
Kioku_FRAMEWORKS := Foundation UIKit JavaScriptCore
Kioku_LDFLAGS := -ObjC -Fkit/resources/Frameworks -Wl,-rpath,@executable_path/Frameworks @kit/link.rsp
Kioku_RESOURCE_DIRS := kit/resources
include $(THEOS_MAKE_PATH)/application.mk
