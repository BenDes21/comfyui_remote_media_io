import os
import requests
import folder_paths # Important pour trouver le chemin des fichiers de sortie de ComfyUI

class BunnyCDNUploadVideo:
    """
    Node to upload a video (or any file) from a ComfyUI workflow to BunnyCDN Storage.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # MODIFIÉ : On accepte n'importe quel type de fichier venant d'un autre noeud
                "media_file": ("*",), 
                "storage_zone_name": ("STRING", {"default": "votre-zone-de-stockage"}),
                "access_key": ("STRING", {"default": "votre-cle-d-acces-stockage", "multiline": True}),
                # NOUVEAU : Un menu déroulant pour les régions, plus sûr et plus pratique
                "storage_zone_region": (["Falkenstein", "New York", "Los Angeles", "Singapore", "Sydney"],),
                "remote_path": ("STRING", {"default": "videos/"}), # Dossier de destination sur le CDN
            },
            "optional": {
                "remote_filename_prefix": ("STRING", {"default": "comfyui_"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("bunny_cdn_url",)
    FUNCTION = "upload_video"
    CATEGORY = "BunnyCDN" # Vous pouvez garder votre catégorie

    def get_bunny_hostname(self, region: str) -> str:
        # NOUVEAU : Fonction pour obtenir le bon hostname de l'API selon la région
        regions = {
            "Falkenstein": "storage.bunnycdn.com",
            "New York": "ny.storage.bunnycdn.com",
            "Los Angeles": "la.storage.bunnycdn.com",
            "Singapore": "sg.storage.bunnycdn.com",
            "Sydney": "syd.storage.bunnycdn.com",
        }
        return regions.get(region, "storage.bunnycdn.com")

    def upload_video(self, media_file: dict, storage_zone_name: str, access_key: str, storage_zone_region: str, remote_path: str, remote_filename_prefix: str = ""):
        # MODIFIÉ : La logique pour extraire le chemin du fichier de l'objet ComfyUI
        if not isinstance(media_file, dict) or 'filename' not in media_file or 'type' not in media_file:
            print("Données d'entrée invalides. Assurez-vous de connecter la sortie d'un noeud de sauvegarde (Save Image, VHS_VideoCombine, etc.).")
            return ("",)

        filename = media_file['filename']
        subfolder = media_file.get('subfolder', '')
        # Construit le chemin local complet du fichier généré par ComfyUI
        local_filepath = os.path.join(folder_paths.get_output_directory(), subfolder, filename)

        if not os.path.exists(local_filepath):
            print(f"Fichier non trouvé à l'emplacement attendu : {local_filepath}")
            return ("",)
            
        # Construit le chemin complet sur le CDN
        remote_full_path = os.path.join(remote_path, f"{remote_filename_prefix}{filename}").replace("\\", "/")
        
        # NOUVEAU : Utilise le bon hostname pour l'URL de l'API
        hostname = self.get_bunny_hostname(storage_zone_region)
        api_url = f"https://{hostname}/{storage_zone_name}/{remote_full_path}"

        headers = {
            "AccessKey": access_key,
            "Content-Type": "application/octet-stream" # Plus spécifique pour les fichiers binaires
        }

        try:
            print(f"Tentative d'envoi de {local_filepath} vers {api_url}...")
            with open(local_filepath, 'rb') as f:
                response = requests.put(api_url, data=f, headers=headers)
            
            # Votre excellente gestion des erreurs
            if response.status_code not in [201, 200]:
                print(f"Échec de l'envoi vers Bunny CDN. Statut : {response.status_code}, Réponse : {response.text}")
                raise Exception(f"Échec de l'envoi : {response.status_code}, {response.text}")

            public_url = f"https://{storage_zone_name}.b-cdn.net/{remote_full_path}"
            print(f"Envoi réussi ! URL : {public_url}")
            return (public_url,)

        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion lors de l'envoi vers Bunny CDN : {e}")
            return ("",)

# Enregistrement du noeud pour que ComfyUI le reconnaisse
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video"
}
