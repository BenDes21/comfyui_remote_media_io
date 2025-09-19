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

    def upload_video(self, media_file: any, storage_zone_name: str, access_key: str, storage_zone_region: str, remote_path: str, remote_filename_prefix: str = ""):
        # Import folder_paths dynamically if it wasn't available at the module level
        global folder_paths
        if folder_paths is None:
            import folder_paths
        
        # Handle cases where media_file is a list
        if isinstance(media_file, list):
            if len(media_file) == 0:
                print("Données d'entrée invalides : la liste media_file est vide.")
                return {"ui": {"bunny_cdn_url": [""]}}
            media_info = media_file[0]
        else:
            media_info = media_file

        # Validate that media_info is a dictionary with the expected keys
        if not isinstance(media_info, dict) or 'filename' not in media_info or 'type' not in media_info:
            print(f"Données d'entrée invalides. Reçu un objet de type {type(media_info)} au lieu d'un dictionnaire attendu.")
            return {"ui": {"bunny_cdn_url": [""]}}

        filename = media_info['filename']
        subfolder = media_info.get('subfolder', '')
        
        # Determine the full local path of the file
        if media_info.get('type') == 'output':
             local_filepath = os.path.join(folder_paths.get_output_directory(), subfolder, filename)
        else:
             local_filepath = os.path.join(folder_paths.get_temp_directory(), subfolder, filename)

        # Fallback check in case the file is not in the expected directory
        if not os.path.exists(local_filepath):
            other_path = os.path.join(folder_paths.get_output_directory(), subfolder, filename)
            if os.path.exists(other_path):
                local_filepath = other_path
            else:
                print(f"Fichier non trouvé dans les dossiers de sortie/temporaires : {filename}")
                return {"ui": {"bunny_cdn_url": [""]}}
            
        # Construct the remote URL for Bunny CDN
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = { "AccessKey": access_key, "Content-Type": "application/octet-stream" }

        try:
            print(f"Tentative d'envoi de '{local_filepath}' vers '{api_url}'...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            # Check for a successful upload
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

# Register the node with ComfyUI
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
