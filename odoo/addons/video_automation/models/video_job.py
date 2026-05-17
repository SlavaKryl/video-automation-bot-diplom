from odoo import fields, models


class VideoJob(models.Model):
    _name = "video.job"
    _description = "Video Processing Job"

    name = fields.Char(required=True)
    source = fields.Char(default="telegram")
    external_ref = fields.Char(index=True)
    transcription = fields.Text()
    content_preview = fields.Text()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("published", "Published"),
            ("failed", "Failed"),
        ],
        default="draft",
        required=True,
    )
