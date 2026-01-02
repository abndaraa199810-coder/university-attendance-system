
import os
import numpy as np
import cv2
import onnxruntime as ort

try:
    import mediapipe as mp  # type: ignore
except Exception:
    mp = None


_MP_BACKEND = None
_mp_detector = None


def _init_mediapipe_detector():
    
    global _MP_BACKEND, _mp_detector

    if mp is None:
        return None

    candidates = []

    try:
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_detection"):
            candidates.append(("mp.solutions", mp.solutions.face_detection))
    except Exception:
        pass

    try:
        from mediapipe.python.solutions import face_detection as fd  # type: ignore
        candidates.append(("mediapipe.python.solutions", fd))
    except Exception:
        pass

    if not candidates:
        return None

    backend_name, face_detection = candidates[0]
    _MP_BACKEND = backend_name

    _mp_detector = face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.3
    )

    def detect(rgb_image: np.ndarray):
        h, w = rgb_image.shape[:2]
        results = _mp_detector.process(rgb_image)
        if not results.detections:
            return None

        det = max(results.detections, key=lambda d: float(d.score[0]) if d.score else 0.0)
        box = det.location_data.relative_bounding_box

        x1 = int(max(0, box.xmin * w))
        y1 = int(max(0, box.ymin * h))
        x2 = int(min(w, (box.xmin + box.width) * w))
        y2 = int(min(h, (box.ymin + box.height) * h))

        # reject tiny crops
        if (x2 - x1) < 40 or (y2 - y1) < 40:
            return None

        return (x1, y1, x2, y2)

    return detect


_haar = None


def _init_haar():
    global _haar
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _haar = cv2.CascadeClassifier(cascade_path)
        if _haar.empty():
            _haar = None
    except Exception:
        _haar = None


def _detect_face_bbox_haar(rgb_image: np.ndarray):
 
    if _haar is None:
        return None

    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    faces = _haar.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )
    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (int(x), int(y), int(x + w), int(y + h))


_detect_face_bbox = _init_mediapipe_detector()
_init_haar()


def detect_single_face_bbox_rgb(rgb_image: np.ndarray, min_size: int = 60):

    bbox = None

    if _detect_face_bbox is not None:
        bbox = _detect_face_bbox(rgb_image)

    if bbox is None:
        bbox = _detect_face_bbox_haar(rgb_image)

    if bbox is not None:
        x1, y1, x2, y2 = bbox
        if (x2 - x1) < min_size or (y2 - y1) < min_size:
            bbox = None
        else:
            return bbox

    h, w = rgb_image.shape[:2]
    size = int(min(h, w) * 0.6)
    x1 = (w - size) // 2
    y1 = (h - size) // 2
    x2 = x1 + size
    y2 = y1 + size
    return (x1, y1, x2, y2)



def crop_and_preprocess_for_arcface(rgb_image: np.ndarray, bbox):
 
    x1, y1, x2, y2 = bbox
    face = rgb_image[y1:y2, x1:x2]
    if face.size == 0:
        raise ValueError("BAD_CROP")

    face = cv2.resize(face, (112, 112), interpolation=cv2.INTER_AREA).astype(np.float32)
    face = (face - 127.5) / 127.5
    face = np.transpose(face, (2, 0, 1))
    face = np.expand_dims(face, axis=0)
    return face


class ArcFaceONNX:
    def __init__(self, model_path: str, providers=None):
        if not model_path:
            raise ValueError("model_path is required")

        if not os.path.isabs(model_path):
            model_path = os.path.join(os.getcwd(), model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ArcFace ONNX model not found: {model_path}")

        if providers is None:
            providers = ["CPUExecutionProvider"]

        self.sess = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name

    def embed_from_rgb(self, rgb_image: np.ndarray) -> np.ndarray:
      
        bbox = detect_single_face_bbox_rgb(rgb_image)
        x = crop_and_preprocess_for_arcface(rgb_image, bbox)

        out = self.sess.run([self.output_name], {self.input_name: x})[0]
        emb = out[0].astype(np.float32)

        
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        return emb

    def detect_and_crop_face(self, rgb_image: np.ndarray):
      
        bbox = detect_single_face_bbox_rgb(rgb_image)
        x1, y1, x2, y2 = bbox
        face = rgb_image[y1:y2, x1:x2]
        if face.size == 0:
            return None
        return cv2.resize(face, (112, 112), interpolation=cv2.INTER_AREA)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))
