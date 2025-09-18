# Fichier __init__.py pour comfyui-bunny-uploader (Version FINALE)

import os
import requests

try:
    import folder_paths
except ImportError:
    folder_paths = None

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
            },
            "optional": {
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_video"
    CATEGORY = "BunnyCDN"
    OUTPUT_NODE = True

    def get_bunny_hostname(self, region: str) -> str:
        regions = {
            "Falkenstein": "storage.bunnycdn.com", "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com", "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }
        return regions.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file: dict, storage_zone_name: str, access_key: str, storage_zone_region: str, remote_path: str, remote_filename_prefix: str = ""):
        global folder_paths
        if folder_paths is None:
            import folder_paths
        
        if not isinstance(media_file, dict) or 'filename' not in media_file or 'type' not in media_file:
            print("Données d'entrée invalides...")
            return {"ui": {"bunny_cdn_url": [""]}}

        filename = media_file['filename']
        subfolder = media_file.get('subfolder', '')
        # --- CORRECTION IMPORTANTE ---
        # Le type de media_file est différent pour les vidéos. Il faut chercher dans le bon dossier.
        if media_file.get('type') == 'output':
             local_filepath = os.path.join(folder_paths.get_output_directory(), subfolder, filename)
        else:
             # Fallback pour d'autres types de fichiers si nécessaire
             local_filepath = os.path.join(folder_paths.get_temp_directory(), subfolder, filename)

        if not os.path.exists(local_filepath):
            # Tentative de recherche dans l'autre dossier au cas où
            other_path = os.path.join(folder_paths.get_output_directory(), subfolder, filename)
            if os.path.exists(other_path):
                local_filepath = other_path
            else:
                print(f"Fichier non trouvé dans les dossiers de sortie/temporaires : {local_filepath}")
                return {"ui": {"bunny_cdn_url": [""]}}
            
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = { "AccessKey": access_key, "Content-Type": "application/octet-stream" }

        try:
            print(f"Tentative d'envoi de {local_filepath} vers {api_url}...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            if response.status_code not in [201, 200]:
                print(f"Échec de l'envoi vers Bunny CDN. Statut : {response.status_code}, Réponse : {response.text}")
                return {"ui": {"bunny_cdn_url": [""]}}

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"Envoi réussi ! URL : {public_url}")
            
            # La sortie qui sera renvoyée par le worker RunPod
            return {"ui": {"bunny_cdn_url": [public_url]}}

        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion lors de l'envoi vers Bunny CDN : {e}")
            return {"ui": {"bunny_cdn_url": [""]}}

# Enregistrement
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
