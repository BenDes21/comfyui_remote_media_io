from fractions import Fraction
from inspect import cleandoc
import time
import requests
from PIL import Image, ImageSequence, ImageOps
from io import BytesIO
import torch
import numpy as np
import av


class LoadRemoteImage:
    """
    A node to load image from URL.

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tulple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tulple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        Return a dictionary which contains config for all input fields.
        Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
        Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
        The type can be a list for selection.

        Returns: `dict`:
            - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
            - Value input_fields (`dict`): Contains input fields config:
                * Key field_name (`string`): Name of a entry-point method's argument
                * Value field_config (`tuple`):
                    + First value is a string indicate the type of field or a list for selection.
                    + Secound value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "image_url": ("STRING", {"multiline": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "load_image"

    # OUTPUT_NODE = False
    # OUTPUT_TOOLTIPS = ("",) # Tooltips for the output node

    CATEGORY = "image"

    def pil_to_tensor(self, pil_image):
        """
        Convert a PIL image (or sequence of images) to torch tensors.

        Args:
            pil_image (PIL.Image): Input image, possibly multi-frame (e.g. GIF).

        Returns:
            tuple[torch.Tensor, torch.Tensor]:
                - image_tensor: Float tensor in [0,1], shape (frames, H, W, 3)
                - mask_tensor:  Float tensor in [0,1], shape (frames, H, W)
        """
        image_tensors = []
        mask_tensors = []

        for frame in ImageSequence.Iterator(pil_image):
            # Handle EXIF orientation
            frame = ImageOps.exif_transpose(frame)

            # Normalize 32-bit integer images
            if frame.mode == "I":
                frame = frame.point(lambda p: p * (1 / 255))

            # Convert to RGB float tensor
            rgb_array = np.array(frame.convert("RGB"), dtype=np.float32) / 255.0
            rgb_tensor = torch.from_numpy(rgb_array).unsqueeze(0)  # (1, H, W, 3)

            # Extract alpha channel as mask if available
            if "A" in frame.getbands():
                alpha_array = np.array(frame.getchannel("A"), dtype=np.float32) / 255.0
                mask_tensor = 1.0 - torch.from_numpy(alpha_array)  # invert alpha
            else:
                # Fallback: dummy mask (64x64, all zeros)
                mask_tensor = torch.zeros((64, 64), dtype=torch.float32)

            image_tensors.append(rgb_tensor)
            mask_tensors.append(mask_tensor.unsqueeze(0))  # add frame dimension

        # Concatenate frames if multiple
        if len(image_tensors) > 1:
            image_tensor = torch.cat(image_tensors, dim=0)
            mask_tensor = torch.cat(mask_tensors, dim=0)
        else:
            image_tensor = image_tensors[0]
            mask_tensor = mask_tensors[0]

        return image_tensor, mask_tensor

    def load_image(self, image_url):
        # download image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        return self.pil_to_tensor(img)

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """

    @classmethod
    def IS_CHANGED(cls, image_url):
        return image_url


class LoadRemoteVideo:
    """
    A node to load video from URL.

    Class methods
    -------------
    INPUT_TYPES (dict):
        Defines required input parameters for the node.
    IS_CHANGED:
        Optional method to control when the node is re-executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tuple.
    FUNCTION (`str`):
        The entry-point method to run.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"multiline": True}),
                "start_second": ("INT", {"multiline": False}),
                "video_length_seconds": ("INT", {"multiline": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "FLOAT")
    RETURN_NAMES = ("IMAGES", "AUDIO", "FPS")
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "load_video"
    CATEGORY = "image/video"

    def load_video(self, video_url, start_second, video_length_seconds):
        """
        Downloads a video from a URL and decodes only the requested segment into tensors
        (both video and audio) in a single loop.
        """

        # download to buffer
        download_start = time.time()
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        buffer = BytesIO(response.content)
        download_end = time.time()
        print(f"Finished downloading in {download_end - download_start:.2f}s.")

        # open container
        container = av.open(buffer)

        # pick streams
        video_stream = next(s for s in container.streams if s.type == "video")
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        frame_rate = video_stream.average_rate or Fraction(25, 1)

        # compute bounds
        start_pts = int(start_second / av.time_base)  # in microseconds
        end_second = start_second + video_length_seconds

        # seek close to start
        container.seek(start_pts, any_frame=False, backward=True, stream=video_stream)

        frames = []
        audio_frames = []

        # decode interleaved
        for packet in container.demux((video_stream, audio_stream) if audio_stream else (video_stream,)):
            for frame in packet.decode():
                t = float(frame.pts * frame.time_base)
                if t < start_second:
                    continue
                if t >= end_second:
                    container.close()
                    images_tensor = torch.cat(frames, dim=0) if frames else None
                    audio_tensor = None
                    if audio_frames:
                        waveform = torch.cat(audio_frames, dim=1).unsqueeze(0)
                        audio_tensor = {
                            "waveform": waveform,
                            "sample_rate": audio_stream.rate,
                        }
                    return images_tensor, audio_tensor, frame_rate

                if packet.stream.type == "video":
                    img = frame.to_ndarray(format="rgb24")
                    img = torch.from_numpy(img).float() / 255.0
                    frames.append(img.unsqueeze(0))

                elif packet.stream.type == "audio":
                    arr = frame.to_ndarray()  # (channels, samples)
                    audio_frames.append(torch.from_numpy(arr))

        # finalize
        images_tensor = torch.cat(frames, dim=0) if frames else None
        audio_tensor = None
        if audio_frames:
            waveform = torch.cat(audio_frames, dim=1).unsqueeze(0)
            audio_tensor = {"waveform": waveform, "sample_rate": audio_stream.rate}

        return images_tensor, audio_tensor, frame_rate

    @classmethod
    def IS_CHANGED(cls, video_url, start_second, video_length_seconds):
        return video_url


class LoadRemoteAudio:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tulple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tulple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
        Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
        The type can be a list for selection.

        Returns: `dict`:
            - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
            - Value input_fields (`dict`): Contains input fields config:
                * Key field_name (`string`): Name of a entry-point method's argument
                * Value field_config (`tuple`):
                    + First value is a string indicate the type of field or a list for selection.
                    + Secound value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "audio_url": ("STRING", {"multiline": True}),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "load_audio"
    CATEGORY = "audio"

    def load_audio(self, audio_url):
        """
        Downloads audio from a URL and decodes only the requested segment
        into a tensor.
        """

        # download to buffer
        download_start = time.time()
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        buffer = BytesIO(response.content)
        download_end = time.time()
        print(f"Finished downloading in {download_end - download_start:.2f}s.")

        # open container
        container = av.open(buffer)

        # pick audio stream
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if not audio_stream:
            raise ValueError("No audio stream found in the file.")

        audio_frames = []

        # decode interleaved
        for packet in container.demux(audio_stream):
            for frame in packet.decode():
                arr = frame.to_ndarray()  # (channels, samples)
                audio_frames.append(torch.from_numpy(arr))

        print(f"Decoded {len(audio_frames)} audio frames.")

        waveform = torch.cat(audio_frames, dim=1).unsqueeze(0)
        audio_tensor = {"waveform": waveform, "sample_rate": audio_stream.rate}

        print(f"Final audio tensor shape: {audio_tensor['waveform'].shape}, sample rate: {audio_tensor['sample_rate']}")

        return (audio_tensor,)

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """

    @classmethod
    def IS_CHANGED(s, audio_url):
        return audio_url
