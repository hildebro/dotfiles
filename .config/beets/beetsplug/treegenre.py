import os
import sys
import yaml
import musicbrainzngs
from beets.plugins import BeetsPlugin
from beets import config

class TreeGenrePlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        
        config_path = self.config['config_file'].as_str(default='genres.yml')
        if not os.path.isabs(config_path):
            config_path = os.path.join(config.config_dir(), config_path)
            
        self.direct_parents = {}
        self.canonical_names = {}
        self.aliases = {}
        
        self.load_tree(config_path)
        
        # Hook into the album info fetching stage
        self.register_listener('albuminfo_received', self.on_albuminfo_received)

    def load_tree(self, path):
        """Reads the YAML file and builds a parent mapping."""
        if not os.path.exists(path):
            self._log.warning(f"Genre config not found at {path}. TreeGenre disabled.")
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # 1. Parse standard trees
        self._add_nodes(data.get('tree', {}), None)
        self._add_nodes(data.get('fusion-tree', {}), None)

        # 2. Parse fusions (multi-inheritance)
        for fusion, parents in data.get('fusions', {}).items():
            f_low = fusion.lower()
            if f_low not in self.direct_parents:
                self.direct_parents[f_low] = []
                self.canonical_names[f_low] = fusion
            
            for p in parents:
                self.direct_parents[f_low].append(p.lower())

        # 3. Parse Aliases
        for alias, canonical in data.get('aliases', {}).items():
            self.aliases[alias.lower()] = canonical

    def _add_nodes(self, node, parent_name):
        """Recursively builds a map of child -> [direct_parent]"""
        if not node:
            return
        
        for genre, children in node.items():
            g_low = genre.lower()
            self.canonical_names[g_low] = genre
            
            if g_low not in self.direct_parents:
                self.direct_parents[g_low] = []
                
            if parent_name:
                self.direct_parents[g_low].append(parent_name.lower())
                
            if children:
                self._add_nodes(children, genre)

    def get_all_ancestors(self, genre_low, seen=None):
        """Recursively fetches all parent genres to roll up the tree."""
        if seen is None:
            seen = set()
            
        if genre_low in seen:
            return []
            
        seen.add(genre_low)
        ancestors = set()
        
        for p in self.direct_parents.get(genre_low, []):
            if p:
                ancestors.add(p)
                ancestors.update(self.get_all_ancestors(p, seen))
                
        return list(ancestors)

    def expand_genres(self, raw_genres, album_name="Unknown Album"):
        """Takes raw MB genres, applies aliases, and returns all canonical parents. Aborts if unmapped."""
        expanded = set()
        
        for g in raw_genres:
            g_low = g.lower()
            
            # Resolve alias if it exists
            if g_low in self.aliases:
                g_low = self.aliases[g_low].lower()
                
            # Check if the genre exists in our canonical mappings
            if g_low in self.canonical_names:
                expanded.add(self.canonical_names[g_low])
                
                # Fetch all parents up the tree
                for ancestor in self.get_all_ancestors(g_low):
                    if ancestor in self.canonical_names:
                        expanded.add(self.canonical_names[ancestor])
            else:
                # STRICT MODE: Abort the entire import if an unknown genre is found
                error_msg = (
                    f"\n\n[TreeGenre Plugin] ABORTING IMPORT\n"
                    f"Found unmapped genre: '{g}' (on album '{album_name}')\n"
                    f"Please update your genres.yml file to include '{g}' (or add it to aliases) and run the import again.\n"
                )
                sys.exit(error_msg)
                        
        return list(expanded)

    def on_albuminfo_received(self, info):
        """Fires when Beets fetches album data from MusicBrainz."""
        if info.data_source != 'MusicBrainz' or not info.releasegroup_id:
            return

        try:
            rg = musicbrainzngs.get_release_group_by_id(info.releasegroup_id, includes=["genres"])
            genre_list = rg.get('release-group', {}).get('genre-list', [])
            mb_genres = [g['name'] for g in genre_list]
            
            if not mb_genres:
                return
                
            # Expand based on the YAML tree, pass album name for the error message
            final_genres = self.expand_genres(mb_genres, getattr(info, 'album', 'Unknown'))
            
            if final_genres:
                genre_string = ",".join(final_genres)
                self._log.debug(f"TreeGenre mapped {mb_genres} -> {genre_string}")
                info.genre = genre_string
                
        except musicbrainzngs.MusicBrainzError as e:
            self._log.error(f"TreeGenre failed to fetch MB genres: {e}")

