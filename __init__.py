"""
Ce fichier __init__.py est le point d'entrée pour ComfyUI.
Il a pour rôle de collecter tous les nœuds définis dans ce package
et de les présenter à ComfyUI sous un format unifié.
"""

# 1. Importer les mappings des nœuds originaux du package
# (Cela peut inclure des nœuds pour Azure, S3, etc., s'ils sont définis dans nodes.py ou saver_nodes.py)
try:
    from .src.comfyui_remote_media_io.nodes import NODE_CLASS_MAPPINGS as original_class_mappings
    from .src.comfyui_remote_media_io.nodes import NODE_DISPLAY_NAME_MAPPINGS as original_display_name_mappings
except ImportError:
    # Si le fichier n'existe pas ou est vide, on part de zéro
    original_class_mappings = {}
    original_display_name_mappings = {}

# 2. Importer les mappings de VOTRE nouveau nœud Bunny CDN
# Assurez-vous que le nom du fichier est bien 'bunny_storage_nodes.py'
try:
    from .src.comfyui_remote_media_io.bunny_storage_nodes import NODE_CLASS_MAPPINGS as bunny_class_mappings
    from .src.comfyui_remote_media_io.bunny_storage_nodes import NODE_DISPLAY_NAME_MAPPINGS as bunny_display_name_mappings
except ImportError as e:
    print(f"[ERROR] Impossible de charger le nœud Bunny CDN : {e}")
    bunny_class_mappings = {}
    bunny_display_name_mappings = {}


# 3. Fusionner tous les dictionnaires de mappings
# On commence avec une copie des originaux...
NODE_CLASS_MAPPINGS = original_class_mappings.copy()
NODE_DISPLAY_NAME_MAPPINGS = original_display_name_mappings.copy()

# ...puis on ajoute (ou on met à jour avec) les vôtres.
NODE_CLASS_MAPPINGS.update(bunny_class_mappings)
NODE_DISPLAY_NAME_MAPPINGS.update(bunny_display_name_mappings)


# 4. Exporter les mappings finaux et complets pour que ComfyUI les trouve
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
