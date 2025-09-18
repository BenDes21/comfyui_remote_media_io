import requests
import os
import uuid
from typing import Any, Dict, List

class BunnyUploadVideo:
    """
    Node to upload a video (or any file) to BunnyCDN Storage
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "file_path": ("STRING", {"multiline": False, "default": ""}),
                "storage_zone": ("STRING", {"multiline": False, "default": "your-storage-zone"}),
                "access_key": ("STRING", {"multiline": False, "default": "your-storage-access-key"}),
                "storage_region": ("STRING", {"multiline": False, "default": "ny"}),  # ex: ny, la, sg
                "destination_path": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("cdn_url",)
    FUNCTION = "upload_to_bunny"
    CATEGORY = "BunnyCDN"

    def upload_to_bunny(self, file_path: str, storage_zone: str, access_key: str, storage_region: str, destination_path: str) -> tuple:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        if not destination_path:
            destination_path = filename
        else:
            destination_path = destination_path.strip("/")
            destination_path = f"{destination_path}/{filename}"

        url = f"https://storage.bunnycdn.com/{storage_zone}/{destination_path}"

        headers = {
            "AccessKey": access_key,
        }

        with open(file_path, "rb") as f:
            resp = requests.put(url, headers=headers, data=f)

        if resp.status_code not in [201, 200]:
            raise Exception(f"Failed to upload: {resp.status_code}, {resp.text}")

        cdn_url = f"https://{storage_zone}.b-cdn.net/{destination_path}"
        return (cdn_url,)


NODE_CLASS_MAPPINGS = {
    "BunnyUploadVideo": BunnyUploadVideo
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyUploadVideo": "BunnyCDN Upload Video"
}
