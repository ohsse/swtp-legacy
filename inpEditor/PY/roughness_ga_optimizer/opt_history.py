from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Optional

from db import DbManager


logger = logging.getLogger(__name__)


class OptimizationHistoryUpdater:
    """Update inp_file_opt_h for a Java-created optimization hist_id."""

    def __init__(self, db: DbManager, hist_id: Optional[int | str]):
        self.db = db
        self.hist_id = hist_id
        self.enabled = hist_id is not None and str(hist_id).strip() != ""
        self._disabled_reason_logged = False

    def mark_running(self, run_id: str, total_generation: int) -> None:
        self._safe_update(
            """
            UPDATE inp_file_opt_h
            SET status_cd = 'RUNNING',
                tot_gener_count = %s,
                impl_gener_count = 0,
                error_text = NULL,
                strt_dttm = NOW(6),
                end_dttm = NULL
            WHERE hist_id = %s
            """,
            (total_generation, self.hist_id),
            action="mark_running",
        )
        logger.info("opt_history_running hist_id=%s run_id=%s", self.hist_id, run_id)

    def update_generation(
        self,
        generation: int,
        total_generation: int,
        best_rmse: float,
        best_r2: float,
        best_corr_r2: float,
    ) -> None:
        del best_rmse, best_r2, best_corr_r2
        self._safe_update(
            """
            UPDATE inp_file_opt_h
            SET impl_gener_count = %s,
                tot_gener_count = %s
            WHERE hist_id = %s
            """,
            (generation, total_generation, self.hist_id),
            action="update_generation",
        )

    def mark_complete(
        self,
        rev_no: Optional[int],
        prev_result_snap: Any,
        result_snap: Any,
    ) -> None:
        self._safe_update(
            """
            UPDATE inp_file_opt_h
            SET status_cd = 'COMPLETED',
                rev_no = %s,
                prev_result_snap = %s,
                result_snap = %s,
                impl_gener_count = tot_gener_count,
                end_dttm = NOW(6),
                error_text = NULL
            WHERE hist_id = %s
            """,
            (
                rev_no,
                json.dumps(prev_result_snap, ensure_ascii=False, default=str, allow_nan=False),
                json.dumps(result_snap, ensure_ascii=False, default=str, allow_nan=False),
                self.hist_id,
            ),
            action="mark_complete",
        )
        logger.info("opt_history_complete hist_id=%s rev_no=%s", self.hist_id, rev_no)

    def mark_error(self, exc: BaseException) -> None:
        error_text = f"{exc}\n\n{traceback.format_exc()}"[:12000]
        self._safe_update(
            """
            UPDATE inp_file_opt_h
            SET status_cd = 'ERROR',
                error_text = %s,
                end_dttm = NOW(6)
            WHERE hist_id = %s
            """,
            (error_text, self.hist_id),
            action="mark_error",
        )
        logger.info("opt_history_error hist_id=%s error=%s", self.hist_id, exc)

    def _safe_update(self, sql: str, params: tuple[Any, ...], action: str) -> None:
        if not self.enabled:
            return

        try:
            affected = self.db.execute(sql, params)
            self.db.commit()
            if affected == 0:
                logger.warning(
                    "opt_history_update_no_rows action=%s hist_id=%s",
                    action,
                    self.hist_id,
                )
        except Exception as exc:
            if not self._disabled_reason_logged:
                logger.warning(
                    "opt_history_update_failed action=%s hist_id=%s error=%s",
                    action,
                    self.hist_id,
                    exc,
                )
                self._disabled_reason_logged = True
            self.enabled = False
