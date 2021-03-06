# Copyright (c) 2016 The GNOME Music Developers
#
# GNOME Music is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# GNOME Music is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNOME Music; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# The GNOME Music authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and GNOME Music.  This permission is above and beyond the permissions
# granted by the GPL license by which GNOME Music is covered.  If you
# modify this code, you may extend this exception to your version of the
# code, but you are not obligated to do so.  If you do not wish to do so,
# delete this exception statement from your version.


from gettext import gettext as _
from gi.repository import Gdk, GObject, Gtk

from gnomemusic import log
from gnomemusic.grilo import grilo
import gnomemusic.utils as utils

NOW_PLAYING_ICON_NAME = 'media-playback-start-symbolic'
ERROR_ICON_NAME = 'dialog-error-symbolic'


class StarImage(Gtk.Image):
    """GtkImage for starring songs"""
    __gtype_name__ = 'StarImage'

    def __repr__(self):
        return '<StarImage>'

    @log
    def __init__(self):
        super().__init__(self)

        self._favorite = False

        self.get_style_context().add_class("star")
        self.show_all()

    @log
    def set_favorite(self, favorite):
        """Set favorite

        Set the current widget as favorite or not.

        :param bool favorite: Value to switch the widget state to
        """
        self._favorite = favorite

        if self._favorite:
            self.set_state_flags(Gtk.StateFlags.SELECTED, False)
        else:
            self.unset_state_flags(Gtk.StateFlags.SELECTED)

    @log
    def get_favorite(self):
        """Return the current state of the widget

        :return: The state of the widget
        :rtype: bool
        """
        return self._favorite

    @log
    def toggle_favorite(self):
        """Toggle the widget state"""
        self._favorite = not self._favorite

        self.set_favorite(self._favorite)

    @log
    def hover(self, widget, event, data):
        self.set_state_flags(Gtk.StateFlags.PRELIGHT, False)

    @log
    def unhover(self, widget, event, data):
        self.unset_state_flags(Gtk.StateFlags.PRELIGHT)


class DiscSongsFlowBox(Gtk.FlowBox):
    """FlowBox containing the songs on one disc

    DiscSongsFlowBox allows setting the number of columns to
    use.
    """
    __gtype_name__ = 'DiscSongsFlowBox'

    def __repr__(self):
        return '<DiscSongsFlowBox>'

    @log
    def __init__(self, columns=1):
        """Initialize

        :param int columns: The number of columns the widget uses
        """
        super().__init__(self)
        super().set_selection_mode(Gtk.SelectionMode.NONE)

        self._columns = columns
        self.get_style_context().add_class('discsongsflowbox')

    @log
    def set_columns(self, columns):
        """Set the number of columns to use

        :param int columns: The number of columns the widget uses
        """
        self._columns = columns

        children_n = len(self.get_children())

        if children_n % self._columns == 0:
            max_per_line = children_n / self._columns
        else:
            max_per_line = int(children_n / self._columns) + 1

        self.set_max_children_per_line(max_per_line)
        self.set_min_children_per_line(max_per_line)


class DiscBox(Gtk.Box):
    """A widget which compromises one disc

    DiscBox contains a disc label for the disc number on top
    with a DiscSongsFlowBox beneath.
    """
    __gtype_name__ = 'DiscBox'

    __gsignals__ = {
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'selection-toggle': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'track-activated': (GObject.SignalFlags.RUN_FIRST, None, (Gtk.Widget,))

    }

    def __repr__(self):
        return '<DiscBox>'

    @log
    def __init__(self, model=None):
        """Initialize

        :param model: The TreeStore to use
        """
        super().__init__(self)

        self._model = model
        self._model.connect('row-changed', self._model_row_changed)

        builder = Gtk.Builder()
        builder.add_from_resource('/org/gnome/Music/ArtistAlbumWidget.ui')

        self._label = builder.get_object('disclabel')
        self._label.set_no_show_all(True)
        self._disc_songs_flowbox = builder.get_object('discsongsflowbox')

        self._selection_mode = False
        self._selection_mode_allowed = True
        self._selected_items = []
        self._songs = []

        self.pack_start(builder.get_object('disc'), True, True, 0)

    @log
    def set_columns(self, columns):
        """Set the number of columns used by the songs list

        :param int columns: Number of columns to display
        """
        self._disc_songs_flowbox.set_columns(columns)

    @log
    def set_disc_number(self, disc_number):
        """Set the dics number to display

        :param int disc_number: Disc number to display
        """
        self._label.set_markup(_("Disc {}").format(disc_number))
        self._label.get_style_context().add_class('dim-label')
        self._label.set_visible(True)

    @log
    def show_disc_label(self, show_header):
        """Wheter to show the disc number label

        :param bool show_header: Display the disc number label
        """
        self._label.set_visible(False)
        self._label.hide()

    @log
    def show_duration(self, show_duration):
        """Wheter to show the song durations

        :param bool show_duration: Display the song durations
        """
        def child_show_duration(child):
            child.get_child().duration.set_visible(show_duration)

        self._disc_songs_flowbox.foreach(child_show_duration)

    @log
    def show_favorites(self, show_favorites):
        """Where to show the favorite switches

        :param bool show_favorites: Display the favorite
        switches
        """
        def child_show_favorites(child):
            child.get_child().starevent.set_visible(show_favorites)

        self._disc_songs_flowbox.foreach(child_show_favorites)

    @log
    def show_song_numbers(self, show_song_number):
        """Whether to show the song numbers

        :param bool show_song_number: Display the song number
        """
        def child_show_song_number(child):
            child.get_child().number.set_visible(show_song_number)

        self._disc_songs_flowbox.foreach(child_show_song_number)

    @log
    def set_tracks(self, tracks):
        """Songs to display

        :param list tracks: A list of Grilo media items to
        add to the widget
        """
        for track in tracks:
            song_widget = self._create_song_widget(track)
            self._disc_songs_flowbox.insert(song_widget, -1)
            track.song_widget = song_widget

    @log
    def set_selection_mode(self, selection_mode):
        """Set selection mode

        :param bool selection_mode: Allow selection mode
        """
        self._selection_mode = selection_mode
        self._disc_songs_flowbox.foreach(self._toggle_widget_selection)

    @log
    def get_selected_items(self):
        """Return all selected items

        :returns: The selected items:
        :rtype: A list if Grilo media items
        """
        self._selected_items = []
        self._disc_songs_flowbox.foreach(self._get_selected)

        return self._selected_items

    @log
    def _get_selected(self, child):
        song_widget = child.get_child()

        if song_widget.check_button.get_active():
            itr = song_widget.itr
            self._selected_items.append(self._model[itr][5])

    # FIXME: select all/none slow probably b/c of the row changes
    # invocations, maybe workaround?
    @log
    def select_all(self):
        """Select all songs"""
        def child_select_all(child):
            song_widget = child.get_child()
            self._model[song_widget.itr][6] = True

        self._disc_songs_flowbox.foreach(child_select_all)

    @log
    def select_none(self):
        """Deselect all songs"""
        def child_select_none(child):
            song_widget = child.get_child()
            self._model[song_widget.itr][6] = False

        self._disc_songs_flowbox.foreach(child_select_none)

    @log
    def _create_song_widget(self, track):
        """Helper function to create a song widget for a
        single song

        :param track: A Grilo media item
        :returns: A complete song widget
        :rtype: Gtk.EventBox
        """
        builder = Gtk.Builder()
        builder.add_from_resource('/org/gnome/Music/TrackWidget.ui')
        song_widget = builder.get_object('eventbox1')
        self._songs.append(song_widget)

        title = utils.get_media_title(track)

        itr = self._model.append(None)

        self._model[itr][0, 1, 2, 5, 6] = [title, '', '', track, False]

        song_widget.itr = itr
        song_widget.model = self._model

        track_number = track.get_track_number()
        if track_number == 0:
            track_number = ""
        song_widget.number = builder.get_object('num')
        song_widget.number.set_markup(
            '<span color=\'grey\'>{}</span>'.format(track_number))
        song_widget.number.set_no_show_all(True)

        song_widget.title = builder.get_object('title')
        song_widget.title.set_text(title)
        song_widget.title.set_max_width_chars(50)

        song_widget.duration = builder.get_object('duration')
        time = utils.seconds_to_string(track.get_duration())
        song_widget.duration.set_text(time)

        song_widget.check_button = builder.get_object('select')
        song_widget.check_button.set_visible(False)
        song_widget.check_button.connect('toggled',
                                         self._check_button_toggled,
                                         song_widget)

        song_widget.now_playing_sign = builder.get_object('image1')
        song_widget.now_playing_sign.set_from_icon_name(
            NOW_PLAYING_ICON_NAME,
            Gtk.IconSize.SMALL_TOOLBAR)
        song_widget.now_playing_sign.set_no_show_all(True)
        song_widget.can_be_played = True
        song_widget.connect('button-release-event', self._track_activated)

        song_widget.star_image = builder.get_object('starimage')
        song_widget.star_image.set_favorite(track.get_favourite())
        song_widget.star_image.set_visible(True)

        song_widget.starevent = builder.get_object('starevent')
        song_widget.starevent.connect('button-release-event',
                                      self._toggle_favorite,
                                      song_widget)
        song_widget.starevent.connect('enter-notify-event',
                                      song_widget.star_image.hover, None)
        song_widget.starevent.connect('leave-notify-event',
                                      song_widget.star_image.unhover, None)
        return song_widget

    @log
    def _toggle_favorite(self, widget, event, song_widget):
        if event.button == Gdk.BUTTON_PRIMARY:
            song_widget.star_image.toggle_favorite()

        # FIXME: ugleh. Should probably be triggered by a
        # signal.
        favorite = song_widget.star_image.get_favorite()
        grilo.set_favorite(self._model[song_widget.itr][5], favorite)
        return True

    @log
    def _check_button_toggled(self, widget, song_widget):
        self.emit('selection-changed')

        return True

    @log
    def _toggle_widget_selection(self, child):
        song_widget = child.get_child()
        song_widget.check_button.set_visible(self._selection_mode)
        if self._selection_mode == False:
            if song_widget.check_button.get_active():
                song_widget.check_button.set_active(False)

    @log
    def _track_activated(self, widget, event):
        # FIXME: don't think keys work correctly, if they did ever
        # even.
        if (not event.button == Gdk.BUTTON_SECONDARY
                or (event.button == Gdk.BUTTON_PRIMARY
                    and event.state & Gdk.ModifierType.CONTROL_MASK)):
            self.emit('track-activated', widget)
            if self._selection_mode:
                itr = widget.itr
                self._model[itr][6] = not self._model[itr][6]
        else:
            self.emit('selection-toggle')
            if self._selection_mode:
                itr = widget.itr
                self._model[itr][6] = True

        return True

    @log
    def _model_row_changed(self, model, path, itr):
        if (not self._selection_mode
                or not model[itr][5]):
            return

        song_widget = model[itr][5].song_widget
        selected = model[itr][6]
        if selected != song_widget.check_button.get_active():
            song_widget.check_button.set_active(selected)

        return True


class DiscListBox(Gtk.Box):
    """A ListBox widget containing all discs of a particular
    album
    """
    __gtype_name__ = 'DiscListBox'

    __gsignals__ = {
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __repr__(self):
        return '<DiscListBox>'

    @log
    def __init__(self):
        """Initialize"""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._selection_mode = False
        self._selection_mode_allowed = False
        self._selected_items = []

    @log
    def add(self, widget):
        """Insert a DiscBox widget"""
        super().add(widget)
        widget.connect('selection-changed', self._on_selection_changed)

    @log
    def _on_selection_changed(self, widget):
        self.emit('selection-changed')

    @log
    def get_selected_items(self):
        """Returns all selected items for all discs

        :returns: All selected items
        :rtype: A list if Grilo media items
        """
        self._selected_items = []

        def get_child_selected_items(child):
            self._selected_items += child.get_selected_items()

        self.foreach(get_child_selected_items)

        return self._selected_items

    @log
    def select_all(self):
        """Select all songs"""
        def child_select_all(child):
            child.select_all()

        self.foreach(child_select_all)

    @log
    def select_none(self):
        """Deselect all songs"""
        def child_select_none(child):
            child.select_none()

        self.foreach(child_select_none)

    @log
    def set_selection_mode(self, selection_mode):
        """Set selection mode

        :param bool selection_mode: Allow selection mode
        """
        if not self._selection_mode_allowed:
            return

        self._selection_mode = selection_mode

        def set_child_selection_mode(child):
            child.set_selection_mode(self._selection_mode)

        self.foreach(set_child_selection_mode)

    @log
    def set_selection_mode_allowed(self, allowed):
        """Set if selection mode is allowed

        :param bool allowed: Allow selection mode
        """
        self._selection_mode_allowed = allowed
