"""Biến ảnh thành vector. Mặc định CLIP ViT-B/32 (ADR-1); cần: pip install -r requirements-ml.txt"""
import numpy as np


class ClipEmbedder:
    MODEL = "openai/clip-vit-base-patch32"

    def __init__(self):
        import torch
        from transformers import CLIPModel, CLIPProcessor
        self._torch = torch
        self.model = CLIPModel.from_pretrained(self.MODEL).eval()
        self.processor = CLIPProcessor.from_pretrained(self.MODEL)

    def embed(self, image):
        """image: PIL.Image -> vector float32 (512,)"""
        inputs = self.processor(images=image.convert("RGB"), return_tensors="pt")
        with self._torch.no_grad():
            feats = self.model.get_image_features(**inputs)
        return feats[0].numpy().astype(np.float32)
