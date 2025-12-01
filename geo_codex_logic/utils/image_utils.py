import base64
from qgis.core import QgsMessageLog, Qgis

def encode_image_to_base64(image_path: str) -> str:
    """
    Reads an image file and encodes it into a Base64 string.

    Args:
        image_path: The path to the image file.

    Returns:
        A Base64 encoded string of the image, or an error string.
    """
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex-ImageUtil', Qgis.Info)
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            log(f"Successfully encoded image at {image_path}")
            return encoded_string
    except Exception as e:
        log(f"Error encoding image: {e}")
        return f"Error: Could not read or encode image file: {e}"