import importlib


# Define a function to lazily import a module
def lazy_import(module_name):
    def _import():
        return importlib.import_module(module_name)

    return _import


# Use the lazy import function
gliner = lazy_import("gliner")

from typing import List

from setting import sensitive_labels


def load_model():
    # Initialize GLiNER with the base model
    model = gliner().GLiNER.from_pretrained("urchade/gliner_mediumv2.1")
    return model


def detect_sensitive_information(model, text: str) -> List[str]:
    sensitive = []
    # Perform entity prediction
    entities = model.predict_entities(text, sensitive_labels, threshold=0.3)

    # Display predicted entities and their labels
    for entity in entities:
        print(entity["text"], "=>", entity["label"])
        sensitive.append(entity["text"])

    return sensitive

""" 
Reference:
@misc{zaratiana2023gliner,
      title={GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer}, 
      author={Urchade Zaratiana and Nadi Tomeh and Pierre Holat and Thierry Charnois},
      year={2023},
      eprint={2311.08526},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
"""