import cv2
import numpy as np
import base64
import logging
import traceback

logger = logging.getLogger(__name__)

USE_DEEPFACE = False
try:
    from deepface import DeepFace
    USE_DEEPFACE = True
    logger.info("DeepFace available - using Facenet embeddings")
except ImportError:
    logger.info("DeepFace not installed - using OpenCV fallback (less accurate)")

face_cascade = None
try:
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if face_cascade.empty():
        face_cascade = None
        logger.warning("Haar cascade file not found")
    else:
        logger.info("OpenCV face detector loaded")
except Exception as e:
    logger.warning(f"Could not load face cascade: {e}")


def _load_image_from_base64(image_b64: str) -> np.ndarray:
    try:
        image_data = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        return None


def detect_face(image_b64: str) -> tuple:
    img = _load_image_from_base64(image_b64)
    if img is None:
        return False, "Invalid image data"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    if face_cascade is not None:
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
    else:
        return False, "Face detector not initialized (missing cascade file)"

    if len(faces) == 0:
        return False, "No face detected in image"

    return True, faces


def _extract_face_region(image_b64: str) -> np.ndarray:
    img = _load_image_from_base64(image_b64)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    if face_cascade is None:
        return None

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
    )
    if len(faces) == 0:
        return None

    (x, y, w, h) = faces[0]
    face_roi = gray[y : y + h, x : x + w]
    face_resized = cv2.resize(face_roi, (100, 100), interpolation=cv2.INTER_AREA)
    return face_resized


def _generate_fallback_embedding(image_b64: str) -> tuple:
    face = _extract_face_region(image_b64)
    if face is None:
        return None, "Could not extract face region"

    face_blur = cv2.GaussianBlur(face, (3, 3), 0)
    face_norm = face_blur.astype(np.float32) / 255.0
    embedding = face_norm.flatten()
    embedding_str = ",".join(f"{v:.6f}" for v in embedding)
    return embedding_str, None


def generate_face_embedding(image_b64: str) -> tuple:
    if USE_DEEPFACE:
        try:
            img = _load_image_from_base64(image_b64)
            if img is None:
                return None, "Invalid image data"

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
            logger.warning(f"DeepFace failed, falling back: {e}")
            return _generate_fallback_embedding(image_b64)
    else:
        return _generate_fallback_embedding(image_b64)


def compare_face_embeddings(embedding1_str: str, embedding2_str: str, threshold: float = 0.4) -> tuple:
    try:
        v1 = np.array([float(x) for x in embedding1_str.split(",")])
        v2 = np.array([float(x) for x in embedding2_str.split(",")])

        if v1.shape != v2.shape:
            return False, "Embedding dimension mismatch"

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return False, "Zero embedding vector"

        similarity = np.dot(v1, v2) / (norm1 * norm2)
        distance = 1 - similarity

        is_match = distance < threshold
        return is_match, float(distance)
    except Exception as e:
        logger.error(f"Embedding comparison error: {e}")
        return False, f"Comparison error: {str(e)}"
