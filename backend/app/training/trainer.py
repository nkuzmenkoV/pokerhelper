"""
YOLO Model Trainer for card detection.

Handles:
- Training job management
- Progress tracking
- Model versioning
- Incremental training
"""

import os
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import json


class TrainingStatus(Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingProgress:
    """Training progress information."""
    status: TrainingStatus = TrainingStatus.IDLE
    current_epoch: int = 0
    total_epochs: int = 0
    current_loss: float = 0.0
    best_loss: float = float('inf')
    metrics: dict = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""
    model_path: str = ""
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "progress_pct": (self.current_epoch / self.total_epochs * 100) if self.total_epochs > 0 else 0,
            "current_loss": self.current_loss,
            "best_loss": self.best_loss if self.best_loss != float('inf') else None,
            "metrics": self.metrics,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "model_path": self.model_path,
        }


@dataclass
class TrainingConfig:
    """Training configuration."""
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    model_size: str = "n"  # n, s, m, l, x
    device: str = "cpu"  # cpu or cuda device
    patience: int = 20
    
    # Incremental training settings
    incremental_enabled: bool = True
    incremental_threshold: int = 100  # Min new samples to trigger retraining
    
    def to_dict(self) -> dict:
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "img_size": self.img_size,
            "model_size": self.model_size,
            "device": self.device,
            "patience": self.patience,
            "incremental_enabled": self.incremental_enabled,
            "incremental_threshold": self.incremental_threshold,
        }


class ModelTrainer:
    """
    Manages YOLO model training for card detection.
    """
    
    def __init__(
        self,
        models_dir: str = "models",
        dataset_path: str = "data/training_dataset",
    ):
        self.models_dir = Path(models_dir)
        self.dataset_path = Path(dataset_path)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress = TrainingProgress()
        self.config = TrainingConfig()
        self._training_thread: Optional[threading.Thread] = None
        self._cancel_flag = False
        
        # Callbacks
        self._on_progress: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None
        
        # Training history
        self.history_path = self.models_dir / "training_history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """Load training history."""
        if self.history_path.exists():
            with open(self.history_path, "r") as f:
                return json.load(f)
        return []
    
    def _save_history(self, entry: dict):
        """Save training history entry."""
        self.history.append(entry)
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2)
    
    def set_config(self, **kwargs):
        """Update training configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_config(self) -> dict:
        """Get current configuration."""
        return self.config.to_dict()
    
    def get_progress(self) -> dict:
        """Get current training progress."""
        return self.progress.to_dict()
    
    def is_training(self) -> bool:
        """Check if training is in progress."""
        return self.progress.status == TrainingStatus.TRAINING
    
    def start_training(
        self,
        dataset_yaml: str,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
    ) -> bool:
        """
        Start training in a background thread.
        
        Args:
            dataset_yaml: Path to dataset.yaml file
            on_progress: Callback for progress updates
            on_complete: Callback when training completes
        
        Returns:
            True if training started successfully
        """
        if self.is_training():
            return False
        
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._cancel_flag = False
        
        # Reset progress
        self.progress = TrainingProgress(
            status=TrainingStatus.PREPARING,
            total_epochs=self.config.epochs,
            started_at=datetime.now(),
        )
        
        # Start training thread
        self._training_thread = threading.Thread(
            target=self._training_worker,
            args=(dataset_yaml,),
            daemon=True,
        )
        self._training_thread.start()
        
        return True
    
    def cancel_training(self) -> bool:
        """Cancel ongoing training."""
        if not self.is_training():
            return False
        
        self._cancel_flag = True
        self.progress.status = TrainingStatus.CANCELLED
        return True
    
    def _training_worker(self, dataset_yaml: str):
        """Background training worker."""
        try:
            self.progress.status = TrainingStatus.TRAINING
            
            # Import YOLO
            try:
                from ultralytics import YOLO
            except ImportError:
                raise RuntimeError("ultralytics not installed")
            
            # Load or create model
            model_name = f"yolov8{self.config.model_size}.pt"
            model = YOLO(model_name)
            
            # Custom callback for progress
            def on_train_epoch_end(trainer):
                if self._cancel_flag:
                    raise KeyboardInterrupt("Training cancelled")
                
                self.progress.current_epoch = trainer.epoch + 1
                self.progress.current_loss = float(trainer.loss)
                
                if trainer.loss < self.progress.best_loss:
                    self.progress.best_loss = float(trainer.loss)
                
                # Update metrics
                if hasattr(trainer, 'metrics'):
                    self.progress.metrics = {
                        k: float(v) for k, v in trainer.metrics.items()
                        if isinstance(v, (int, float))
                    }
                
                if self._on_progress:
                    self._on_progress(self.progress.to_dict())
            
            # Add callback
            model.add_callback("on_train_epoch_end", on_train_epoch_end)
            
            # Generate output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"cards_{timestamp}"
            
            # Train
            results = model.train(
                data=dataset_yaml,
                epochs=self.config.epochs,
                batch=self.config.batch_size,
                imgsz=self.config.img_size,
                project=str(self.models_dir),
                name=output_name,
                patience=self.config.patience,
                device=self.config.device,
                verbose=False,
            )
            
            # Training completed
            self.progress.status = TrainingStatus.COMPLETED
            self.progress.completed_at = datetime.now()
            
            # Get best model path
            best_model = self.models_dir / output_name / "weights" / "best.pt"
            self.progress.model_path = str(best_model)
            
            # Copy best model to main models directory
            if best_model.exists():
                import shutil
                dest = self.models_dir / "cards_yolo.pt"
                shutil.copy2(best_model, dest)
                self.progress.model_path = str(dest)
            
            # Save to history
            self._save_history({
                "timestamp": timestamp,
                "epochs": self.config.epochs,
                "best_loss": self.progress.best_loss,
                "metrics": self.progress.metrics,
                "model_path": self.progress.model_path,
            })
            
            if self._on_complete:
                self._on_complete(self.progress.to_dict())
        
        except KeyboardInterrupt:
            self.progress.status = TrainingStatus.CANCELLED
            self.progress.completed_at = datetime.now()
        
        except Exception as e:
            self.progress.status = TrainingStatus.FAILED
            self.progress.error_message = str(e)
            self.progress.completed_at = datetime.now()
            
            if self._on_complete:
                self._on_complete(self.progress.to_dict())
    
    def get_available_models(self) -> list[dict]:
        """Get list of trained models."""
        models = []
        
        # Check for main model
        main_model = self.models_dir / "cards_yolo.pt"
        if main_model.exists():
            models.append({
                "name": "cards_yolo.pt",
                "path": str(main_model),
                "is_active": True,
                "modified": datetime.fromtimestamp(main_model.stat().st_mtime).isoformat(),
            })
        
        # Check training runs
        for run_dir in self.models_dir.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("cards_"):
                best_model = run_dir / "weights" / "best.pt"
                if best_model.exists():
                    models.append({
                        "name": run_dir.name,
                        "path": str(best_model),
                        "is_active": False,
                        "modified": datetime.fromtimestamp(best_model.stat().st_mtime).isoformat(),
                    })
        
        return models
    
    def get_training_history(self) -> list[dict]:
        """Get training history."""
        return self.history
    
    def validate_model(
        self,
        model_path: Optional[str] = None,
        dataset_yaml: Optional[str] = None,
    ) -> dict:
        """
        Validate model on dataset.
        
        Returns validation metrics.
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            return {"error": "ultralytics not installed"}
        
        if model_path is None:
            model_path = str(self.models_dir / "cards_yolo.pt")
        
        if not Path(model_path).exists():
            return {"error": "Model not found"}
        
        model = YOLO(model_path)
        
        if dataset_yaml:
            results = model.val(data=dataset_yaml)
            return {
                "mAP50": float(results.box.map50),
                "mAP50-95": float(results.box.map),
                "precision": float(results.box.mp),
                "recall": float(results.box.mr),
            }
        
        return {"status": "ready", "model_path": model_path}
