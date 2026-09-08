import os
import re
import yaml
from beets.plugins import BeetsPlugin
from beets import config

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

        self.register_listener('trackinfo_received', self.process_track_info)
        self.register_listener('albuminfo_received', self.process_album_info)
        self.register_listener('import_task_apply', self.process_task_apply)

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

    def process_genres(self, genre_data):
        if not genre_data:
            return []
        
        if isinstance(genre_data, list):
            raw_genres = [str(g) for g in genre_data]
        else:
            raw_genres = [g.strip() for g in re.split(r'[;,]', str(genre_data)) if g.strip()]
        
        final_genres = set()
        for g in raw_genres:
            g_lower = g.lower()
            canonical_lower = self.alias_map.get(g_lower, g_lower)
            
            if canonical_lower in self.parent_map:
                final_genres.update(self.parent_map[canonical_lower])
            else:
                # Force print to console so Beets doesn't hide it
                print(f"[GenreTree] Skipping unsupported genre: {g}", flush=True)
        
        return sorted(list(final_genres))

    def process_track_info(self, info, **kwargs):
        try:
            # Older beets pipeline uses string 'genre'
            if getattr(info, 'genre', None):
                info.genre = ", ".join(self.process_genres(info.genre))
            
            # Newer beets pipeline uses list 'genres'
            if getattr(info, 'genres', None):
                info.genres = self.process_genres(info.genres)
        except Exception as e:
            print(f"[GenreTree] ERROR in process_track_info: {e}", flush=True)

    def process_album_info(self, info, **kwargs):
        try:
            if getattr(info, 'genre', None):
                info.genre = ", ".join(self.process_genres(info.genre))
            
            if getattr(info, 'genres', None):
                info.genres = self.process_genres(info.genres)
        except Exception as e:
            print(f"[GenreTree] ERROR in process_album_info: {e}", flush=True)

    def process_task_apply(self, task, session, **kwargs):
        try:
            # Safely process all individual tracks (the actual files)
            for item in getattr(task, 'items', []):
                current_genre = item.get('genre')
                if current_genre:
                    # NOTE: change ", " to "/" if you want Plex to split them explicitly
                    new_genre = "/".join(self.process_genres(current_genre)) 
                    if new_genre != current_genre:
                        item['genre'] = new_genre
                        item.store()
        except Exception as e:
            print(f"[GenreTree] ERROR in process_task_apply: {e}", flush=True)

