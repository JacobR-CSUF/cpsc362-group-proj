"""
ShieldGemma Text Moderation Service
Analyzes text content for safety using Google's ShieldGemma 2B model.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
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
    """

    _model = None
    _tokenizer = None
    _device = None

    # Safety policy definitions
    POLICIES = {
        SafetyCategory.DANGEROUS_CONTENT: (
            '"Dangerous Content": Content that enables, encourages, or excuses the commission '
            'of dangerous acts or violent crimes, including: (1) Unlawful violence or threats; '
            '(2) Promotion or creation of weapons, explosives, or dangerous materials; '
            '(3) Instructions for self-harm or suicide; (4) Illegal drug use or creation.'
        ),
        SafetyCategory.HARASSMENT: (
            '"Harassment": Content that is malicious, intimidating, bullying, or abusive '
            'targeting another individual including: (1) Threats of violence; '
            '(2) Stalking or intimidation; (3) Degrading or demeaning content.'
        ),
        SafetyCategory.HATE_SPEECH: (
            '"Hate Speech": Content that is hateful toward people based on protected '
            'characteristics (race, ethnicity, religion, disability, age, nationality, '
            'veteran status, sexual orientation, gender, gender identity, caste), '
            'including slurs, dehumanization, or calls for violence.'
        ),
        SafetyCategory.SEXUALLY_EXPLICIT: (
            '"Sexually Explicit": Content including graphic sexual activity, '
            'pornographic material, or content designed for sexual arousal.'
        ),
    }

    @classmethod
    def _load_model(cls):
        """Load ShieldGemma model with GPU support"""
        if cls._model is not None:
            return

        logger.info("=" * 60)
        logger.info("LOADING SHIELDGEMMA MODEL")
        logger.info(f"Model: {settings.SHIELDGEMMA_MODEL_NAME}")
        logger.info(f"Device: {settings.SHIELDGEMMA_DEVICE}")
        logger.info("=" * 60)

        try:
            import os
            from huggingface_hub import login

            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                login(token=hf_token)
                logger.info("✅ Authenticated with Hugging Face")

            # Set device
            if settings.SHIELDGEMMA_DEVICE == "cuda" and torch.cuda.is_available():
                cls._device = "cuda"
                logger.info(f"✅ Using GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            else:
                cls._device = "cpu"
                if settings.SHIELDGEMMA_DEVICE == "cuda":
                    logger.warning("⚠️ CUDA requested but not available, falling back to CPU")

            # Load tokenizer
            logger.info("Loading tokenizer...")
            cls._tokenizer = AutoTokenizer.from_pretrained(
                settings.SHIELDGEMMA_MODEL_NAME,
                trust_remote_code=True,
                token=hf_token
            )

            if cls._tokenizer.pad_token is None:
                cls._tokenizer.pad_token = cls._tokenizer.eos_token

            logger.info(f"✅ Tokenizer loaded (vocab size: {len(cls._tokenizer)})")

            # Load model
            logger.info(f"Loading model to {cls._device.upper()}...")

            if cls._device == "cuda":
                cls._model = AutoModelForCausalLM.from_pretrained(
                    settings.SHIELDGEMMA_MODEL_NAME,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    token=hf_token
                )
            else:
                cls._model = AutoModelForCausalLM.from_pretrained(
                    settings.SHIELDGEMMA_MODEL_NAME,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True,
                    token=hf_token
                )
                cls._model = cls._model.to(cls._device)

            cls._model.eval()

            logger.info("=" * 60)
            logger.info("✅ SHIELDGEMMA MODEL LOADED SUCCESSFULLY")
            if cls._device == "cuda":
                logger.info(f"GPU Memory Used: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
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

        Returns:
            Tuple of (is_violation, confidence_score, explanation)
        """
        cls._load_model()

        policy = cls.POLICIES[category]

        # ShieldGemma prompt format
        prompt = f"""You are a policy expert trying to help determine whether a user prompt is in violation of the defined safety policies.

<start_of_turn>
Human Question: {text}
<end_of_turn>

Our safety principle is defined in the below:

* {policy}

Does the human question violate the above principle? Your answer must start with 'Yes' or 'No'. And then walk through step by step to be sure we answer correctly.

"""

        logger.info(f"Analyzing: {category.value}")
        logger.debug(f"Text: {text[:100]}...")

        # Tokenize
        inputs = cls._tokenizer(
            prompt,
            return_tensors="pt",
            max_length=settings.SHIELDGEMMA_MAX_LENGTH,
            truncation=True,
            padding=True
        ).to(cls._device)

        input_length = inputs['input_ids'].shape[1]
        logger.debug(f"Input tokens: {input_length}")

        try:
            with torch.no_grad():
                outputs = cls._model.generate(
                    **inputs,
                    max_new_tokens=150,
                    min_new_tokens=5,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=cls._tokenizer.pad_token_id,
                    eos_token_id=cls._tokenizer.eos_token_id,
                )
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise ShieldGemmaError(f"Text generation failed: {e}")

        # Extract only new tokens
        new_tokens = outputs[0][input_length:]
        generated_text = cls._tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        logger.info(f"Generated ({len(generated_text)} chars): {generated_text[:150]}...")

        if not generated_text:
            logger.warning("Empty generation, defaulting to safe")
            return False, 0.15, "Model generated empty response"

        # ✅ FIXED: Correct method name
        is_violation, confidence = cls._parse_response(generated_text)

        return is_violation, confidence, generated_text

    @classmethod
    def _parse_response(cls, response: str) -> Tuple[bool, float]:
        """
        Parse ShieldGemma's response to extract violation status and confidence.

        The confidence score represents VIOLATION LIKELIHOOD:
        - High score (0.7-0.95) = likely violates policy
        - Low score (0.05-0.3) = likely safe

        Returns:
            Tuple of (is_violation, violation_likelihood_score)
        """
        if not response:
            logger.warning("Empty response from ShieldGemma, defaulting to safe")
            return False, 0.15

        response_lower = response.lower().strip()

        # Extract first word (remove punctuation)
        words = response_lower.split()
        first_word = words[0].rstrip('.,!?:;') if words else ""

        logger.debug(f"Parsing response, first word: '{first_word}'")

        # Determine violation status and base score
        is_violation = False
        base_score = 0.5

        if first_word == "yes":
            is_violation = True
            base_score = 0.80  # High score for explicit violation
        elif first_word == "no":
            is_violation = False
            base_score = 0.15  # Low score for explicit safe
        else:
            # Fallback: Search for yes/no in first 100 chars
            first_part = response_lower[:100]

            violation_phrases = [
                'yes,', 'yes.', 'yes ',
                'violates', 'violation', 'does violate',
                'is harmful', 'is dangerous', 'is unsafe'
            ]
            safe_phrases = [
                'no,', 'no.', 'no ',
                'does not violate', 'no violation',
                'is safe', 'is not harmful', 'is acceptable'
            ]

            has_violation = any(phrase in first_part for phrase in violation_phrases)
            has_safe = any(phrase in first_part for phrase in safe_phrases)

            if has_violation and not has_safe:
                is_violation = True
                base_score = 0.65
            elif has_safe and not has_violation:
                is_violation = False
                base_score = 0.25
            else:
                logger.warning(f"Ambiguous response format: {response[:80]}")
                is_violation = False
                base_score = 0.35

        # Adjust score based on reasoning strength
        score_adjustment = 0.0

        strong_indicators = [
            'clearly', 'definitely', 'obviously', 'certainly',
            'absolutely', 'explicitly', 'directly', 'unambiguously'
        ]
        uncertain_indicators = [
            'might', 'could', 'possibly', 'maybe', 'perhaps',
            'unclear', 'ambiguous', 'debatable', 'borderline'
        ]
        severity_indicators = [
            'severe', 'serious', 'extreme', 'dangerous',
            'harmful', 'threatening', 'violent'
        ]

        for indicator in strong_indicators:
            if indicator in response_lower:
                if is_violation:
                    score_adjustment += 0.05
                else:
                    score_adjustment -= 0.05

        for indicator in uncertain_indicators:
            if indicator in response_lower:
                if is_violation:
                    score_adjustment -= 0.08
                else:
                    score_adjustment += 0.08

        if is_violation:
            for indicator in severity_indicators:
                if indicator in response_lower:
                    score_adjustment += 0.03

        # Calculate final score
        final_score = base_score + score_adjustment

        # Clamp to valid range
        if is_violation:
            final_score = max(0.55, min(0.95, final_score))  # Violations: 0.55-0.95
        else:
            final_score = max(0.05, min(0.40, final_score))  # Safe: 0.05-0.40

        logger.info(
            f"Parsed: violation={is_violation}, "
            f"base={base_score:.2f}, adj={score_adjustment:+.2f}, "
            f"final={final_score:.2f}"
        )

        return is_violation, round(final_score, 3)

    @classmethod
    def moderate_text(
        cls,
        text: str,
        categories: Optional[List[SafetyCategory]] = None
    ) -> Dict[str, Any]:
        """
        Moderate text content against safety categories.

        Returns:
            Moderation results dictionary
        """
        if not text or not text.strip():
            return {
                "verdict": ModerationVerdict.SAFE.value,
                "is_safe": True,
                "categories": {},
                "flagged_categories": [],
                "explanation": "Empty text provided",
                "max_violation_score": 0.0
            }

        if categories is None:
            categories = list(SafetyCategory)

        logger.info(f"Moderating text ({len(text)} chars) against {len(categories)} categories")

        category_results = {}
        flagged_categories = []
        explanations = []
        max_score = 0.0

        for category in categories:
            try:
                is_violation, confidence, explanation = cls._analyze_category(text, category)

                category_results[category.value] = {
                    "violated": is_violation,
                    "confidence": round(confidence, 3)
                }

                if is_violation:
                    flagged_categories.append(category.value)
                    explanations.append(f"{category.value}: {explanation[:150]}")
                    max_score = max(max_score, confidence)

                logger.info(f"  {category.value}: violated={is_violation}, confidence={confidence:.3f}")

            except Exception as e:
                logger.error(f"Error analyzing {category.value}: {e}")
                category_results[category.value] = {
                    "violated": False,
                    "confidence": 0.0,
                    "error": str(e)
                }

        # Determine verdict
        if max_score >= settings.SHIELDGEMMA_THRESHOLD_UNSAFE:
            verdict = ModerationVerdict.UNSAFE
            is_safe = False
        elif max_score >= settings.SHIELDGEMMA_THRESHOLD_WARNING:
            verdict = ModerationVerdict.WARNING
            is_safe = False
        else:
            verdict = ModerationVerdict.SAFE
            is_safe = True

        final_explanation = "; ".join(explanations) if explanations else "Content passes all safety checks"

        logger.info(f"Final verdict: {verdict.value}, max_score={max_score:.3f}")

        return {
            "verdict": verdict.value,
            "is_safe": is_safe,
            "categories": category_results,
            "flagged_categories": flagged_categories,
            "explanation": final_explanation,
            "max_violation_score": round(max_score, 3)
        }


# Convenience function
def moderate_text(
    text: str,
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Moderate text using ShieldGemma."""
    category_enums = None
    if categories:
        category_enums = []
        for cat in categories:
            try:
                category_enums.append(SafetyCategory(cat))
            except ValueError:
                logger.warning(f"Unknown category: {cat}")

    return ShieldGemmaService.moderate_text(text, category_enums)
