"""Native deck actions and touch layout for the iOS study screens."""
from ctypes import c_void_p
import logging

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget
from rubicon.objc import NSObject, ObjCClass, ObjCInstance, SEL, objc_method

from .webview import prop


class KiokuDeckActionTarget(NSObject):
    @objc_method
    def activate_(self, sender) -> None:
        import aqt

        index = int(prop(sender, "tag"))
        command = self.commands[index]
        if aqt.mw.state == "deckBrowser":
            QTimer.singleShot(0, lambda: aqt.mw.state == "deckBrowser"
                              and aqt.mw.deckBrowser._linkHandler(command))


class DeckBar(QWidget):
    def __init__(self, mw):
        super().__init__(mw)
        self.hide()
        self.setFixedHeight(52)
        host = ObjCInstance(c_void_p(int(self.winId())))
        self.target = KiokuDeckActionTarget.alloc().init()
        self.target.commands = []
        self.toolbar = ObjCClass("UIToolbar").alloc().initWithFrame_(prop(host, "bounds"))
        self.toolbar.setAutoresizingMask_(2 | 16)  # flexible width and height
        host.addSubview_(self.toolbar)
        self.links = None

    def configure(self, links):
        if links == self.links:
            return
        item_class = ObjCClass("UIBarButtonItem")
        symbols = {"shared": "globe", "create": "plus", "import": "square.and.arrow.down"}
        items = []
        commands = []
        for _, command, title in links:
            if items:
                items.append(item_class.alloc().initWithBarButtonSystemItem_target_action_(
                    5, None, None))  # flexible space
            image = (ObjCClass("UIImage").systemImageNamed_(symbols[command])
                     if command in symbols else None)
            if image is None:
                item = item_class.alloc().initWithTitle_style_target_action_(
                    title, 0, self.target, SEL("activate:"))
            else:
                item = item_class.alloc().initWithImage_style_target_action_(
                    image, 0, self.target, SEL("activate:"))
            item.setAccessibilityLabel_(title)
            item.setTag_(len(commands))
            commands.append(command)
            items.append(item)
        self.toolbar.setItems_(ObjCClass("NSArray").arrayWithArray_(items))
        self.target.commands = commands
        self.links = links


def install(mw):
    from aqt import gui_hooks

    bar = DeckBar(mw)
    mw.mainLayout.addWidget(bar)
    classic = mw.form.menuqt_accel_view.addAction("Use original deck toolbar")
    classic.setCheckable(True)
    classic.setChecked(bool(mw.pm.meta.get("kioku_original_deck_toolbar", False)))

    def update(*_):
        active = mw.state == "deckBrowser" and not classic.isChecked()
        if active:
            bar.configure(tuple(tuple(link) for link in mw.deckBrowser.drawLinks))
            mw.bottomWeb.setVisible(False)
            bar.show()
        elif not bar.isHidden():
            bar.hide()
            mw.bottomWeb.setVisible(True)

    def toggle(checked):
        mw.pm.meta["kioku_original_deck_toolbar"] = checked
        mw.pm.db.execute("update profiles set data = ? where name = ?",
                         mw.pm._pickle(mw.pm.meta), "_global")
        mw.pm.db.commit()
        update()

    classic.toggled.connect(toggle)
    gui_hooks.state_did_change.append(update)
    gui_hooks.deck_browser_did_render.append(update)
    update()


def register():
    import aqt
    from aqt import gui_hooks
    from aqt.deckbrowser import DeckBrowser
    from aqt.reviewer import ReviewerBottomBar

    def style(content, context):
        if isinstance(context, DeckBrowser):
            content.head += """<style>
            body { font: -apple-system-body; }
            center > table { width: min(100%, 48rem); border-spacing: 0; }
            tr.deck td { height: 48px; border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent); }
            tr.deck a.deck { font-weight: 600; overflow-wrap: anywhere; }
            tr.deck .count { font-variant-numeric: tabular-nums; }
            #studiedToday { font: -apple-system-footnote; }
            </style>"""
        elif isinstance(context, ReviewerBottomBar):
            content.head += """<style>
            button { min-height: 44px; border-radius: 12px; font: -apple-system-body; }
            button[data-ease] { padding-inline: clamp(2px, 1vw, 8px); }
            </style>"""

    def setup():
        try:
            install(aqt.mw)
        except Exception:
            logging.getLogger("kioku.studyui").exception("native deck toolbar")

    gui_hooks.webview_will_set_content.append(style)
    gui_hooks.main_window_did_init.append(setup)
