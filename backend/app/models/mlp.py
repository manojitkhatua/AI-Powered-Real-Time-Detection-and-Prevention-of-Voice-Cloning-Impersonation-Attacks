import torch
import torch.nn as nn


class VoiceAntiSpoofMLP(nn.Module):
    """
    Lightweight MLP for voice anti-spoofing.

    Input:
        20 MFCC features

    Output:
        1 logit
        sigmoid(logit) -> spoof probability
    """

    def __init__(self, input_size=20):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(0.30),

            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.network(x)