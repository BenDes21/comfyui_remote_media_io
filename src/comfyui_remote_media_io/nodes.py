from .loader_nodes import (
    LoadRemoteAudio,
    LoadRemoteImage,
    LoadRemoteVideo,
)

from .saver_nodes import SaveAudioToRemote, SaveImageToRemote, SaveVideoToRemote

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique


NODE_CLASS_MAPPINGS = {
    "LoadRemoteImage": LoadRemoteImage,
    "LoadRemoteVideo": LoadRemoteVideo,
    "LoadRemoteAudio": LoadRemoteAudio,
    # This nodes require a input (bucket saving path & name)
    "SaveImageToRemote": SaveImageToRemote,
    "SaveVideoToRemote": SaveVideoToRemote,
    "SaveAudioToRemote": SaveAudioToRemote,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadRemoteImage": "Load Remote Image",
    "LoadRemoteVideo": "Load Remote Video",
    "LoadRemoteAudio": "Load Remote Audio",
    "SaveImageToRemote": "Save Image To Remote",
    "SaveVideoToRemote": "Save Video To Remote",
    "SaveAudioToRemote": "Save Audio To Remote",
}
