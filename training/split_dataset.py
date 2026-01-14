"""
Split dataset into train and validation sets.

Usage:
    python split_dataset.py --input card_dataset/images/raw --ratio 0.8
"""

import os
import random
import shutil
import argparse
from pathlib import Path


def split_dataset(
    input_dir: str,
    output_dir: str = None,
    train_ratio: float = 0.8,
    seed: int = 42,
):
    """
    Split images into train and validation sets.
    
    Args:
        input_dir: Directory containing raw images
        output_dir: Output directory (default: parent of input_dir)
        train_ratio: Ratio of images for training (0-1)
        seed: Random seed for reproducibility
    """
    input_path = Path(input_dir)
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = input_path.parent
    
    # Create output directories
    train_dir = output_path / "train"
    val_dir = output_path / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all images
    extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    images = [f for f in input_path.iterdir() if f.suffix.lower() in extensions]
    
    if not images:
        print(f"No images found in {input_dir}")
        return
    
    print(f"Found {len(images)} images")
    
    # Shuffle and split
    random.seed(seed)
    random.shuffle(images)
    
    split_idx = int(len(images) * train_ratio)
    train_images = images[:split_idx]
    val_images = images[split_idx:]
    
    print(f"Train: {len(train_images)}, Val: {len(val_images)}")
    
    # Copy files
    for img in train_images:
        shutil.copy2(img, train_dir / img.name)
        
        # Also copy label if exists
        label_file = img.with_suffix(".txt")
        if label_file.exists():
            shutil.copy2(label_file, train_dir.parent.parent / "labels" / "train" / label_file.name)
    
    for img in val_images:
        shutil.copy2(img, val_dir / img.name)
        
        # Also copy label if exists
        label_file = img.with_suffix(".txt")
        if label_file.exists():
            shutil.copy2(label_file, val_dir.parent.parent / "labels" / "val" / label_file.name)
    
    print(f"\nDataset split complete!")
    print(f"  Train: {train_dir}")
    print(f"  Val: {val_dir}")


def main():
    parser = argparse.ArgumentParser(description="Split dataset into train/val")
    parser.add_argument("--input", "-i", required=True, help="Input directory with images")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--ratio", "-r", type=float, default=0.8, help="Train ratio")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    split_dataset(
        input_dir=args.input,
        output_dir=args.output,
        train_ratio=args.ratio,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
