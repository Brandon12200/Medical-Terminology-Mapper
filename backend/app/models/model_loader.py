"""Model loader for BioBERT NER model."""

import os
import torch
import argparse
import logging
import json
import gc

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelManager:
    """Manages BioBERT model loading and inference."""
    
    def __init__(self, model_path=None):
        """Initialize the model manager."""
        # Default to local model directory if path not provided
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'biobert_model')
        
        # Set device (use CUDA if available, else CPU)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        # Model components
        self.tokenizer = None
        self.model = None
        self.entity_labels = None
        self.is_initialized = False
        self.model_config = {}
        
    def initialize(self):
        """
        Load model and tokenizer.
        
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        try:
            # Check if model path exists
            if not os.path.exists(self.model_path):
                logger.warning(f"Model path {self.model_path} does not exist, attempting to create it")
                os.makedirs(self.model_path, exist_ok=True)
            
            logger.info(f"Initializing model from {self.model_path}")
            
            # Load or create config file
            config_path = os.path.join(self.model_path, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.model_config = json.load(f)
                logger.info(f"Loaded model config: {self.model_config}")
            else:
                # Create default config with terminology-specific entity types
                self.model_config = {
                    "model_type": "biobert",
                    "name": "biobert-base-cased",
                    "version": "placeholder-v1.0",
                    "entity_types": ["CONDITION", "MEDICATION", "PROCEDURE", "LAB_TEST", "OBSERVATION"],
                }
                # Save default config
                with open(config_path, 'w') as f:
                    json.dump(self.model_config, f, indent=2)
                logger.info(f"Created default model config: {self.model_config}")
            
            # Create or load entity labels file
            entity_labels_path = os.path.join(self.model_path, 'entity_labels.txt')
            if not os.path.exists(entity_labels_path):
                # Create default entity labels based on config
                with open(entity_labels_path, 'w') as f:
                    f.write("O\n")  # Outside tag
                    for entity_type in self.model_config.get("entity_types", []):
                        f.write(f"B-{entity_type}\n")  # Beginning tags
                        f.write(f"I-{entity_type}\n")  # Inside tags
                logger.info(f"Created default entity labels file")
            
            # Load entity labels
            with open(entity_labels_path, 'r') as f:
                self.entity_labels = [line.strip() for line in f.readlines()]
            logger.info(f"Loaded {len(self.entity_labels)} entity labels")
            
            # Load the actual model and tokenizer
            try:
                from transformers import AutoTokenizer, AutoModelForTokenClassification
                
                # Check if offline mode is enabled
                offline_marker = os.path.join(self.model_path, 'offline_mode_enabled.txt')
                use_offline_mode = os.path.exists(offline_marker)
                
                if use_offline_mode:
                    logger.info("Offline mode is enabled, using dummy implementation")
                    self.tokenizer = self._create_dummy_tokenizer()
                    self.model = self._create_dummy_model()
                else:
                    # Try to use the pretrained BioBERT model directly
                    try:
                        logger.info(f"Loading base BioBERT model")
                        # Load directly from HuggingFace
                        model_name = "dmis-lab/biobert-base-cased-v1.2"
                        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                        
                        # Create model with NER labels
                        num_labels = len(self.entity_labels)
                        id2label = {i: label for i, label in enumerate(self.entity_labels)}
                        label2id = {v: k for k, v in id2label.items()}
                        
                        # Configure model for NER
                        from transformers import AutoConfig
                        config = AutoConfig.from_pretrained(
                            model_name,
                            num_labels=num_labels,
                            id2label=id2label,
                            label2id=label2id
                        )
                        
                        self.model = AutoModelForTokenClassification.from_pretrained(
                            model_name, 
                            config=config
                        )
                        self.model.to(self.device)
                        logger.info("Successfully loaded BioBERT model and configured for NER")
                        
                    except Exception as e:
                        logger.warning(f"Could not load BioBERT model: {e}, using dummy model")
                        # For the placeholder, we'll simulate having a model and tokenizer
                        self.tokenizer = self._create_dummy_tokenizer()
                        self.model = self._create_dummy_model()
                        logger.warning("Using dummy model implementation")
            except Exception as e:
                logger.error(f"Error loading actual model, falling back to dummy implementation: {e}")
                # Fallback to dummy implementation
                self.tokenizer = self._create_dummy_tokenizer()
                self.model = self._create_dummy_model()
            
            # Set models to evaluation mode
            if hasattr(self.model, 'eval'):
                logger.info("Setting NER model to evaluation mode")
                self.model.eval()
            
            self.is_initialized = True
            logger.info("Models initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing models: {e}", exc_info=True)
            self.is_initialized = False
            return False
    
    def _create_dummy_tokenizer(self):
        """Create a placeholder tokenizer object with minimal functionality."""
        class DummyTokenizer:
            def __call__(self, text, return_tensors=None, truncation=None, 
                        max_length=None, return_offsets_mapping=None, padding=None):
                # Return a dummy encoding object
                if isinstance(text, list):
                    batch_size = len(text)
                else:
                    batch_size = 1
                    text = [text]
                
                result = {
                    "input_ids": torch.ones((batch_size, 10)),
                    "attention_mask": torch.ones((batch_size, 10))
                }
                
                if return_offsets_mapping:
                    # Create dummy offset mapping (token start/end positions)
                    offsets = []
                    for t in text:
                        # Create 10 token offsets for each text
                        text_offsets = []
                        pos = 0
                        for i in range(10):
                            if i == 0:  # CLS token
                                text_offsets.append((0, 0))
                            elif i == 9:  # SEP token
                                text_offsets.append((0, 0))
                            else:
                                # Create realistic token offsets
                                token_len = min(5, len(t) - pos)
                                if token_len <= 0:
                                    text_offsets.append((0, 0))
                                else:
                                    text_offsets.append((pos, pos + token_len))
                                    pos += token_len
                        offsets.append(text_offsets)
                    
                    if batch_size == 1:
                        result["offset_mapping"] = torch.tensor(offsets[0])
                    else:
                        result["offset_mapping"] = torch.tensor(offsets)
                
                return DummyEncoding(result)
        
        class DummyEncoding(dict):
            def __init__(self, d):
                super().__init__(d)
            
            def pop(self, key):
                value = self[key]
                del self[key]
                return value
        
        return DummyTokenizer()
    
    def _create_dummy_model(self):
        """Create a placeholder model object with minimal functionality for entity extraction."""
        class DummyModel:
            def __init__(self):
                pass
                
            def __call__(self, **kwargs):
                # Return dummy outputs with logits for entity prediction
                input_ids = kwargs.get("input_ids", None)
                if input_ids is not None:
                    batch_size, seq_len = input_ids.shape
                else:
                    batch_size, seq_len = 1, 10
                
                num_labels = len(self.entity_labels) if hasattr(self, 'entity_labels') else 10
                logits = torch.randn(batch_size, seq_len, num_labels)
                
                class DummyOutput:
                    def __init__(self, logits):
                        self.logits = logits
                
                return DummyOutput(logits)
            
            def to(self, device):
                # Placeholder for device movement
                return self
                
            def eval(self):
                # Placeholder for evaluation mode
                pass
        
        dummy_model = DummyModel()
        # Attach entity labels for consistent dummy predictions
        dummy_model.entity_labels = self.entity_labels
        return dummy_model
    
    def cleanup(self):
        """
        Free resources and clear memory.
        
        Proper cleanup of model resources to prevent memory leaks.
        """
        logger.info("Cleaning up model resources")
        
        # Set models to None to remove references
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if available
        if self.device == 'cuda' and torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
    
    def get_model(self):
        """Get the loaded model."""
        if not self.is_initialized:
            logger.warning("Model not initialized. Call initialize() first.")
        return self.model
    
    def get_tokenizer(self):
        """Get the loaded tokenizer."""
        if not self.is_initialized:
            logger.warning("Model not initialized. Call initialize() first.")
        return self.tokenizer
    
    def get_entity_labels(self):
        """Get the entity label list."""
        return self.entity_labels
    
    def is_ready(self):
        """Check if model is initialized and ready."""
        return self.is_initialized


def download_model(model_name="dmis-lab/biobert-base-cased-v1.2", local_dir=None, force=False):
    """
    Download model from HuggingFace Hub or create a placeholder.
    
    Args:
        model_name (str, optional): Model name or HF Hub ID. Defaults to "dmis-lab/biobert-base-cased-v1.2".
        local_dir (str, optional): Output directory. Defaults to None (uses default location).
        force (bool, optional): Force redownload even if model exists. Defaults to False.
        
    Returns:
        str: Path to the model directory
    """
    if local_dir is None:
        local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'biobert_model')
    
    # Check if model already exists
    if not force and os.path.exists(os.path.join(local_dir, 'config.json')):
        model_ready = False
        
        # Verify that the model is properly downloaded with required files
        required_files = ['config.json', 'entity_labels.txt']
        
        model_ready = all(os.path.exists(os.path.join(local_dir, file)) for file in required_files)
            
        if model_ready:
            logger.info(f"Model already exists and is complete at {local_dir}. Use --force to redownload.")
            return local_dir
        else:
            logger.warning(f"Model exists at {local_dir} but appears incomplete. Will attempt to download missing files.")
    
    try:
        # Try to use HuggingFace Hub to download the model
        logger.info(f"Attempting to download model {model_name} to {local_dir}")
        
        try:
            from transformers import AutoConfig, AutoModelForTokenClassification, AutoTokenizer
            
            # First create the directory
            os.makedirs(local_dir, exist_ok=True)
            
            # Download and save the model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            tokenizer.save_pretrained(local_dir)
            logger.info(f"Successfully downloaded tokenizer to {local_dir}")
            
            # Download and save the model configuration
            config = AutoConfig.from_pretrained(model_name)
            config.save_pretrained(local_dir)
            logger.info(f"Successfully downloaded model config to {local_dir}")
            
            # Create entity labels file if it doesn't exist
            entity_labels_path = os.path.join(local_dir, 'entity_labels.txt')
            if not os.path.exists(entity_labels_path):
                # Updated entity types for terminology mapping
                entity_types = ["CONDITION", "MEDICATION", "PROCEDURE", "LAB_TEST", "OBSERVATION"]
                with open(entity_labels_path, 'w') as f:
                    f.write("O\n")  # Outside tag
                    for entity_type in entity_types:
                        f.write(f"B-{entity_type}\n")  # Beginning tags
                        f.write(f"I-{entity_type}\n")  # Inside tags
                logger.info(f"Created entity labels file at {entity_labels_path}")
            
            logger.info(f"Model {model_name} successfully downloaded to {local_dir}")
            return local_dir
        except Exception as e:
            logger.error(f"Error downloading model with transformers: {e}")
            raise
    except Exception as e:
        logger.warning(f"Failed to download model: {e}. Creating fallback version instead.")
        
        # If download fails, create a backup/placeholder model
        os.makedirs(local_dir, exist_ok=True)
        
        # Create a basic config file with terminology-specific entity types
        config = {
            "model_type": "biobert",
            "name": model_name,
            "version": "placeholder-v1.0",
            "entity_types": ["CONDITION", "MEDICATION", "PROCEDURE", "LAB_TEST", "OBSERVATION"],
            "offline_mode": True
        }
        
        with open(os.path.join(local_dir, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create entity labels file
        with open(os.path.join(local_dir, 'entity_labels.txt'), 'w') as f:
            f.write("O\n")  # Outside tag
            for entity_type in config["entity_types"]:
                f.write(f"B-{entity_type}\n")  # Beginning tags
                f.write(f"I-{entity_type}\n")  # Inside tags
        
        # Create offline mode marker file
        with open(os.path.join(local_dir, 'offline_mode_enabled.txt'), 'w') as f:
            f.write("This file enables offline mode with dummy model implementations.\n")
            f.write("Delete this file to attempt loading the actual model.\n")
        
        logger.info(f"Fallback model created successfully at {local_dir}")
        return local_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download model for Medical Terminology Mapper')
    parser.add_argument('--model', default="dmis-lab/biobert-base-cased-v1.2", 
                        help='Model name on HuggingFace')
    parser.add_argument('--output', help='Output directory for model')
    parser.add_argument('--force', action='store_true', 
                        help='Force redownload even if model exists')
    parser.add_argument('--download', action='store_true', help='Download the model')
    parser.add_argument('--test', action='store_true', 
                        help='Test model loading after download')
    parser.add_argument('--offline', action='store_true',
                        help='Enable offline mode with dummy implementation')
    args = parser.parse_args()
    
    if args.download:
        model_dir = download_model(args.model, args.output, args.force)
        logger.info(f"Model saved to: {model_dir}")
        
        # Create offline mode marker if requested
        if args.offline:
            offline_marker = os.path.join(model_dir, 'offline_mode_enabled.txt')
            with open(offline_marker, 'w') as f:
                f.write("This file enables offline mode with dummy model implementations.\n")
                f.write("Delete this file to attempt loading the actual model.\n")
            logger.info("Offline mode enabled")
        
        if args.test:
            logger.info("Testing model initialization")
            manager = ModelManager(model_dir)
            success = manager.initialize()
            if success:
                logger.info("Model initialization successful!")
                manager.cleanup()
            else:
                logger.error("Model initialization failed!")