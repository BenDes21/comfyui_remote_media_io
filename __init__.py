# /comfyui/custom_nodes/comfyui_remote_media_io/__init__.py

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]

# Cette ligne importe TOUT ce qui est défini dans saver_nodes.py
from .src.comfyui_remote_media_io.saver_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

print("Custom Nodes: BunnyCDN Uploader (remplaçant remote_media_io) chargé.")
