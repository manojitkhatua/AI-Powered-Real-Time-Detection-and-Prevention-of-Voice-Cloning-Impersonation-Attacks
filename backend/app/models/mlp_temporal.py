import torch
import torch.nn as nn


class VoiceAntiSpoofTemporalMLP(nn.Module):
    """
    Model B: MFCC temporal-statistics MLP.

    Input:
        80 features
        = 20 MFCC coefficients ×
          (mean, std, min, max)

    Output:
        1 logit
    """

    def __init__(self, input_size: int = 80):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.30),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)