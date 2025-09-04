from inspect import cleandoc
import io
import os
from PIL import Image
from io import BytesIO
import numpy as np
import av
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import torchaudio

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

azure_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net",
    credential=azure_credential,
)


def get_blob_client(blob_name: str):
    print("Container name:", os.getenv("AZURE_STORAGE_CONTAINER"))
    blob_client = blob_service_client.get_blob_client(container=os.getenv("AZURE_STORAGE_CONTAINER"), blob=blob_name)

    return blob_client


class SaveImageToRemote:
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
                "image": ("IMAGE", {"tooltip": "The image to save."}),
                "filename": (
                    "STRING",
                    {"tooltip": "The full path to save the file."},
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("URL",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "save_image"

    OUTPUT_NODE = True
    # OUTPUT_TOOLTIPS = ("",) # Tooltips for the output node

    CATEGORY = "image"

    def tensor_to_pil(self, image_tensor):
        """
        Convert a torch tensor back to a list of PIL images.

        Args:
            image_tensor (torch.Tensor): Float tensor in [0,1],
                                        shape (frames, H, W, 3) or (H, W, 3)

        Returns:
            list[PIL.Image.Image]: One or more PIL images (frames).
        """
        # Ensure 4D shape: (frames, H, W, 3)
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)

        frames = []
        for i in range(image_tensor.shape[0]):
            rgb = image_tensor[i].clamp(0, 1).numpy()  # (H, W, 3)
            rgb_uint8 = (rgb * 255).astype(np.uint8)
            frame = Image.fromarray(rgb_uint8, mode="RGB")
            frames.append(frame)

        return frames

    def save_image(self, image, filename):
        format = filename.split(".")[-1].lower()

        if format not in ["png"]:
            raise ValueError("SaveImageToRemote only supports PNG format.")

        frames = self.tensor_to_pil(image)

        file = BytesIO()
        frames[0].save(file, format=format)
        file.seek(0)

        # upload image to Azure storage
        try:
            blob_client = get_blob_client(filename)
            blob_client.upload_blob(file, overwrite=True)
        except Exception as e:
            print("Error uploading to Azure Blob Storage:", e)
            raise e

        return (
            f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{os.getenv('AZURE_STORAGE_CONTAINER')}/{filename}",
        )


class SaveVideoToRemote:
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
                "video": ("VIDEO", {"tooltip": "The video to save."}),
                "filename": (
                    "STRING",
                    {"tooltip": "The full path to save the file."},
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("URL",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "save_video"
    CATEGORY = "image/video"

    OUTPUT_NODE = True

    def save_video(self, video, filename):
        format = filename.split(".")[-1].lower()

        # Save to os temp folder
        output_path = f"/tmp/{filename}"

        # Use VideoFromFile.save_to from ComfyUI python backend.
        video.save_to(
            output_path,
            format=format,
            codec="h264",
        )

        file = open(output_path, "rb")

        # upload video to Azure storage
        try:
            blob_client = get_blob_client(filename)
            blob_client.upload_blob(file, overwrite=True)
        except Exception as e:
            print("Error uploading to Azure Blob Storage:", e)
            raise e
        finally:
            file.close()
            os.remove(output_path)

        return (
            f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{os.getenv('AZURE_STORAGE_CONTAINER')}/{filename}",
        )


class SaveAudioToRemote:
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
                "audio": ("AUDIO", {"tooltip": "The audio to save."}),
                "filename": ("STRING", {"tooltip": "The full path to save the file."}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("URL",)
    DESCRIPTION = cleandoc(__doc__)
    FUNCTION = "save_audio"
    CATEGORY = "audio"

    OUTPUT_NODE = True

    def save_audio(
        self,
        audio,
        filename,
        quality="128k",
    ):
        format = filename.split(".")[-1].lower()

        # Opus supported sample rates
        OPUS_RATES = [8000, 12000, 16000, 24000, 48000]

        # Only process 1 batch at a time for now
        batch_number = audio["waveform"].shape[0]
        if batch_number > 1:
            raise ValueError("SaveAudioToRemote only supports batch size of 1.")

        for batch_number, waveform in enumerate(audio["waveform"].cpu()):
            output_path = f"/tmp/{filename}"

            # Use original sample rate initially
            sample_rate = audio["sample_rate"]

            # Handle Opus sample rate requirements
            if format == "opus":
                if sample_rate > 48000:
                    sample_rate = 48000
                elif sample_rate not in OPUS_RATES:
                    # Find the next highest supported rate
                    for rate in sorted(OPUS_RATES):
                        if rate > sample_rate:
                            sample_rate = rate
                            break
                    if sample_rate not in OPUS_RATES:  # Fallback if still not supported
                        sample_rate = 48000

                # Resample if necessary
                if sample_rate != audio["sample_rate"]:
                    waveform = torchaudio.functional.resample(waveform, audio["sample_rate"], sample_rate)

            # Create output with specified format
            output_buffer = io.BytesIO()
            output_container = av.open(output_buffer, mode="w", format=format)

            # Set up the output stream with appropriate properties
            if format == "opus":
                out_stream = output_container.add_stream("libopus", rate=sample_rate)
                if quality == "64k":
                    out_stream.bit_rate = 64000
                elif quality == "96k":
                    out_stream.bit_rate = 96000
                elif quality == "128k":
                    out_stream.bit_rate = 128000
                elif quality == "192k":
                    out_stream.bit_rate = 192000
                elif quality == "320k":
                    out_stream.bit_rate = 320000
            elif format == "mp3":
                out_stream = output_container.add_stream("libmp3lame", rate=sample_rate)
                if quality == "V0":
                    # TODO i would really love to support V3 and V5 but there doesn't seem to be a way to set the qscale level, the property below is a bool
                    out_stream.codec_context.qscale = 1
                elif quality == "128k":
                    out_stream.bit_rate = 128000
                elif quality == "320k":
                    out_stream.bit_rate = 320000
            else:  # format == "flac":
                out_stream = output_container.add_stream("flac", rate=sample_rate)

            frame = av.AudioFrame.from_ndarray(
                waveform.movedim(0, 1).reshape(1, -1).float().numpy(),
                format="flt",
                layout="mono" if waveform.shape[0] == 1 else "stereo",
            )
            frame.sample_rate = sample_rate
            frame.pts = 0
            output_container.mux(out_stream.encode(frame))

            # Flush encoder
            output_container.mux(out_stream.encode(None))

            # Close containers
            output_container.close()

            # Write the output to file
            output_buffer.seek(0)
            with open(output_path, "wb") as f:
                f.write(output_buffer.getbuffer())

            file = open(output_path, "rb")
            # upload audio to Azure storage
            try:
                blob_client = get_blob_client(filename)
                blob_client.upload_blob(file, overwrite=True)
            except Exception as e:
                print("Error uploading to Azure Blob Storage:", e)
                raise e
            finally:
                file.close()
                os.remove(output_path)

        return (
            f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{os.getenv('AZURE_STORAGE_CONTAINER')}/{filename}",
        )
