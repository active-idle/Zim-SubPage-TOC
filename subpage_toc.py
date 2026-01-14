# -*- coding: utf-8 -*-
"""
Zim Wiki SubPage TOC Plugin

Generates a hierarchical table of contents for subpages of the current page.
Inserts the TOC as formatted wiki links at the cursor position with configurable
depth.
"""

from zim.plugins import PluginClass
from zim.gui.mainwindow import MainWindowExtension as MainWindowExtensionBase
from zim.actions import action

class TestPlugin(PluginClass):

    plugin_info = {
        'name': 'SubPage TOC',
        'description': 'Insert table of contents for subpages at cursor position',
        'author': 'Robbi',
    }

    plugin_preferences = (
        # key, type, label, default, (min, max)
        ('max_depth', 'int', 'Maximum depth of subpages', 1, (1, 10)),
    )

class MainWindowExtension(MainWindowExtensionBase):

    def __init__(self, plugin, window):
        MainWindowExtensionBase.__init__(self, plugin, window)

    def _get_subpages(self, notebook, page, depth, max_depth):
        """Recursively collect subpages up to specified depth"""
        result = []

        # Stop if maximum depth reached
        if depth >= max_depth:
            return result

        # Get direct children of current page
        subpages = list(notebook.pages.list_pages(page))

        for subpage in subpages:
            # Add subpage with its depth level
            result.append((depth, subpage))

            # Recursively get children if not at max depth
            if depth + 1 < max_depth:
                result.extend(self._get_subpages(notebook, subpage, depth + 1, max_depth))

        return result

    @action('Insert Table of Contents', accelerator='<Primary><Shift>t', menuhints='tools')
    def insert_toc(self):
        """Generate and insert TOC for current page's subpages"""
        # Get current page
        page = self.window.pageview.page
        if not page:
            from zim.gui.widgets import MessageDialog
            MessageDialog(self.window, ('error', 'No page opened!')).run()
            return

        # Get notebook reference
        notebook = self.window.notebook

        # Get depth setting from preferences
        max_depth = self.plugin.preferences.get('max_depth', 1)

        # Collect subpages recursively
        subpages = self._get_subpages(notebook, page, depth=0, max_depth=max_depth)

        if not subpages:
            from zim.gui.widgets import MessageDialog
            MessageDialog(self.window, ('info', 'No subpages found!')).run()
            return

        # Build table of contents text with indentation
        toc_text = "**Table of Contents:**\n"
        for level, subpage in subpages:
            indent = "\t" * level
            link = "[[" + subpage.name + "|" + subpage.basename + "]]"
            toc_text += indent + "* " + link + "\n"

        # Insert at cursor position
        textview = self.window.pageview.textview
        buffer = textview.get_buffer()
        insert_mark = buffer.get_insert()
        cursor_iter = buffer.get_iter_at_mark(insert_mark)
        buffer.insert(cursor_iter, toc_text)

        # Trigger page reload to render wiki markup
        try:
            self.window.pageview.reload_page()
        except:
            try:
                self.window.pageview.save_page()
                self.window.pageview.set_page(page)
            except:
                pass
