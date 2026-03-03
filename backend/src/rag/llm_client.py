import logging
from typing import List, Optional

from src.rag.config import DEVICE, LLM_MODEL

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Local LLM client su dung transformers pipeline.
    Ho tro sinh cau tra loi tu RAG context.
    """

    def __init__(self):
        self._pipeline = None

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _load(self):
        if self._pipeline is not None:
            return

        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            pipeline,
        )

        logger.info(f"Loading LLM: {LLM_MODEL} on {DEVICE}")

        dtype = torch.float16 if DEVICE == "cuda" else torch.float32

        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)

        # device_map="auto" yeu cau accelerate, thu dung no truoc
        try:
            import accelerate  # noqa: F401

            model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL,
                dtype=dtype,
                device_map="auto",
            )
        except ImportError:
            # Fallback: load binh thuong, chuyen sang device thu cong
            logger.warning("`accelerate` not found, loading model without device_map.")
            model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL,
                dtype=dtype,
            )
            model = model.to(DEVICE)

        self._pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )
        logger.info("LLM loaded successfully.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_answer(self, query: str, contexts: List[str]) -> str:
        """
        Sinh cau tra loi dua tren query va danh sach context da retrieve.
        """
        self._load()

        context_text = "\n\n".join(contexts)

        prompt = (
            "You are an expert academic assistant.\n"
            "Use ONLY the provided context to answer the question.\n"
            "If the context does not contain enough information, say so clearly.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )

        output = self._pipeline(
            prompt,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=self._pipeline.tokenizer.eos_token_id,
        )

        full_text: str = output[0]["generated_text"]

        # Chi lay phan sau "Answer:"
        if "Answer:" in full_text:
            return full_text.split("Answer:")[-1].strip()
        return full_text.strip()

    def is_loaded(self) -> bool:
        return self._pipeline is not None
