"""
API routes for model training and dataset management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio

from app.training.dataset_manager import DatasetManager, CARD_CLASSES, CLASS_TO_ID
from app.training.trainer import ModelTrainer, TrainingConfig
from app.training.auto_detector import CardAutoDetector, PokerOKLayout, POKEROK_PRESETS

router = APIRouter()

# Global instances
dataset_manager = DatasetManager(base_path="data/training_dataset")
trainer = ModelTrainer(models_dir="models", dataset_path="data/training_dataset")
auto_detector = CardAutoDetector(
    model_path="models/cards_yolo.pt",
    config_path="data/detector_config.json"
)


# ============ Request/Response Models ============

class BoundingBoxInput(BaseModel):
    """Bounding box input."""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


class SaveImageRequest(BaseModel):
    """Request to save a labeled image."""
    image_data: str  # Base64 encoded
    boxes: list[BoundingBoxInput]
    source: str = "browser"


class AddLabelRequest(BaseModel):
    """Request to add a label to existing image."""
    image_id: str
    box: BoundingBoxInput


class DetectRequest(BaseModel):
    """Request to detect card regions."""
    image_data: str  # Base64 encoded
    use_model: bool = True
    use_heuristics: bool = True
    use_positions: bool = True


class PositionUpdate(BaseModel):
    """Update a card position."""
    region_type: str  # "hero" or "board"
    index: int
    x: float
    y: float
    width: float
    height: float


class LayoutUpdate(BaseModel):
    """Full layout update."""
    name: str = "custom"
    hero_cards: list[dict]
    board_cards: list[dict]


class TrainingConfigRequest(BaseModel):
    """Training configuration request."""
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    model_size: str = "n"
    device: str = "cpu"


class ExportRequest(BaseModel):
    """Dataset export request."""
    output_path: str = "data/export"
    train_ratio: float = 0.8


# ============ Dataset Routes ============

@router.get("/training/cards")
async def get_card_classes():
    """Get list of all card classes."""
    return {
        "classes": CARD_CLASSES,
        "class_to_id": CLASS_TO_ID,
        "total": len(CARD_CLASSES),
    }


@router.get("/training/dataset/stats")
async def get_dataset_stats():
    """Get dataset statistics."""
    return dataset_manager.get_stats()


@router.get("/training/dataset/images")
async def get_dataset_images(limit: int = 100, offset: int = 0):
    """Get list of images in dataset."""
    images = dataset_manager.get_images_list(limit=limit, offset=offset)
    return {
        "images": images,
        "total": len(dataset_manager.metadata.get("images", {})),
        "limit": limit,
        "offset": offset,
    }


@router.get("/training/dataset/image/{image_id}")
async def get_image(image_id: str):
    """Get image data by ID."""
    image = dataset_manager.get_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.post("/training/dataset/save")
async def save_labeled_image(request: SaveImageRequest):
    """Save a labeled image to the dataset."""
    try:
        boxes = [box.model_dump() for box in request.boxes]
        labeled_image = dataset_manager.save_image(
            image_data=request.image_data,
            boxes=boxes,
            source=request.source,
        )
        return {
            "status": "saved",
            "image_id": labeled_image.image_id,
            "filename": labeled_image.filename,
            "boxes_count": len(labeled_image.boxes),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/training/dataset/label")
async def add_label(request: AddLabelRequest):
    """Add a label to an existing image."""
    success = dataset_manager.add_label(
        image_id=request.image_id,
        box=request.box.model_dump(),
    )
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "added"}


@router.delete("/training/dataset/image/{image_id}")
async def delete_image(image_id: str):
    """Delete an image from the dataset."""
    success = dataset_manager.delete_image(image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "deleted"}


@router.post("/training/dataset/export")
async def export_dataset(request: ExportRequest):
    """Export dataset in YOLO format."""
    try:
        result = dataset_manager.export_yolo_dataset(
            output_path=request.output_path,
            train_ratio=request.train_ratio,
        )
        return {
            "status": "exported",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/training/dataset/clear")
async def clear_dataset():
    """Clear all data from dataset."""
    dataset_manager.clear_dataset()
    return {"status": "cleared"}


# ============ Auto-Detection Routes ============

@router.post("/training/detect")
async def detect_cards(request: DetectRequest):
    """Detect card regions in image."""
    try:
        regions = auto_detector.detect_regions(
            image_data=request.image_data,
            use_model=request.use_model,
            use_heuristics=request.use_heuristics,
            use_positions=request.use_positions,
        )
        return {
            "regions": regions,
            "count": len(regions),
            "model_available": auto_detector.model is not None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Layout/Calibration Routes ============

@router.get("/training/layout")
async def get_layout():
    """Get current card position layout."""
    return auto_detector.get_current_layout()


@router.post("/training/layout")
async def update_layout(request: LayoutUpdate):
    """Update full layout configuration."""
    try:
        layout = PokerOKLayout.from_dict(request.model_dump())
        auto_detector.set_layout(layout)
        return {"status": "updated", "layout": auto_detector.get_current_layout()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/training/layout/position")
async def update_position(request: PositionUpdate):
    """Update a single card position."""
    auto_detector.update_position(
        region_type=request.region_type,
        index=request.index,
        x=request.x,
        y=request.y,
        width=request.width,
        height=request.height,
    )
    return {"status": "updated", "layout": auto_detector.get_current_layout()}


@router.get("/training/layout/presets")
async def get_presets():
    """Get available layout presets."""
    presets = {}
    for name, layout in POKEROK_PRESETS.items():
        presets[name] = layout.to_dict()
    return {"presets": presets}


@router.post("/training/layout/preset/{preset_name}")
async def apply_preset(preset_name: str):
    """Apply a layout preset."""
    if auto_detector.set_preset(preset_name):
        return {"status": "applied", "layout": auto_detector.get_current_layout()}
    raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")


@router.post("/training/detect/reload-model")
async def reload_detection_model(model_path: str = "models/cards_yolo.pt"):
    """Reload the detection model."""
    auto_detector.reload_model(model_path)
    return {
        "status": "reloaded",
        "model_available": auto_detector.model is not None,
    }


# ============ Training Routes ============

@router.get("/training/config")
async def get_training_config():
    """Get current training configuration."""
    return trainer.get_config()


@router.post("/training/config")
async def set_training_config(request: TrainingConfigRequest):
    """Update training configuration."""
    trainer.set_config(**request.model_dump())
    return {"status": "updated", "config": trainer.get_config()}


@router.get("/training/status")
async def get_training_status():
    """Get current training status and progress."""
    return trainer.get_progress()


@router.post("/training/start")
async def start_training(background_tasks: BackgroundTasks):
    """Start model training."""
    # First export dataset
    export_result = dataset_manager.export_yolo_dataset(
        output_path="data/export",
        train_ratio=0.8,
    )
    
    if export_result["total"] < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough data. Need at least 10 images, have {export_result['total']}"
        )
    
    dataset_yaml = "data/export/dataset.yaml"
    
    # Start training
    success = trainer.start_training(dataset_yaml=dataset_yaml)
    
    if not success:
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    return {
        "status": "started",
        "dataset": export_result,
    }


@router.post("/training/cancel")
async def cancel_training():
    """Cancel ongoing training."""
    success = trainer.cancel_training()
    if not success:
        raise HTTPException(status_code=400, detail="No training in progress")
    return {"status": "cancelled"}


@router.get("/training/models")
async def get_available_models():
    """Get list of available trained models."""
    return {
        "models": trainer.get_available_models(),
    }


@router.get("/training/history")
async def get_training_history():
    """Get training history."""
    return {
        "history": trainer.get_training_history(),
    }


@router.post("/training/validate")
async def validate_model(model_path: Optional[str] = None):
    """Validate model on dataset."""
    # Export dataset first
    export_result = dataset_manager.export_yolo_dataset(
        output_path="data/validation",
        train_ratio=0.8,
    )
    
    result = trainer.validate_model(
        model_path=model_path,
        dataset_yaml="data/validation/dataset.yaml" if export_result["total"] > 0 else None,
    )
    
    return result
