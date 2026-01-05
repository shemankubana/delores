import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from sentence_transformers import SentenceTransformer
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class LocalModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info("loading Local Models... This may take a while on first run.")
        
        # Determine device
        self.device = "cpu"
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info("🚀 CUDA (NVIDIA GPU) detected. Using CUDA acceleration!")
        else:
            # MPS (Mac GPU) causes "unsupported autocast device_type 'mps'" in torch 2.2.1 / transformers 4.38
            # So we force CPU for stability.
            logger.info("ℹ️ MPS detected but disabled due to torch autocast compatibility issues. Running on CPU.")
            logger.info("⚠️ No compatible GPU detected. Running on CPU (slow).")

        # 1. Vision Model (BLIP)
        logger.info("   Loading Vision Model (BLIP)...")
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(self.device)
        
        # 2. Text Embedding Model
        logger.info("   Loading Embedding Model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
        
        # 3. LLM (TinyLlama - Small & Fast)
        logger.info("   Loading LLM (TinyLlama)...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Use float16 for CUDA, float32 for CPU
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch_dtype, 
            device_map=self.device
        )
        
        self._initialized = True
        logger.info("✅ All Local Models Loaded Successfully.")

    def caption_image(self, image: Image):
        """Generates a text caption for a PIL Image."""
        try:
            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
            out = self.blip_model.generate(**inputs, max_new_tokens=50)
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            logger.error(f"Error captioning image: {e}")
            return "Image could not be processed."

    def embed_text(self, text):
        """Generates embedding vector for text."""
        return self.embedding_model.encode(text).tolist()
    
    def generate_response(self, prompt):
        """Generates full text response from LLM (Blocking)."""
        formatted_prompt = f"<|system|>\nYou are Delores, a helpful assistant for Irembo.<|user|>\n{prompt}<|assistant|>\n"
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
        
        outputs = self.llm_model.generate(**inputs, max_new_tokens=256, temperature=0.7, do_sample=True)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).split("<|assistant|>\n")[-1].strip()

    def generate_response_stream(self, prompt):
        """Generates text response from LLM (Streaming)."""
        formatted_prompt = f"<|system|>\nYou are Delores, a helpful assistant for Irembo.<|user|>\n{prompt}<|assistant|>\n"
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
        
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(
            **inputs, 
            streamer=streamer, 
            max_new_tokens=256, 
            temperature=0.7, 
            do_sample=True
        )
        
        thread = Thread(target=self.llm_model.generate, kwargs=generation_kwargs)
        thread.start()
        
        for new_text in streamer:
            yield new_text

# Global instance
local_models = LocalModelManager()
