#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# TermRoom
# Copyright (c) 2008 Egon Bianchet
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import gconf
import gtk
import pango
import sys
import vte


PROFILE_DEFAULT = "/apps/gnome-terminal/profiles/Default"
PROFILE_TERMROOM = "/apps/gnome-terminal/profiles/TermRoom"
SYSTEM_FONT = "/desktop/gnome/interface/monospace_font_name"
SYSTEM_COLORS = "/desktop/gnome/interface/gtk_color_scheme"

WIDTH_RATIO = 0.6
HEIGHT_RATIO = 0.95


class TerminalProfile(object):
    def __init__(self):
        self.client = gconf.Client()
        if self.client.dir_exists(PROFILE_TERMROOM):
            self.profile = PROFILE_TERMROOM
        else:
            self.profile = PROFILE_DEFAULT

        if self["use_system_font"]:
            self.font = self.client.get(SYSTEM_FONT).get_string()

        if self["use_theme_colors"]:
            colors = {}
            lines = self.client.get(SYSTEM_COLORS).get_string().split("\n");
            for line in lines:
                var, color = line.split(":")
                colors[var] = color
            self.background_color = colors['bg_color']
            self.foreground_color = colors['fg_color']

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            value = self.client.get("%s/%s" % (self.profile, item))
            if value:
                return getattr(value, "get_%s" % value.type.value_nick)()


class TermRoom(object):
    def __init__(self, cmd=None):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_name("TermRoom")
        self.window.set_title("TermRoom")
        self.window.connect("destroy", self.destroy)

        self.terminal = vte.Terminal()
        self.terminal.connect("child-exited", lambda term: gtk.main_quit())
        self.terminal.fork_command()
        if cmd:
            self.terminal.feed_child(cmd+"\n")

        self.fixed = gtk.Fixed()
        self.window.add(self.fixed)
        self.vbox = gtk.VBox()
        self.fixed.put(self.vbox, 0, 0)
        self.vbox.pack_start(self.terminal, True, True, 6)

        self.profile = TerminalProfile()

        self.window.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.color_parse(self.profile["background_color"]))
         
        self.terminal.set_font_from_string(self.profile["font"])
        self.terminal.set_allow_bold(self.profile["allow_bold"]) 
        self.terminal.set_audible_bell(not self.profile["silent_bell"]) 
        self.terminal.set_colors(
            gtk.gdk.color_parse(self.profile["foreground_color"]), 
            gtk.gdk.color_parse(self.profile["background_color"]),
            [gtk.gdk.color_parse(x) for x in self.profile["palette"].split(":")])

        (w, h) = (gtk.gdk.screen_width(), gtk.gdk.screen_height())
        width = int(WIDTH_RATIO * w)
        height = int(HEIGHT_RATIO * h)
        padding_x = int((w - width)/ 2)
        padding_y = int((h - height)/ 2)
        self.vbox.set_size_request(width, height)
        self.fixed.move(self.vbox, padding_x, padding_y)

        self.window.show_all()
        self.window.fullscreen()

    def destroy(self, widget, data=None):
        gtk.main_quit()


if __name__ == "__main__":
    TermRoom = TermRoom(cmd=" ".join(sys.argv[1:]))
    gtk.main()
