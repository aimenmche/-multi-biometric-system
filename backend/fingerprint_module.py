import hashlib
import json
import logging

logger = logging.getLogger(__name__)

SIMULATION_MODE = True


def extract_fingerprint_features(fingerprint_b64: str) -> tuple:
    if SIMULATION_MODE:
        feature_hash = hashlib.sha256(fingerprint_b64.encode()).hexdigest()
        feature_vector = _generate_simulated_minutiae(fingerprint_b64)
        features = json.dumps({
            "hash": feature_hash,
            "minutiae_count": len(feature_vector),
            "minutiae": feature_vector[:50],
        })
        return features, None
    else:
        return None, "Hardware fingerprint scanner not available"


def _generate_simulated_minutiae(seed_data: str) -> list:
    seed_hash = hashlib.md5(seed_data.encode()).hexdigest()
    minutiae = []
    for i in range(0, 100):
        x = (int(seed_hash[i % 32], 16) * 10 + i * 7) % 256
        y = (int(seed_hash[(i + 1) % 32], 16) * 10 + i * 13) % 256
        angle = (int(seed_hash[(i + 2) % 32], 16) * 22) % 360
        minutiae.append({"x": x, "y": y, "angle": angle, "type": "ridge_ending" if i % 2 == 0 else "bifurcation"})
    return minutiae


def match_fingerprint_templates(stored_template: str, new_template: str, threshold: float = 0.75) -> tuple:
    try:
        stored = json.loads(stored_template)
        new = json.loads(new_template)

        stored_hash = stored.get("hash", "")
        new_hash = new.get("hash", "")

        if SIMULATION_MODE:
            hamming_distance = sum(
                1 for a, b in zip(stored_hash, new_hash) if a != b
            ) / max(len(stored_hash), len(new_hash))

            match_score = 1.0 - hamming_distance
            is_match = match_score >= threshold
            return is_match, float(match_score)
        else:
            stored_min = stored.get("minutiae", [])
            new_min = new.get("minutiae", [])

            matches = 0
            for sp in stored_min:
                for np_pt in new_min:
                    dx = sp["x"] - np_pt["x"]
                    dy = sp["y"] - np_pt["y"]
                    if (dx * dx + dy * dy) < 25:
                        matches += 1
                        break

            total = max(len(stored_min), len(new_min))
            score = matches / total if total > 0 else 0
            is_match = score >= threshold
            return is_match, float(score)
    except Exception as e:
        logger.error(f"Fingerprint matching error: {e}")
        return False, 0.0
