import os
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import cv2
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import models

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Subtype mapping
subtype_mapping = {
    "adenosis": 0, "fibroadenoma": 1, "tubular_adenoma": 2, "phyllodes_tumor": 3,
    "ductal_carcinoma": 4, "lobular_carcinoma": 5, "mucinous_carcinoma": 6, "papillary_carcinoma": 7
}
idx_to_subtype = {v: k for k, v in subtype_mapping.items()}

# Image Transformations (No Normalization)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Load Trained Model
def load_model(model_path):
    model = models.resnet50(weights=None)  # Fixed deprecated warning
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(subtype_mapping))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

model_path = "/Users/trishajanath/MlModel/breast_cancer_cnn.pth"
model = load_model(model_path)
print("✅ Model Loaded Successfully!")
torch.manual_seed(42)


class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hook_handles = []

        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        self.hook_handles.append(self.target_layer.register_forward_hook(forward_hook))
        self.hook_handles.append(self.target_layer.register_full_backward_hook(backward_hook))

    def __call__(self, input_tensor, target_class):
        self.model.eval()
        self.model.zero_grad()

        output = self.model(input_tensor)
        loss = output[0, target_class]
        loss.backward()

        gradients = self.gradients.cpu().data.numpy()[0]
        activations = self.activations.cpu().data.numpy()[0]

        weights = np.mean(gradients, axis=(1, 2))
        cam = np.zeros(activations.shape[1:], dtype=np.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = np.maximum(cam, 0)
        cam = cv2.resize(cam, (input_tensor.size(2), input_tensor.size(3)))
        cam = cam - np.min(cam)
        cam = cam / np.max(cam)

        return cam

    def remove_hooks(self):
        for handle in self.hook_handles:
            handle.remove()

# ✅ Function to Predict Tumor Subtype and Generate Heatmap
def predict_subtype_with_heatmap(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        output = model(image_tensor)
        _, predicted_class = torch.max(output, 1)
        predicted_subtype = list(subtype_mapping.keys())[predicted_class.item()]
        probabilities = torch.nn.functional.softmax(output, dim=1)[0] * 100

    grad_cam = GradCAM(model, model.layer4[-1])
    heatmap = grad_cam(image_tensor, predicted_class.item())
    grad_cam.remove_hooks()

    heatmap = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    heatmap = np.float32(heatmap) / 255
    heatmap = heatmap + np.float32(image.resize((224, 224))) / 255
    heatmap = heatmap / np.max(heatmap)


    return predicted_subtype, probabilities[predicted_class.item()],heatmap


