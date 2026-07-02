"""CNN-JEPA building blocks for SE-ResNet pretraining."""

from models.jepa.encoder import JEPAEncoder
from models.jepa.loss import latent_prediction_loss
from models.jepa.masking import BlockMaskGenerator
from models.jepa.module import JEPAModule
from models.jepa.predictor import ConvPredictor

__all__ = [
    "BlockMaskGenerator",
    "ConvPredictor",
    "JEPAEncoder",
    "JEPAModule",
    "latent_prediction_loss",
]
