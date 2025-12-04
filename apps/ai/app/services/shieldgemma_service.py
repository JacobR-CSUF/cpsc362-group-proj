"""
ShieldGemma Text Moderation Service
Analyzes text content for safety using Google's ShieldGemma 2B model.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafetyCategory(str, Enum):
    """ShieldGemma safety categories"""
    DANGEROUS_CONTENT = "Dangerous Content"
    HARASSMENT = "Harassment"
    HATE_SPEECH = "Hate Speech"
    SEXUALLY_EXPLICIT = "Sexually Explicit"


class ModerationVerdict(str, Enum):
    """Moderation outcome"""
    SAFE = "safe"
    WARNING = "warning"
    UNSAFE = "unsafe"


class ShieldGemmaError(Exception):
    """Base exception for ShieldGemma errors"""
    pass


class ShieldGemmaService:
    """
    Text content moderation using Google's ShieldGemma 2B.

    ShieldGemma uses a chat-based interface with specific control tokens
    to classify text as safe or unsafe.
    """

    _model = None
    _tokenizer = None
    _device = None

    # Safety policy definitions
    POLICIES = {
        SafetyCategory.DANGEROUS_CONTENT: (
            '"Dangerous Content": AI models should not create content that enables, '
            'encourages, or excuses the commission of dangerous acts or violent crimes, '
            'including: (1) Unlawful violence or threats thereof; (2) Promotion or creation '
            'of weapons; (3) Illegal drug use.'
        ),
        SafetyCategory.HARASSMENT: (
            '"Harassment": AI models should not create content that is malicious, intimidating, '
            'bullying, or abusive content targeting another individual including: '
            '(1) Negative or harmful characterizations of individuals based on sensitive attributes; '
            '(2) Dehumanization of individuals; (3) Threats or incitement to violence.'
        ),
        SafetyCategory.HATE_SPEECH: (
            '"Hate Speech": AI models should not create content that is hateful toward people '
            'based on protected characteristics (race, ethnicity, religion, disability, age, '
            'nationality, veteran status, sexual orientation, gender, gender identity, caste, '
            'or any other characteristic protected by law), and should not contain slurs.'
        ),
        SafetyCategory.SEXUALLY_EXPLICIT: (
            '"Sexually Explicit": AI models should not create sexually explicit content including: '
            '(1) Depictions of graphic sexual activity; (2) Content intended for arousal; '
            '(3) Descriptions of sexual services (commercial or otherwise).'
        ),
    }

    @classmethod
    def _load_model(cls):
        """Load ShieldGemma model and tokenizer"""
        if cls._model is not None:
            logger.info("Model already loaded")
            return

        logger.info("=" * 60)
        logger.info("LOADING SHIELDGEMMA MODEL")
        logger.info(f"Model: {settings.SHIELDGEMMA_MODEL_NAME}")
        logger.info(f"Device: {settings.SHIELDGEMMA_DEVICE}")
        logger.info("=" * 60)

        try:
            # Authenticate with Hugging Face
            import os
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                from huggingface_hub import login
                login(token=hf_token)
                logger.info("✅ Authenticated with Hugging Face")

            # Set device
            cls._device = "cpu"
            logger.info(f"Using device: {cls._device}")

            # Load tokenizer
            logger.info("Loading tokenizer...")
            cls._tokenizer = AutoTokenizer.from_pretrained(
                settings.SHIELDGEMMA_MODEL_NAME,
                trust_remote_code=True,
                token=hf_token
            )
            logger.info("✅ Tokenizer loaded")

            # Set padding token if not present
            if cls._tokenizer.pad_token is None:
                cls._tokenizer.pad_token = cls._tokenizer.eos_token
                logger.info(f"Set pad_token to eos_token: {cls._tokenizer.eos_token}")

            # Load model (this is SLOW - 5-10 minutes on CPU)
            logger.info("Loading model weights (this takes 5-10 minutes on CPU)...")
            logger.info("Please be patient...")

            cls._model = AutoModelForCausalLM.from_pretrained(
                settings.SHIELDGEMMA_MODEL_NAME,
                torch_dtype=torch.float32,  # Use float32 for CPU
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                token=hf_token
            )

            logger.info("Moving model to CPU...")
            cls._model = cls._model.to(cls._device)
            cls._model.eval()

            logger.info("=" * 60)
            logger.info("✅ SHIELDGEMMA MODEL FULLY LOADED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Failed to load ShieldGemma: {e}", exc_info=True)
            cls._model = None
            cls._tokenizer = None
            raise ShieldGemmaError(f"Model loading failed: {e}")


    @classmethod
    def _analyze_category(
        cls,
        text: str,
        category: SafetyCategory
    ) -> Tuple[bool, float, str]:
        """
        Analyze text against a specific safety category.
        Uses ShieldGemma's required prompt format.

        Returns:
            Tuple of (is_violation, confidence_score, explanation)
        """
        # Ensure model is loaded
        cls._load_model()

        # Get policy description
        policy = cls.POLICIES[category]

        # ✅ FIX: Use ShieldGemma's EXACT prompt format
        # Format from official documentation
        prompt = f"""You are a policy expert trying to help determine whether a user prompt is in violation of the defined safety policies.

    <start_of_turn>
    Human Question: {text}
    <end_of_turn>

    Our safety principle is defined in the below:

    * {policy}

    Does the human question violate the above principle? Your answer must start with 'Yes' or 'No'. And then walk through step by step to be sure we answer correctly.

    """

        logger.debug(f"Analyzing {category.value}. Prompt length: {len(prompt)} chars")

        # Tokenize
        inputs = cls._tokenizer(
            prompt,
            return_tensors="pt",
            max_length=settings.SHIELDGEMMA_MAX_LENGTH,
            truncation=True,
            padding=True
        ).to(cls._device)

        logger.debug(f"Input tokens: {inputs['input_ids'].shape[1]}")

        # Generate response
        try:
            with torch.no_grad():
                outputs = cls._model.generate(
                    **inputs,
                    max_new_tokens=50,
                    do_sample=False,
                    temperature=None,
                    top_p=None,
                    pad_token_id=cls._tokenizer.pad_token_id or cls._tokenizer.eos_token_id,
                    eos_token_id=cls._tokenizer.eos_token_id
                )
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise ShieldGemmaError(f"Text generation failed: {e}")

        # Decode response
        full_response = cls._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the generated part (after the prompt)
        generated_text = full_response[len(prompt):].strip()

        logger.info(f"{category.value} response: {generated_text[:100]}")

        # Parse response
        # ShieldGemma responds with "Yes" or "No" at the start
        first_word = generated_text.split()[0].lower() if generated_text else "no"
        is_violation = first_word == "yes"

        # Calculate confidence
        if is_violation:
            confidence = 0.9
        else:
            confidence = 0.1

        return is_violation, confidence, generated_text

    @classmethod
    def moderate_text(
        cls,
        text: str,
        categories: Optional[List[SafetyCategory]] = None
    ) -> Dict[str, Any]:
        """
        Moderate text content against safety categories.

        Args:
            text: Text content to analyze
            categories: List of categories to check (default: all)

        Returns:
            {
                "verdict": "safe" | "warning" | "unsafe",
                "is_safe": bool,
                "categories": {
                    "Dangerous Content": {"violated": bool, "confidence": float},
                    ...
                },
                "flagged_categories": ["category1", "category2"],
                "explanation": "reason for flagging",
                "max_violation_score": float
            }
        """
        if not text or not text.strip():
            return {
                "verdict": ModerationVerdict.SAFE,
                "is_safe": True,
                "categories": {},
                "flagged_categories": [],
                "explanation": "Empty text provided",
                "max_violation_score": 0.0
            }

        # Default to all categories
        if categories is None:
            categories = list(SafetyCategory)

        logger.info(f"Moderating text ({len(text)} chars) against {len(categories)} categories")

        # Analyze each category
        category_results = {}
        flagged_categories = []
        explanations = []
        max_score = 0.0

        for category in categories:
            try:
                logger.info(f"Analyzing category: {category.value}")
                is_violation, confidence, explanation = cls._analyze_category(text, category)

                category_results[category.value] = {
                    "violated": is_violation,
                    "confidence": confidence
                }

                logger.info(
                    f"{category.value}: violated={is_violation}, confidence={confidence:.2f}"
                )

                if is_violation:
                    flagged_categories.append(category.value)
                    explanations.append(f"{category.value}: {explanation[:200]}")
                    max_score = max(max_score, confidence)

            except Exception as e:
                logger.error(f"Error analyzing {category.value}: {e}", exc_info=True)
                category_results[category.value] = {
                    "violated": False,
                    "confidence": 0.0,
                    "error": str(e)
                }

        # Determine overall verdict
        if max_score >= settings.SHIELDGEMMA_THRESHOLD_UNSAFE:
            verdict = ModerationVerdict.UNSAFE
            is_safe = False
        elif max_score >= settings.SHIELDGEMMA_THRESHOLD_WARNING:
            verdict = ModerationVerdict.WARNING
            is_safe = False
        else:
            verdict = ModerationVerdict.SAFE
            is_safe = True

        explanation = "; ".join(explanations) if explanations else "Content passes all safety checks"

        logger.info(f"Moderation verdict: {verdict}, max_score={max_score:.2f}")

        return {
            "verdict": verdict,
            "is_safe": is_safe,
            "categories": category_results,
            "flagged_categories": flagged_categories,
            "explanation": explanation,
            "max_violation_score": max_score
        }


# Convenience function
def moderate_text(text: str, categories: Optional[List[SafetyCategory]] = None) -> Dict[str, Any]:
    """
    Moderate text using ShieldGemma.

    Args:
        text: Text to analyze
        categories: Optional list of categories to check

    Returns:
        Moderation results dictionary
    """
    return ShieldGemmaService.moderate_text(text, categories)
