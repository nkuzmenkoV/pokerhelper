"""
Automated Screenshot Collector for PokerOK

This script captures screenshots from PokerOK client at regular intervals
for building a training dataset for card detection.

Features:
- Automatic window detection
- Configurable capture interval
- Smart filtering (only saves when cards are visible)
- Organized folder structure
- Duplicate detection

Usage:
    python screenshot_collector.py --interval 2 --output ./card_dataset/images/train
"""

import os
import sys
import time
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import json

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install pyautogui opencv-python pillow")
    sys.exit(1)

# Try to import Windows-specific modules
try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    print("Warning: pygetwindow not available, using full screen capture")


class ScreenshotCollector:
    """Collects screenshots from PokerOK window."""
    
    # Keywords to identify PokerOK windows
    WINDOW_KEYWORDS = ["pokerok", "poker", "holdem", "nlh", "table"]
    
    # Color ranges for detecting poker table (green felt)
    TABLE_GREEN_LOW = np.array([35, 50, 50])
    TABLE_GREEN_HIGH = np.array([85, 255, 200])
    
    def __init__(
        self,
        output_dir: str,
        interval: float = 2.0,
        quality: int = 95,
        min_table_ratio: float = 0.15,
    ):
        """
        Initialize the collector.
        
        Args:
            output_dir: Directory to save screenshots
            interval: Capture interval in seconds
            quality: JPEG quality (0-100)
            min_table_ratio: Minimum ratio of green pixels to consider valid table
        """
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.quality = quality
        self.min_table_ratio = min_table_ratio
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track captured images to avoid duplicates
        self.captured_hashes = set()
        self.stats = {
            "total_captured": 0,
            "duplicates_skipped": 0,
            "invalid_skipped": 0,
            "start_time": None,
        }
        
        # Load existing hashes
        self._load_existing_hashes()
    
    def _load_existing_hashes(self):
        """Load hashes of existing images to avoid duplicates."""
        hash_file = self.output_dir / ".image_hashes.json"
        if hash_file.exists():
            try:
                with open(hash_file, "r") as f:
                    self.captured_hashes = set(json.load(f))
                print(f"Loaded {len(self.captured_hashes)} existing image hashes")
            except Exception as e:
                print(f"Warning: Could not load hash file: {e}")
    
    def _save_hashes(self):
        """Save image hashes to file."""
        hash_file = self.output_dir / ".image_hashes.json"
        try:
            with open(hash_file, "w") as f:
                json.dump(list(self.captured_hashes), f)
        except Exception as e:
            print(f"Warning: Could not save hash file: {e}")
    
    def find_poker_window(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Find PokerOK window and return its bounding box.
        
        Returns:
            Tuple of (left, top, width, height) or None if not found
        """
        if not HAS_PYGETWINDOW:
            return None
        
        try:
            windows = gw.getAllWindows()
            for window in windows:
                title = window.title.lower()
                if any(keyword in title for keyword in self.WINDOW_KEYWORDS):
                    if window.width > 400 and window.height > 300:  # Minimum size
                        return (window.left, window.top, window.width, window.height)
        except Exception as e:
            print(f"Error finding window: {e}")
        
        return None
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Capture screenshot of specified region or full screen.
        
        Args:
            region: (left, top, width, height) or None for full screen
            
        Returns:
            Screenshot as numpy array (BGR)
        """
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        # Convert PIL Image to numpy array (RGB -> BGR for OpenCV)
        img_array = np.array(screenshot)
        return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    def is_valid_poker_table(self, image: np.ndarray) -> bool:
        """
        Check if image contains a valid poker table.
        
        Uses color analysis to detect the green felt.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create mask for green table
        mask = cv2.inRange(hsv, self.TABLE_GREEN_LOW, self.TABLE_GREEN_HIGH)
        
        # Calculate ratio of green pixels
        green_ratio = np.sum(mask > 0) / mask.size
        
        return green_ratio >= self.min_table_ratio
    
    def compute_image_hash(self, image: np.ndarray) -> str:
        """
        Compute perceptual hash of image for duplicate detection.
        
        Uses a simplified average hash (aHash) approach.
        """
        # Resize to small size
        small = cv2.resize(image, (16, 16))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Compute average
        avg = gray.mean()
        
        # Create binary hash
        binary = (gray > avg).flatten()
        
        # Convert to hex string
        hash_int = sum(1 << i for i, b in enumerate(binary) if b)
        return hex(hash_int)[2:].zfill(64)
    
    def is_duplicate(self, image: np.ndarray) -> bool:
        """Check if image is a duplicate of previously captured."""
        img_hash = self.compute_image_hash(image)
        
        if img_hash in self.captured_hashes:
            return True
        
        self.captured_hashes.add(img_hash)
        return False
    
    def save_screenshot(self, image: np.ndarray) -> str:
        """
        Save screenshot to output directory.
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.jpg"
        filepath = self.output_dir / filename
        
        # Save with quality setting
        cv2.imwrite(
            str(filepath),
            image,
            [cv2.IMWRITE_JPEG_QUALITY, self.quality]
        )
        
        return str(filepath)
    
    def capture_once(self) -> Optional[str]:
        """
        Capture a single screenshot if valid.
        
        Returns:
            Path to saved file or None if skipped
        """
        # Find poker window
        region = self.find_poker_window()
        
        # Capture screen
        image = self.capture_screen(region)
        
        # Validate
        if not self.is_valid_poker_table(image):
            self.stats["invalid_skipped"] += 1
            return None
        
        # Check for duplicates
        if self.is_duplicate(image):
            self.stats["duplicates_skipped"] += 1
            return None
        
        # Save
        filepath = self.save_screenshot(image)
        self.stats["total_captured"] += 1
        
        return filepath
    
    def run(self, duration: Optional[float] = None, max_images: Optional[int] = None):
        """
        Run the collector continuously.
        
        Args:
            duration: Maximum duration in seconds (None for unlimited)
            max_images: Maximum number of images to capture (None for unlimited)
        """
        self.stats["start_time"] = time.time()
        
        print(f"Starting screenshot collector")
        print(f"  Output: {self.output_dir}")
        print(f"  Interval: {self.interval}s")
        print(f"  Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                # Check limits
                if duration and (time.time() - self.stats["start_time"]) >= duration:
                    print(f"\nDuration limit ({duration}s) reached")
                    break
                
                if max_images and self.stats["total_captured"] >= max_images:
                    print(f"\nImage limit ({max_images}) reached")
                    break
                
                # Capture
                result = self.capture_once()
                
                if result:
                    print(f"✓ Captured: {Path(result).name} "
                          f"(total: {self.stats['total_captured']})")
                else:
                    status = "duplicate" if self.stats["duplicates_skipped"] > 0 else "no table"
                    print(f"○ Skipped ({status})", end="\r")
                
                # Wait for next capture
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        
        finally:
            self._save_hashes()
            self._print_stats()
    
    def _print_stats(self):
        """Print collection statistics."""
        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        print("\n" + "=" * 40)
        print("Collection Statistics:")
        print(f"  Total captured: {self.stats['total_captured']}")
        print(f"  Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"  Invalid skipped: {self.stats['invalid_skipped']}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Rate: {self.stats['total_captured'] / max(elapsed, 1) * 60:.1f} images/min")
        print("=" * 40)


class CardRegionExtractor:
    """Extracts card regions from full table screenshots."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Approximate card regions (will be refined based on actual screenshots)
        # Format: (x_ratio, y_ratio, width_ratio, height_ratio)
        self.card_regions = {
            "hero_left": (0.42, 0.65, 0.06, 0.12),
            "hero_right": (0.48, 0.65, 0.06, 0.12),
            "board_1": (0.32, 0.36, 0.05, 0.10),
            "board_2": (0.38, 0.36, 0.05, 0.10),
            "board_3": (0.44, 0.36, 0.05, 0.10),
            "board_4": (0.50, 0.36, 0.05, 0.10),
            "board_5": (0.56, 0.36, 0.05, 0.10),
        }
    
    def extract_cards(self, image: np.ndarray, prefix: str = "") -> list:
        """
        Extract card regions from a table screenshot.
        
        Returns list of saved file paths.
        """
        h, w = image.shape[:2]
        saved = []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for region_name, (x_r, y_r, w_r, h_r) in self.card_regions.items():
            x = int(x_r * w)
            y = int(y_r * h)
            rw = int(w_r * w)
            rh = int(h_r * h)
            
            # Extract region
            card_img = image[y:y+rh, x:x+rw]
            
            # Skip if too small or empty
            if card_img.size < 100:
                continue
            
            # Save
            filename = f"{prefix}{timestamp}_{region_name}.jpg"
            filepath = self.output_dir / filename
            cv2.imwrite(str(filepath), card_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved.append(str(filepath))
        
        return saved


def main():
    parser = argparse.ArgumentParser(
        description="Collect screenshots from PokerOK for training dataset"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./card_dataset/images/raw",
        help="Output directory for screenshots"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=2.0,
        help="Capture interval in seconds"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="Maximum duration in seconds"
    )
    parser.add_argument(
        "--max-images", "-n",
        type=int,
        default=None,
        help="Maximum number of images to capture"
    )
    parser.add_argument(
        "--quality", "-q",
        type=int,
        default=95,
        help="JPEG quality (0-100)"
    )
    parser.add_argument(
        "--extract-cards",
        action="store_true",
        help="Also extract card regions from screenshots"
    )
    
    args = parser.parse_args()
    
    # Create collector
    collector = ScreenshotCollector(
        output_dir=args.output,
        interval=args.interval,
        quality=args.quality,
    )
    
    # Run
    collector.run(
        duration=args.duration,
        max_images=args.max_images,
    )


if __name__ == "__main__":
    main()
