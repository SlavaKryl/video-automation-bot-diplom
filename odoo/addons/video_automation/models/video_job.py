from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VideoJob(models.Model):
    _name = "video.job"
    _description = "Video Processing Job"
    _order = "create_date desc"

    name = fields.Char(required=True)
    source = fields.Char(default="telegram")
    external_ref = fields.Char(index=True)
    transcription = fields.Text()
    content_preview = fields.Text()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_approval", "Pending Approval"),
            ("approved", "Approved"),
            ("processing", "Processing"),
            ("published", "Published"),
            ("failed", "Failed"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    attempt_count = fields.Integer(default=0, readonly=True)
    max_retries = fields.Integer(default=3)
    last_error = fields.Text(readonly=True)
    approved_by_id = fields.Many2one("res.users", readonly=True)
    approved_at = fields.Datetime(readonly=True)

    asset_ids = fields.One2many("video.asset", "job_id", string="Assets")
    publication_ids = fields.One2many("video.publication", "job_id", string="Publications")

    def action_submit_for_approval(self):
        for rec in self:
            if rec.state not in ("draft", "failed"):
                raise UserError(_("Only draft or failed jobs can be submitted for approval."))
            rec.state = "pending_approval"

    def action_approve(self):
        for rec in self:
            if rec.state != "pending_approval":
                raise UserError(_("Only jobs pending approval can be approved."))
            rec.write(
                {
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approved_at": fields.Datetime.now(),
                    "last_error": False,
                }
            )

    def action_retry(self):
        for rec in self:
            if rec.state != "failed":
                raise UserError(_("Retry is available only for failed jobs."))
            if rec.attempt_count >= rec.max_retries:
                raise UserError(_("Retry limit reached for this job."))
            rec.write({"state": "approved", "last_error": False})

    def _process_job(self):
        self.ensure_one()
        self.write({"state": "processing", "attempt_count": self.attempt_count + 1})

        # MVP stub for background processing.
        should_fail = any(asset.state == "failed" for asset in self.asset_ids)
        if should_fail:
            self.write({"state": "failed", "last_error": _("Asset processing failed.")})
            return

        self.write({"state": "published", "last_error": False})

        for publication in self.publication_ids.filtered(lambda p: p.state in ("draft", "failed")):
            publication._process_publication()

    @api.model
    def cron_process_jobs(self, limit=20):
        jobs = self.search([("state", "=", "approved")], limit=limit)
        for job in jobs:
            if job.attempt_count >= job.max_retries:
                job.write({"state": "failed", "last_error": _("Retry limit reached.")})
                continue
            job._process_job()


class VideoAsset(models.Model):
    _name = "video.asset"
    _description = "Video Asset"

    job_id = fields.Many2one("video.job", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    asset_type = fields.Selection(
        [("video", "Video"), ("audio", "Audio"), ("subtitle", "Subtitle"), ("thumbnail", "Thumbnail")],
        required=True,
        default="video",
    )
    storage_uri = fields.Char(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("ready", "Ready"), ("failed", "Failed")],
        default="draft",
        required=True,
    )
    error_message = fields.Text()


class VideoPublication(models.Model):
    _name = "video.publication"
    _description = "Video Publication"

    job_id = fields.Many2one("video.job", required=True, ondelete="cascade", index=True)
    platform = fields.Selection(
        [
            ("telegram", "Telegram"),
            ("vk", "VK"),
            ("youtube", "YouTube"),
            ("rutube", "RuTube"),
            ("dzen", "Dzen"),
            ("max", "MAX"),
        ],
        required=True,
        default="telegram",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("queued", "Queued"), ("published", "Published"), ("failed", "Failed")],
        default="draft",
        required=True,
    )
    external_id = fields.Char()
    last_error = fields.Text()

    def _process_publication(self):
        for rec in self:
            rec.write({"state": "queued"})
            rec.write({"state": "published", "last_error": False})
