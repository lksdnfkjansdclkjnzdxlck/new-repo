
import numpy as np
from light_embed import TextEmbedding

model = TextEmbedding(
    model_name_or_path="onnx-models/all-MiniLM-L6-v2-onnx"
)

texts = [
    "This is a sentence for embedding.",
    "This sentence is about machine learning."
]

embeddings = np.asarray(model.encode(texts))

print("Shape:", embeddings.shape)
print(embeddings)
