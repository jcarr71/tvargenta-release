#!/usr/bin/env python3
"""
TVArgenta Modular System

Provides a lightweight plugin/mod system for TVArgenta features.
Mods can register routes, hooks, and be enabled/disabled dynamically.

Mod Structure:
  content/mods/mod_name/
  ├── manifest.json          # Mod metadata
  ├── __init__.py           # Mod entry point
  └── handlers.py           # Route handlers
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
from contextlib import contextmanager

logger = logging.getLogger("tvargenta.mods")


class ModManifest:
    """Represents a mod's metadata from manifest.json"""
    
    def __init__(self, manifest_path: Path):
        self.path = manifest_path
        self.mod_dir = manifest_path.parent
        self.data = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        """Load manifest.json"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load manifest at {self.path}: {e}")
            return {}
    
    @property
    def mod_id(self) -> str:
        """Unique mod identifier"""
        return self.data.get('id', self.mod_dir.name)
    
    @property
    def enabled(self) -> bool:
        """Whether this mod is enabled"""
        return self.data.get('enabled', True)
    
    @property
    def entry_point(self) -> str:
        """Module to import for mod initialization"""
        return self.data.get('entry_point', f'{self.mod_dir.name}.handlers')
    
    @property
    def version(self) -> str:
        """Mod version"""
        return self.data.get('version', '0.0.1')
    
    @property
    def description(self) -> str:
        """Human-readable mod description"""
        return self.data.get('description', '')
    
    def set_enabled(self, enabled: bool):
        """Enable or disable this mod"""
        self.data['enabled'] = enabled
        self._save_manifest()
    
    def _save_manifest(self):
        """Save manifest changes"""
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save manifest at {self.path}: {e}")


class ModRegistry:
    """Central registry for all mods"""
    
    def __init__(self, mods_dir: Path):
        self.mods_dir = mods_dir
        self.mods: Dict[str, 'Mod'] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Create mods directory if needed
        self.mods_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_mods(self) -> List[ModManifest]:
        """Discover all available mods"""
        manifests = []
        for mod_dir in self.mods_dir.iterdir():
            if not mod_dir.is_dir():
                continue
            
            manifest_path = mod_dir / 'manifest.json'
            if manifest_path.exists():
                manifests.append(ModManifest(manifest_path))
        
        return manifests
    
    def load_mods(self) -> Dict[str, 'Mod']:
        """Load all enabled mods"""
        manifests = self.discover_mods()
        loaded = {}
        
        for manifest in manifests:
            if not manifest.enabled:
                logger.info(f"Skipping disabled mod: {manifest.mod_id}")
                continue
            
            try:
                mod = Mod(manifest, self)
                mod.load()
                self.mods[manifest.mod_id] = mod
                loaded[manifest.mod_id] = mod
                logger.info(f"Loaded mod: {manifest.mod_id} v{manifest.version}")
            except Exception as e:
                logger.error(f"Failed to load mod {manifest.mod_id}: {e}")
        
        return loaded
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a callback for a hook point"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """Trigger all callbacks for a hook"""
        if hook_name not in self.hooks:
            return []
        
        results = []
        for callback in self.hooks[hook_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in hook {hook_name}: {e}")
        
        return results
    
    def get_mod(self, mod_id: str) -> Optional['Mod']:
        """Get a loaded mod by ID"""
        return self.mods.get(mod_id)
    
    def list_mods(self) -> List[str]:
        """List all loaded mod IDs"""
        return list(self.mods.keys())
    
    def enable_mod(self, mod_id: str) -> bool:
        """Enable a mod (updates manifest, requires app restart)"""
        manifests = self.discover_mods()
        for manifest in manifests:
            if manifest.mod_id == mod_id:
                manifest.set_enabled(True)
                logger.info(f"Enabled mod: {mod_id}")
                return True
        return False
    
    def disable_mod(self, mod_id: str) -> bool:
        """Disable a mod (updates manifest, requires app restart)"""
        manifests = self.discover_mods()
        for manifest in manifests:
            if manifest.mod_id == mod_id:
                manifest.set_enabled(False)
                logger.info(f"Disabled mod: {mod_id}")
                return True
        return False


class Mod:
    """Represents a loaded mod"""
    
    def __init__(self, manifest: ModManifest, registry: ModRegistry):
        self.manifest = manifest
        self.registry = registry
        self.module = None
        self.routes = []
        self.initialized = False
    
    def load(self):
        """Load and initialize the mod"""
        import sys
        import importlib
        
        # Add mod directory to path
        mod_path = str(self.manifest.mod_dir.parent)
        if mod_path not in sys.path:
            sys.path.insert(0, mod_path)
        
        # Import the entry point module
        try:
            module_name = self.manifest.entry_point
            self.module = importlib.import_module(module_name)
            
            # Call init function if it exists
            if hasattr(self.module, 'init_mod'):
                self.module.init_mod(self.registry)
            
            self.initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to load mod module {self.manifest.entry_point}: {e}")
    
    def get_routes(self) -> List[tuple]:
        """Get Flask routes from this mod"""
        if hasattr(self.module, 'get_routes'):
            return self.module.get_routes()
        return []
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get hook registrations from this mod"""
        if hasattr(self.module, 'get_hooks'):
            return self.module.get_hooks()
        return {}


def setup_mods(app, content_dir: Path) -> ModRegistry:
    """Initialize mod system in Flask app"""
    mods_dir = content_dir / 'mods'
    
    if not mods_dir.exists():
        logger.warning(f"Mods directory not found: {mods_dir}")
        return ModRegistry(mods_dir)
    
    registry = ModRegistry(mods_dir)
    
    try:
        # Load all mods
        registry.load_mods()
        logger.info(f"Loaded {len(registry.mods)} mods")
        
        # Register mod routes with Flask
        routes_registered = 0
        for mod_id, mod in registry.mods.items():
            if not mod.manifest.enabled:
                logger.info(f"Skipping disabled mod: {mod_id}")
                continue
            
            try:
                routes = mod.get_routes()
                for rule, view_func, methods in routes:
                    endpoint = f'{mod_id}_{view_func.__name__}'
                    app.add_url_rule(rule, endpoint, view_func, methods=methods)
                    logger.info(f"[MOD {mod_id}] Registered route {rule} ({methods})")
                    routes_registered += 1
                
                # Register hooks
                hooks = mod.get_hooks()
                for hook_name, callback in hooks.items():
                    registry.register_hook(hook_name, callback)
                    logger.info(f"[MOD {mod_id}] Registered hook {hook_name}")
            
            except Exception as e:
                logger.error(f"[MOD {mod_id}] Failed to load routes/hooks: {e}")
        
        logger.info(f"Registered {routes_registered} routes from {len(registry.mods)} mods")
        
        # Store registry on app for later access
        app.mod_registry = registry
        
        return registry
    
    except Exception as e:
        logger.error(f"Failed to initialize mod system: {e}")
        return registry


@contextmanager
def mod_enabled(registry: ModRegistry, mod_id: str):
    """Context manager to check if mod is loaded"""
    if mod_id in registry.mods:
        yield registry.mods[mod_id]
    else:
        yield None
