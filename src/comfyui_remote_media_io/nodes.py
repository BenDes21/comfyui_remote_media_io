# Fichier : /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/nodes.py
# Version finale, simple et optimisée pour l'upload de vidéos vers BunnyCDN.

import os
import requests
import folder_paths

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        """Définit les entrées nécessaires pour le node."""
        return {
            "required": {
                "media_file": ("*",),  # Accepte la sortie vidéo de n'importe quel node
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
        """Retourne le hostname de l'API de stockage en fonction de la région."""
        return {
            "Falkenstein": "storage.bunnycdn.com",
            "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com",
            "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        """Fonction principale qui reçoit le fichier, trouve son chemin local et l'upload sur BunnyCDN."""
        
        # 1. Vérification des identifiants
        if not storage_zone_name or not access_key:
            print("ERREUR: Le nom de la zone de stockage ou la clé d'accès ne sont pas définis.")
            return {"result": ("",)}

        # 2. Extraction du chemin du fichier local
        # Le node `Create Video` renvoie une liste contenant un tuple : [('ComfyUI_00001_.mp4',)]
        try:
            filename = media_file[0][0]
            local_filepath = os.path.join(folder_paths.get_temp_directory(), filename)
        except (TypeError, IndexError):
            print(f"ERREUR: Impossible d'extraire le nom du fichier depuis l'entrée. Données reçues: {media_file}")
            return {"result": ("",)}

        if not os.path.exists(local_filepath):
            print(f"ERREUR: Fichier vidéo non trouvé à l'emplacement attendu : {local_filepath}")
            return {"result": ("",)}

        # 3. Construction de l'URL et des en-têtes pour l'upload
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = {"AccessKey": access_key, "Content-Type": "application/octet-stream"}

        # 4. Upload du fichier
        try:
            print(f"Envoi de '{local_filepath}' vers BunnyCDN...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
                response.raise_for_status()  # Lève une exception si l'upload échoue

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"SUCCÈS ! URL publique : {public_url}")
            
            # Retourne le résultat pour le webhook
            return {"ui": {"bunny_cdn_url": [public_url]}, "result": (public_url,)}

        except Exception as e:
            print(f"ERREUR lors de l'upload vers Bunny CDN : {e}")
            return {"result": ("",)}

# Enregistrement du node pour ComfyUI
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}

# Nom d'affichage du node dans l'interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
