import os
import re
import yaml
from beets.plugins import BeetsPlugin
from beets import config
from beets.mediafile import MediaFile
from beets.util import syspath

# ANSI escape codes for coloring terminal output
def _grey(text): return f"\033[90m{text}\033[0m"
def _green(text): return f"\033[92m{text}\033[0m"
def _blue(text): return f"\033[94m{text}\033[0m"
def _bold(text): return f"\033[1m{text}\033[0m"

class GenreTreePlugin(BeetsPlugin):
    def __init__(self):
        super(GenreTreePlugin, self).__init__()

        config_dir = config.config_dir()
        if isinstance(config_dir, bytes):
            config_dir = config_dir.decode('utf-8')

        genres_file = os.path.join(config_dir, 'genres.yaml')

        if not os.path.isfile(genres_file):
            print(f"[GenreTree] WARNING: genres.yaml not found at {genres_file}")
            self.parent_map = {}
            self.alias_map = {}
            return

        try:
            with open(genres_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[GenreTree] ERROR: Failed to load genres.yaml: {e}")
            self.parent_map = {}
            self.alias_map = {}
            return

        self.alias_map = {k.lower(): v.lower() for k, v in (data.get('aliases') or {}).items()}
        self.parent_map = {}

        self._build_map(data.get('tree') or {})
        self._build_map(data.get('fusion-tree') or {})

        fusions = data.get('fusions') or {}
        for fusion, bases in fusions.items():
            fusion_lower = fusion.lower()
            if fusion_lower in self.parent_map:
                for base in bases:
                    base_lower = base.lower()
                    if base_lower in self.parent_map:
                        self.parent_map[fusion_lower].update(self.parent_map[base_lower])

        self.register_listener('album_imported', self.on_album_imported)
        self.register_listener('item_imported', self.on_item_imported)

    def _build_map(self, tree_node, current_parents=None):
        if current_parents is None:
            current_parents = set()
        if not tree_node:
            return

        for node, children in tree_node.items():
            node_parents = current_parents | {node}
            self.parent_map[node.lower()] = node_parents
            if children:
                self._build_map(children, node_parents)

    def process_genres_categorized(self, raw_genres):
        """Sorts a set of raw strings into 4 lists: (final, accepted, added_parents, dropped)"""
        accepted = set()
        added = set()
        dropped = set()

        for g in raw_genres:
            g_lower = g.lower()
            canonical_lower = self.alias_map.get(g_lower, g_lower)

            if canonical_lower in self.parent_map:
                node_parents = self.parent_map[canonical_lower]
                for n in node_parents:
                    if n.lower() == canonical_lower:
                        accepted.add(n)
                    else:
                        added.add(n)
            else:
                dropped.add(g)

        added = added - accepted
        final_genres = accepted | added
        return sorted(list(final_genres)), sorted(list(accepted)), sorted(list(added)), sorted(list(dropped))

    def _extract_raw_genres(self, mf, item, album=None):
        """Safely extracts all genres, handling lists, strings, and multi-value ID3v2.4 arrays."""
        raw_genres = set()
        
        def _add_genres(field_val):
            if not field_val:
                return
            # Force into a list so we can process strings and lists identically
            vals = field_val if isinstance(field_val, list) else [str(field_val)]
            for v in vals:
                # Safely split and strip each value
                raw_genres.update([g.strip() for g in re.split(r'[;,/\x00]', str(v)) if g.strip()])

        # 1. Check the physical file
        if mf:
            if hasattr(mf, 'genres') and mf.genres:
                _add_genres(mf.genres)
            elif getattr(mf, 'genre', None):
                _add_genres(mf.genre)

        # 2. Check the database items
        if item and getattr(item, 'genre', None):
            _add_genres(item.genre)
        if album and getattr(album, 'genre', None):
            _add_genres(album.genre)

        return raw_genres

    def on_album_imported(self, lib, album, **kwargs):
        try:
            raw_genres = set()
            items = list(album.items())
            
            for item in items:
                mf = None
                try:
                    # Safely convert the bytes path for the OS
                    mf = MediaFile(syspath(item.path))
                except Exception as e:
                    print(f"  [_grey('Warning: Could not read file for genre extraction:')] {e}")

                try:
                    # Extract genres even if mf failed (so it checks the DB fallback)
                    raw_genres.update(self._extract_raw_genres(mf, item, album))
                except Exception as e:
                    print(f"  [_grey('Warning: Error extracting genres:')] {e}")

            artist = getattr(album, 'albumartist', 'Unknown Artist')
            title = getattr(album, 'album', 'Unknown Album')

            if not raw_genres:
                print(f"\n[GenreTree] 💿 {_bold(artist + ' - ' + title)}", flush=True)
                print(f"  {_grey('No genre data found on physical files or database.')}\n", flush=True)
                return

            final, acc, add, drp = self.process_genres_categorized(raw_genres)
            new_genre_str = "; ".join(final)

            print(f"\n[GenreTree] 💿 {_bold(artist + ' - ' + title)}", flush=True)
            if drp: print(f"  Dropped:  {', '.join([_grey(g) for g in drp])}", flush=True)
            if acc: print(f"  Accepted: {', '.join([_green(g) for g in acc])}", flush=True)
            if add: print(f"  Parents:  {', '.join([_blue(g) for g in add])}", flush=True)
            print(f"  Final:    {new_genre_str if new_genre_str else _grey('(none)')}\n", flush=True)

            # Update the database
            album.genre = new_genre_str
            album.store()

            for item in items:
                item.genre = new_genre_str
                item.store()
                try:
                    mf = MediaFile(syspath(item.path))
                    mf.genre = new_genre_str
                    mf.save()
                except Exception as e:
                    print(f"  [_grey('Warning: Failed to save genre to file:')] {e}")

        except Exception as e:
            print(f"[GenreTree] ERROR in on_album_imported: {e}", flush=True)

    def on_item_imported(self, lib, item, **kwargs):
        # Skip items that are part of an album import to avoid double-processing
        if item.get_album():
            return
            
        try:
            raw_genres = set()
            mf = None

            try:
                # Safely convert the bytes path for the OS
                mf = MediaFile(syspath(item.path))
            except Exception as e:
                print(f"  [_grey('Warning: Could not read file for genre extraction:')] {e}")

            try:
                # Extract genres even if mf failed (so it checks the DB fallback)
                raw_genres.update(self._extract_raw_genres(mf, item))
            except Exception as e:
                print(f"  [_grey('Warning: Error extracting genres:')] {e}")

            artist = getattr(item, 'artist', 'Unknown Artist')
            title = getattr(item, 'title', 'Unknown Title')

            if not raw_genres:
                print(f"\n[GenreTree] 🎵 {_bold(artist + ' - ' + title)}", flush=True)
                print(f"  {_grey('No genre data found on physical file.')}\n", flush=True)
                return

            final, acc, add, drp = self.process_genres_categorized(raw_genres)
            new_genre_str = "; ".join(final)

            print(f"\n[GenreTree] 🎵 {_bold(artist + ' - ' + title)}", flush=True)
            if drp: print(f"  Dropped:  {', '.join([_grey(g) for g in drp])}", flush=True)
            if acc: print(f"  Accepted: {', '.join([_green(g) for g in acc])}", flush=True)
            if add: print(f"  Parents:  {', '.join([_blue(g) for g in add])}", flush=True)
            print(f"  Final:    {new_genre_str if new_genre_str else _grey('(none)')}\n", flush=True)

            # Update the database
            item.genre = new_genre_str
            item.store()

            try:
                if not mf:
                    mf = MediaFile(syspath(item.path))
                mf.genre = new_genre_str
                mf.save()
            except Exception as e:
                print(f"  [_grey('Warning: Failed to save genre to file:')] {e}")

        except Exception as e:
            print(f"[GenreTree] ERROR in on_item_imported: {e}", flush=True)
