{
    "name": "Video Automation",
    "version": "17.0.2.0.0",
    "summary": "Video processing jobs, assets and publications",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/video_job_views.xml",
        "data/video_job_cron.xml",
    ],
    "installable": True,
    "application": True,
}
