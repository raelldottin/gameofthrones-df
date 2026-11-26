"""Real SQLite ledger contracts; test credentials only."""
import copy
import json
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from scripts.dragon_analyzer.ledger import Ledger, LedgerError, seal, GENESIS
from scripts.dragon_analyzer.reconcile import digest, formation_is_stale

KEYS={"reader":("extractor",b"r"*32),"reviewer":("reviewer",b"v"*32),
      "operator":("operator",b"o"*32)}
ID="test-ledger"
JAN="2026-01-15T00:00:00Z"
FEB="2026-02-02T00:00:00Z"
NOW="2026-02-10T00:00:00Z"

def event(name="Jagadrix",stars=5,level=22,reign="r1",at=JAN,source="one"):
    return dict(
        source_sha256=digest(source),observed_at=at,reign_id=reign,name=name,extractor_id="reader",
        permanent=dict(stars=stars,relics_current=50,relics_required=500,habits=[1]*(stars//2)),
        seasonal=dict(level=level,xp_current=10,xp_required_display="165",power=100,
                      capacity=200,energy_current=250,energy_maximum=100))

def command(head,kind,actor,payload,ledger_id=ID):
    return dict(ledger_id=ledger_id,previous=head,kind=kind,actor=actor,payload=payload)

def add(l,kind,actor,payload):
    c=command(l.head(),kind,actor,payload)
    return l.append(c,seal(c,KEYS[actor][1]))

def open_ledger(path):
    return Ledger(path,ID,KEYS)

def setup(l):
    add(l,"reign","operator",{"id":"r1","starts_at":"2026-01-01T00:00:00Z"})
    return event()

def approve(l,e):
    add(l,"observe","reader",e)
    return add(l,"approve","reviewer",{"event":digest(e)})

def test_unapproved_observation_not_promoted(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        e=setup(l)
        add(l,"observe","reader",e)
        assert l.snapshot(as_of=NOW)["permanent"]=={}
        assert l.snapshot(as_of=NOW)["quarantine"][0]["reason"]=="unapproved"

def test_durable_approval_reign_reset_and_transaction_history(tmp_path):
    path=tmp_path/"db"
    with open_ledger(path) as l:
        e=setup(l); approve(l,e)
        before=l.head()
        add(l,"reign","operator",{"id":"r2","starts_at":"2026-02-01T00:00:00Z"})
        current=l.head()
    with open_ledger(path) as l:
        old=l.snapshot(as_of=NOW,at_head=before)
        new=l.snapshot(as_of=NOW)
        assert old["seasonal"]["Jagadrix"]["level"]==22
        assert new["seasonal"]=={} and new["permanent"]==old["permanent"]
        assert formation_is_stale(old["formation_basis"],new)
        assert l.head()==current
        assert new["history"]["r1"]["Jagadrix"]["level"]==22

def test_new_reign_lower_level_preserves_stars(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        approve(l,setup(l))
        add(l,"reign","operator",{"id":"r2","starts_at":"2026-02-01T00:00:00Z"})
        approve(l,event(stars=6,level=1,reign="r2",at=FEB,source="two"))
        state=l.snapshot(as_of=NOW)
        assert state["permanent"]["Jagadrix"]["stars"]==6
        assert state["seasonal"]["Jagadrix"]["level"]==1

def test_forged_signature_rejected(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        c=command(GENESIS,"reign","operator",{"id":"r1","starts_at":JAN})
        with pytest.raises(LedgerError,match="signature"): l.append(c,"0"*64)
        assert l.head()==GENESIS

def test_role_separation(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        e=setup(l);add(l,"observe","reader",e)
        with pytest.raises(LedgerError,match="role"):
            add(l,"approve","reader",{"event":digest(e)})
        assert l.snapshot(as_of=NOW)["permanent"]=={}

def test_extractor_cannot_impersonate(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        e=setup(l);e["extractor_id"]="other"
        with pytest.raises(LedgerError,match="extractor"):
            add(l,"observe","reader",e)

def test_cross_ledger_replay_rejected(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        c=command(GENESIS,"reign","operator",{"id":"r1","starts_at":JAN},"other-ledger")
        with pytest.raises(LedgerError,match="ledger"): l.append(c,seal(c,KEYS["operator"][1]))

def test_exact_retry_idempotent_stale_new_command_rejected(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        c=command(GENESIS,"reign","operator",{"id":"r1","starts_at":JAN})
        s=seal(c,KEYS["operator"][1]);h=l.append(c,s)
        assert l.append(c,s)==h and l.head()==h
        d=command(GENESIS,"reign","operator",{"id":"r2","starts_at":FEB})
        with pytest.raises(LedgerError,match="stale"):l.append(d,seal(d,KEYS["operator"][1]))

def test_revoke_preserves_transaction_history_and_is_terminal(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        e=setup(l);approve(l,e);before=l.head()
        add(l,"revoke","reviewer",{"event":digest(e),"reason":"incorrect read"})
        assert l.snapshot(as_of=NOW)["permanent"]=={}
        assert l.snapshot(as_of=NOW,at_head=before)["permanent"]["Jagadrix"]["stars"]==5
        with pytest.raises(LedgerError,match="terminal"):
            add(l,"approve","reviewer",{"event":digest(e)})

def test_correction_atomic_same_source_replaces_old_approval(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        a=setup(l);approve(l,a);before=l.head()
        b=event(stars=4,level=21);add(l,"observe","reader",b)
        add(l,"correct","reviewer",{"old":digest(a),"new":digest(b),"reason":"digit correction"})
        out=l.snapshot(as_of=NOW)
        assert out["permanent"]["Jagadrix"]["stars"]==4
        assert out["seasonal"]["Jagadrix"]["level"]==21
        assert out["accepted"]==[digest(b)]
        assert l.snapshot(as_of=NOW,at_head=before)["permanent"]["Jagadrix"]["stars"]==5

def test_correction_cannot_change_source(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        a=setup(l);approve(l,a);b=event(stars=4,source="other")
        add(l,"observe","reader",b);head=l.head()
        with pytest.raises(LedgerError,match="identity"):
            add(l,"correct","reviewer",{"old":digest(a),"new":digest(b),"reason":"wrong source"})
        assert l.head()==head

def test_same_source_conflicting_approved_events_quarantine(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        a=setup(l);approve(l,a);b=event(stars=4);approve(l,b)
        assert l.snapshot(as_of=NOW)["permanent"]=={}
        assert {x["reason"] for x in l.snapshot(as_of=NOW)["quarantine"]}=={"source_conflict"}

def test_duplicate_observation_rejected_without_extra_event(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        e=setup(l);add(l,"observe","reader",e);head=l.head()
        with pytest.raises(LedgerError,match="duplicate"):
            add(l,"observe","reader",e)
        assert l.head()==head

def test_concurrent_head_compare_and_swap(tmp_path):
    path=tmp_path/"db"
    with open_ledger(path): pass
    def attempt(i):
        c=command(GENESIS,"reign","operator",{"id":"r"+str(i),"starts_at":JAN})
        with open_ledger(path) as l:
            try:l.append(c,seal(c,KEYS["operator"][1]));return "accepted"
            except LedgerError:return "rejected"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt,[1,2]))==["accepted","rejected"]

def test_tampered_payload_rejected(tmp_path):
    path=tmp_path/"db"
    with open_ledger(path) as l: setup(l)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE entries SET payload=? WHERE seq=1",("{}",))
    with pytest.raises(LedgerError):
        with open_ledger(path) as l: l.snapshot(as_of=NOW)

def test_tail_truncation_detected_by_external_checkpoint(tmp_path):
    path=tmp_path/"db"
    with open_ledger(path) as l:
        approve(l,setup(l));head=l.head()
    with sqlite3.connect(path) as db: db.execute("DELETE FROM entries WHERE seq=3")
    with open_ledger(path) as l:
        with pytest.raises(LedgerError,match="checkpoint"): l.verify(expected_head=head)

def test_backup_restore_preserves_head_and_state(tmp_path):
    path=tmp_path/"db";backup=tmp_path/"backup"
    with open_ledger(path) as l:
        approve(l,setup(l));head=l.head();state=l.snapshot(as_of=NOW)
        l.backup(backup)
        with pytest.raises(FileExistsError):l.backup(backup)
    with open_ledger(backup) as l:
        assert l.verify(expected_head=head)==head
        assert l.snapshot(as_of=NOW)==state

def test_actual_legacy_staged_not_promoted(tmp_path):
    root=Path(__file__).resolve().parents[1]
    p=json.loads((root/"player-state/dragon-update-2026-11-26.json").read_text())
    s=json.loads((root/"player-state/dragon-reign-snapshot-2026-11-26.json").read_text())
    with open_ledger(tmp_path/"db") as l:
        add(l,"stage_legacy","operator",{"persistent":p,"seasonal":s})
        assert len(l.staged()[0]["profiles"])==38
        assert l.snapshot(as_of=NOW)["permanent"]=={}
        assert l.snapshot(as_of=NOW)["current_reign"] is None

def test_unknown_historical_head_rejected(tmp_path):
    with open_ledger(tmp_path/"db") as l:
        with pytest.raises(LedgerError,match="historical"):
            l.snapshot(as_of=NOW,at_head="f"*64)
