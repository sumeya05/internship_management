# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class InterviewSchedule(Document):
	"""Interview scheduling + evaluation logic.

	This Doctype already defines the schema (panel, evaluation table, scores,
	recommendation, HR decision fields). This implementation wires:
	- score aggregation (average_score)
	- recommendation derivation
	- evaluation metadata (evaluated_by, evaluation_date)
	- HR outcome mapping + decision_date
	- attendance tracking validation (No Show handling)
	"""

	# Expose constants for easy adjustment.
	_RECOMMENDATION_THRESHOLDS = [
		# (min_average_score, recommendation)
		(80, "Highly Recommended"),
		(60, "Recommended"),
		(40, "Reserve List"),
	]

	_OUTCOME_BY_RECOMMENDATION = {
		"Highly Recommended": "Passed",
		"Recommended": "Passed",
		"Reserve List": "Awaiting Decision",
		"Not Recommended": "Failed",
	}

	_ALLOWED_INTERVIEW_STATUSES_FOR_EVALUATION = {
		"Evaluation Pending",
		"Completed",
	}

	def _compute_average_score(self) -> float | None:
		rows = self.get("interview_evaluation") or []
		total_awarded = 0
		total_max = 0
		for r in rows:
			max_scores = int(r.get("maximum_scores") or 0)
			awarded = int(r.get("score_awarded") or 0)
			total_awarded += awarded
			total_max += max_scores

		if total_max <= 0:
			return None

		# Score normalization: percentage-like average.
		return (total_awarded / total_max) * 100

	def _derive_recommendation(self, average_score: float | None) -> str | None:
		if average_score is None:
			return None

		for min_score, rec in self._RECOMMENDATION_THRESHOLDS:
			if average_score >= min_score:
				return rec
		return "Not Recommended"

	def _map_outcome(self, recommendation: str | None) -> str | None:
		if not recommendation:
			return None
		return self._OUTCOME_BY_RECOMMENDATION.get(recommendation)

	def _present_panel_count(self) -> int:
		panel_rows = self.get("interview_panel") or []
		present = 0
		for r in panel_rows:
			if int(r.get("present") or 0) == 1:
				present += 1
		return present

	def validate(self) -> None:
		# Attendance tracking: if HR marks evaluation outcome but no one was
		# present, we keep integrity by forcing No Show.
		# (Front-end may set interview_status; we add server-side safety.)
		if self.interview_status == "Completed":
			present_count = self._present_panel_count()
			if present_count == 0:
				self.interview_status = "No Show"

	def before_save(self) -> None:
		# Compute evaluation-derived fields whenever evaluation rows change.
		avg = self._compute_average_score()
		self.average_score = avg

		rec = self._derive_recommendation(avg)
		if rec:
			self.recommendation = rec

		# If HR hasn't set a final outcome, keep outcome consistent with recommendation.
		# HR can still override by explicitly setting hr_decision/outcome.
		if getattr(self, "hr_decision", None):
			# hr_decision set -> outcome should be non-None.
			self.outcome = self._map_outcome(rec) or self.outcome
		elif not self.outcome:
			self.outcome = self._map_outcome(rec)

	def on_update(self) -> None:
		# When evaluation is being filled, set evaluated_by and evaluation_date.
		rows = self.get("interview_evaluation") or []
		if not rows:
			return

		# Consider evaluated if any row has a score.
		scored = any(int(r.get("score_awarded") or 0) > 0 for r in rows)
		if not scored:
			return

		if self.interview_status in self._ALLOWED_INTERVIEW_STATUSES_FOR_EVALUATION:
			self.evaluated_by = frappe.session.user
			self.evaluation_date = now_datetime()

	def set_hr_decision(self, *, decision: str, final_remarks: str | None = None) -> None:
		"""HR helper to set HR decision + outcome.

		decision is expected to be one of:
		- Successful
		- Unsuccessful
		- Reserve
		- Pending Decision

		It updates:
		- hr_decision
		- outcome (Passed/Failed/Awaiting Decision)
		- decision_date
		- final_remarks (optional)
		"""

		if decision not in ("Successful", "Unsuccessful", "Reserve", "Pending Decision"):
			raise frappe.ValidationError("Invalid HR decision")

		self.hr_decision = frappe.session.user
		self.decision_date = frappe.utils.nowdate()
		if final_remarks:
			self.final_remarks = final_remarks

		mapping = {
			"Successful": "Passed",
			"Unsuccessful": "Failed",
			"Reserve": "Awaiting Decision",
			"Pending Decision": "Awaiting Decision",
		}
		self.outcome = mapping[decision]

		# If HR decided, interviewer evaluation should be treated as completed.
		if self.interview_status in ("Evaluation Pending", "Scheduled", "Rescheduled"):
			self.interview_status = "Completed"

