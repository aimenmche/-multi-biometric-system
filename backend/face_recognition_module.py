import cv2
import numpy as np
import base64
import logging
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

face_cascade = None
embedding_model = None

try:
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    logger.info("OpenCV face detector loaded")
except Exception as e:
    logger.warning(f"Could not load face cascade: {e}")


def _load_image_from_base64(image_b64: str) -> np.ndarray:
    image_data = base64.b64decode(image_b64)
    np_arr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


def detect_face(image_b64: str) -> tuple:
    img = _load_image_from_base64(image_b64)
    if img is None:
        return False, "Invalid image data"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if face_cascade is not None:
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
    else:
        return False, "Face detector not initialized"

    if len(faces) == 0:
        return False, "No face detected in image"

    return True, faces


def generate_face_embedding(image_b64: str) -> tuple:
    try:
        from deepface import DeepFace
    except ImportError:
        return None, "DeepFace not installed. Run: pip install deepface"

    img = _load_image_from_base64(image_b64)
    if img is None:
        return None, "Invalid image data"

    try:
        embedding = DeepFace.represent(
            img_path=img,
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv",
            align=True,
        )
        if embedding and len(embedding) > 0:
            emb_vector = embedding[0]["embedding"]
            emb_str = ",".join(str(v) for v in emb_vector)
            return emb_str, None
        return None, "Could not generate embedding"
    except Exception as e:
        logger.error(f"DeepFace error: {e}")
        return None, f"Face recognition error: {str(e)}"


def compare_face_embeddings(embedding1_str: str, embedding2_str: str, threshold: float = 0.4) -> tuple:
    try:
        v1 = np.array([float(x) for x in embedding1_str.split(",")])
        v2 = np.array([float(x) for x in embedding2_str.split(",")])

        if v1.shape != v2.shape:
            return False, "Embedding dimension mismatch"

        similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        distance = 1 - similarity

        is_match = distance < threshold
        return is_match, float(distance)
    except Exception as e:
        logger.error(f"Embedding comparison error: {e}")
        return False, f"Comparison error: {str(e)}"
