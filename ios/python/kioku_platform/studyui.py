"""Native deck actions and touch layout for the iOS study screens."""
from ctypes import c_void_p
import logging

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMenu, QWidget
from pathlib import Path
from rubicon.objc import NSObject, ObjCClass, ObjCInstance, SEL, objc_method

from .webview import prop


class KiokuDeckActionTarget(NSObject):
    @objc_method
    def activate_(self, sender) -> None:
        import aqt

        index = int(prop(sender, "tag"))
        callback = self.commands[index]
        state = aqt.mw.state
        QTimer.singleShot(0, lambda: aqt.mw.state == state and callback())



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

        items = []
        commands = []
        for symbol, title, command in links:
            if command is None and not title:
                items.append(item_class.alloc().initWithBarButtonSystemItem_target_action_(
                    5, None, None))
                continue
            image = (ObjCClass("UIImage").systemImageNamed_(symbol)
                     if symbol else None)
            if image is None:
                item = item_class.alloc().initWithTitle_style_target_action_(
                    title, 0, self.target, SEL("activate:"))
            else:
                item = item_class.alloc().initWithImage_style_target_action_(
                    image, 0, self.target, SEL("activate:"))
            item.setAccessibilityLabel_(title)
            if command is None:
                item.setTintColor_(prop(ObjCClass("UIColor"), "systemBlueColor"))
            item.setEnabled_(command is not None)
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
    classic = mw.form.menuqt_accel_view.addAction("Use original Anki toolbars")
    classic.setCheckable(True)
    classic.setChecked(bool(mw.pm.meta.get("kioku_original_deck_toolbar", False)))

    from aqt.utils import openLink
    from PyQt6.QtCore import QPoint
    top = DeckBar(mw)
    mw.mainLayout.insertWidget(0, top)
    space = (None, "", None)

    def popup(entries, widget):
        menu = QMenu(mw)
        for title, callback in entries:
            menu.addAction(title, callback)
        menu.aboutToHide.connect(menu.deleteLater)
        menu.popup(widget.mapToGlobal(QPoint(12, widget.height() // 2)))

    def add_export():
        entries = [("Add Notes", mw.onAddCard)]
        for _, command, label in mw.deckBrowser.drawLinks:
            entries.append((label, lambda checked=False, cmd=command: mw.deckBrowser._linkHandler(cmd)))
        entries.append(("Export", lambda: mw.onExport()))
        popup(entries, bar)

    def settings():
        menu = QMenu(mw)
        menu.addAction("Preferences", mw.onPrefs)
        for action in mw.menuBar().actions():
            if action.menu():
                menu.addMenu(action.menu())
        menu.aboutToHide.connect(menu.deleteLater)
        menu.popup(top.mapToGlobal(QPoint(top.width()-48, top.height())))

    deck_header = [
        ("questionmark.circle", "Help", lambda: openLink("https://docs.ankiweb.net/")),
        ("chart.xyaxis.line", "Statistics", mw.onStats), space,
        (None, "Decks", None), space,
        ("magnifyingglass", "Search", mw.onBrowse),
        ("gearshape", "Settings", settings),
    ]
    review_header = [
        (None, "Decks", lambda: mw.moveToState("deckBrowser")), space,
        (None, "Add", mw.onAddCard), space, (None, "Edit", mw.onEditCurrent),
        space, (None, "Browse", mw.onBrowse),
    ]
    deck_footer = [(None, "Add/Export", add_export), space,
                   (None, "Synchronize", mw.on_sync_button_clicked)]
    saved_menu = None

    def update(*_):
        nonlocal saved_menu
        active = mw.state in ("deckBrowser", "review") and not classic.isChecked()
        decks = active and mw.state == "deckBrowser"
        if active:
            top.configure(deck_header if decks else review_header)
            if saved_menu is None:
                saved_menu = mw.menuBar().isVisible()
            mw.menuBar().setVisible(False)
            mw.toolbarWeb.setVisible(False)
            top.show()
        elif saved_menu is not None:
            top.hide()
            mw.toolbarWeb.setVisible(True)
            mw.menuBar().setVisible(saved_menu)
            saved_menu = None
        if decks:
            bar.configure(deck_footer)
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

    directory = Path(__file__).parent
    deck_css = (directory / "decks.css").read_text()
    deck_js = (directory / "decks.js").read_text()

    def style(content, context):
        if isinstance(context, DeckBrowser):
            content.head += "<style>" + deck_css + "</style>"
            content.body += "<script>" + deck_js + "</script>"
        elif isinstance(context, ReviewerBottomBar) and not aqt.mw.pm.meta.get("kioku_original_deck_toolbar", False):
            content.head += """<style>
            button { min-height: 44px; border-radius: 12px; font: -apple-system-body; }
            .nightMode, .night_mode { background: #141416; }
            #innertable .stat:first-child { display: none; }
            #ansbut:has(.stattxt span) { font-size: 0; border: none; background: transparent; box-shadow: none; }
            #ansbut .stattxt { font: -apple-system-title2; }
            #innertable .stat:last-child button { font-size: 0; }
            #innertable .stat:last-child button::before { content: "⚙"; color: #89cafa; font-size: 24px; }
            button[data-ease] { padding-inline: clamp(2px, 1vw, 8px); }
            </style>"""

    def setup():
        try:
            install(aqt.mw)
        except Exception:
            logging.getLogger("kioku.studyui").exception("native deck toolbar")

    gui_hooks.webview_will_set_content.append(style)
    gui_hooks.main_window_did_init.append(setup)
