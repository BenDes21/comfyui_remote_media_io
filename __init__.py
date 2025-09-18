# Fichier __init__.py pour comfyui-bunny-uploader (version de test minimaliste)

class BunnyCDNUploadVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"media_file": ("*",)}}
    
    RETURN_TYPES = ()
    FUNCTION = "do_nothing"
    CATEGORY = "BunnyCDN_Test"
    OUTPUT_NODE = True

    def do_nothing(self, media_file):
        print("--- LE NOEUD FACTICE BunnyCDNUploadVideo A ÉTÉ EXÉCUTÉ ---")
        return {} # Ne fait absolument rien

# Enregistrement
NODE_CLASS_MAPPINGS = {
    "BunnyCDNUploadVideo": BunnyCDNUploadVideo
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "BunnyCDNUploadVideo": "BunnyCDN Upload Video (TEST)"
}
