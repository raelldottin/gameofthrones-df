"""Signed append-only local ledger; external key custody and checkpoints required."""
from contextlib import closing
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3

from .reconcile import digest, instant, nonblank, valid, reign_registry, reconcile, stage_legacy

GENESIS="0"*64
ROLES={"reign":"operator","observe":"extractor","approve":"reviewer",
       "revoke":"reviewer","correct":"reviewer","stage_legacy":"operator"}
FIELDS={"ledger_id","previous","kind","actor","payload"}
MAX_BYTES=2_000_000


class LedgerError(ValueError):
    pass


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)


def seal(command,key):
    if not isinstance(key,bytes) or len(key)<32:
        raise ValueError("invalid signing key")
    body=canonical(command).encode()
    if len(body)>MAX_BYTES:
        raise LedgerError("oversized command")
    return hmac.new(key,b"dragonfire-ledger-v1\0"+body,hashlib.sha256).hexdigest()


def fresh():
    return {"events":{},"approvals":{},"revoked":set(),"reigns":[],"staged":[]}


def apply(state,c):
    p=c["payload"];kind=c["kind"];actor=c["actor"]
    if not isinstance(p,dict):
        raise LedgerError("invalid payload")
    events=state["events"];approved=state["approvals"];revoked=state["revoked"]
    if kind=="reign":
        proposed=state["reigns"]+[p]
        reign_registry(proposed)
        if state["reigns"] and instant(p["starts_at"])<=instant(state["reigns"][-1]["starts_at"]):
            raise LedgerError("reign must advance chronologically")
        state["reigns"]=proposed
    elif kind=="observe":
        if not valid(p):
            raise LedgerError("invalid observation")
        if p["extractor_id"]!=actor:
            raise LedgerError("extractor identity mismatch")
        key=digest(p)
        if key in events:
            raise LedgerError("duplicate observation")
        events[key]=p
    elif kind=="approve":
        if set(p)!={"event"} or not isinstance(p["event"],str) or p["event"] not in events:
            raise LedgerError("unknown observation")
        key=p["event"]
        if key in revoked:
            raise LedgerError("terminal revocation")
        if events[key]["extractor_id"]==actor or key in approved:
            raise LedgerError("duplicate or self approval")
        approved[key]=actor
    elif kind=="revoke":
        if set(p)!={"event","reason"} or not isinstance(p["event"],str) or p["event"] not in approved or not nonblank(p["reason"]):
            raise LedgerError("invalid revocation")
        if events[p["event"]]["extractor_id"]==actor:
            raise LedgerError("self revocation")
        approved.pop(p["event"])
        revoked.add(p["event"])
    elif kind=="correct":
        if (set(p)!={"old","new","reason"} or not nonblank(p["reason"])
                or not all(isinstance(p[k],str) for k in ("old","new"))
                or p["old"] not in approved or p["new"] not in events
                or p["new"] in approved or p["new"] in revoked):
            raise LedgerError("invalid correction")
        old,new=events[p["old"]],events[p["new"]]
        if any(old[k]!=new[k] for k in ("name","source_sha256","reign_id","observed_at")):
            raise LedgerError("correction identity mismatch")
        if actor in (old["extractor_id"],new["extractor_id"]):
            raise LedgerError("self correction")
        approved.pop(p["old"])
        revoked.add(p["old"])
        approved[p["new"]]=actor
    elif kind=="stage_legacy":
        if set(p)!={"persistent","seasonal"}:
            raise LedgerError("invalid migration payload")
        staged=stage_legacy(p["persistent"],p["seasonal"])
        if staged in state["staged"]:
            raise LedgerError("duplicate migration")
        state["staged"].append(staged)


class Ledger:
    """SQLite journal with full authenticated replay; no canonical file writes.

    Fixed per-ledger role/key registry is supplied by trusted operator. Historical
    key rotation, remote replication, encryption, and external checkpoint custody
    are deployment responsibilities, not implemented here.
    """
    def __init__(self,path,ledger_id,keys):
        if not nonblank(ledger_id) or not isinstance(keys,dict) or not keys:
            raise ValueError("invalid ledger identity or key registry")
        if any(not nonblank(actor) or not isinstance(item,tuple) or len(item)!=2
               or item[0] not in set(ROLES.values()) or not isinstance(item[1],bytes)
               or len(item[1])<32 for actor,item in keys.items()):
            raise ValueError("invalid role or key")
        if len({item[1] for item in keys.values()})!=len(keys):
            raise ValueError("distinct actors require distinct keys")
        self.id=ledger_id
        self.keys=dict(keys)
        self.db=sqlite3.connect(Path(path),isolation_level=None,timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS ledger_identity(slot INTEGER PRIMARY KEY CHECK(slot=1), id TEXT NOT NULL)")
        self.db.execute("INSERT OR IGNORE INTO ledger_identity VALUES(1,?)",(self.id,))
        if self.db.execute("SELECT id FROM ledger_identity WHERE slot=1").fetchone()!=(self.id,):
            self.db.close()
            raise LedgerError("ledger identity mismatch")
        self.db.execute("""CREATE TABLE IF NOT EXISTS entries(
            seq INTEGER PRIMARY KEY, hash TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL, signature TEXT NOT NULL)""")

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.db.close()

    def authenticate(self,c,signature):
        if not isinstance(c,dict) or set(c)!=FIELDS or c["ledger_id"]!=self.id:
            raise LedgerError("invalid ledger command")
        if not isinstance(c["actor"],str) or not isinstance(c["kind"],str):
            raise LedgerError("invalid actor or command")
        actor=self.keys.get(c["actor"])
        if actor is None or ROLES.get(c["kind"])!=actor[0]:
            raise LedgerError("invalid actor role")
        if not isinstance(signature,str) or not hmac.compare_digest(seal(c,actor[1]),signature):
            raise LedgerError("invalid signature")

    def _replay(self,at_head=None):
        state=fresh();head=GENESIS
        rows=self.db.execute("SELECT seq,hash,payload,signature FROM entries ORDER BY seq").fetchall()
        selected=fresh() if at_head==GENESIS else None
        for expected,(seq,key,body,sig) in enumerate(rows,1):
            try:
                c=json.loads(body)
                self.authenticate(c,sig)
                if seq!=expected or c["previous"]!=head or digest(c)!=key:
                    raise LedgerError("broken journal chain")
                apply(state,c)
                head=key
                if head==at_head:
                    # Replay a separate immutable copy at the selected transaction boundary.
                    import copy
                    selected=copy.deepcopy(state)
            except (ValueError,TypeError,KeyError,OverflowError) as exc:
                raise LedgerError("journal integrity failure at sequence "+str(seq)) from exc
        if at_head is not None and selected is None:
            raise LedgerError("unknown historical head")
        return head,state if at_head is None else selected

    def head(self):
        return self._replay()[0]

    def verify(self,expected_head=None):
        if self.db.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:
            raise LedgerError("SQLite integrity failure")
        head=self.head()
        if expected_head is not None and head!=expected_head:
            raise LedgerError("external checkpoint mismatch")
        return head

    def append(self,c,signature):
        self.authenticate(c,signature)
        key=digest(c)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            head,state=self._replay()
            old=self.db.execute("SELECT payload,signature FROM entries WHERE hash=?",(key,)).fetchone()
            if old is not None:
                if old!=(canonical(c),signature):
                    raise LedgerError("conflicting replay")
                self.db.execute("COMMIT")
                return key
            if c["previous"]!=head:
                raise LedgerError("stale transaction head")
            apply(state,c)
            self.db.execute("INSERT INTO entries(hash,payload,signature) VALUES(?,?,?)",
                            (key,canonical(c),signature))
            self.db.execute("COMMIT")
            return key
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def snapshot(self,*,as_of,at_head=None):
        _,state=self._replay(at_head)
        # Revoked observations remain in journal, but cannot poison the active projection.
        events=[v for k,v in state["events"].items() if k not in state["revoked"]]
        return reconcile(events,state["approvals"],state["reigns"],as_of=as_of)

    def staged(self):
        return self._replay()[1]["staged"]

    def backup(self,destination,*,expected_head=None):
        """Exclusive destination, consistent SQLite backup, authenticated replay check."""
        path=Path(destination)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.close(fd)
        try:
            with closing(sqlite3.connect(path)) as dest:
                self.db.backup(dest)
            with Ledger(path,self.id,self.keys) as restored:
                return restored.verify(expected_head=expected_head)
        except Exception:
            path.unlink(missing_ok=True)
            raise
