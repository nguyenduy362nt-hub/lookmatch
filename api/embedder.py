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
        """image: PIL.Image -> vector float32 (512,)

        Lấy đặc trưng từ nhánh ảnh rồi chiếu sang không gian chung ảnh–văn bản.
        Cách này giống get_image_features nhưng không phụ thuộc kiểu trả về của từng phiên bản.
        """
        inputs = self.processor(images=image.convert("RGB"), return_tensors="pt")
        with self._torch.no_grad():
            pooled = self.model.vision_model(pixel_values=inputs["pixel_values"]).pooler_output
            feats = self.model.visual_projection(pooled)
        vec = feats.reshape(-1).numpy().astype(np.float32)  # ép về 1 chiều (512,)
        if vec.shape[0] != 512:
            raise ValueError(f"vector sai kích thước: {vec.shape}")
        return vec
