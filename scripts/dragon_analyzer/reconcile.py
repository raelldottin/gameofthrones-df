"""Deterministic, read-only evidence replay. Approval registry is an external trust boundary."""
import copy
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

PERMANENT = {"stars", "relics_current", "relics_required", "habits"}
SEASONAL = {"level", "xp_current", "xp_required_display", "power", "capacity",
            "energy_current", "energy_maximum"}
EVENT = {"source_sha256", "observed_at", "reign_id", "name", "extractor_id",
         "permanent", "seasonal"}


def digest(value):
    """Canonical JSON hash, not a digital signature."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string with explicit offset")
    at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("Timestamp must include an offset")
    return at.astimezone(timezone.utc)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def integer(value, low=0, high=2**53-1):
    return type(value) is int and low <= value <= high


def exact_keys(value, keys):
    return isinstance(value, dict) and set(value) == keys


def valid(e):
    if not exact_keys(e, EVENT):
        return False
    if not all(nonblank(e[k]) for k in ("name", "extractor_id", "reign_id")):
        return False
    if not isinstance(e["source_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", e["source_sha256"]):
        return False
    try:
        instant(e["observed_at"])
    except (ValueError, TypeError, OverflowError):
        return False
    p,s=e["permanent"],e["seasonal"]
    if not exact_keys(p, PERMANENT) or not exact_keys(s, SEASONAL):
        return False
    if not (integer(p["stars"],1,10) and integer(p["relics_current"])
            and integer(p["relics_required"],1) and p["relics_current"] < p["relics_required"]
            and isinstance(p["habits"],list) and len(p["habits"]) == p["stars"]//2
            and all(integer(x,1,5) for x in p["habits"])):
        return False
    # Permit additional unlocked habit slots to be absent? No: full observed progression required.
    return (all(integer(s[k]) for k in ("xp_current","power","capacity","energy_current"))
            and integer(s["level"],1) and integer(s["energy_maximum"],1)
            and isinstance(s["xp_required_display"],str)
            and bool(re.fullmatch(r"(?:[1-9]\d*|[1-9]\d*(?:\.\d+)?[KM])",s["xp_required_display"])))


def reign_registry(reigns):
    entries=[]
    for r in reigns:
        if not exact_keys(r,{"id","starts_at"}) or not nonblank(r["id"]):
            raise ValueError("Invalid reign registry entry")
        entries.append((instant(r["starts_at"]),r["id"]))
    if len({t for t,_ in entries}) != len(entries) or len({n for _,n in entries}) != len(entries):
        raise ValueError("Ambiguous reign registry")
    return sorted(entries)


def active_reign(entries, at):
    return next((name for start,name in reversed(entries) if start<=at),None)


def progression_regresses(previous, observed, previous_season):
    p,s=observed["permanent"],observed["seasonal"]
    if previous is not None:
        if p["stars"] < previous["stars"] or len(p["habits"]) < len(previous["habits"]):
            return True
        if any(a>b for a,b in zip(previous["habits"],p["habits"])):
            return True
    if previous_season is not None:
        if s["level"] < previous_season["level"]:
            return True
        if s["level"] == previous_season["level"] and s["xp_current"] < previous_season["xp_current"]:
            return True
    return False


def reconcile(events, approvals, reigns, *, as_of):
    """Replay a JSON ledger in observation-time order; never writes or edits inputs.

    Approvals maps exact event digests to trusted reviewer IDs. The caller must
    authenticate and protect that registry; this pure function cannot verify identity.
    Conflicts between admitted events quarantine all implicated observations.
    as_of is observation-time replay, not a historical transaction-time reconstruction.
    """
    cutoff=instant(as_of)
    registry=reign_registry(reigns)
    current=active_reign(registry,cutoff)
    unique={digest(e):e for e in events}
    admitted={}
    quarantine={}
    for key,e in sorted(unique.items()):
        if not valid(e):
            quarantine[key]="invalid_event"
            continue
        at=instant(e["observed_at"])
        if at>cutoff:
            continue
        reviewer=approvals.get(key)
        if not nonblank(reviewer):
            quarantine[key]="unapproved"
        elif reviewer == e["extractor_id"]:
            quarantine[key]="self_approval"
        elif active_reign(registry,at)!=e["reign_id"]:
            quarantine[key]="reign_mismatch"
        else:
            admitted[key]=e
    sources=defaultdict(list)
    for key,e in admitted.items():
        sources[e["source_sha256"]].append(key)
    for keys in sources.values():
        if len(keys)>1:
            for key in keys:
                quarantine[key]="source_conflict"
    simultaneous=defaultdict(list)
    for key,e in admitted.items():
        if key not in quarantine:
            simultaneous[(e["name"],instant(e["observed_at"]))].append(key)
    for keys in simultaneous.values():
        payloads={digest([admitted[k]["permanent"],admitted[k]["seasonal"]]) for k in keys}
        if len(payloads)>1:
            for key in keys:
                quarantine[key]="timestamp_conflict"
    permanent={}
    history={}
    accepted=[]
    for key,e in sorted(admitted.items(),key=lambda kv:(instant(kv[1]["observed_at"]),kv[0])):
        if key in quarantine:
            continue
        name,reign=e["name"],e["reign_id"]
        prior=history.get(reign,{}).get(name)
        if progression_regresses(permanent.get(name),e,prior):
            quarantine[key]="progression_regression"
            continue
        permanent[name]=copy.deepcopy(e["permanent"])
        history.setdefault(reign,{})[name]=copy.deepcopy(e["seasonal"])
        accepted.append(key)
    seasonal=copy.deepcopy(history.get(current,{}))
    # All formation inputs provided by this engine; commander/equipment dependencies remain external.
    basis=digest({"reign":current,"permanent":permanent,"seasonal":seasonal})
    return {"schema_version":1,"current_reign":current,"permanent":permanent,
            "seasonal":seasonal,"history":history,"accepted":accepted,
            "quarantine":[{"event":k,"reason":v} for k,v in sorted(quarantine.items())],
            "formation_basis":basis}


def formation_is_stale(stored_basis, state):
    return stored_basis is None or stored_basis != state["formation_basis"]


def stage_legacy(persistent,seasonal):
    """Preserve dated source records without inventing image digests, approvals or reign IDs."""
    p,s=persistent["updates"],seasonal["dragons"]
    pm,sm={x["name"]:x for x in p},{x["name"]:x for x in s}
    if len(pm)!=len(p) or len(sm)!=len(s) or pm.keys()!=sm.keys():
        raise ValueError("Legacy roster mismatch or duplicate name")
    if persistent.get("observed_date")!=seasonal.get("observed_date"):
        raise ValueError("Legacy observation date mismatch")
    profiles=[]
    for n in sorted(pm):
        x,y=copy.deepcopy(pm[n]),copy.deepcopy(sm[n])
        if any(k in x for k in ("level","xp","displayed_power","displayed_troop_capacity","energy")):
            raise ValueError("Seasonal field in legacy permanent record")
        profiles.append({"name":n,"permanent":x,"seasonal":y})
    return {"schema_version":1,"status":"migration_pending_verification",
            "observed_date":persistent.get("observed_date"),"reign_id":None,
            "source_document_digests":[digest(persistent),digest(seasonal)],
            "profiles":profiles,"events":[]}
