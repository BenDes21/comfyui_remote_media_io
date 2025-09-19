# /comfyui/custom_nodes/comfyui_remote_media_io/src/comfyui_remote_media_io/saver_nodes.py
# Fichier modifié pour utiliser BunnyCDN au lieu d'Azure.

import os
import requests
import folder_paths

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        """
        Définit les entrées requises pour le node dans l'interface de ComfyUI.
        """
        return {
            "required": {
                "media_file": ("*",), # Le type '*' accepte n'importe quelle entrée
                "storage_zone_name": ("STRING", {"default": "votre-zone-de-stockage"}),
                "access_key": ("STRING", {"default": "votre-cle-d-acces-stockage", "multiline": True}),
                "storage_zone_region": (["Falkenstein", "New York", "Los Angeles", "Singapore", "Sydney"],),
                "remote_path": ("STRING", {"default": "videos/"}),
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    # Définition des sorties et de la fonction principale
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_video"
    CATEGORY = "BunnyCDN" # Une catégorie claire pour le retrouver
    OUTPUT_NODE = True

    def get_bunny_hostname(self, region: str):
        """Retourne le hostname de l'API de stockage BunnyCDN en fonction de la région."""
        regions = {
            "Falkenstein": "storage.bunnycdn.com",
            "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com",
            "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }
        return regions.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file, storage_zone_name, access_key, storage_zone_region, remote_path, remote_filename_prefix=""):
        """
        Fonction principale qui reçoit le fichier, trouve son chemin local et l'upload sur BunnyCDN.
        """
        print("BunnyCDN Uploader: Début du processus d'upload.")

        local_filepath = None
        filename = None
        
        # Logique robuste pour trouver le nom du fichier local
        try:
            # Le node CreateVideo renvoie une liste contenant un tuple, ex: [('ComfyUI_00001_.mp4',)]
            # Nous extrayons le nom du fichier de cette structure.
            if isinstance(media_file, list) and len(media_file) > 0 and \
               isinstance(media_file[0], tuple) and len(media_file[0]) > 0:
                filename = media_file[0][0]
                # Les vidéos du node CreateVideo sont toujours dans le dossier temporaire.
                local_filepath = os.path.join(folder_paths.get_temp_directory(), filename)
                print(f"BunnyCDN Uploader: Fichier identifié depuis la sortie de CreateVideo -> {filename}")
        except Exception:
             print("BunnyCDN Uploader: Impossible d'extraire depuis le format CreateVideo. Tentative sur d'autres formats.")
             pass # Si ça échoue, on essaie une autre méthode ci-dessous

        # Fallback si l'entrée est un format dictionnaire plus standard
        if not local_filepath:
             try:
                media_info = media_file[0] if isinstance(media_file, list) else media_file
                if isinstance(media_info, dict) and 'filename' in media_info:
                    filename = media_info['filename']
                    subfolder = media_info.get('subfolder', '')
                    file_type = media_info.get('type', 'output')
                    base_path = folder_paths.get_output_directory() if file_type == 'output' else folder_paths.get_temp_directory()
                    local_filepath = os.path.join(base_path, subfolder, filename)
                    print(f"BunnyCDN Uploader: Fichier identifié depuis un dictionnaire -> {filename}")
             except Exception:
                 pass # Échec silencieux pour passer au verdict final

        if not local_filepath or not os.path.exists(local_filepath):
            print(f"ERREUR: Impossible de trouver un fichier vidéo valide à uploader. Entrée reçue: {media_file}")
            # Retourner un résultat vide pour que le workflow ne plante pas
            return {"ui": {"bunny_cdn_url": ["upload_failed"]}, "result": ("",)}

        # Construction de l'URL pour l'API BunnyCDN
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"
        headers = { "AccessKey": access_key, "Content-Type": "application/octet-stream" }

        try:
            print(f"BunnyCDN Uploader: Envoi de '{local_filepath}' vers '{api_url}'...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"SUCCÈS ! Envoi réussi. URL publique : {public_url}")
            
            # Le format "result" est important pour que le webhook puisse récupérer la donnée
            return {"ui": {"bunny_cdn_url": [public_url]}, "result": (public_url,)}

        except requests.exceptions.HTTPError as e:
            print(f"ERREUR HTTP lors de l'upload vers Bunny CDN. Statut : {e.response.status_code}, Réponse : {e.response.text}")
        except Exception as e:
            print(f"Une erreur inattendue est survenue pendant l'upload : {e}")
        
        return {"ui": {"bunny_cdn_url": ["upload_failed"]}, "result": ("",)}

# On déclare à ComfyUI que notre node existe
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}

# On donne un nom lisible à notre node dans l'interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
