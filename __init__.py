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

    def get_bunny_hostname(self, region: str):
        regions = {
            "Falkenstein": "storage.bunnycdn.com", "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com", "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }
        return regions.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        global folder_paths
        if folder_paths is None:
            import folder_paths
        
        # --- DÉBUT DE LA CORRECTION ---
        # Cette nouvelle logique est plus intelligente pour trouver le nom du fichier.
        
        filename = None
        # Cas 1: L'entrée est une liste (comportement typique de l'UI de Comfy)
        if isinstance(media_file, list) and len(media_file) > 0:
            media_info = media_file[0]
            if isinstance(media_info, dict) and 'filename' in media_info:
                filename = media_info.get('filename')
                subfolder = media_info.get('subfolder', '')
                file_type = media_info.get('type', 'output')

        # Cas 2: L'entrée vient directement d'un node comme CreateVideo (tuple ou autre)
        # On essaie d'extraire le premier élément s'il ressemble à un nom de fichier.
        elif isinstance(media_file, (list, tuple)) and len(media_file) > 0 and isinstance(media_file[0], str):
             filename = media_file[0]
             subfolder = ""
             file_type = "output" # Les vidéos sont généralement dans le dossier de sortie

        # Si on n'a toujours pas trouvé, on affiche une erreur claire
        if filename is None:
            print(f"Erreur : Impossible d'extraire le nom de fichier depuis l'entrée de type {type(media_file)}")
            return {"ui": {"bunny_cdn_url": [""]}}
            
        print(f"Fichier identifié : {filename}, type: {file_type}, sous-dossier: {subfolder}")

        if file_type == 'output':
             local_filepath = os.path.join(folder_paths.get_output_directory(), subfolder, filename)
        else:
             local_filepath = os.path.join(folder_paths.get_temp_directory(), subfolder, filename)
        # --- FIN DE LA CORRECTION ---

        if not os.path.exists(local_filepath):
            print(f"Fichier non trouvé à l'emplacement attendu : {local_filepath}")
            return {"ui": {"bunny_cdn_url": [""]}}
            
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = { "AccessKey": access_key, "Content-Type": "application/octet-stream" }

        try:
            print(f"Tentative d'envoi de '{local_filepath}' vers '{api_url}'...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            if response.status_code not in [201, 200]:
                print(f"Échec de l'envoi vers Bunny CDN. Statut : {response.status_code}, Réponse : {response.text}")
                return {"ui": {"bunny_cdn_url": [""]}}

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"Envoi réussi ! URL : {public_url}")
            
            return {"ui": {"bunny_cdn_url": [public_url]}}

        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion : {e}")
            return {"ui": {"bunny_cdn_url": [""]}}
        except FileNotFoundError:
            print(f"Erreur fatale : Fichier non trouvé au moment de l'ouverture : {local_filepath}")
            return {"ui": {"bunny_cdn_url": [""]}}


NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
