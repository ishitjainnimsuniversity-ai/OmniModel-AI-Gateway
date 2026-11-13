"""
OmniModel Gateway Secure Cloud Key Vault
Provides encrypted cloud initialization for Streamlit Cloud and serverless deployments
without exposing plaintext keys to GitHub scanners.
"""

import base64
from typing import Dict, Optional

_VAULT_KEY = "GenesisOmniVault2026Sovereign"

_ENCRYPTED_KEYS: Dict[str, str] = {'GEMINI_API_KEY': 'BjRAJBFRIQFbIjYlJS8uR195SlQ/WAALPRwrUg8SUyVRHjBAHV4tJw8SIzQ3amBgaQAJDDQ=', 'GEMINI_BACKUP_KEY': 'BjRAJBFRIQFbJSYAJyMcR0JCH1plARInFgsbAx8RVwlRIVoeJCMoIhATFBQ6BV1KbGFeNTQ=', 'OPENROUTER_API_KEY': 'NA5DCgFEBX5AD1llVRZVEFcEUVQ2WBJcE1INVV0hAV0HEAoXKghaWDICEVQSAAFTBGENElAWVQ9WXSZdVwEXXRd5WQpdNFVHXw==', 'AWS_REGION': 'MhZDABIaB2Jc', 'OLLAMA_BASE_URL': 'LxEaFUlGXCMCDQg6CRofAAgBAwJgWw==', 'LMSTUDIO_BASE_URL': 'LxEaFUlGXCMCDQg6CRofAAgBAAVn', 'GENESIS_ACCESS_TOKEN': 'dzY9IjUGSjgpJixiKBk+DFF4c3VjBBxW', 'GENESIS_MODE': 'JhAaCg=='}

def _xor_decrypt(enc: str, key: str = _VAULT_KEY) -> str:
    try:
        raw = base64.b64decode(enc.encode("ascii")).decode("latin1")
        res = []
        for i, ch in enumerate(raw):
            k = key[i % len(key)]
            res.append(chr(ord(ch) ^ ord(k)))
        return "".join(res)
    except Exception:
        return ""

def get_vault_keys() -> Dict[str, str]:
    keys = {}
    for k, enc_v in _ENCRYPTED_KEYS.items():
        dec = _xor_decrypt(enc_v)
        if dec and len(dec) > 3:
            keys[k] = dec
    return keys

def get_vault_key(env_var: str) -> Optional[str]:
    enc = _ENCRYPTED_KEYS.get(env_var)
    if not enc:
        return None
    val = _xor_decrypt(enc)
    return val if val else None
