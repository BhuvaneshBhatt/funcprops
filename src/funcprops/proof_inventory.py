"""Release inventory of proof records, checker support and public entry points."""

import json
from importlib.resources import files


def proof_api_manifest():
    """Return proof-type and API metadata, including each declared replay contract.

    Entry-point discovery follows the static call graph conservatively: an API
    listed here can reach a proof-record constructor, but may also return an
    ordinary result or decline. The inventory is not a mathematical capability
    claim. Unsupported record types remain listed with replay_supported=False.
    """
    return json.loads(
        files("funcprops").joinpath("data/proof_api_manifest.json").read_text()
    )
