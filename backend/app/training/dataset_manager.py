"""
Dataset Manager for card detection training.

Handles:
- Image storage and organization
- Label management (YOLO format)
- Dataset statistics
- Train/val splitting
- Export functionality
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
import base64

import cv2
import numpy as np


# Card classes (52 cards)
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['c', 'd', 'h', 's']  # clubs, diamonds, hearts, spades
CARD_CLASSES = [f"{r}{s}" for s in SUITS for r in RANKS]
CLASS_TO_ID = {card: idx for idx, card in enumerate(CARD_CLASSES)}
ID_TO_CLASS = {idx: card for card, idx in CLASS_TO_ID.items()}


@dataclass
class BoundingBox:
    """Bounding box in normalized coordinates (0-1)."""
    x_center: float
    y_center: float
    width: float
    height: float
    class_id: int
    class_name: str = ""
    confidence: float = 1.0
    
    def to_yolo(self) -> str:
        """Convert to YOLO format string."""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"
    
    @classmethod
    def from_yolo(cls, line: str) -> 'BoundingBox':
        """Parse from YOLO format string."""
        parts = line.strip().split()
        class_id = int(parts[0])
        return cls(
            class_id=class_id,
            class_name=ID_TO_CLASS.get(class_id, ""),
            x_center=float(parts[1]),
            y_center=float(parts[2]),
            width=float(parts[3]),
            height=float(parts[4]),
        )
    
    def to_pixel(self, img_width: int, img_height: int) -> tuple[int, int, int, int]:
        """Convert to pixel coordinates (x1, y1, x2, y2)."""
        w = self.width * img_width
        h = self.height * img_height
        x1 = int((self.x_center * img_width) - w / 2)
        y1 = int((self.y_center * img_height) - h / 2)
        x2 = int(x1 + w)
        y2 = int(y1 + h)
        return (x1, y1, x2, y2)


@dataclass
class LabeledImage:
    """A labeled training image."""
    image_id: str
    filename: str
    width: int
    height: int
    boxes: list[BoundingBox] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "image_id": self.image_id,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "boxes": [
                {
                    "class_id": b.class_id,
                    "class_name": b.class_name,
                    "x_center": b.x_center,
                    "y_center": b.y_center,
                    "width": b.width,
                    "height": b.height,
                }
                for b in self.boxes
            ],
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DatasetStats:
    """Statistics about the dataset."""
    total_images: int = 0
    total_boxes: int = 0
    cards_count: dict = field(default_factory=dict)  # card_name -> count
    
    def to_dict(self) -> dict:
        return {
            "total_images": self.total_images,
            "total_boxes": self.total_boxes,
            "cards_count": self.cards_count,
            "coverage": self._calculate_coverage(),
            "missing_cards": self._get_missing_cards(),
            "balanced": self._is_balanced(),
        }
    
    def _calculate_coverage(self) -> float:
        """Calculate what percentage of cards have at least 1 sample."""
        if not CARD_CLASSES:
            return 0.0
        covered = sum(1 for card in CARD_CLASSES if self.cards_count.get(card, 0) > 0)
        return (covered / len(CARD_CLASSES)) * 100
    
    def _get_missing_cards(self) -> list[str]:
        """Get list of cards with no samples."""
        return [card for card in CARD_CLASSES if self.cards_count.get(card, 0) == 0]
    
    def _is_balanced(self, threshold: float = 0.5) -> bool:
        """Check if dataset is balanced (no card has less than threshold * avg)."""
        if not self.cards_count:
            return False
        counts = list(self.cards_count.values())
        if not counts:
            return False
        avg = sum(counts) / len(counts)
        return all(c >= avg * threshold for c in counts)


class DatasetManager:
    """
    Manages the training dataset for card detection.
    """
    
    def __init__(self, base_path: str = "data/training_dataset"):
        self.base_path = Path(base_path)
        self.images_path = self.base_path / "images"
        self.labels_path = self.base_path / "labels"
        self.metadata_path = self.base_path / "metadata.json"
        
        # Create directories
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.labels_path.mkdir(parents=True, exist_ok=True)
        
        # Load metadata
        self.metadata: dict = self._load_metadata()
        self.stats = self._calculate_stats()
    
    def _load_metadata(self) -> dict:
        """Load dataset metadata from file."""
        if self.metadata_path.exists():
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {
            "images": {},
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
        }
    
    def _save_metadata(self):
        """Save metadata to file."""
        self.metadata["updated_at"] = datetime.now().isoformat()
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    def _calculate_stats(self) -> DatasetStats:
        """Calculate dataset statistics."""
        stats = DatasetStats()
        stats.cards_count = {card: 0 for card in CARD_CLASSES}
        
        for image_id, image_data in self.metadata.get("images", {}).items():
            stats.total_images += 1
            for box in image_data.get("boxes", []):
                stats.total_boxes += 1
                card_name = box.get("class_name", "")
                if card_name in stats.cards_count:
                    stats.cards_count[card_name] += 1
        
        return stats
    
    def _generate_image_id(self, image_data: bytes) -> str:
        """Generate unique image ID based on content hash."""
        return hashlib.md5(image_data).hexdigest()[:12]
    
    def save_image(
        self,
        image_data: str,  # Base64 encoded
        boxes: list[dict],
        source: str = "browser",
    ) -> LabeledImage:
        """
        Save a labeled image to the dataset.
        
        Args:
            image_data: Base64 encoded JPEG image
            boxes: List of bounding boxes with class_id and coordinates
            source: Source of the image (browser, screenshot, etc.)
        
        Returns:
            LabeledImage object
        """
        # Decode image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image")
        
        height, width = img.shape[:2]
        
        # Generate image ID
        image_id = self._generate_image_id(img_bytes)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image_id}.jpg"
        
        # Save image
        image_path = self.images_path / filename
        cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Create bounding boxes
        bbox_list = []
        for box in boxes:
            bbox = BoundingBox(
                class_id=box["class_id"],
                class_name=ID_TO_CLASS.get(box["class_id"], ""),
                x_center=box["x_center"],
                y_center=box["y_center"],
                width=box["width"],
                height=box["height"],
            )
            bbox_list.append(bbox)
        
        # Save YOLO label file
        label_filename = filename.replace(".jpg", ".txt")
        label_path = self.labels_path / label_filename
        with open(label_path, "w") as f:
            for bbox in bbox_list:
                f.write(bbox.to_yolo() + "\n")
        
        # Create labeled image object
        labeled_image = LabeledImage(
            image_id=image_id,
            filename=filename,
            width=width,
            height=height,
            boxes=bbox_list,
        )
        
        # Update metadata
        self.metadata["images"][image_id] = labeled_image.to_dict()
        self._save_metadata()
        
        # Update stats
        self.stats = self._calculate_stats()
        
        return labeled_image
    
    def add_label(self, image_id: str, box: dict) -> bool:
        """
        Add a single label to an existing image.
        
        Args:
            image_id: ID of the image
            box: Bounding box data
        
        Returns:
            True if successful
        """
        if image_id not in self.metadata["images"]:
            return False
        
        image_data = self.metadata["images"][image_id]
        
        # Add box to metadata
        bbox = BoundingBox(
            class_id=box["class_id"],
            class_name=ID_TO_CLASS.get(box["class_id"], ""),
            x_center=box["x_center"],
            y_center=box["y_center"],
            width=box["width"],
            height=box["height"],
        )
        
        image_data["boxes"].append({
            "class_id": bbox.class_id,
            "class_name": bbox.class_name,
            "x_center": bbox.x_center,
            "y_center": bbox.y_center,
            "width": bbox.width,
            "height": bbox.height,
        })
        
        # Update label file
        filename = image_data["filename"]
        label_filename = filename.replace(".jpg", ".txt")
        label_path = self.labels_path / label_filename
        with open(label_path, "a") as f:
            f.write(bbox.to_yolo() + "\n")
        
        self._save_metadata()
        self.stats = self._calculate_stats()
        
        return True
    
    def get_image(self, image_id: str) -> Optional[dict]:
        """Get image data by ID."""
        return self.metadata["images"].get(image_id)
    
    def get_stats(self) -> dict:
        """Get dataset statistics."""
        return self.stats.to_dict()
    
    def get_card_counts(self) -> dict:
        """Get count of samples for each card."""
        return self.stats.cards_count
    
    def get_images_list(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get list of images with pagination."""
        images = list(self.metadata["images"].values())
        return images[offset:offset + limit]
    
    def delete_image(self, image_id: str) -> bool:
        """Delete an image from the dataset."""
        if image_id not in self.metadata["images"]:
            return False
        
        image_data = self.metadata["images"][image_id]
        filename = image_data["filename"]
        
        # Delete files
        image_path = self.images_path / filename
        label_path = self.labels_path / filename.replace(".jpg", ".txt")
        
        if image_path.exists():
            image_path.unlink()
        if label_path.exists():
            label_path.unlink()
        
        # Remove from metadata
        del self.metadata["images"][image_id]
        self._save_metadata()
        self.stats = self._calculate_stats()
        
        return True
    
    def export_yolo_dataset(self, output_path: str, train_ratio: float = 0.8) -> dict:
        """
        Export dataset in YOLO format for training.
        
        Args:
            output_path: Path to export to
            train_ratio: Ratio of images for training (rest for validation)
        
        Returns:
            Export statistics
        """
        import random
        
        output = Path(output_path)
        
        # Create directories
        (output / "images" / "train").mkdir(parents=True, exist_ok=True)
        (output / "images" / "val").mkdir(parents=True, exist_ok=True)
        (output / "labels" / "train").mkdir(parents=True, exist_ok=True)
        (output / "labels" / "val").mkdir(parents=True, exist_ok=True)
        
        # Get all images
        images = list(self.metadata["images"].values())
        random.shuffle(images)
        
        split_idx = int(len(images) * train_ratio)
        train_images = images[:split_idx]
        val_images = images[split_idx:]
        
        # Copy files
        for img_data in train_images:
            self._copy_image_files(img_data, output, "train")
        
        for img_data in val_images:
            self._copy_image_files(img_data, output, "val")
        
        # Create dataset.yaml
        yaml_content = f"""# Card Detection Dataset
path: {output.absolute()}
train: images/train
val: images/val

nc: {len(CARD_CLASSES)}
names: {CARD_CLASSES}
"""
        with open(output / "dataset.yaml", "w") as f:
            f.write(yaml_content)
        
        # Create classes.txt
        with open(output / "classes.txt", "w") as f:
            f.write("\n".join(CARD_CLASSES))
        
        return {
            "total": len(images),
            "train": len(train_images),
            "val": len(val_images),
            "output_path": str(output),
        }
    
    def _copy_image_files(self, img_data: dict, output: Path, split: str):
        """Copy image and label files to export directory."""
        filename = img_data["filename"]
        
        src_image = self.images_path / filename
        src_label = self.labels_path / filename.replace(".jpg", ".txt")
        
        dst_image = output / "images" / split / filename
        dst_label = output / "labels" / split / filename.replace(".jpg", ".txt")
        
        if src_image.exists():
            shutil.copy2(src_image, dst_image)
        if src_label.exists():
            shutil.copy2(src_label, dst_label)
    
    def clear_dataset(self) -> bool:
        """Clear all data from the dataset."""
        # Remove all images and labels
        for f in self.images_path.glob("*"):
            f.unlink()
        for f in self.labels_path.glob("*"):
            f.unlink()
        
        # Reset metadata
        self.metadata = {
            "images": {},
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
        }
        self._save_metadata()
        self.stats = self._calculate_stats()
        
        return True
