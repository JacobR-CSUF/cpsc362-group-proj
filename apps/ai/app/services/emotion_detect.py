# app/services/emotion_service.py

from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import torch
from io import BytesIO

MODEL_ID = "abhilash88/face-emotion-detection"

EMOTION_LABELS = {
    "LABEL_0": "angry",
    "LABEL_1": "disgust",
    "LABEL_2": "fear",
    "LABEL_3": "happy",
    "LABEL_4": "sad",
    "LABEL_5": "surprise",
    "LABEL_6": "neutral"
}

# --- load model once a time when starting application ---
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")

PROCESSOR = ViTImageProcessor.from_pretrained(MODEL_ID)
MODEL = ViTForImageClassification.from_pretrained(MODEL_ID).to(DEVICE)
MODEL.eval()


def predict_emotion_from_bytes(image_bytes: bytes):
    """
    Analyze emotion from FastAPI image bytes
    """
    # load image
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # preprocessing
    inputs = PROCESSOR(images=image, return_tensors="pt").to(DEVICE)

    # inference
    with torch.no_grad():
        outputs = MODEL(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

    # label for best score
    top_idx = int(probs.argmax())
    raw_label = MODEL.config.id2label[top_idx]
    human_label = EMOTION_LABELS.get(raw_label, raw_label)
    top_score = float(probs[top_idx])

    # mapping entire label score
    full_scores = {
        EMOTION_LABELS.get(MODEL.config.id2label[i], MODEL.config.id2label[i]): float(probs[i])
        for i in range(len(probs))
    }

    return human_label, top_score, full_scores
