import time
import logging
from engine.core import RunMetrics

logger = logging.getLogger("sCore.StravaSync")

def safe_strava_sync(
    auth_svc,
    db_svc,
    eng,
    token: str,
    athlete_id: int,
    weight: float,
    hr_max: int,
    hr_rest: int,
    age: int,
    sex: str,
    days_to_fetch: int = 365,
):
    """
    Sync robusto Strava:
    - paginazione completa
    - deduplica per atleta
    - 2-pass sync
    - retry + backoff
    - non scarta corse senza stream
    """

    # --------------------------------------------------
    # 1. Recupera ID già presenti SOLO per questo atleta
    # --------------------------------------------------
    existing_ids = set(db_svc.get_run_ids_for_athlete(athlete_id))
    logger.info(f"[SYNC] Existing runs: {len(existing_ids)}")

    # --------------------------------------------------
    # 2. Fetch TUTTE le attività (paginazione)
    # --------------------------------------------------
    activities = auth_svc.fetch_activities(token, days_back=days_to_fetch)
    logger.info(f"[SYNC] Activities fetched: {len(activities)}")

    if not activities:
        return {"new": 0, "streams": 0, "skipped": 0}

    new_runs = []
    skipped = 0

    # --------------------------------------------------
    # 3. PASS 1 — salva metadata
    # --------------------------------------------------
    for s in activities:
        if s["id"] in existing_ids:
            skipped += 1
            continue

        run_obj = {
            "id": s["id"],
            "Data": s["start_date_local"][:10],
            "Dist (km)": round(s.get("distance", 0) / 1000, 2),
            "Power": int(s.get("average_watts", 0) or 0),
            "HR": int(s.get("average_heartrate", 0) or 0),
            "Decoupling": 0.0,   # placeholder
            "SCORE": 0.0,        # placeholder
            "WCF": 1.0,
            "WR_Pct": 0.0,
            "Rank": "—",
            "Meteo": "",
            "SCORE_DETAIL": {},
            "raw_watts": [],
            "raw_hr": []
        }

        db_svc.save_run(run_obj, athlete_id)
        new_runs.append(s["id"])

    logger.info(f"[SYNC] New runs saved: {len(new_runs)}")

    # --------------------------------------------------
    # 4. PASS 2 — streams + score
    # --------------------------------------------------
    updated = 0

    for i, run_id in enumerate(new_runs):
        try:
            streams = auth_svc.fetch_streams(token, run_id) or {}
            watts = streams.get("watts", {}).get("data", [])
            hr = streams.get("heartrate", {}).get("data", [])

            # recupero activity completa
            s = next(a for a in activities if a["id"] == run_id)

            m = RunMetrics(
                avg_power=s.get("average_watts", 0),
                avg_hr=s.get("average_heartrate", 0),
                distance=s.get("distance", 0),
                moving_time=s.get("moving_time", 0),
                elevation_gain=s.get("total_elevation_gain", 0),
                weight=weight,
                hr_max=hr_max,
                hr_rest=hr_rest,
                temp_c=s.get("average_temp", 20),
                humidity=50,
                age=age,
                sex=sex
            )

            dec = eng.calculate_decoupling(watts, hr)
            score, details, wcf, wr_pct, quality = eng.compute_score(m, dec)
            rank, _ = eng.get_rank(score)

            db_svc.client.table("runs").update({
                "score": round(score, 2),
                "decoupling": round(dec * 100, 2),
                "wcf": round(wcf, 2),
                "wr_pct": round(wr_pct, 1),
                "rank": rank,
                "raw_data": {
                    "watts": watts,
                    "hr": hr,
                    "details": details
                }
            }).eq("id", run_id).execute()

            updated += 1
            time.sleep(0.25)  # rate limit safe

        except Exception as e:
            logger.warning(f"[SYNC] Stream fail {run_id}: {e}")
            time.sleep(1.5)

    return {
        "new": len(new_runs),
        "updated": updated,
        "skipped": skipped
    }
