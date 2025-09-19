# Fichier : /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/nodes.py
# Ce fichier contient maintenant la logique et l'enregistrement du node BunnyCDN.

import os
import requests
import folder_paths

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "media_file": ("*",),
                "storage_zone_name": ("STRING", {"default": "votre-zone-de-stockage"}),
                "access_key": ("STRING", {"default": "votre-cle-d-acces-stockage", "multiline": True}),
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
        regions = {
            "Falkenstein": "storage.bunnycdn.com",
            "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com",
            "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }
        return regions.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        print("BunnyCDN Uploader: Début du processus d'upload.")

        local_filepath = None
        filename = None
        
        # Logique robuste pour extraire le nom du fichier depuis la sortie du node "Create Video"
        try:
            # Le format de sortie est [('nom_fichier.mp4',)]
            if isinstance(media_file, list) and len(media_file) > 0 and \
               isinstance(media_file[0], tuple) and len(media_file[0]) > 0:
                filename = media_file[0][0]
                # Les vidéos du node CreateVideo sont toujours dans le dossier temporaire
                local_filepath = os.path.join(folder_paths.get_temp_directory(), filename)
                print(f"BunnyCDN Uploader: Fichier identifié -> {filename}")
        except Exception as e:
            print(f"BunnyCDN Uploader: Erreur lors de l'extraction du nom de fichier : {e}")

        if not local_filepath or not os.path.exists(local_filepath):
            print(f"ERREUR: Impossible de trouver un fichier vidéo valide à uploader. Entrée reçue: {media_file}")
            return {"ui": {"bunny_cdn_url": ["upload_failed"]}, "result": ("",)}

        # Logique d'upload vers BunnyCDN
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = { "AccessKey": access_key, "Content-Type": "application/octet-stream" }

        try:
            print(f"BunnyCDN Uploader: Envoi de '{local_filepath}' vers '{api_url}'...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"SUCCÈS ! Envoi réussi. URL publique : {public_url}")
            
            # Le format "result" est important pour que le webhook puisse récupérer la donnée
            return {"ui": {"bunny_cdn_url": [public_url]}, "result": (public_url,)}

        except Exception as e:
            print(f"Une erreur inattendue est survenue pendant l'upload : {e}")
            return {"ui": {"bunny_cdn_url": ["upload_failed"]}, "result": ("",)}

# On déclare à ComfyUI nos nodes. Ici, il n'y a plus que le nôtre.
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}

# On donne un nom lisible à notre node dans l'interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
