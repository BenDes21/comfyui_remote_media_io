"""
__init__.py de production :
Tente de charger tous les nœuds de manière robuste.
"""

# On commence avec des dictionnaires vides
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

print("--- [comfyui_remote_media_io] Début du chargement des nœuds ---")

# 1. Tentative de chargement des nœuds originaux (Azure, etc.)
try:
    from .src.comfyui_remote_media_io.nodes import NODE_CLASS_MAPPINGS as original_class_mappings
    from .src.comfyui_remote_media_io.nodes import NODE_DISPLAY_NAME_MAPPINGS as original_display_name_mappings
    NODE_CLASS_MAPPINGS.update(original_class_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(original_display_name_mappings)
    print("--- [comfyui_remote_media_io] Nœuds originaux chargés avec succès.")
except ImportError:
    print("--- [comfyui_remote_media_io] Avertissement : Impossible de trouver les nœuds originaux. On continue.")
except Exception as e:
    print(f"--- [comfyui_remote_media_io] Avertissement : Erreur lors du chargement des nœuds originaux : {e}")

# 2. Tentative de chargement de VOTRE nœud Bunny CDN
try:
    from .src.comfyui_remote_media_io.bunny_storage_nodes import NODE_CLASS_MAPPINGS as bunny_class_mappings
    from .src.comfyui_remote_media_io.bunny_storage_nodes import NODE_DISPLAY_NAME_MAPPINGS as bunny_display_name_mappings
    NODE_CLASS_MAPPINGS.update(bunny_class_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(bunny_display_name_mappings)
    print("--- [comfyui_remote_media_io] Nœud Bunny CDN chargé avec succès.")
except ImportError:
    print("--- [ERREUR] Impossible de trouver le fichier 'bunny_storage_nodes.py'.")
except Exception as e:
    print(f"--- [ERREUR] Erreur lors du chargement du nœud Bunny CDN : {e}")

print(f"--- [comfyui_remote_media_io] Chargement terminé. Nœuds totaux chargés: {len(NODE_CLASS_MAPPINGS)}")

# On exporte les mappings finaux pour ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
