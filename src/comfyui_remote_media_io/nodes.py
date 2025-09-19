# Fichier : /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/nodes.py
# Version finale et corrigée pour l'upload de vidéos vers BunnyCDN.

import os
import requests
import folder_paths
import uuid # Pour générer des noms de fichiers uniques

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "media_file": ("*",),
                "storage_zone_name": ("STRING", {"default": ""}),
                "access_key": ("STRING", {"default": "", "multiline": True}),
                "storage_zone_region": (["Falkenstein", "New York", "Los Angeles", "Singapore", "Sydney"],),
                "remote_path": ("STRING", {"default": "videos/"}),
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_video"
    CATEGORY = "BunnyCDN"
    OUTPUT_NODE = True

    def get_bunny_hostname(self, region: str):
        return {
            "Falkenstein": "storage.bunnycdn.com", "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com", "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        # 1. Vérification des identifiants (via node ou variables d'environnement)
        szn = storage_zone_name or os.getenv("BUNNY_STORAGE_ZONE_NAME")
        ak = access_key or os.getenv("BUNNY_ACCESS_KEY")
        if not szn or not ak:
            print("ERREUR: Le nom de la zone de stockage ou la clé d'accès ne sont pas définis.")
            return {"result": ("",)}

        # 2. Sauvegarde de la vidéo dans un fichier temporaire
        temp_dir = folder_paths.get_temp_directory()
        # Génère un nom de fichier unique pour éviter les conflits et les problèmes de nommage
        filename = f"{remote_filename_prefix}{uuid.uuid4()}.mp4"
        local_filepath = os.path.join(temp_dir, filename)

        try:
            print(f"Sauvegarde de la vidéo en cours dans le fichier temporaire : {local_filepath}")
            # --- CORRECTION FINALE ---
            # On appelle directement .save_to() sur l'objet media_file
            media_file.save_to(local_filepath, format="mp4", codec="h264")
        except Exception as e:
            print(f"ERREUR lors de la sauvegarde de la vidéo en fichier temporaire : {e}")
            return {"result": ("",)}

        # 3. Upload du fichier temporaire
        remote_full_path = os.path.join(remote_path, filename).replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{szn}/{remote_full_path}"
        headers = {"AccessKey": ak, "Content-Type": "application/octet-stream"}

        try:
            print(f"Envoi de '{local_filepath}' vers BunnyCDN...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
                response.raise_for_status()

            public_url = f"https://{szn}.b-cdn.net/{remote_full_path}"
            print(f"SUCCÈS ! URL publique : {public_url}")
            
            return {"ui": {"bunny_cdn_url": [public_url]}, "result": (public_url,)}

        except Exception as e:
            print(f"ERREUR lors de l'upload vers Bunny CDN : {e}")
            return {"result": ("",)}
        finally:
            # 4. Nettoyage du fichier temporaire après l'upload
            if os.path.exists(local_filepath):
                print(f"Nettoyage du fichier temporaire : {local_filepath}")
                os.remove(local_filepath)

# Enregistrement du node pour ComfyUI
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
# Nom d'affichage du node dans l'interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
